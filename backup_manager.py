#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Otomatik Yedekleme Sistemi
Zamanlanmış yedekleme, otomatik temizleme ve kurtarma işlemleri
"""

import os
import shutil
import sqlite3
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import zipfile
import hashlib
import threading
import time
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

class ScheduledBackupManager(QObject):
    """Zamanlanmış yedekleme yöneticisi"""
    
    # Signals
    backup_completed = pyqtSignal(bool, str)  # success, message
    backup_started = pyqtSignal()
    
    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.logger = logging.getLogger(__name__)
        
        # Zamanlayıcı ayarları
        self.backup_time = "23:00"  # Varsayılan yedekleme saati
        self.backup_enabled = True
        self.last_backup_date = None
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_backup_schedule)
        self.timer.start(60000)  # Her dakika kontrol et
        
        self.logger.info("Scheduled backup manager initialized")
    
    def set_backup_time(self, time_str: str):
        """Yedekleme saatini ayarla (HH:MM formatında)"""
        try:
            # Saat formatını doğrula
            datetime.strptime(time_str, "%H:%M")
            self.backup_time = time_str
            self.logger.info(f"Backup time set to: {time_str}")
        except ValueError:
            self.logger.error(f"Invalid time format: {time_str}")
    
    def enable_scheduled_backup(self, enabled: bool):
        """Zamanlanmış yedeklemeyi aç/kapat"""
        self.backup_enabled = enabled
        self.logger.info(f"Scheduled backup {'enabled' if enabled else 'disabled'}")
    
    def check_backup_schedule(self):
        """Yedekleme zamanını kontrol et"""
        if not self.backup_enabled:
            return
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.date()
        
        # Yedekleme saati geldi mi?
        if current_time == self.backup_time:
            # Bugün zaten yedek alındı mı?
            if self.last_backup_date != current_date:
                self.logger.info("Scheduled backup time reached, starting backup...")
                self.start_scheduled_backup()
    
    def start_scheduled_backup(self):
        """Zamanlanmış yedeklemeyi başlat"""
        try:
            self.backup_started.emit()
            
            # Arka planda yedekleme yap
            def backup_thread():
                try:
                    success, message = self.backup_manager.create_backup(
                        compressed=True, 
                        include_metadata=True
                    )
                    
                    if success:
                        self.last_backup_date = datetime.now().date()
                        self.logger.info("Scheduled backup completed successfully")
                    else:
                        self.logger.error(f"Scheduled backup failed: {message}")
                    
                    self.backup_completed.emit(success, message)
                    
                except Exception as e:
                    error_msg = f"Scheduled backup error: {e}"
                    self.logger.error(error_msg)
                    self.backup_completed.emit(False, error_msg)
            
            # Thread'de çalıştır
            threading.Thread(target=backup_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduled backup: {e}")

class BackupManager:
    """Gelişmiş otomatik yedekleme yönetim sınıfı"""
    
    # Constants
    BACKUP_DIR = "backups"
    MAX_BACKUPS = 7  # 1 haftalık yedek (7 gün)
    BACKUP_EXTENSION = ".db"
    COMPRESSED_EXTENSION = ".zip"
    
    def __init__(self, db_path: str = "tezgah_takip_v2.db"):
        self.db_path = db_path
        self.backup_dir = Path(self.BACKUP_DIR)
        self.logger = logging.getLogger(__name__)
        
        # Yedek klasörünü oluştur
        self._ensure_backup_directory()
        
        # Zamanlanmış yedekleme yöneticisi
        self.scheduled_manager = None
    
    def _ensure_backup_directory(self):
        """Yedek klasörünü güvenli şekilde oluştur"""
        try:
            self.backup_dir.mkdir(exist_ok=True, mode=0o755)
            self.logger.info(f"Backup directory ensured: {self.backup_dir}")
        except OSError as e:
            self.logger.error(f"Failed to create backup directory: {e}")
            raise
    
    def _generate_backup_filename(self, compressed: bool = False) -> str:
        """Yedek dosya adı oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"tezgah_takip_backup_{timestamp}"
        
        if compressed:
            return f"{base_name}{self.COMPRESSED_EXTENSION}"
        else:
            return f"{base_name}{self.BACKUP_EXTENSION}"
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Dosya hash'i hesapla (bütünlük kontrolü için)"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Hash calculation error: {e}")
            return ""
    
    def create_backup(self, compressed: bool = True, include_metadata: bool = True) -> Tuple[bool, str]:
        """
        Veritabanı yedeği oluştur
        
        Args:
            compressed: Sıkıştırılmış yedek oluştur
            include_metadata: Metadata dosyası dahil et
            
        Returns:
            (success, message/filepath)
        """
        try:
            if not os.path.exists(self.db_path):
                return False, f"Veritabanı dosyası bulunamadı: {self.db_path}"
            
            # Yedek dosya adı
            backup_filename = self._generate_backup_filename(compressed)
            backup_path = self.backup_dir / backup_filename
            
            if compressed:
                # Sıkıştırılmış yedek
                success, message = self._create_compressed_backup(backup_path, include_metadata)
            else:
                # Basit kopya
                success, message = self._create_simple_backup(backup_path)
            
            if success:
                # Eski yedekleri temizle
                self._cleanup_old_backups()
                
                self.logger.info(f"Backup created successfully: {backup_path}")
                return True, str(backup_path)
            else:
                return False, message
                
        except Exception as e:
            error_msg = f"Yedekleme hatası: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _create_simple_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """Basit veritabanı kopyası oluştur"""
        try:
            # SQLite veritabanını güvenli şekilde kopyala
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Veritabanını kopyala
            source_conn.backup(backup_conn)
            
            # Bağlantıları kapat
            backup_conn.close()
            source_conn.close()
            
            return True, "Basit yedek oluşturuldu"
            
        except Exception as e:
            return False, f"Basit yedek hatası: {e}"
    
    def _create_compressed_backup(self, backup_path: Path, include_metadata: bool) -> Tuple[bool, str]:
        """Sıkıştırılmış yedek oluştur"""
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Veritabanı dosyasını ekle
                zipf.write(self.db_path, os.path.basename(self.db_path))
                
                if include_metadata:
                    # Metadata oluştur
                    metadata = self._create_backup_metadata()
                    
                    # Geçici metadata dosyası
                    metadata_path = self.backup_dir / "backup_metadata.json"
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
                    
                    # Metadata'yı zip'e ekle
                    zipf.write(metadata_path, "backup_metadata.json")
                    
                    # Geçici dosyayı sil
                    metadata_path.unlink()
                
                # Log dosyalarını ekle (varsa)
                log_dir = Path("logs")
                if log_dir.exists():
                    for log_file in log_dir.glob("*.log"):
                        if log_file.stat().st_size < 10 * 1024 * 1024:  # 10MB'dan küçükse
                            zipf.write(log_file, f"logs/{log_file.name}")
            
            return True, "Sıkıştırılmış yedek oluşturuldu"
            
        except Exception as e:
            return False, f"Sıkıştırılmış yedek hatası: {e}"
    
    def _create_backup_metadata(self) -> Dict:
        """Yedek metadata'sı oluştur"""
        try:
            # Veritabanı istatistikleri
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Güvenli tablo listesi - sadece bilinen tablolar
            ALLOWED_TABLES = ['tezgah', 'bakimlar', 'pil_degisimler', 'kullanici', 'ayar']
            
            # Tablo sayıları - SQL injection korumalı
            tables_info = {}
            
            for table in ALLOWED_TABLES:
                try:
                    # Güvenli parameterized query kullan
                    # SQLite'da tablo adları parameterize edilemez, bu yüzden whitelist kullanıyoruz
                    if table in ALLOWED_TABLES:  # Double check
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")  # Backtick ile escape
                        count = cursor.fetchone()[0]
                        tables_info[table] = count
                except sqlite3.Error as e:
                    self.logger.warning(f"Table {table} count failed: {e}")
                    tables_info[table] = 0
            
            # Veritabanı boyutu
            db_size = os.path.getsize(self.db_path)
            
            # Hash hesapla
            db_hash = self._calculate_file_hash(Path(self.db_path))
            
            conn.close()
            
            metadata = {
                "backup_info": {
                    "created_at": datetime.now(timezone.utc),
                    "version": "2.1.3",
                    "backup_type": "compressed",
                    "source_db": self.db_path
                },
                "database_info": {
                    "size_bytes": db_size,
                    "size_mb": round(db_size / (1024 * 1024), 2),
                    "hash_sha256": db_hash,
                    "tables": tables_info,
                    "total_records": sum(tables_info.values())
                },
                "system_info": {
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                    "platform": os.name,
                    "backup_tool": "TezgahTakip BackupManager v2.1.3"
                }
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Metadata creation error: {e}")
            return {
                "backup_info": {
                    "created_at": datetime.now(timezone.utc),
                    "version": "2.1.3",
                    "error": str(e)
                }
            }
    
    def restore_backup(self, backup_path: str, verify_integrity: bool = True) -> Tuple[bool, str]:
        """
        Yedekten geri yükle
        
        Args:
            backup_path: Yedek dosya yolu
            verify_integrity: Bütünlük kontrolü yap
            
        Returns:
            (success, message)
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, f"Yedek dosyası bulunamadı: {backup_path}"
            
            # Mevcut veritabanının yedeğini al
            current_backup = f"{self.db_path}.restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, current_backup)
            
            try:
                if backup_file.suffix == self.COMPRESSED_EXTENSION:
                    # Sıkıştırılmış yedekten geri yükle
                    success, message = self._restore_from_compressed(backup_file, verify_integrity)
                else:
                    # Basit yedekten geri yükle
                    success, message = self._restore_from_simple(backup_file, verify_integrity)
                
                if success:
                    # Eski yedek dosyasını sil
                    os.remove(current_backup)
                    self.logger.info(f"Database restored from: {backup_path}")
                    return True, "Veritabanı başarıyla geri yüklendi"
                else:
                    # Geri yükleme başarısızsa eski veritabanını geri getir
                    shutil.move(current_backup, self.db_path)
                    return False, f"Geri yükleme başarısız: {message}"
                    
            except Exception as e:
                # Hata durumunda eski veritabanını geri getir
                shutil.move(current_backup, self.db_path)
                raise e
                
        except Exception as e:
            error_msg = f"Geri yükleme hatası: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _restore_from_simple(self, backup_path: Path, verify_integrity: bool) -> Tuple[bool, str]:
        """Basit yedekten geri yükle"""
        try:
            if verify_integrity:
                # Veritabanı bütünlüğünü kontrol et
                if not self._verify_database_integrity(backup_path):
                    return False, "Yedek dosyası bozuk"
            
            # Dosyayı kopyala
            shutil.copy2(backup_path, self.db_path)
            
            return True, "Basit yedekten geri yüklendi"
            
        except Exception as e:
            return False, f"Basit geri yükleme hatası: {e}"
    
    def _restore_from_compressed(self, backup_path: Path, verify_integrity: bool) -> Tuple[bool, str]:
        """Sıkıştırılmış yedekten geri yükle"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Zip içeriğini kontrol et
                file_list = zipf.namelist()
                db_file = None
                
                for file_name in file_list:
                    if file_name.endswith('.db'):
                        db_file = file_name
                        break
                
                if not db_file:
                    return False, "Zip dosyasında veritabanı bulunamadı"
                
                # Geçici klasöre çıkart
                temp_dir = self.backup_dir / "temp_restore"
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    # Veritabanını çıkart
                    zipf.extract(db_file, temp_dir)
                    extracted_db = temp_dir / db_file
                    
                    if verify_integrity:
                        # Bütünlük kontrolü
                        if not self._verify_database_integrity(extracted_db):
                            return False, "Çıkarılan veritabanı bozuk"
                    
                    # Ana veritabanına kopyala
                    shutil.copy2(extracted_db, self.db_path)
                    
                    return True, "Sıkıştırılmış yedekten geri yüklendi"
                    
                finally:
                    # Geçici dosyaları temizle
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                        
        except Exception as e:
            return False, f"Sıkıştırılmış geri yükleme hatası: {e}"
    
    def _verify_database_integrity(self, db_path: Path) -> bool:
        """Veritabanı bütünlüğünü kontrol et"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            return result and result[0] == "ok"
            
        except Exception as e:
            self.logger.error(f"Integrity check error: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Mevcut yedekleri listele"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob(f"*{self.BACKUP_EXTENSION}"):
                backups.append(self._get_backup_info(backup_file))
            
            for backup_file in self.backup_dir.glob(f"*{self.COMPRESSED_EXTENSION}"):
                backups.append(self._get_backup_info(backup_file))
            
            # Tarihe göre sırala (en yeni önce)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"List backups error: {e}")
            return []
    
    def _get_backup_info(self, backup_path: Path) -> Dict:
        """Yedek dosyası bilgilerini al"""
        try:
            stat = backup_path.stat()
            
            info = {
                "filename": backup_path.name,
                "filepath": str(backup_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "type": "compressed" if backup_path.suffix == self.COMPRESSED_EXTENSION else "simple",
                "hash": self._calculate_file_hash(backup_path)
            }
            
            # Sıkıştırılmış dosyaysa metadata'yı oku
            if backup_path.suffix == self.COMPRESSED_EXTENSION:
                metadata = self._read_backup_metadata(backup_path)
                if metadata:
                    info["metadata"] = metadata
            
            return info
            
        except Exception as e:
            self.logger.error(f"Get backup info error: {e}")
            return {
                "filename": backup_path.name,
                "filepath": str(backup_path),
                "error": str(e)
            }
    
    def _read_backup_metadata(self, backup_path: Path) -> Optional[Dict]:
        """Yedek metadata'sını oku"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if "backup_metadata.json" in zipf.namelist():
                    with zipf.open("backup_metadata.json") as f:
                        return json.load(f)
            return None
            
        except Exception as e:
            self.logger.error(f"Read metadata error: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """Eski yedekleri temizle"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.MAX_BACKUPS:
                # En eski yedekleri sil
                old_backups = backups[self.MAX_BACKUPS:]
                
                for backup in old_backups:
                    try:
                        backup_path = Path(backup['filepath'])
                        if backup_path.exists():
                            backup_path.unlink()
                            self.logger.info(f"Old backup deleted: {backup_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete old backup: {e}")
                        
        except Exception as e:
            self.logger.error(f"Cleanup old backups error: {e}")
    
    def delete_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Yedek dosyasını sil"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, "Yedek dosyası bulunamadı"
            
            # Güvenlik kontrolü - sadece backup klasöründeki dosyalar
            if not str(backup_file.resolve()).startswith(str(self.backup_dir.resolve())):
                return False, "Güvenlik ihlali: Geçersiz dosya yolu"
            
            backup_file.unlink()
            self.logger.info(f"Backup deleted: {backup_path}")
            
            return True, "Yedek dosyası silindi"
            
        except Exception as e:
            error_msg = f"Yedek silme hatası: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def schedule_automatic_backup(self, interval_hours: int = 24) -> bool:
        """Otomatik yedekleme zamanla (basit implementasyon)"""
        try:
            # Bu fonksiyon gelecekte cron job veya Windows Task Scheduler ile entegre edilebilir
            # Şimdilik sadece log kaydı
            self.logger.info(f"Automatic backup scheduled every {interval_hours} hours")
            return True
            
        except Exception as e:
            self.logger.error(f"Schedule backup error: {e}")
            return False
    
    def get_backup_statistics(self) -> Dict:
        """Yedekleme istatistikleri"""
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    "total_backups": 0,
                    "total_size_mb": 0,
                    "oldest_backup": None,
                    "newest_backup": None,
                    "average_size_mb": 0
                }
            
            total_size = sum(b.get('size_bytes', 0) for b in backups)
            
            stats = {
                "total_backups": len(backups),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_backup": backups[-1]['created_at'] if backups else None,
                "newest_backup": backups[0]['created_at'] if backups else None,
                "average_size_mb": round((total_size / len(backups)) / (1024 * 1024), 2),
                "backup_types": {
                    "compressed": len([b for b in backups if b.get('type') == 'compressed']),
                    "simple": len([b for b in backups if b.get('type') == 'simple'])
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Get backup statistics error: {e}")
            return {"error": str(e)}

# Test fonksiyonu
def test_backup_manager():
    """Backup manager'ı test et"""
    print("🧪 Backup Manager Test Başlıyor...")
    
    try:
        # Test veritabanı oluştur
        test_db = "test_backup.db"
        
        import sqlite3
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES ('Test Data')")
        conn.commit()
        conn.close()
        
        # Backup manager oluştur
        backup_manager = BackupManager(test_db)
        
        # Yedek oluştur
        success, result = backup_manager.create_backup(compressed=True)
        print(f"Backup creation: {success} - {result}")
        
        # Yedekleri listele
        backups = backup_manager.list_backups()
        print(f"Total backups: {len(backups)}")
        
        # İstatistikler
        stats = backup_manager.get_backup_statistics()
        print(f"Backup statistics: {stats}")
        
        # Temizlik
        if os.path.exists(test_db):
            os.remove(test_db)
        
        print("✅ Backup Manager testi başarılı!")
        
    except Exception as e:
        print(f"❌ Backup Manager testi başarısız: {e}")

if __name__ == "__main__":
    test_backup_manager()
    
    def start_scheduled_backup(self, backup_time: str = "23:00"):
        """Zamanlanmış yedeklemeyi başlat"""
        try:
            if self.scheduled_manager is None:
                self.scheduled_manager = ScheduledBackupManager(self)
            
            self.scheduled_manager.set_backup_time(backup_time)
            self.scheduled_manager.enable_scheduled_backup(True)
            
            self.logger.info(f"Scheduled backup started for {backup_time}")
            return True, "Zamanlanmış yedekleme başlatıldı"
            
        except Exception as e:
            error_msg = f"Zamanlanmış yedekleme başlatılamadı: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def stop_scheduled_backup(self):
        """Zamanlanmış yedeklemeyi durdur"""
        try:
            if self.scheduled_manager:
                self.scheduled_manager.enable_scheduled_backup(False)
                self.logger.info("Scheduled backup stopped")
                return True, "Zamanlanmış yedekleme durduruldu"
            else:
                return False, "Zamanlanmış yedekleme zaten çalışmıyor"
                
        except Exception as e:
            error_msg = f"Zamanlanmış yedekleme durdurulamadı: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_backup_status(self) -> Dict[str, any]:
        """Yedekleme durumu bilgilerini al"""
        try:
            status = {
                'scheduled_enabled': False,
                'backup_time': '23:00',
                'last_backup_date': None,
                'total_backups': 0,
                'backup_size_mb': 0,
                'oldest_backup': None,
                'newest_backup': None
            }
            
            # Zamanlanmış yedekleme durumu
            if self.scheduled_manager:
                status['scheduled_enabled'] = self.scheduled_manager.backup_enabled
                status['backup_time'] = self.scheduled_manager.backup_time
                status['last_backup_date'] = self.scheduled_manager.last_backup_date
            
            # Yedek dosyalarını analiz et
            backup_files = self.list_backups()
            status['total_backups'] = len(backup_files)
            
            if backup_files:
                # Toplam boyut
                total_size = 0
                dates = []
                
                for backup_info in backup_files:
                    total_size += backup_info['size']
                    dates.append(backup_info['date'])
                
                status['backup_size_mb'] = round(total_size / (1024 * 1024), 2)
                status['oldest_backup'] = min(dates)
                status['newest_backup'] = max(dates)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Get backup status error: {e}")
            return {}
    
    def _cleanup_old_backups(self):
        """Eski yedekleri temizle (sadece 7 tanesini tut)"""
        try:
            backup_files = []
            
            # Tüm yedek dosyalarını bul
            for file_path in self.backup_dir.glob("tezgah_takip_backup_*"):
                if file_path.is_file():
                    backup_files.append({
                        'path': file_path,
                        'mtime': file_path.stat().st_mtime
                    })
            
            # Tarihe göre sırala (en yeni önce)
            backup_files.sort(key=lambda x: x['mtime'], reverse=True)
            
            # MAX_BACKUPS'tan fazlasını sil
            if len(backup_files) > self.MAX_BACKUPS:
                files_to_delete = backup_files[self.MAX_BACKUPS:]
                
                for file_info in files_to_delete:
                    try:
                        file_info['path'].unlink()
                        self.logger.info(f"Old backup deleted: {file_info['path'].name}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete old backup {file_info['path']}: {e}")
                
                self.logger.info(f"Cleaned up {len(files_to_delete)} old backup files")
            
        except Exception as e:
            self.logger.error(f"Cleanup old backups error: {e}")
    
    def get_backup_settings(self) -> Dict[str, any]:
        """Yedekleme ayarlarını al"""
        return {
            'backup_dir': str(self.backup_dir),
            'max_backups': self.MAX_BACKUPS,
            'db_path': self.db_path,
            'scheduled_enabled': self.scheduled_manager.backup_enabled if self.scheduled_manager else False,
            'backup_time': self.scheduled_manager.backup_time if self.scheduled_manager else '23:00'
        }
    
    def update_backup_settings(self, settings: Dict[str, any]) -> Tuple[bool, str]:
        """Yedekleme ayarlarını güncelle"""
        try:
            if 'backup_time' in settings and self.scheduled_manager:
                self.scheduled_manager.set_backup_time(settings['backup_time'])
            
            if 'scheduled_enabled' in settings and self.scheduled_manager:
                self.scheduled_manager.enable_scheduled_backup(settings['scheduled_enabled'])
            
            self.logger.info("Backup settings updated successfully")
            return True, "Yedekleme ayarları güncellendi"
            
        except Exception as e:
            error_msg = f"Yedekleme ayarları güncellenemedi: {e}"
            self.logger.error(error_msg)
            return False, error_msg

# Test fonksiyonu
def test_scheduled_backup():
    """Zamanlanmış yedekleme sistemini test et"""
    print("🧪 Zamanlanmış Yedekleme Test Başlıyor...")
    
    try:
        # Backup manager oluştur
        backup_manager = BackupManager()
        
        # Zamanlanmış yedeklemeyi başlat (test için 1 dakika sonra)
        from datetime import datetime, timedelta
        test_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
        
        success, message = backup_manager.start_scheduled_backup(test_time)
        print(f"Zamanlanmış yedekleme: {success} - {message}")
        
        # Durum bilgilerini göster
        status = backup_manager.get_backup_status()
        print(f"Yedekleme durumu: {status}")
        
        # Manuel yedek test
        success, message = backup_manager.create_backup()
        print(f"Manuel yedek: {success} - {message}")
        
        print("✅ Test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_scheduled_backup()