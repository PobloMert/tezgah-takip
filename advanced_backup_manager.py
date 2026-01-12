#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Otomatik Yedekleme Sistemi v2.0
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

class AdvancedBackupManager:
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
    
    def create_backup(self, compressed: bool = True, include_metadata: bool = True) -> Tuple[bool, str]:
        """Veritabanı yedeği oluştur"""
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
            
            return True, "Sıkıştırılmış yedek oluşturuldu"
            
        except Exception as e:
            return False, f"Sıkıştırılmış yedek hatası: {e}"
    
    def _create_backup_metadata(self) -> Dict:
        """Yedek metadata'sı oluştur"""
        try:
            # Veritabanı istatistikleri
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Güvenli tablo listesi
            ALLOWED_TABLES = ['tezgah', 'bakimlar', 'pil_degisimler', 'kullanici', 'ayar']
            
            # Tablo sayıları
            tables_info = {}
            
            for table in ALLOWED_TABLES:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = cursor.fetchone()[0]
                    tables_info[table] = count
                except sqlite3.Error as e:
                    self.logger.warning(f"Table {table} count failed: {e}")
                    tables_info[table] = 0
            
            # Veritabanı boyutu
            db_size = os.path.getsize(self.db_path)
            
            conn.close()
            
            metadata = {
                "backup_info": {
                    "created_at": datetime.now(timezone.utc),
                    "version": "2.0.0",
                    "backup_type": "compressed",
                    "source_db": self.db_path
                },
                "database_info": {
                    "size_bytes": db_size,
                    "size_mb": round(db_size / (1024 * 1024), 2),
                    "tables": tables_info,
                    "total_records": sum(tables_info.values())
                },
                "system_info": {
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                    "platform": os.name,
                    "backup_tool": "TezgahTakip AdvancedBackupManager v2.0"
                }
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Metadata creation error: {e}")
            return {
                "backup_info": {
                    "created_at": datetime.now(timezone.utc),
                    "version": "2.0.0",
                    "error": str(e)
                }
            }
    
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
    
    def list_backups(self) -> List[Dict]:
        """Mevcut yedekleri listele"""
        try:
            backups = []
            
            # Yedek dosyalarını bul
            for backup_file in self.backup_dir.glob("tezgah_takip_backup_*"):
                if backup_file.is_file():
                    backup_info = self._get_backup_info(backup_file)
                    backups.append(backup_info)
            
            # Tarihe göre sırala (en yeni önce)
            backups.sort(key=lambda x: x['date'], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"List backups error: {e}")
            return []
    
    def _get_backup_info(self, backup_path: Path) -> Dict:
        """Yedek dosyası bilgilerini al"""
        try:
            stat = backup_path.stat()
            
            return {
                'name': backup_path.name,
                'path': str(backup_path),
                'size': stat.st_size,
                'date': datetime.fromtimestamp(stat.st_mtime),
                'type': 'compressed' if backup_path.suffix == '.zip' else 'simple'
            }
            
        except Exception as e:
            self.logger.error(f"Get backup info error: {e}")
            return {
                'name': backup_path.name,
                'path': str(backup_path),
                'size': 0,
                'date': datetime.now(),
                'type': 'unknown'
            }
    
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
def test_advanced_backup():
    """Gelişmiş yedekleme sistemini test et"""
    print("🧪 Gelişmiş Yedekleme Test Başlıyor...")
    
    try:
        # Backup manager oluştur
        backup_manager = AdvancedBackupManager()
        
        # Manuel yedek test
        print("📦 Manuel yedek oluşturuluyor...")
        success, message = backup_manager.create_backup()
        print(f"Manuel yedek: {success} - {message}")
        
        # Zamanlanmış yedeklemeyi başlat
        print("⏰ Zamanlanmış yedekleme başlatılıyor...")
        success, message = backup_manager.start_scheduled_backup("23:00")
        print(f"Zamanlanmış yedekleme: {success} - {message}")
        
        # Durum bilgilerini göster
        print("📊 Yedekleme durumu:")
        status = backup_manager.get_backup_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("✅ Test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_advanced_backup()