#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Enhanced Database Manager
Gelişmiş veritabanı yönetim sistemi - fallback, integrity check ve error handling ile
"""

import os
import logging
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import existing components
from database_models import DatabaseManager
from database_path_resolver import DatabasePathResolver
from file_access_validator import FileAccessValidator
from database_integrity_checker import DatabaseIntegrityChecker
from fallback_system import FallbackSystem
from exception_handler import EnhancedErrorHandler
from automatic_retry_manager import AutomaticRetryManager, retry_database_operation
from database_error_models import (
    DatabaseStatus, FallbackType, ErrorSeverity, 
    IntegrityCheckResult, FallbackResult, ErrorAnalysis
)

class EnhancedDatabaseManager(DatabaseManager):
    """
    Gelişmiş veritabanı yönetim sınıfı
    
    Mevcut DatabaseManager'ı genişletir ve şu özellikleri ekler:
    - Otomatik path resolution ve fallback
    - Dosya erişim doğrulama
    - Veritabanı bütünlük kontrolü
    - Gelişmiş hata yönetimi
    - Kullanıcı dostu bildirimler
    """
    
    def __init__(self, db_path: Optional[str] = None, enable_fallback: bool = True, notification_callback=None):
        """
        Enhanced Database Manager başlat
        
        Args:
            db_path: Veritabanı dosya yolu (None ise otomatik çözümlenir)
            enable_fallback: Fallback sistemini etkinleştir
            notification_callback: Bildirimler için callback fonksiyonu
        """
        self.enable_fallback = enable_fallback
        self.notification_callback = notification_callback
        self.logger = logging.getLogger(__name__)
        
        # Enhanced bileşenleri başlat
        self.path_resolver = DatabasePathResolver()
        self.file_validator = FileAccessValidator()
        self.error_handler = EnhancedErrorHandler()
        self.fallback_system = FallbackSystem()
        self.retry_manager = AutomaticRetryManager(
            max_retries=3,
            base_delay=0.5,
            max_delay=10.0
        )
        
        # Performans metrikleri
        self.performance_metrics = {
            'connection_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'fallback_activations': 0,
            'integrity_checks': 0,
            'last_connection_time': None,
            'average_connection_time': 0.0,
            'total_connection_time': 0.0,
            'health_check_count': 0,
            'last_health_check': None,
            'health_check_failures': 0
        }
        
        # Veritabanı durumu
        self.database_status = DatabaseStatus(
            is_connected=False,
            database_path="",
            is_fallback=False,
            fallback_type=None,
            last_error=None,
            connection_attempts=0,
            integrity_status="unknown",
            last_check_time=datetime.now(timezone.utc)
        )
        
        # Integrity checker (path belirlendikten sonra başlatılacak)
        self.integrity_checker = None
        
        # Veritabanını başlat
        self.init_database_with_fallback(db_path)
    
    def _notify(self, message: str, severity: str = "info", details: dict = None):
        """
        Bildirim gönder (callback varsa)
        
        Args:
            message: Bildirim mesajı
            severity: Önem seviyesi (info, warning, error)
            details: Ek detaylar
        """
        if self.notification_callback:
            try:
                self.notification_callback(message, severity, details)
            except Exception as e:
                self.logger.warning(f"Notification callback hatası: {e}")
    
    def init_database_with_fallback(self, preferred_path: Optional[str] = None) -> bool:
        """
        Fallback desteği ile veritabanını başlat
        
        Args:
            preferred_path: Tercih edilen veritabanı yolu
            
        Returns:
            bool: Başlatma başarılı mı
        """
        self.logger.info("🚀 Enhanced Database Manager başlatılıyor...")
        
        start_time = datetime.now()
        self.performance_metrics['connection_attempts'] += 1
        
        try:
            # 1. Veritabanı yolunu çözümle
            resolved_path = self._resolve_database_path(preferred_path)
            if not resolved_path:
                raise Exception("Uygun veritabanı yolu bulunamadı")
            
            # 2. Dosya erişim izinlerini kontrol et
            if not self._validate_file_access(resolved_path):
                if self.enable_fallback:
                    return self._attempt_fallback_initialization()
                else:
                    raise Exception("Veritabanı dosyasına erişim izni yok")
            
            # 3. Veritabanı bütünlük kontrolü
            integrity_result = self._check_database_integrity(resolved_path)
            
            # 4. Bozuk veritabanı için fallback
            if not integrity_result.is_valid and integrity_result.corruption_detected:
                self.logger.warning("⚠️ Veritabanı bozulması tespit edildi")
                if self.enable_fallback:
                    return self._handle_corrupted_database(resolved_path, integrity_result)
                else:
                    raise Exception("Veritabanı bozuk ve fallback devre dışı")
            
            # 5. Normal başlatma
            success = self._initialize_database(resolved_path, integrity_result)
            
            if success:
                # Başarılı bağlantı metrikleri
                connection_time = (datetime.now() - start_time).total_seconds()
                self.performance_metrics['successful_connections'] += 1
                self.performance_metrics['last_connection_time'] = datetime.now()
                self.performance_metrics['total_connection_time'] += connection_time
                
                if self.performance_metrics['successful_connections'] > 0:
                    self.performance_metrics['average_connection_time'] = (
                        self.performance_metrics['total_connection_time'] / 
                        self.performance_metrics['successful_connections']
                    )
            
            return success
            
        except Exception as e:
            self.database_status.last_error = str(e)
            self.database_status.connection_attempts += 1
            self.performance_metrics['failed_connections'] += 1
            
            # Hata analizi ve kullanıcı bildirimi
            error_analysis = self.error_handler.analyze_sqlite_error(e)
            user_message = self.error_handler.format_user_message(e, error_analysis.suggested_actions)
            
            self.logger.error(f"❌ Veritabanı başlatma hatası: {user_message}")
            
            # Son çare fallback
            if self.enable_fallback and self.database_status.connection_attempts < 3:
                self.logger.info("🔄 Fallback sistemi devreye giriyor...")
                return self._attempt_fallback_initialization()
            
            raise Exception(f"Veritabanı başlatılamadı: {user_message}")
    
    def _resolve_database_path(self, preferred_path: Optional[str]) -> Optional[str]:
        """Veritabanı yolunu çözümle"""
        try:
            self.logger.info("📍 Veritabanı yolu çözümleniyor...")
            
            if preferred_path:
                # Tercih edilen yolu kontrol et
                result = self.path_resolver.resolve_database_path(preferred_path)
                if result.resolved_path:
                    self.logger.info(f"✅ Tercih edilen yol kullanılıyor: {result.resolved_path}")
                    return result.resolved_path
            
            # Otomatik yol çözümleme
            result = self.path_resolver.resolve_database_path()
            if result.resolved_path:
                self.logger.info(f"✅ Otomatik yol çözümlendi: {result.resolved_path}")
                return result.resolved_path
            
            self.logger.error("❌ Uygun veritabanı yolu bulunamadı")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Yol çözümleme hatası: {e}")
            return None
    
    def _validate_file_access(self, db_path: str) -> bool:
        """Dosya erişim izinlerini doğrula"""
        try:
            self.logger.info(f"🔐 Dosya erişim izinleri kontrol ediliyor: {db_path}")
            
            # Dizin izinlerini kontrol et
            directory = os.path.dirname(db_path)
            dir_result = self.file_validator.check_directory_permissions(directory)
            
            if not dir_result.can_write:
                self.logger.warning(f"⚠️ Dizin yazma izni yok: {directory}")
                return False
            
            # Dosya varsa izinlerini kontrol et
            if os.path.exists(db_path):
                file_result = self.file_validator.check_file_permissions(db_path)
                if not file_result.can_read or not file_result.can_write:
                    self.logger.warning(f"⚠️ Dosya erişim izni yetersiz: {db_path}")
                    return False
            
            self.logger.info("✅ Dosya erişim izinleri uygun")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Dosya erişim kontrolü hatası: {e}")
            return False
    
    def _check_database_integrity(self, db_path: str) -> IntegrityCheckResult:
        """Veritabanı bütünlük kontrolü"""
        try:
            self.logger.info(f"🔍 Veritabanı bütünlük kontrolü: {db_path}")
            
            # Integrity checker'ı başlat
            self.integrity_checker = DatabaseIntegrityChecker(db_path)
            
            # Bütünlük kontrolü yap
            result = self.integrity_checker.check_database_integrity(create_backup=True)
            
            # Durumu güncelle
            self.database_status.integrity_status = "healthy" if result.is_valid else "corrupted" if result.corruption_detected else "warning"
            self.database_status.last_check_time = result.check_timestamp
            
            if result.is_valid:
                self.logger.info("✅ Veritabanı bütünlük kontrolü başarılı")
            else:
                self.logger.warning(f"⚠️ Bütünlük kontrolü sorunları: {len(result.error_details)} hata")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Bütünlük kontrolü hatası: {e}")
            # Hata durumunda varsayılan sonuç döndür
            return IntegrityCheckResult(
                is_valid=False,
                corruption_detected=True,
                error_details=[f"Bütünlük kontrolü hatası: {e}"],
                repair_possible=False,
                backup_recommended=True,
                check_timestamp=datetime.now(timezone.utc)
            )
    
    def _initialize_database(self, db_path: str, integrity_result: IntegrityCheckResult) -> bool:
        """Normal veritabanı başlatma - Retry mekanizması ile"""
        try:
            self.logger.info(f"🔧 Veritabanı başlatılıyor: {db_path}")
            
            # Retry mekanizması ile veritabanı başlatma
            def database_init_operation():
                self.db_path = db_path
                super(EnhancedDatabaseManager, self).init_database()
                return True
            
            # Retry ile başlatma dene
            retry_result = self.retry_manager.retry_with_backoff(
                database_init_operation,
                retry_on_exceptions=(sqlite3.OperationalError, sqlite3.DatabaseError, PermissionError, OSError)
            )
            
            if retry_result.success:
                # Durumu güncelle
                self.database_status.is_connected = True
                self.database_status.database_path = db_path
                self.database_status.is_fallback = False
                self.database_status.fallback_type = None
                self.database_status.last_error = None
                
                if retry_result.final_attempt_number > 0:
                    self.logger.info(f"✅ Veritabanı başarıyla başlatıldı ({retry_result.final_attempt_number + 1}. denemede)")
                else:
                    self.logger.info("✅ Veritabanı başarıyla başlatıldı")
                
                return True
            else:
                self.logger.error(f"❌ Veritabanı başlatma başarısız: {retry_result.error}")
                raise retry_result.error
            
        except Exception as e:
            self.logger.error(f"❌ Veritabanı başlatma hatası: {e}")
            raise
    
    def _handle_corrupted_database(self, db_path: str, integrity_result: IntegrityCheckResult) -> bool:
        """Bozuk veritabanı durumunu ele al"""
        try:
            self.logger.warning("🚨 Bozuk veritabanı tespit edildi, kurtarma işlemi başlatılıyor...")
            
            # Onarım mümkünse dene
            if integrity_result.repair_possible and self.integrity_checker:
                self.logger.info("🔧 Veritabanı onarımı deneniyor...")
                success, message, warnings = self.integrity_checker.repair_database()
                
                if success:
                    self.logger.info(f"✅ Veritabanı onarımı başarılı: {message}")
                    return self._initialize_database(db_path, integrity_result)
                else:
                    self.logger.error(f"❌ Veritabanı onarımı başarısız: {message}")
            
            # Fallback sistemi devreye gir
            return self._attempt_fallback_initialization()
            
        except Exception as e:
            self.logger.error(f"❌ Bozuk veritabanı işleme hatası: {e}")
            return self._attempt_fallback_initialization()
    
    def _attempt_fallback_initialization(self) -> bool:
        """Fallback sistemi ile başlatma"""
        try:
            self.logger.info("🔄 Fallback sistemi devreye giriyor...")
            self.performance_metrics['fallback_activations'] += 1
            
            # Yedekten geri yükleme dene
            backup_result = self.fallback_system.restore_from_backup()
            if backup_result.success:
                self.logger.info(f"✅ Yedekten geri yükleme başarılı: {backup_result.message}")
                return self._initialize_fallback_database(backup_result)
            
            # Alternatif konum dene
            alternative_result = self.fallback_system.create_alternative_database()
            if alternative_result.success:
                self.logger.info(f"✅ Alternatif konum başarılı: {alternative_result.message}")
                return self._initialize_fallback_database(alternative_result)
            
            # Temiz veritabanı oluştur
            clean_result = self.fallback_system.create_clean_database()
            if clean_result.success:
                self.logger.info(f"✅ Temiz veritabanı oluşturuldu: {clean_result.message}")
                return self._initialize_fallback_database(clean_result)
            
            # Son çare: bellek içi veritabanı
            memory_result = self.fallback_system.create_memory_database()
            if memory_result.success:
                self.logger.warning(f"⚠️ Bellek içi veritabanı kullanılıyor: {memory_result.message}")
                return self._initialize_fallback_database(memory_result)
            
            # Tüm fallback seçenekleri başarısız
            raise Exception("Tüm fallback seçenekleri başarısız oldu")
            
        except Exception as e:
            self.logger.error(f"❌ Fallback sistemi hatası: {e}")
            return False
    
    def _initialize_fallback_database(self, fallback_result: FallbackResult) -> bool:
        """Fallback veritabanını başlat"""
        try:
            # Fallback veritabanı yolunu ayarla
            if fallback_result.database_path:
                self.db_path = fallback_result.database_path
            else:
                # Bellek içi veritabanı için
                self.db_path = ":memory:"
            
            # SQLAlchemy engine'i kullan (eğer varsa)
            if fallback_result.engine:
                self.engine = fallback_result.engine
                from sqlalchemy.orm import sessionmaker
                self.Session = sessionmaker(bind=self.engine)
            else:
                # Normal başlatma
                super().init_database()
            
            # Durumu güncelle
            self.database_status.is_connected = True
            self.database_status.database_path = self.db_path
            self.database_status.is_fallback = True
            self.database_status.fallback_type = fallback_result.fallback_type
            self.database_status.last_error = None
            
            # Kullanıcıyı bilgilendir
            if fallback_result.fallback_type == FallbackType.MEMORY_DATABASE:
                self.logger.warning("⚠️ DİKKAT: Bellek içi veritabanı kullanılıyor - veriler kalıcı değil!")
            
            self.logger.info(f"✅ Fallback veritabanı başarıyla başlatıldı: {fallback_result.fallback_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fallback veritabanı başlatma hatası: {e}")
            return False
    
    def handle_connection_error(self, error: Exception) -> bool:
        """Bağlantı hatalarını ele al - Enhanced retry mekanizması ile"""
        try:
            self.logger.warning(f"🔄 Bağlantı hatası ele alınıyor: {error}")
            
            # Hata analizi
            error_analysis = self.error_handler.analyze_sqlite_error(error)
            
            # Retry ile otomatik düzeltme dene
            if error_analysis.auto_fixable:
                self.logger.info("🔧 Retry mekanizması ile otomatik düzeltme deneniyor...")
                
                def recovery_operation():
                    # Dosya kilidi durumu için özel bekleme
                    if "database is locked" in str(error).lower():
                        # File lock detection
                        if hasattr(self, 'db_path') and self.db_path:
                            locks = self.retry_manager.detect_file_locks(self.db_path)
                            if locks:
                                self.logger.info(f"🔒 Detected {len(locks)} file locks on database")
                                # Process'lerin tamamlanmasını bekle
                                process_names = [lock.get('process_name', '') for lock in locks]
                                self.retry_manager.wait_for_process_completion(process_names, timeout=10.0)
                        
                        # Test connection
                        return self._test_database_connection()
                    
                    # İzin sorunları için fallback
                    elif "permission denied" in str(error).lower():
                        return self._attempt_fallback_initialization()
                    
                    # Genel retry
                    else:
                        return self._test_database_connection()
                
                # Retry ile recovery dene
                retry_result = self.retry_manager.retry_with_backoff(
                    recovery_operation,
                    retry_on_exceptions=(sqlite3.OperationalError, PermissionError, OSError),
                    custom_retry_logic=lambda e: "locked" in str(e).lower() or "busy" in str(e).lower()
                )
                
                if retry_result.success:
                    self.logger.info(f"✅ Bağlantı hatası retry ile çözüldü ({retry_result.final_attempt_number + 1}. denemede)")
                    return True
                else:
                    self.logger.warning(f"⚠️ Retry ile çözülemedi, fallback'e geçiliyor: {retry_result.error}")
            
            # Fallback sistemi
            if self.enable_fallback:
                return self._attempt_fallback_initialization()
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Bağlantı hatası işleme hatası: {e}")
            return False
    
    def _test_database_connection(self) -> bool:
        """Veritabanı bağlantısını test et"""
        try:
            if self.engine and self.Session:
                with self.get_session() as session:
                    from sqlalchemy import text
                    result = session.execute(text("SELECT 1")).fetchone()
                    return result and result[0] == 1
            return False
        except Exception as e:
            self.logger.debug(f"Database connection test failed: {e}")
            return False
    
    def switch_to_fallback_database(self) -> bool:
        """Fallback veritabanına geç"""
        try:
            self.logger.info("🔄 Fallback veritabanına geçiliyor...")
            
            # Mevcut bağlantıyı kapat
            if self.engine:
                self.engine.dispose()
            
            # Fallback başlat
            return self._attempt_fallback_initialization()
            
        except Exception as e:
            self.logger.error(f"❌ Fallback geçiş hatası: {e}")
            return False
    
    def get_database_status(self) -> DatabaseStatus:
        """Gelişmiş veritabanı durumu bilgilerini al"""
        # Bağlantı sağlık kontrolü yap
        self._perform_health_check()
        
        return self.database_status
    
    def _perform_health_check(self):
        """Veritabanı bağlantı sağlık kontrolü"""
        start_time = datetime.now()
        
        try:
            self.performance_metrics['health_check_count'] += 1
            
            if self.engine and self.Session:
                # Basit bağlantı testi
                with self.get_session() as session:
                    from sqlalchemy import text
                    result = session.execute(text("SELECT 1")).fetchone()
                    
                    if result and result[0] == 1:
                        self.database_status.is_connected = True
                        self.database_status.last_error = None
                        
                        # Performans metrikleri güncelle
                        check_time = (datetime.now() - start_time).total_seconds()
                        self.performance_metrics['last_health_check'] = datetime.now()
                        
                        # Ortalama hesapla
                        if self.performance_metrics['health_check_count'] > 1:
                            total_time = (self.performance_metrics['average_connection_time'] * 
                                        (self.performance_metrics['health_check_count'] - 1) + check_time)
                            self.performance_metrics['average_connection_time'] = (
                                total_time / self.performance_metrics['health_check_count']
                            )
                        else:
                            self.performance_metrics['average_connection_time'] = check_time
                        
                        self.logger.debug(f"Sağlık kontrolü başarılı: {check_time:.3f}s")
                    else:
                        raise Exception("Sağlık kontrolü sorgusu başarısız")
            else:
                self.database_status.is_connected = False
                self.database_status.last_error = "Engine veya Session mevcut değil"
                
        except Exception as e:
            self.database_status.is_connected = False
            self.database_status.last_error = str(e)
            self.performance_metrics['health_check_failures'] += 1
            
            self.logger.warning(f"Sağlık kontrolü başarısız: {e}")
    
    def get_connection_health_report(self) -> Dict[str, Any]:
        """Bağlantı sağlık raporu al"""
        return {
            'connection_status': {
                'is_connected': self.database_status.is_connected,
                'database_path': self.database_status.database_path,
                'is_fallback': self.database_status.is_fallback,
                'fallback_type': self.database_status.fallback_type.value if self.database_status.fallback_type else None,
                'last_error': self.database_status.last_error,
                'integrity_status': self.database_status.integrity_status
            },
            'performance_metrics': {
                'connection_attempts': self.performance_metrics['connection_attempts'],
                'successful_connections': self.performance_metrics['successful_connections'],
                'failed_connections': self.performance_metrics['failed_connections'],
                'success_rate': (
                    self.performance_metrics['successful_connections'] / 
                    max(1, self.performance_metrics['connection_attempts'])
                ) * 100,
                'fallback_activations': self.performance_metrics['fallback_activations'],
                'average_connection_time': self.performance_metrics['average_connection_time'],
                'last_connection_time': self.performance_metrics['last_connection_time'].isoformat() if self.performance_metrics['last_connection_time'] else None
            },
            'health_checks': {
                'total_checks': self.performance_metrics['health_check_count'],
                'failed_checks': self.performance_metrics['health_check_failures'],
                'success_rate': (
                    (self.performance_metrics['health_check_count'] - self.performance_metrics['health_check_failures']) / 
                    max(1, self.performance_metrics['health_check_count'])
                ) * 100,
                'last_check': self.performance_metrics['last_health_check'].isoformat() if self.performance_metrics['last_health_check'] else None
            },
            'integrity_info': {
                'last_integrity_check': self.database_status.last_check_time.isoformat() if self.database_status.last_check_time else None,
                'integrity_checks_performed': self.performance_metrics['integrity_checks'],
                'current_status': self.database_status.integrity_status
            }
        }
    
    def get_fallback_usage_metrics(self) -> Dict[str, Any]:
        """Fallback kullanım metrikleri al"""
        fallback_status = self.fallback_system.get_fallback_status()
        
        return {
            'fallback_enabled': self.enable_fallback,
            'is_fallback_active': fallback_status['is_fallback_active'],
            'current_fallback_type': fallback_status['fallback_type'],
            'fallback_path': fallback_status['fallback_path'],
            'primary_db_path': fallback_status['primary_db_path'],
            'available_backups': fallback_status['available_backups'],
            'total_fallback_activations': self.performance_metrics['fallback_activations'],
            'fallback_options': len(self.get_fallback_options())
        }
    
    def monitor_database_performance(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Belirli süre boyunca veritabanı performansını izle
        
        Args:
            duration_minutes: İzleme süresi (dakika)
            
        Returns:
            Dict[str, Any]: Performans raporu
        """
        import time
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        monitoring_data = {
            'start_time': start_time.isoformat(),
            'duration_minutes': duration_minutes,
            'health_checks': [],
            'connection_tests': [],
            'performance_summary': {}
        }
        
        self.logger.info(f"🔍 Veritabanı performans izleme başlatıldı: {duration_minutes} dakika")
        
        check_count = 0
        while datetime.now() < end_time:
            check_start = datetime.now()
            
            # Sağlık kontrolü yap
            try:
                self._perform_health_check()
                
                check_duration = (datetime.now() - check_start).total_seconds()
                
                monitoring_data['health_checks'].append({
                    'timestamp': check_start.isoformat(),
                    'duration_seconds': check_duration,
                    'success': self.database_status.is_connected,
                    'error': self.database_status.last_error if not self.database_status.is_connected else None
                })
                
                check_count += 1
                
                # 30 saniye bekle
                time.sleep(30)
                
            except KeyboardInterrupt:
                self.logger.info("Performans izleme kullanıcı tarafından durduruldu")
                break
            except Exception as e:
                self.logger.error(f"Performans izleme hatası: {e}")
                break
        
        # Özet istatistikleri hesapla
        successful_checks = [c for c in monitoring_data['health_checks'] if c['success']]
        failed_checks = [c for c in monitoring_data['health_checks'] if not c['success']]
        
        if monitoring_data['health_checks']:
            avg_duration = sum(c['duration_seconds'] for c in monitoring_data['health_checks']) / len(monitoring_data['health_checks'])
            max_duration = max(c['duration_seconds'] for c in monitoring_data['health_checks'])
            min_duration = min(c['duration_seconds'] for c in monitoring_data['health_checks'])
        else:
            avg_duration = max_duration = min_duration = 0
        
        monitoring_data['performance_summary'] = {
            'total_checks': len(monitoring_data['health_checks']),
            'successful_checks': len(successful_checks),
            'failed_checks': len(failed_checks),
            'success_rate_percent': (len(successful_checks) / max(1, len(monitoring_data['health_checks']))) * 100,
            'average_response_time': avg_duration,
            'max_response_time': max_duration,
            'min_response_time': min_duration,
            'end_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"✅ Performans izleme tamamlandı: {check_count} kontrol yapıldı")
        
        return monitoring_data
    
    def perform_integrity_check(self, create_backup: bool = True) -> IntegrityCheckResult:
        """Manuel bütünlük kontrolü"""
        if not self.integrity_checker:
            self.integrity_checker = DatabaseIntegrityChecker(self.db_path)
        
        self.performance_metrics['integrity_checks'] += 1
        
        result = self.integrity_checker.check_database_integrity(create_backup)
        
        # Durumu güncelle
        self.database_status.integrity_status = "healthy" if result.is_valid else "corrupted" if result.corruption_detected else "warning"
        self.database_status.last_check_time = result.check_timestamp
        
        return result
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Detaylı bütünlük raporu al"""
        if not self.integrity_checker:
            self.integrity_checker = DatabaseIntegrityChecker(self.db_path)
        
        return self.integrity_checker.get_integrity_report()
    
    def repair_database(self, backup_before_repair: bool = True) -> Tuple[bool, str, List[str]]:
        """Veritabanını onar"""
        if not self.integrity_checker:
            self.integrity_checker = DatabaseIntegrityChecker(self.db_path)
        
        return self.integrity_checker.repair_database(backup_before_repair)
    
    def get_fallback_options(self) -> List[Dict[str, Any]]:
        """Mevcut fallback seçeneklerini al"""
        return self.fallback_system.get_available_options()
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Eski yedekleri temizle"""
        if self.integrity_checker:
            self.integrity_checker.cleanup_old_logs(days_to_keep)
        
        self.fallback_system.cleanup_old_backups(days_to_keep)
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Gelişmiş istatistikler - Retry metrikleri dahil"""
        base_stats = super().get_dashboard_stats() if hasattr(super(), 'get_dashboard_stats') else {}
        
        enhanced_stats = {
            'database_status': self.get_database_status().__dict__,
            'fallback_enabled': self.enable_fallback,
            'integrity_last_check': self.database_status.last_check_time.isoformat() if self.database_status.last_check_time else None,
            'connection_attempts': self.database_status.connection_attempts,
            'performance_metrics': self.performance_metrics.copy(),
            'connection_health': self.get_connection_health_report(),
            'fallback_metrics': self.get_fallback_usage_metrics(),
            'retry_statistics': self.retry_manager.get_retry_statistics()
        }
        
        # Datetime objelerini string'e çevir
        if enhanced_stats['performance_metrics']['last_connection_time']:
            enhanced_stats['performance_metrics']['last_connection_time'] = enhanced_stats['performance_metrics']['last_connection_time'].isoformat()
        if enhanced_stats['performance_metrics']['last_health_check']:
            enhanced_stats['performance_metrics']['last_health_check'] = enhanced_stats['performance_metrics']['last_health_check'].isoformat()
        
        return {**base_stats, **enhanced_stats}
    
    def close(self):
        """Gelişmiş kapatma işlemi"""
        try:
            # Retry istatistiklerini logla
            retry_stats = self.retry_manager.get_retry_statistics()
            self.logger.info(f"📊 Retry Statistics: {retry_stats['summary']}")
            
            # Integrity checker'ı temizle
            if self.integrity_checker:
                self.integrity_checker.cleanup_old_logs(7)  # Son 7 günü sakla
            
            # Ana sınıfın close metodunu çağır
            super().close()
            
            self.logger.info("✅ Enhanced Database Manager kapatıldı")
            
        except Exception as e:
            self.logger.error(f"❌ Kapatma hatası: {e}")
    
    def execute_with_retry(self, operation: callable, *args, **kwargs):
        """
        Veritabanı operasyonunu retry mekanizması ile çalıştır
        
        Args:
            operation: Çalıştırılacak operasyon
            args: Operasyon argümanları
            kwargs: Operasyon keyword argümanları
            
        Returns:
            RetryResult: Operasyon sonucu
        """
        return self.retry_manager.retry_with_backoff(
            operation,
            *args,
            retry_on_exceptions=(sqlite3.OperationalError, sqlite3.DatabaseError, PermissionError, OSError),
            **kwargs
        )
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Retry istatistiklerini al"""
        return self.retry_manager.get_retry_statistics()
    
    def reset_retry_statistics(self):
        """Retry istatistiklerini sıfırla"""
        self.retry_manager.reset_statistics()
        self.logger.info("📊 Retry statistics reset")
    
    def get_session_with_retry(self):
        """Retry mekanizması ile session al"""
        def get_session_operation():
            return self.get_session()
        
        return self.execute_with_retry(get_session_operation)
    
    def execute_query_with_retry(self, query: str, params: tuple = None):
        """Retry mekanizması ile query çalıştır"""
        def execute_query():
            with self.get_session() as session:
                if params:
                    result = session.execute(query, params)
                else:
                    result = session.execute(query)
                session.commit()
                return result
        
        return self.execute_with_retry(execute_query)
    
    def handle_database_lock_with_retry(self, operation: callable, *args, **kwargs):
        """
        Veritabanı kilidi durumunda özel retry mantığı
        
        Args:
            operation: Çalıştırılacak operasyon
            args: Operasyon argümanları
            kwargs: Operasyon keyword argümanları
        """
        def custom_retry_logic(error: Exception) -> bool:
            error_str = str(error).lower()
            
            # Database locked hatası için özel mantık
            if "database is locked" in error_str:
                self.logger.info("🔒 Database locked detected, checking for file locks...")
                
                # Dosya kilitlerini kontrol et
                if hasattr(self, 'db_path') and self.db_path:
                    locks = self.retry_manager.detect_file_locks(self.db_path)
                    if locks:
                        self.logger.warning(f"⚠️ Found {len(locks)} file locks on database")
                        
                        # Process'lerin tamamlanmasını bekle
                        process_names = [lock.get('process_name', '') for lock in locks]
                        self.retry_manager.wait_for_process_completion(process_names, timeout=10.0)
                
                return True
            
            return False
        
        result = self.retry_manager.retry_with_backoff(
            operation,
            *args,
            custom_retry_logic=custom_retry_logic,
            **kwargs
        )
        
        if not result.success:
            raise result.error
        
        return result.result
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Retry istatistiklerini al"""
        return self.retry_manager.get_retry_statistics()
    
    def reset_retry_statistics(self):
        """Retry istatistiklerini sıfırla"""
        self.retry_manager.reset_statistics()
        self.logger.info("📊 Retry statistics reset")
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive database health check
        
        Returns:
            Dict: Health check results with status, warnings, and recommendations
        """
        try:
            health_status = {
                'status': 'OK',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'checks': {},
                'warnings': [],
                'recommendations': [],
                'metrics': {}
            }
            
            # 1. Connection health
            try:
                connection_start = time.time()
                conn = self._get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    connection_time = time.time() - connection_start
                    
                    health_status['checks']['connection'] = 'OK'
                    health_status['metrics']['connection_time_ms'] = connection_time * 1000
                    
                    if connection_time > 1.0:
                        health_status['warnings'].append(f"Slow database connection: {connection_time:.2f}s")
                    
                    conn.close()
                else:
                    health_status['checks']['connection'] = 'FAILED'
                    health_status['status'] = 'WARNING'
                    
            except Exception as e:
                health_status['checks']['connection'] = f'ERROR: {e}'
                health_status['status'] = 'ERROR'
            
            # 2. Database integrity
            if hasattr(self, 'db_path') and self.db_path and os.path.exists(self.db_path):
                try:
                    integrity_checker = DatabaseIntegrityChecker(self.db_path)
                    integrity_result = integrity_checker.check_database_integrity(create_backup=False)
                    
                    if integrity_result.is_valid:
                        health_status['checks']['integrity'] = 'OK'
                    else:
                        health_status['checks']['integrity'] = f'FAILED: {integrity_result.error_details}'
                        health_status['status'] = 'ERROR'
                        health_status['recommendations'].append("Database integrity check failed - consider backup restoration")
                        
                except Exception as e:
                    health_status['checks']['integrity'] = f'ERROR: {e}'
                    health_status['warnings'].append(f"Could not perform integrity check: {e}")
            
            # 3. File system health
            if hasattr(self, 'db_path') and self.db_path:
                try:
                    # File size
                    if os.path.exists(self.db_path):
                        file_size = os.path.getsize(self.db_path)
                        health_status['metrics']['database_size_mb'] = file_size / (1024 * 1024)
                        
                        # Check for unusually large database
                        if file_size > 500 * 1024 * 1024:  # 500MB
                            health_status['warnings'].append(f"Large database file: {file_size/(1024*1024):.1f} MB")
                            health_status['recommendations'].append("Consider database optimization or archiving old data")
                    
                    # Disk space
                    db_dir = os.path.dirname(self.db_path)
                    if os.path.exists(db_dir):
                        import shutil
                        total, used, free = shutil.disk_usage(db_dir)
                        free_gb = free / (1024**3)
                        health_status['metrics']['free_disk_space_gb'] = free_gb
                        
                        if free_gb < 1.0:
                            health_status['warnings'].append(f"Low disk space: {free_gb:.1f} GB free")
                            health_status['recommendations'].append("Free up disk space to prevent database issues")
                            health_status['status'] = 'WARNING'
                    
                    # File permissions
                    if os.path.exists(self.db_path):
                        readable = os.access(self.db_path, os.R_OK)
                        writable = os.access(self.db_path, os.W_OK)
                        
                        if readable and writable:
                            health_status['checks']['permissions'] = 'OK'
                        else:
                            health_status['checks']['permissions'] = f'LIMITED: R={readable}, W={writable}'
                            health_status['warnings'].append("Limited file permissions detected")
                            if not writable:
                                health_status['status'] = 'WARNING'
                    
                except Exception as e:
                    health_status['warnings'].append(f"File system check error: {e}")
            
            # 4. Performance metrics
            try:
                # Query performance test
                query_start = time.time()
                tezgah_count = self.get_tezgah_count()
                query_time = time.time() - query_start
                
                health_status['metrics']['query_time_ms'] = query_time * 1000
                health_status['metrics']['tezgah_count'] = tezgah_count
                
                if query_time > 2.0:
                    health_status['warnings'].append(f"Slow query performance: {query_time:.2f}s")
                    health_status['recommendations'].append("Consider database optimization or indexing")
                
            except Exception as e:
                health_status['warnings'].append(f"Performance test error: {e}")
            
            # 5. Fallback status
            status = self.get_database_status()
            if status.is_fallback:
                health_status['checks']['fallback_active'] = True
                health_status['metrics']['fallback_type'] = status.fallback_type.value if status.fallback_type else 'unknown'
                health_status['warnings'].append(f"Running in fallback mode: {status.fallback_type.value if status.fallback_type else 'unknown'}")
                
                if status.fallback_type == FallbackType.MEMORY:
                    health_status['recommendations'].append("Data is not persistent in memory mode - resolve database issues")
                    health_status['status'] = 'WARNING'
            else:
                health_status['checks']['fallback_active'] = False
            
            # 6. Connection pool health (if applicable)
            if hasattr(self, 'connection_pool_size'):
                health_status['metrics']['connection_pool_size'] = getattr(self, 'connection_pool_size', 0)
            
            # Final status determination
            if health_status['status'] == 'OK' and health_status['warnings']:
                health_status['status'] = 'WARNING'
            
            self.logger.info(f"🏥 Database health check completed: {health_status['status']}")
            if health_status['warnings']:
                self.logger.info(f"   Warnings: {len(health_status['warnings'])}")
            if health_status['recommendations']:
                self.logger.info(f"   Recommendations: {len(health_status['recommendations'])}")
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"❌ Health check error: {e}")
            return {
                'status': 'ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'checks': {},
                'warnings': [f"Health check failed: {e}"],
                'recommendations': ['Restart application or check database configuration'],
                'metrics': {}
            }