#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Enhanced Exception Handler
Gelişmiş veritabanı hata analizi ve çözüm önerisi sistemi
"""

import sqlite3
import os
import shutil
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from database_error_models import (
    ErrorAnalysis, ErrorSeverity, DatabaseErrorType,
    ERROR_MESSAGES_TR, SOLUTION_SUGGESTIONS_TR
)

# Custom Exception Classes
class DatabaseException(Exception):
    """Veritabanı işlemleri için özel hata sınıfı"""
    def __init__(self, message, error_code=None, original_error=None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error

class ValidationException(Exception):
    """Veri doğrulama için özel hata sınıfı"""
    def __init__(self, message, field_name=None, invalid_value=None):
        super().__init__(message)
        self.field_name = field_name
        self.invalid_value = invalid_value

class EnhancedErrorHandler:
    """
    Gelişmiş hata yönetimi sınıfı
    SQLite hatalarını analiz eder ve kullanıcı dostu çözümler önerir
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Enhanced Error Handler başlatıcı
        
        Args:
            logger: Loglama için kullanılacak logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._error_patterns = self._initialize_error_patterns()
        
    def _initialize_error_patterns(self) -> Dict[str, DatabaseErrorType]:
        """SQLite hata mesajları için pattern tanımları"""
        return {
            r"unable to open database file": DatabaseErrorType.FILE_NOT_FOUND,
            r"database is locked": DatabaseErrorType.FILE_LOCKED,
            r"permission denied": DatabaseErrorType.PERMISSION_DENIED,
            r"access is denied": DatabaseErrorType.PERMISSION_DENIED,
            r"no such file or directory": DatabaseErrorType.FILE_NOT_FOUND,
            r"disk I/O error": DatabaseErrorType.DISK_FULL,
            r"database disk image is malformed": DatabaseErrorType.CORRUPTION,
            r"file is not a database": DatabaseErrorType.CORRUPTION,
            r"database corruption": DatabaseErrorType.CORRUPTION,
            r"network path": DatabaseErrorType.NETWORK_PATH,
            r"unc path": DatabaseErrorType.NETWORK_PATH,
            r"virus": DatabaseErrorType.ANTIVIRUS_BLOCK,
            r"antivirus": DatabaseErrorType.ANTIVIRUS_BLOCK,
            r"invalid path": DatabaseErrorType.INVALID_PATH,
            r"path too long": DatabaseErrorType.INVALID_PATH,
        }
    
    def analyze_sqlite_error(self, error: Exception) -> ErrorAnalysis:
        """
        SQLite hatasını analiz eder ve detaylı bilgi sağlar
        
        Args:
            error: Analiz edilecek hata
            
        Returns:
            ErrorAnalysis: Hata analizi sonucu
        """
        error_message = str(error).lower()
        error_type = self._detect_error_type(error_message)
        
        # Hata kodunu çıkar
        error_code = self._extract_error_code(error)
        
        # Olası nedeni belirle
        probable_cause = self._determine_probable_cause(error_type, error_message)
        
        # Önem seviyesini belirle
        severity = self._determine_severity(error_type)
        
        # Otomatik düzeltilebilirlik
        auto_fixable = self._is_auto_fixable(error_type)
        
        # Önerilen aksiyonlar
        suggested_actions = self._get_suggested_actions(error_type)
        
        # Teknik detaylar
        technical_details = self._gather_technical_details(error, error_type)
        
        analysis = ErrorAnalysis(
            error_type=error_type.value,
            error_code=error_code,
            probable_cause=probable_cause,
            severity=severity,
            auto_fixable=auto_fixable,
            suggested_actions=suggested_actions,
            technical_details=technical_details,
            timestamp=datetime.now()
        )
        
        self.log_error_with_context(error, analysis.__dict__)
        return analysis
    
    def _detect_error_type(self, error_message: str) -> DatabaseErrorType:
        """Hata mesajından hata türünü tespit eder"""
        for pattern, error_type in self._error_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                return error_type
        return DatabaseErrorType.UNKNOWN
    
    def _extract_error_code(self, error: Exception) -> Optional[str]:
        """Hata nesnesinden hata kodunu çıkarır"""
        if isinstance(error, sqlite3.Error):
            # SQLite hata kodlarını çıkar
            error_str = str(error)
            code_match = re.search(r'\((\d+)\)', error_str)
            if code_match:
                return code_match.group(1)
        return None
    
    def _determine_probable_cause(self, error_type: DatabaseErrorType, error_message: str) -> str:
        """Hata türüne göre olası nedeni belirler"""
        cause_map = {
            DatabaseErrorType.FILE_NOT_FOUND: "Veritabanı dosyası mevcut değil veya yol hatalı",
            DatabaseErrorType.PERMISSION_DENIED: "Dosya erişim izinleri yetersiz",
            DatabaseErrorType.DISK_FULL: "Disk alanı yetersiz veya I/O hatası",
            DatabaseErrorType.FILE_LOCKED: "Dosya başka bir işlem tarafından kullanılıyor",
            DatabaseErrorType.CORRUPTION: "Veritabanı dosyası bozulmuş",
            DatabaseErrorType.NETWORK_PATH: "Ağ yolunda erişim sorunu",
            DatabaseErrorType.ANTIVIRUS_BLOCK: "Antivirüs yazılımı erişimi engelliyor",
            DatabaseErrorType.INVALID_PATH: "Geçersiz veya çok uzun dosya yolu",
            DatabaseErrorType.UNKNOWN: "Bilinmeyen sistem hatası"
        }
        return cause_map.get(error_type, "Belirlenemeyen neden")
    
    def _determine_severity(self, error_type: DatabaseErrorType) -> ErrorSeverity:
        """Hata türüne göre önem seviyesini belirler"""
        severity_map = {
            DatabaseErrorType.FILE_NOT_FOUND: ErrorSeverity.HIGH,
            DatabaseErrorType.PERMISSION_DENIED: ErrorSeverity.HIGH,
            DatabaseErrorType.DISK_FULL: ErrorSeverity.CRITICAL,
            DatabaseErrorType.FILE_LOCKED: ErrorSeverity.MEDIUM,
            DatabaseErrorType.CORRUPTION: ErrorSeverity.CRITICAL,
            DatabaseErrorType.NETWORK_PATH: ErrorSeverity.MEDIUM,
            DatabaseErrorType.ANTIVIRUS_BLOCK: ErrorSeverity.HIGH,
            DatabaseErrorType.INVALID_PATH: ErrorSeverity.MEDIUM,
            DatabaseErrorType.UNKNOWN: ErrorSeverity.MEDIUM
        }
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)
    
    def _is_auto_fixable(self, error_type: DatabaseErrorType) -> bool:
        """Hatanın otomatik olarak düzeltilebilir olup olmadığını belirler"""
        auto_fixable_types = {
            DatabaseErrorType.FILE_NOT_FOUND,
            DatabaseErrorType.FILE_LOCKED,
            DatabaseErrorType.INVALID_PATH
        }
        return error_type in auto_fixable_types
    
    def _get_suggested_actions(self, error_type: DatabaseErrorType) -> List[str]:
        """Hata türüne göre önerilen aksiyonları döndürür"""
        return SOLUTION_SUGGESTIONS_TR.get(error_type, [])
    
    def _gather_technical_details(self, error: Exception, error_type: DatabaseErrorType) -> Dict[str, Any]:
        """Teknik detayları toplar"""
        details = {
            "exception_type": type(error).__name__,
            "exception_message": str(error),
            "error_category": error_type.value,
            "system_info": self._get_system_info()
        }
        
        # SQLite özel bilgileri
        if isinstance(error, sqlite3.Error):
            details["sqlite_version"] = sqlite3.sqlite_version
            details["sqlite_version_info"] = sqlite3.version_info
        
        return details
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Sistem bilgilerini toplar"""
        return {
            "platform": os.name,
            "current_directory": os.getcwd(),
            "available_disk_space": self._get_available_disk_space(),
            "temp_directory": self._get_temp_directory()
        }
    
    def _get_available_disk_space(self) -> Optional[int]:
        """Mevcut disk alanını döndürür (bytes)"""
        try:
            _, _, free_bytes = shutil.disk_usage(os.getcwd())
            return free_bytes
        except Exception:
            return None
    
    def _get_temp_directory(self) -> str:
        """Geçici dizin yolunu döndürür"""
        try:
            return str(Path.home() / "AppData" / "Local" / "Temp")
        except Exception:
            return os.path.expanduser("~")
    
    def get_solution_suggestions(self, error_type: str) -> List[str]:
        """
        Hata türüne göre çözüm önerilerini döndürür
        
        Args:
            error_type: Hata türü string değeri
            
        Returns:
            List[str]: Çözüm önerileri listesi
        """
        try:
            db_error_type = DatabaseErrorType(error_type)
            return SOLUTION_SUGGESTIONS_TR.get(db_error_type, [])
        except ValueError:
            return ["Bilinmeyen hata türü için genel çözümler deneyin"]
    
    def format_user_message(self, error: Exception, solutions: List[str]) -> str:
        """
        Kullanıcı dostu hata mesajı formatlar
        
        Args:
            error: Hata nesnesi
            solutions: Çözüm önerileri
            
        Returns:
            str: Formatlanmış kullanıcı mesajı
        """
        analysis = self.analyze_sqlite_error(error)
        
        # Ana hata mesajı
        main_message = ERROR_MESSAGES_TR.get(
            DatabaseErrorType(analysis.error_type),
            "Veritabanı erişim hatası oluştu"
        )
        
        # Detaylı açıklama
        detailed_explanation = f"Neden: {analysis.probable_cause}"
        
        # Çözüm önerileri
        solutions_text = ""
        if solutions:
            solutions_text = "\n\nÖnerilen Çözümler:\n"
            for i, solution in enumerate(solutions, 1):
                solutions_text += f"{i}. {solution}\n"
        
        # Önem seviyesine göre ek bilgi
        severity_info = ""
        if analysis.severity == ErrorSeverity.CRITICAL:
            severity_info = "\n⚠️ KRİTİK: Bu hata uygulamanın çalışmasını engelleyebilir."
        elif analysis.severity == ErrorSeverity.HIGH:
            severity_info = "\n⚠️ ÖNEMLİ: Bu hata çözülmezse veri kaybı yaşanabilir."
        
        return f"{main_message}\n\n{detailed_explanation}{solutions_text}{severity_info}"
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Hatayı context bilgileriyle birlikte loglar
        
        Args:
            error: Hata nesnesi
            context: Context bilgileri
        """
        log_message = f"Database Error Analysis: {type(error).__name__}: {str(error)}"
        
        # Context bilgilerini ekle
        if context:
            log_message += f"\nContext: {context}"
        
        self.logger.error(log_message, exc_info=True)
    
    def check_disk_space(self, path: str, required_mb: int = 100) -> Dict[str, Any]:
        """
        Disk alanını kontrol eder ve temizlik önerileri sunar
        
        Args:
            path: Kontrol edilecek yol
            required_mb: Gerekli alan (MB)
            
        Returns:
            Dict: Disk alanı bilgileri ve öneriler
        """
        try:
            total, used, free = shutil.disk_usage(path)
            free_mb = free // (1024 * 1024)
            
            result = {
                "free_space_mb": free_mb,
                "required_mb": required_mb,
                "sufficient": free_mb >= required_mb,
                "cleanup_suggestions": []
            }
            
            if not result["sufficient"]:
                result["cleanup_suggestions"] = [
                    "Geri Dönüşüm Kutusu'nu boşaltın",
                    "Geçici dosyaları temizleyin (%temp% klasörü)",
                    "Kullanılmayan programları kaldırın",
                    "Disk Temizleme aracını çalıştırın",
                    f"En az {required_mb - free_mb} MB daha alan açmanız gerekiyor"
                ]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Disk alanı kontrolü başarısız: {e}")
            return {
                "free_space_mb": 0,
                "required_mb": required_mb,
                "sufficient": False,
                "cleanup_suggestions": ["Disk alanı kontrol edilemedi"]
            }
    
    def get_permission_fix_instructions(self, path: str) -> List[str]:
        """
        İzin sorunları için düzeltme talimatları
        
        Args:
            path: Sorunlu dosya yolu
            
        Returns:
            List[str]: Adım adım talimatlar
        """
        return [
            f"1. '{path}' klasörüne sağ tıklayın",
            "2. 'Özellikler' seçeneğini tıklayın",
            "3. 'Güvenlik' sekmesine geçin",
            "4. 'Düzenle' butonuna tıklayın",
            "5. Kullanıcı adınızı seçin",
            "6. 'Tam denetim' kutusunu işaretleyin",
            "7. 'Tamam' butonlarına tıklayarak kaydedin",
            "8. Uygulamayı yeniden başlatın"
        ]
    
    def get_antivirus_exclusion_recommendations(self, app_path: str) -> List[str]:
        """
        Antivirüs istisna önerileri
        
        Args:
            app_path: Uygulama yolu
            
        Returns:
            List[str]: Antivirüs ayar önerileri
        """
        return [
            "Antivirüs yazılımınızın ayarlarını açın",
            f"İstisna listesine şu klasörü ekleyin: {app_path}",
            "TezgahTakip.exe dosyasını istisna listesine ekleyin",
            "Veritabanı dosyalarını (.db, .sqlite) istisna listesine ekleyin",
            "Gerçek zamanlı taramayı geçici olarak kapatmayı deneyin",
            "Antivirüs güncellemelerini kontrol edin",
            "Farklı bir antivirüs yazılımı kullanmayı düşünün"
        ]
    
    def get_comprehensive_solution_suggestions(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Kapsamlı çözüm önerisi sistemi
        Hata analizi, disk alanı kontrolü ve özel öneriler içerir
        
        Args:
            error: Analiz edilecek hata
            context: Ek context bilgileri
            
        Returns:
            Dict: Kapsamlı çözüm önerileri
        """
        analysis = self.analyze_sqlite_error(error)
        context = context or {}
        
        # Temel çözüm önerileri
        base_solutions = self.get_solution_suggestions(analysis.error_type)
        
        # Disk alanı kontrolü
        current_path = context.get('database_path', '.')
        disk_info = self.check_disk_space(current_path)
        
        # İzin kontrolü önerileri
        permission_instructions = []
        if analysis.error_type in [DatabaseErrorType.PERMISSION_DENIED.value]:
            permission_instructions = self.get_permission_fix_instructions(current_path)
        
        # Antivirüs önerileri
        antivirus_recommendations = []
        if analysis.error_type in [DatabaseErrorType.ANTIVIRUS_BLOCK.value, DatabaseErrorType.PERMISSION_DENIED.value]:
            app_path = context.get('app_path', os.getcwd())
            antivirus_recommendations = self.get_antivirus_exclusion_recommendations(app_path)
        
        # Acil durum çözümleri
        emergency_solutions = self._get_emergency_solutions(analysis.error_type)
        
        # Önleyici tedbirler
        preventive_measures = self._get_preventive_measures(analysis.error_type)
        
        return {
            "error_analysis": analysis,
            "immediate_solutions": base_solutions,
            "disk_space_info": disk_info,
            "permission_instructions": permission_instructions,
            "antivirus_recommendations": antivirus_recommendations,
            "emergency_solutions": emergency_solutions,
            "preventive_measures": preventive_measures,
            "priority_order": self._determine_solution_priority(analysis.error_type),
            "estimated_fix_time": self._estimate_fix_time(analysis.error_type),
            "requires_admin": self._requires_admin_rights(analysis.error_type)
        }
    
    def _get_emergency_solutions(self, error_type: str) -> List[str]:
        """Acil durum çözümleri"""
        emergency_map = {
            DatabaseErrorType.DISK_FULL.value: [
                "Geçici dosyaları hemen silin (%temp% klasörü)",
                "Geri Dönüşüm Kutusu'nu boşaltın",
                "Büyük dosyaları başka bir diske taşıyın",
                "Sistem geri yükleme noktalarını silin"
            ],
            DatabaseErrorType.CORRUPTION.value: [
                "Uygulamayı hemen kapatın",
                "Veritabanı dosyasını yedekleyin (bozuk olsa bile)",
                "Son yedekten geri yükleme yapın",
                "Veri kurtarma araçları kullanın"
            ],
            DatabaseErrorType.FILE_LOCKED.value: [
                "Tüm TezgahTakip uygulamalarını kapatın",
                "Görev Yöneticisi'nden ilgili işlemleri sonlandırın",
                "Bilgisayarı yeniden başlatın",
                "Güvenli modda çalıştırın"
            ]
        }
        return emergency_map.get(error_type, [])
    
    def _get_preventive_measures(self, error_type: str) -> List[str]:
        """Önleyici tedbirler"""
        preventive_map = {
            DatabaseErrorType.DISK_FULL.value: [
                "Otomatik disk temizleme ayarlayın",
                "Düzenli yedekleme yapın",
                "Disk alanı izleme araçları kullanın",
                "Veritabanı boyutunu düzenli kontrol edin"
            ],
            DatabaseErrorType.CORRUPTION.value: [
                "Düzenli veritabanı yedeklemesi yapın",
                "Sistem kararlılığını kontrol edin",
                "Disk sağlığını izleyin",
                "UPS kullanarak ani güç kesintilerini önleyin"
            ],
            DatabaseErrorType.PERMISSION_DENIED.value: [
                "Kullanıcı hesabı izinlerini düzenli kontrol edin",
                "Antivirüs istisnalarını güncel tutun",
                "Sistem güncellemelerini takip edin",
                "Yönetici hakları gerektiren işlemleri belirleyin"
            ]
        }
        return preventive_map.get(error_type, [])
    
    def _determine_solution_priority(self, error_type: str) -> List[str]:
        """Çözüm öncelik sırası"""
        priority_map = {
            DatabaseErrorType.FILE_LOCKED.value: [
                "emergency_solutions", "immediate_solutions", "preventive_measures"
            ],
            DatabaseErrorType.DISK_FULL.value: [
                "emergency_solutions", "disk_space_info", "immediate_solutions"
            ],
            DatabaseErrorType.PERMISSION_DENIED.value: [
                "permission_instructions", "antivirus_recommendations", "immediate_solutions"
            ],
            DatabaseErrorType.CORRUPTION.value: [
                "emergency_solutions", "immediate_solutions", "preventive_measures"
            ]
        }
        return priority_map.get(error_type, ["immediate_solutions", "preventive_measures"])
    
    def _estimate_fix_time(self, error_type: str) -> str:
        """Tahmini çözüm süresi"""
        time_map = {
            DatabaseErrorType.FILE_LOCKED.value: "2-5 dakika",
            DatabaseErrorType.PERMISSION_DENIED.value: "5-15 dakika",
            DatabaseErrorType.DISK_FULL.value: "10-30 dakika",
            DatabaseErrorType.CORRUPTION.value: "15-60 dakika",
            DatabaseErrorType.ANTIVIRUS_BLOCK.value: "5-10 dakika"
        }
        return time_map.get(error_type, "5-20 dakika")
    
    def _requires_admin_rights(self, error_type: str) -> bool:
        """Yönetici hakları gereksinimi"""
        admin_required = {
            DatabaseErrorType.PERMISSION_DENIED.value,
            DatabaseErrorType.ANTIVIRUS_BLOCK.value,
            DatabaseErrorType.FILE_LOCKED.value
        }
        return error_type in admin_required

# Decorator Functions
def handle_exceptions(func):
    """
    Genel hata yakalama decorator'ı
    Fonksiyonları otomatik hata yönetimi ile sarar
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseException as e:
            # Veritabanı hatalarını özel olarak işle
            handler = EnhancedErrorHandler()
            analysis = handler.analyze_sqlite_error(e.original_error or e)
            
            # Kullanıcı dostu mesaj göster
            user_message = handler.format_user_message(e.original_error or e, 
                                                     handler.get_solution_suggestions(analysis.error_type))
            
            # Log'a kaydet
            handler.log_error_with_context(e, {'function': func.__name__, 'args': str(args)})
            
            # Hata mesajını döndür veya yeniden fırlat
            raise DatabaseException(user_message, original_error=e.original_error)
            
        except ValidationException as e:
            # Doğrulama hatalarını işle
            handler = EnhancedErrorHandler()
            handler.logger.warning(f"Validation error in {func.__name__}: {e}")
            raise
            
        except Exception as e:
            # Diğer tüm hataları işle
            handler = EnhancedErrorHandler()
            handler.logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            
            # SQLite hatası ise özel işlem yap
            if 'sqlite' in str(e).lower() or 'database' in str(e).lower():
                analysis = handler.analyze_sqlite_error(e)
                user_message = handler.format_user_message(e, 
                                                         handler.get_solution_suggestions(analysis.error_type))
                raise DatabaseException(user_message, original_error=e)
            else:
                # Genel hata olarak yeniden fırlat
                raise
    
    return wrapper

def database_operation(func):
    """
    Veritabanı işlemleri için özel decorator
    SQLite hatalarını otomatik olarak yakalar ve analiz eder
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            # SQLite hatalarını özel olarak işle
            handler = EnhancedErrorHandler()
            analysis = handler.analyze_sqlite_error(e)
            
            # Kapsamlı çözüm önerileri al
            solutions = handler.get_comprehensive_solution_suggestions(e, {
                'function': func.__name__,
                'database_path': kwargs.get('db_path', '.'),
                'app_path': os.getcwd()
            })
            
            # Kullanıcı dostu mesaj oluştur
            user_message = handler.format_user_message(e, solutions['immediate_solutions'])
            
            # DatabaseException olarak yeniden fırlat
            raise DatabaseException(user_message, error_code=analysis.error_code, original_error=e)
            
        except Exception as e:
            # Diğer hataları genel handler'a yönlendir
            return handle_exceptions(func)(*args, **kwargs)
    
    return wrapper

def validation_required(required_fields=None, field_types=None):
    """
    Veri doğrulama decorator'ı
    Fonksiyon parametrelerini otomatik olarak doğrular
    
    Args:
        required_fields: Zorunlu alanlar listesi
        field_types: Alan tipleri sözlüğü {field_name: expected_type}
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Zorunlu alanları kontrol et
            if required_fields:
                for field in required_fields:
                    if field not in kwargs or kwargs[field] is None:
                        raise ValidationException(
                            f"Zorunlu alan eksik: {field}",
                            field_name=field
                        )
            
            # Alan tiplerini kontrol et
            if field_types:
                for field_name, expected_type in field_types.items():
                    if field_name in kwargs:
                        value = kwargs[field_name]
                        if value is not None and not isinstance(value, expected_type):
                            raise ValidationException(
                                f"Geçersiz veri tipi: {field_name} {expected_type.__name__} olmalı, {type(value).__name__} verildi",
                                field_name=field_name,
                                invalid_value=value
                            )
            
            # Fonksiyonu çalıştır
            return func(*args, **kwargs)
        
        return wrapper
    return decorator