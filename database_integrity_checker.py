#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Database Integrity Checker
Veritabanı bütünlük kontrolü ve onarım sistemi
"""

import os
import sqlite3
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from database_error_models import IntegrityCheckResult
from database_models import DatabaseManager

class DatabaseIntegrityChecker:
    """Veritabanı bütünlük kontrolü ve onarım sistemi"""
    
    def __init__(self, database_path: str, log_file_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.database_path = database_path
        self.backup_dir = Path("backups")
        self.log_file_path = log_file_path or "integrity_checks.log"
        
        # Yedek dizinini oluştur
        self._ensure_backup_directory()
        
        # Integrity check için özel logger oluştur
        self._setup_integrity_logger()
    
    def _ensure_backup_directory(self):
        """Yedek dizinini güvenli şekilde oluştur"""
        try:
            self.backup_dir.mkdir(exist_ok=True, mode=0o755)
            self.logger.debug(f"Backup directory ensured: {self.backup_dir}")
        except OSError as e:
            self.logger.warning(f"Failed to create backup directory: {e}")
    
    def _setup_integrity_logger(self):
        """Bütünlük kontrolü için özel logger oluştur"""
        try:
            # Integrity check için ayrı logger
            self.integrity_logger = logging.getLogger(f"{__name__}.integrity")
            
            # Eğer handler yoksa ekle
            if not self.integrity_logger.handlers:
                # Dosya handler
                file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                
                # Format
                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)
                
                self.integrity_logger.addHandler(file_handler)
                self.integrity_logger.setLevel(logging.INFO)
                
                # Ana logger'a da propagate et
                self.integrity_logger.propagate = True
                
            self.logger.debug(f"Integrity logger configured: {self.log_file_path}")
            
        except Exception as e:
            self.logger.warning(f"Integrity logger setup failed: {e}")
            # Fallback olarak ana logger kullan
            self.integrity_logger = self.logger
    
    def check_database_integrity(self, create_backup: bool = True) -> IntegrityCheckResult:
        """
        Veritabanı bütünlük kontrolü yap
        
        Args:
            create_backup: Kontrol öncesi yedek oluştur
            
        Returns:
            IntegrityCheckResult: Bütünlük kontrolü sonucu
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info(f"🔍 Veritabanı bütünlük kontrolü başlatılıyor: {self.database_path}")
        self.integrity_logger.info(f"=== BÜTÜNLÜK KONTROLÜ BAŞLADI ===")
        self.integrity_logger.info(f"Veritabanı: {self.database_path}")
        self.integrity_logger.info(f"Başlangıç zamanı: {start_time.isoformat()}")
        self.integrity_logger.info(f"Yedek oluştur: {create_backup}")
        
        try:
            # Dosya varlığını kontrol et
            if not os.path.exists(self.database_path):
                error_msg = "Veritabanı dosyası bulunamadı"
                self.integrity_logger.error(f"HATA: {error_msg}")
                self.integrity_logger.info(f"=== BÜTÜNLÜK KONTROLÜ BİTTİ (HATA) ===")
                
                return IntegrityCheckResult(
                    is_valid=False,
                    corruption_detected=False,
                    error_details=[error_msg],
                    repair_possible=False,
                    backup_recommended=False,
                    check_timestamp=start_time
                )
            
            # Dosya boyutu ve temel bilgileri logla
            file_size = os.path.getsize(self.database_path)
            self.integrity_logger.info(f"Dosya boyutu: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            
            # Yedek oluştur (istenirse)
            backup_path = None
            if create_backup:
                backup_start = datetime.now(timezone.utc)
                backup_path = self._create_integrity_backup()
                backup_duration = (datetime.now(timezone.utc) - backup_start).total_seconds()
                
                if backup_path:
                    self.logger.info(f"📁 Bütünlük kontrolü öncesi yedek oluşturuldu: {backup_path}")
                    self.integrity_logger.info(f"Yedek oluşturuldu: {backup_path} ({backup_duration:.2f}s)")
                else:
                    self.integrity_logger.warning("Yedek oluşturulamadı")
            
            # Bütünlük kontrolü yap
            integrity_errors = []
            corruption_detected = False
            
            # 1. SQLite PRAGMA integrity_check
            self.integrity_logger.info("1. SQLite PRAGMA integrity_check başlatılıyor...")
            pragma_start = datetime.now(timezone.utc)
            pragma_result = self._run_pragma_integrity_check()
            pragma_duration = (datetime.now(timezone.utc) - pragma_start).total_seconds()
            
            if not pragma_result['is_ok']:
                integrity_errors.extend(pragma_result['errors'])
                corruption_detected = True
                self.integrity_logger.error(f"PRAGMA integrity_check BAŞARISIZ ({pragma_duration:.2f}s): {len(pragma_result['errors'])} hata")
                for error in pragma_result['errors']:
                    self.integrity_logger.error(f"  - {error}")
            else:
                self.integrity_logger.info(f"PRAGMA integrity_check BAŞARILI ({pragma_duration:.2f}s)")
            
            # 2. Tablo yapısı kontrolü
            self.integrity_logger.info("2. Tablo yapısı kontrolü başlatılıyor...")
            schema_start = datetime.now(timezone.utc)
            schema_result = self._check_schema_integrity()
            schema_duration = (datetime.now(timezone.utc) - schema_start).total_seconds()
            
            if not schema_result['is_ok']:
                integrity_errors.extend(schema_result['errors'])
                self.integrity_logger.warning(f"Şema kontrolü UYARI ({schema_duration:.2f}s): {len(schema_result['errors'])} sorun")
                for error in schema_result['errors']:
                    self.integrity_logger.warning(f"  - {error}")
            else:
                self.integrity_logger.info(f"Şema kontrolü BAŞARILI ({schema_duration:.2f}s)")
            
            # 3. Veri tutarlılığı kontrolü
            self.integrity_logger.info("3. Veri tutarlılığı kontrolü başlatılıyor...")
            data_start = datetime.now(timezone.utc)
            data_result = self._check_data_consistency()
            data_duration = (datetime.now(timezone.utc) - data_start).total_seconds()
            
            if not data_result['is_ok']:
                integrity_errors.extend(data_result['errors'])
                self.integrity_logger.warning(f"Veri tutarlılığı UYARI ({data_duration:.2f}s): {len(data_result['errors'])} sorun")
                for error in data_result['errors']:
                    self.integrity_logger.warning(f"  - {error}")
            else:
                self.integrity_logger.info(f"Veri tutarlılığı BAŞARILI ({data_duration:.2f}s)")
            
            # 4. İndeks kontrolü
            self.integrity_logger.info("4. İndeks kontrolü başlatılıyor...")
            index_start = datetime.now(timezone.utc)
            index_result = self._check_index_integrity()
            index_duration = (datetime.now(timezone.utc) - index_start).total_seconds()
            
            if not index_result['is_ok']:
                integrity_errors.extend(index_result['errors'])
                self.integrity_logger.warning(f"İndeks kontrolü UYARI ({index_duration:.2f}s): {len(index_result['errors'])} sorun")
                for error in index_result['errors']:
                    self.integrity_logger.warning(f"  - {error}")
            else:
                self.integrity_logger.info(f"İndeks kontrolü BAŞARILI ({index_duration:.2f}s)")
            
            # 5. Dosya boyutu ve yapısı kontrolü
            self.integrity_logger.info("5. Dosya yapısı kontrolü başlatılıyor...")
            file_start = datetime.now(timezone.utc)
            file_result = self._check_file_structure()
            file_duration = (datetime.now(timezone.utc) - file_start).total_seconds()
            
            if not file_result['is_ok']:
                integrity_errors.extend(file_result['errors'])
                if file_result.get('corruption_detected'):
                    corruption_detected = True
                    self.integrity_logger.error(f"Dosya yapısı KRİTİK HATA ({file_duration:.2f}s): {len(file_result['errors'])} sorun")
                else:
                    self.integrity_logger.warning(f"Dosya yapısı UYARI ({file_duration:.2f}s): {len(file_result['errors'])} sorun")
                for error in file_result['errors']:
                    level = "ERROR" if file_result.get('corruption_detected') else "WARNING"
                    self.integrity_logger.log(logging.ERROR if level == "ERROR" else logging.WARNING, f"  - {error}")
            else:
                self.integrity_logger.info(f"Dosya yapısı BAŞARILI ({file_duration:.2f}s)")
            
            # Sonuç değerlendirmesi
            is_valid = len(integrity_errors) == 0
            # Tamamen bozuk dosyalar (header bozuk) onarılamaz
            file_corruption = any("Geçersiz SQLite dosya başlığı" in error or "file is not a database" in error 
                                for error in integrity_errors)
            repair_possible = not file_corruption and corruption_detected and len(integrity_errors) < 10
            backup_recommended = corruption_detected or len(integrity_errors) > 0
            
            # Toplam süre
            total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Sonuç loglama
            status = "SAĞLIKLI" if is_valid else "BOZUK" if corruption_detected else "UYARI"
            self.integrity_logger.info(f"=== SONUÇ ===")
            self.integrity_logger.info(f"Durum: {status}")
            self.integrity_logger.info(f"Geçerli: {is_valid}")
            self.integrity_logger.info(f"Bozulma tespit edildi: {corruption_detected}")
            self.integrity_logger.info(f"Toplam hata sayısı: {len(integrity_errors)}")
            self.integrity_logger.info(f"Onarım mümkün: {repair_possible}")
            self.integrity_logger.info(f"Yedek öneriliyor: {backup_recommended}")
            self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
            self.integrity_logger.info(f"Bitiş zamanı: {datetime.now(timezone.utc).isoformat()}")
            self.integrity_logger.info(f"=== BÜTÜNLÜK KONTROLÜ BİTTİ ===")
            
            self.logger.info(f"✅ Bütünlük kontrolü tamamlandı - Geçerli: {is_valid}, Hata sayısı: {len(integrity_errors)}")
            
            return IntegrityCheckResult(
                is_valid=is_valid,
                corruption_detected=corruption_detected,
                error_details=integrity_errors,
                repair_possible=repair_possible,
                backup_recommended=backup_recommended,
                check_timestamp=start_time
            )
            
        except Exception as e:
            error_msg = f"Bütünlük kontrolü hatası: {e}"
            total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            self.logger.error(f"❌ {error_msg}")
            self.integrity_logger.error(f"KRİTİK HATA: {error_msg}")
            self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
            self.integrity_logger.info(f"=== BÜTÜNLÜK KONTROLÜ BİTTİ (HATA) ===")
            
            return IntegrityCheckResult(
                is_valid=False,
                corruption_detected=True,
                error_details=[error_msg],
                repair_possible=False,
                backup_recommended=True,
                check_timestamp=start_time
            )
    
    def _run_pragma_integrity_check(self) -> Dict[str, Any]:
        """SQLite PRAGMA integrity_check çalıştır"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            results = cursor.fetchall()
            
            conn.close()
            
            # Sonuçları değerlendir
            if len(results) == 1 and results[0][0] == 'ok':
                return {'is_ok': True, 'errors': []}
            else:
                errors = [f"SQLite integrity check: {result[0]}" for result in results]
                return {'is_ok': False, 'errors': errors}
                
        except Exception as e:
            return {'is_ok': False, 'errors': [f"PRAGMA integrity_check hatası: {e}"]}
    
    def _check_schema_integrity(self) -> Dict[str, Any]:
        """Tablo şeması bütünlük kontrolü"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            errors = []
            
            # Temel tabloların varlığını kontrol et
            expected_tables = [
                'kullanicilar', 'tezgahlar', 'piller', 'bakimlar', 
                'ayarlar', 'loglar', 'yedekler'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in expected_tables:
                if table not in existing_tables:
                    errors.append(f"Eksik tablo: {table}")
            
            # Her tablo için temel sütunları kontrol et
            table_schemas = {
                'kullanicilar': ['id', 'kullanici_adi', 'ad_soyad', 'email'],
                'tezgahlar': ['id', 'numarasi', 'aciklama', 'durum'],
                'piller': ['id', 'tezgah_id', 'eksen', 'degisim_tarihi'],
                'bakimlar': ['id', 'tezgah_id', 'bakim_tarihi', 'aciklama'],
                'ayarlar': ['id', 'anahtar', 'deger'],
                'loglar': ['id', 'seviye', 'mesaj', 'tarih'],
                'yedekler': ['id', 'dosya_adi', 'tarih', 'boyut']
            }
            
            for table, required_columns in table_schemas.items():
                if table in existing_tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    for column in required_columns:
                        if column not in columns:
                            errors.append(f"Tablo {table} eksik sütun: {column}")
            
            conn.close()
            
            return {'is_ok': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            return {'is_ok': False, 'errors': [f"Şema kontrolü hatası: {e}"]}
    
    def _check_data_consistency(self) -> Dict[str, Any]:
        """Veri tutarlılığı kontrolü"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            errors = []
            
            # Foreign key kontrolü (eğer tablolar varsa)
            try:
                # Piller tablosunda geçersiz tezgah_id kontrolü
                cursor.execute("""
                    SELECT COUNT(*) FROM piller p 
                    LEFT JOIN tezgahlar t ON p.tezgah_id = t.id 
                    WHERE t.id IS NULL AND p.tezgah_id IS NOT NULL
                """)
                invalid_battery_refs = cursor.fetchone()[0]
                if invalid_battery_refs > 0:
                    errors.append(f"Geçersiz tezgah referansı olan {invalid_battery_refs} pil kaydı")
                
                # Bakımlar tablosunda geçersiz tezgah_id kontrolü
                cursor.execute("""
                    SELECT COUNT(*) FROM bakimlar b 
                    LEFT JOIN tezgahlar t ON b.tezgah_id = t.id 
                    WHERE t.id IS NULL AND b.tezgah_id IS NOT NULL
                """)
                invalid_maintenance_refs = cursor.fetchone()[0]
                if invalid_maintenance_refs > 0:
                    errors.append(f"Geçersiz tezgah referansı olan {invalid_maintenance_refs} bakım kaydı")
                
            except sqlite3.OperationalError:
                # Tablolar yoksa bu kontrolleri atla
                pass
            
            # Tarih tutarlılığı kontrolü
            try:
                # Gelecek tarihli bakım kayıtları (makul sınır)
                future_limit = datetime.now() + timedelta(days=365*2)  # 2 yıl sonrası
                cursor.execute("""
                    SELECT COUNT(*) FROM bakimlar 
                    WHERE bakim_tarihi > ?
                """, (future_limit,))
                future_maintenance = cursor.fetchone()[0]
                if future_maintenance > 0:
                    errors.append(f"{future_maintenance} bakım kaydı çok uzak gelecek tarihli")
                
            except (sqlite3.OperationalError, NameError):
                # Tarih sütunu yoksa veya datetime import edilmemişse atla
                pass
            
            # Duplicate kontrolü
            try:
                # Aynı kullanıcı adına sahip kullanıcılar
                cursor.execute("""
                    SELECT kullanici_adi, COUNT(*) 
                    FROM kullanicilar 
                    GROUP BY kullanici_adi 
                    HAVING COUNT(*) > 1
                """)
                duplicate_users = cursor.fetchall()
                for username, count in duplicate_users:
                    errors.append(f"Duplicate kullanıcı adı: {username} ({count} adet)")
                
            except sqlite3.OperationalError:
                # Tablo yoksa atla
                pass
            
            conn.close()
            
            return {'is_ok': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            return {'is_ok': False, 'errors': [f"Veri tutarlılığı kontrolü hatası: {e}"]}
    
    def _check_index_integrity(self) -> Dict[str, Any]:
        """İndeks bütünlük kontrolü"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            errors = []
            
            # İndeksleri kontrol et
            cursor.execute("PRAGMA integrity_check")
            # Bu zaten genel integrity check'te yapılıyor, burada ek kontroller
            
            # İndeks istatistiklerini güncelle ve kontrol et
            try:
                cursor.execute("ANALYZE")
                # Analiz başarılıysa indeksler çalışıyor demektir
            except Exception as e:
                errors.append(f"İndeks analizi hatası: {e}")
            
            conn.close()
            
            return {'is_ok': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            return {'is_ok': False, 'errors': [f"İndeks kontrolü hatası: {e}"]}
    
    def _check_file_structure(self) -> Dict[str, Any]:
        """Dosya yapısı kontrolü"""
        try:
            errors = []
            corruption_detected = False
            
            # Dosya boyutu kontrolü
            file_size = os.path.getsize(self.database_path)
            if file_size == 0:
                errors.append("Veritabanı dosyası boş")
                corruption_detected = True
            elif file_size < 1024:  # 1KB'den küçük
                errors.append("Veritabanı dosyası çok küçük (muhtemelen bozuk)")
                corruption_detected = True
            
            # SQLite header kontrolü
            try:
                with open(self.database_path, 'rb') as f:
                    header = f.read(16)
                    if not header.startswith(b'SQLite format 3\x00'):
                        errors.append("Geçersiz SQLite dosya başlığı")
                        corruption_detected = True
            except Exception as e:
                errors.append(f"Dosya başlığı okunamadı: {e}")
                corruption_detected = True
            
            # Dosya izinleri kontrolü
            if not os.access(self.database_path, os.R_OK):
                errors.append("Dosya okuma izni yok")
            
            if not os.access(self.database_path, os.W_OK):
                errors.append("Dosya yazma izni yok")
            
            return {
                'is_ok': len(errors) == 0,
                'errors': errors,
                'corruption_detected': corruption_detected
            }
            
        except Exception as e:
            return {
                'is_ok': False,
                'errors': [f"Dosya yapısı kontrolü hatası: {e}"],
                'corruption_detected': True
            }
    
    def repair_database(self, backup_before_repair: bool = True) -> Tuple[bool, str, List[str]]:
        """
        Veritabanını onar
        
        Args:
            backup_before_repair: Onarım öncesi yedek oluştur
            
        Returns:
            Tuple[bool, str, List[str]]: Başarı durumu, mesaj, uyarılar
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info(f"🔧 Veritabanı onarımı başlatılıyor: {self.database_path}")
        self.integrity_logger.info(f"=== VERİTABANI ONARIMI BAŞLADI ===")
        self.integrity_logger.info(f"Veritabanı: {self.database_path}")
        self.integrity_logger.info(f"Başlangıç zamanı: {start_time.isoformat()}")
        self.integrity_logger.info(f"Onarım öncesi yedek: {backup_before_repair}")
        
        try:
            warnings = []
            
            # Onarım öncesi yedek
            if backup_before_repair:
                backup_start = datetime.now(timezone.utc)
                backup_path = self._create_repair_backup()
                backup_duration = (datetime.now(timezone.utc) - backup_start).total_seconds()
                
                if backup_path:
                    warnings.append(f"Onarım öncesi yedek: {backup_path}")
                    self.logger.info(f"📁 Onarım öncesi yedek oluşturuldu: {backup_path}")
                    self.integrity_logger.info(f"Onarım öncesi yedek oluşturuldu: {backup_path} ({backup_duration:.2f}s)")
                else:
                    self.integrity_logger.warning("Onarım öncesi yedek oluşturulamadı")
            
            # Geçici onarım dosyası oluştur
            temp_path = f"{self.database_path}.repair_temp"
            self.integrity_logger.info(f"Geçici onarım dosyası: {temp_path}")
            
            # SQLite .dump ve .restore kullanarak onar
            dump_start = datetime.now(timezone.utc)
            self.integrity_logger.info("Dump/restore işlemi başlatılıyor...")
            success = self._repair_using_dump_restore(temp_path)
            dump_duration = (datetime.now(timezone.utc) - dump_start).total_seconds()
            
            if success:
                self.integrity_logger.info(f"Dump/restore işlemi BAŞARILI ({dump_duration:.2f}s)")
                
                # Onarılan dosyayı test et
                test_start = datetime.now(timezone.utc)
                self.integrity_logger.info("Onarılan veritabanı test ediliyor...")
                test_result = self._test_repaired_database(temp_path)
                test_duration = (datetime.now(timezone.utc) - test_start).total_seconds()
                
                if test_result['is_ok']:
                    self.integrity_logger.info(f"Onarılan veritabanı testi BAŞARILI ({test_duration:.2f}s)")
                    
                    # Orijinal dosyayı değiştir
                    replace_start = datetime.now(timezone.utc)
                    shutil.move(temp_path, self.database_path)
                    replace_duration = (datetime.now(timezone.utc) - replace_start).total_seconds()
                    
                    total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                    
                    success_msg = "Veritabanı başarıyla onarıldı"
                    self.logger.info("✅ Veritabanı onarımı başarılı")
                    self.integrity_logger.info(f"Dosya değiştirme işlemi BAŞARILI ({replace_duration:.2f}s)")
                    self.integrity_logger.info(f"=== SONUÇ: BAŞARILI ===")
                    self.integrity_logger.info(f"Mesaj: {success_msg}")
                    self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
                    self.integrity_logger.info(f"Bitiş zamanı: {datetime.now(timezone.utc).isoformat()}")
                    self.integrity_logger.info(f"=== VERİTABANI ONARIMI BİTTİ ===")
                    
                    return True, success_msg, warnings
                else:
                    # Onarım başarısız
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    error_msg = f"Onarılan veritabanı test edilemedi: {test_result.get('error', 'Bilinmeyen hata')}"
                    total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                    
                    self.logger.error(f"❌ {error_msg}")
                    self.integrity_logger.error(f"Onarılan veritabanı testi BAŞARISIZ ({test_duration:.2f}s): {test_result.get('error', 'Bilinmeyen hata')}")
                    self.integrity_logger.info(f"=== SONUÇ: BAŞARISIZ ===")
                    self.integrity_logger.info(f"Hata: {error_msg}")
                    self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
                    self.integrity_logger.info(f"=== VERİTABANI ONARIMI BİTTİ ===")
                    
                    return False, error_msg, warnings
            else:
                error_msg = "Veritabanı dump/restore işlemi başarısız"
                total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                self.logger.error(f"❌ {error_msg}")
                self.integrity_logger.error(f"Dump/restore işlemi BAŞARISIZ ({dump_duration:.2f}s)")
                self.integrity_logger.info(f"=== SONUÇ: BAŞARISIZ ===")
                self.integrity_logger.info(f"Hata: {error_msg}")
                self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
                self.integrity_logger.info(f"=== VERİTABANI ONARIMI BİTTİ ===")
                
                return False, error_msg, warnings
                
        except Exception as e:
            error_msg = f"Veritabanı onarım hatası: {e}"
            total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            self.logger.error(f"❌ {error_msg}")
            self.integrity_logger.error(f"KRİTİK HATA: {error_msg}")
            self.integrity_logger.info(f"=== SONUÇ: KRİTİK HATA ===")
            self.integrity_logger.info(f"Hata: {error_msg}")
            self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
            self.integrity_logger.info(f"=== VERİTABANI ONARIMI BİTTİ ===")
            
            return False, error_msg, warnings
    
    def _repair_using_dump_restore(self, output_path: str) -> bool:
        """SQLite dump/restore kullanarak onar"""
        try:
            # Kaynak veritabanından dump al
            source_conn = sqlite3.connect(self.database_path)
            
            # Yeni veritabanı oluştur
            target_conn = sqlite3.connect(output_path)
            
            # Dump işlemi
            for line in source_conn.iterdump():
                try:
                    target_conn.execute(line)
                except sqlite3.Error as e:
                    # Hatalı satırları atla ve logla
                    self.logger.warning(f"Dump satırı atlandı: {e}")
            
            target_conn.commit()
            target_conn.close()
            source_conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Dump/restore hatası: {e}")
            return False
    
    def _test_repaired_database(self, db_path: str) -> Dict[str, Any]:
        """Onarılan veritabanını test et"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Temel testler
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            if integrity_result[0] == 'ok' and table_count > 0:
                return {'is_ok': True}
            else:
                return {'is_ok': False, 'error': f"Integrity: {integrity_result[0]}, Tables: {table_count}"}
                
        except Exception as e:
            return {'is_ok': False, 'error': str(e)}
    
    def _create_integrity_backup(self) -> Optional[str]:
        """Bütünlük kontrolü öncesi yedek oluştur"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"integrity_check_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(self.database_path, backup_path)
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Bütünlük yedek oluşturma hatası: {e}")
            return None
    
    def _create_repair_backup(self) -> Optional[str]:
        """Onarım öncesi yedek oluştur"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"repair_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(self.database_path, backup_path)
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Onarım yedek oluşturma hatası: {e}")
            return None
    
    def get_integrity_report(self, save_to_file: bool = True) -> Dict[str, Any]:
        """Detaylı bütünlük raporu oluştur"""
        start_time = datetime.now(timezone.utc)
        self.logger.info("📊 Detaylı bütünlük raporu oluşturuluyor...")
        self.integrity_logger.info(f"=== BÜTÜNLÜK RAPORU OLUŞTURMA BAŞLADI ===")
        self.integrity_logger.info(f"Başlangıç zamanı: {start_time.isoformat()}")
        
        # Bütünlük kontrolü yap
        integrity_result = self.check_database_integrity(create_backup=False)
        
        # Ek istatistikler
        stats_start = datetime.now(timezone.utc)
        stats = self._get_database_statistics()
        stats_duration = (datetime.now(timezone.utc) - stats_start).total_seconds()
        self.integrity_logger.info(f"İstatistik toplama süresi: {stats_duration:.2f} saniye")
        
        # Rapor oluştur
        report = {
            'database_path': self.database_path,
            'report_generation_time': start_time.isoformat(),
            'check_timestamp': integrity_result.check_timestamp.isoformat(),
            'overall_status': 'HEALTHY' if integrity_result.is_valid else 'CORRUPTED' if integrity_result.corruption_detected else 'WARNING',
            'integrity_result': {
                'is_valid': integrity_result.is_valid,
                'corruption_detected': integrity_result.corruption_detected,
                'error_count': len(integrity_result.error_details),
                'errors': integrity_result.error_details,
                'repair_possible': integrity_result.repair_possible,
                'backup_recommended': integrity_result.backup_recommended
            },
            'statistics': stats,
            'recommendations': self._get_integrity_recommendations(integrity_result),
            'report_metadata': {
                'generator': 'TezgahTakip DatabaseIntegrityChecker',
                'version': '1.0',
                'generation_duration_seconds': (datetime.now(timezone.utc) - start_time).total_seconds()
            }
        }
        
        # Raporu dosyaya kaydet
        if save_to_file:
            report_saved = self._save_report_to_file(report)
            if report_saved:
                self.integrity_logger.info(f"Rapor dosyaya kaydedildi: {report_saved}")
            else:
                self.integrity_logger.warning("Rapor dosyaya kaydedilemedi")
        
        total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        report['report_metadata']['generation_duration_seconds'] = total_duration
        
        self.logger.info(f"✅ Bütünlük raporu oluşturuldu - Durum: {report['overall_status']}")
        self.integrity_logger.info(f"Rapor durumu: {report['overall_status']}")
        self.integrity_logger.info(f"Toplam süre: {total_duration:.2f} saniye")
        self.integrity_logger.info(f"=== BÜTÜNLÜK RAPORU OLUŞTURMA BİTTİ ===")
        
        return report
    
    def _get_database_statistics(self) -> Dict[str, Any]:
        """Veritabanı istatistikleri"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Dosya boyutu
            stats['file_size_bytes'] = os.path.getsize(self.database_path)
            stats['file_size_mb'] = round(stats['file_size_bytes'] / (1024 * 1024), 2)
            
            # Tablo sayısı
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            stats['table_count'] = cursor.fetchone()[0]
            
            # İndeks sayısı
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            stats['index_count'] = cursor.fetchone()[0]
            
            # Sayfa bilgileri
            cursor.execute("PRAGMA page_count")
            stats['page_count'] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            stats['page_size'] = cursor.fetchone()[0]
            
            # Tablo başına kayıt sayıları
            table_counts = {}
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    table_counts[table_name] = cursor.fetchone()[0]
                except sqlite3.Error:
                    table_counts[table_name] = "ERROR"
            
            stats['table_record_counts'] = table_counts
            
            conn.close()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"İstatistik toplama hatası: {e}")
            return {'error': str(e)}
    
    def _get_integrity_recommendations(self, integrity_result: IntegrityCheckResult) -> List[str]:
        """Bütünlük durumuna göre öneriler"""
        recommendations = []
        
        if integrity_result.is_valid:
            recommendations.append("✅ Veritabanı sağlıklı durumda")
            recommendations.append("🔄 Düzenli yedekleme yapmaya devam edin")
            recommendations.append("📊 Aylık bütünlük kontrolü yapın")
        else:
            if integrity_result.corruption_detected:
                recommendations.append("🚨 KRİTİK: Veritabanı bozulması tespit edildi")
                if integrity_result.repair_possible:
                    recommendations.append("🔧 Otomatik onarım denenebilir")
                else:
                    recommendations.append("💾 Yedekten geri yükleme gerekli")
                recommendations.append("⚠️ Veri kaybı riski var")
            else:
                recommendations.append("⚠️ Veritabanında sorunlar tespit edildi")
                recommendations.append("🔍 Detaylı inceleme yapın")
            
            if integrity_result.backup_recommended:
                recommendations.append("📁 Mevcut durumun yedeğini alın")
            
            recommendations.append("🛠️ Sistem yöneticisine başvurun")
        
        return recommendations
    
    def _save_report_to_file(self, report: Dict[str, Any]) -> Optional[str]:
        """Bütünlük raporunu dosyaya kaydet"""
        try:
            import json
            
            # Rapor dosya adı
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"integrity_report_{timestamp}.json"
            report_path = Path("reports") / report_filename
            
            # Rapor dizinini oluştur
            report_path.parent.mkdir(exist_ok=True)
            
            # Raporu JSON formatında kaydet
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.integrity_logger.info(f"Rapor kaydedildi: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.integrity_logger.error(f"Rapor kaydetme hatası: {e}")
            return None
    
    def get_integrity_summary(self) -> str:
        """Kısa bütünlük özeti döndür"""
        try:
            result = self.check_database_integrity(create_backup=False)
            
            if result.is_valid:
                return "✅ Veritabanı sağlıklı"
            elif result.corruption_detected:
                return f"🚨 Veritabanı bozuk ({len(result.error_details)} hata)"
            else:
                return f"⚠️ Veritabanında sorunlar var ({len(result.error_details)} uyarı)"
                
        except Exception as e:
            return f"❌ Kontrol hatası: {e}"
    
    def log_integrity_check_result(self, result: IntegrityCheckResult):
        """Bütünlük kontrolü sonucunu detaylı logla"""
        self.integrity_logger.info("=== BÜTÜNLÜK KONTROLÜ SONUÇ ÖZETI ===")
        self.integrity_logger.info(f"Veritabanı: {self.database_path}")
        self.integrity_logger.info(f"Kontrol zamanı: {result.check_timestamp.isoformat()}")
        self.integrity_logger.info(f"Geçerli: {result.is_valid}")
        self.integrity_logger.info(f"Bozulma tespit edildi: {result.corruption_detected}")
        self.integrity_logger.info(f"Hata sayısı: {len(result.error_details)}")
        self.integrity_logger.info(f"Onarım mümkün: {result.repair_possible}")
        self.integrity_logger.info(f"Yedek öneriliyor: {result.backup_recommended}")
        
        if result.error_details:
            self.integrity_logger.info("Tespit edilen hatalar:")
            for i, error in enumerate(result.error_details, 1):
                self.integrity_logger.info(f"  {i}. {error}")
        
        self.integrity_logger.info("=== SONUÇ ÖZETI BİTTİ ===")
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Eski log dosyalarını temizle"""
        try:
            if not os.path.exists(self.log_file_path):
                return
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Log dosyasının değiştirilme tarihini kontrol et
            log_mtime = datetime.fromtimestamp(os.path.getmtime(self.log_file_path))
            
            if log_mtime < cutoff_date:
                # Eski log dosyasını arşivle
                archive_name = f"{self.log_file_path}.{log_mtime.strftime('%Y%m%d')}"
                shutil.move(self.log_file_path, archive_name)
                self.integrity_logger.info(f"Eski log dosyası arşivlendi: {archive_name}")
            
            # Eski rapor dosyalarını temizle
            reports_dir = Path("reports")
            if reports_dir.exists():
                for report_file in reports_dir.glob("integrity_report_*.json"):
                    file_mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        report_file.unlink()
                        self.integrity_logger.info(f"Eski rapor dosyası silindi: {report_file}")
                        
        except Exception as e:
            self.integrity_logger.error(f"Log temizleme hatası: {e}")