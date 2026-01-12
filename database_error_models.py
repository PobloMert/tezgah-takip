#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Database Error Models
Enhanced database error handling data models
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class PermissionLevel(Enum):
    """Dosya erişim izin seviyeleri"""
    FULL_ACCESS = "full_access"
    READ_ONLY = "read_only"
    NO_ACCESS = "no_access"
    PATH_NOT_EXISTS = "path_not_exists"

class ErrorSeverity(Enum):
    """Hata önem seviyeleri"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FallbackType(Enum):
    """Fallback veritabanı türleri"""
    MEMORY_DATABASE = "memory_database"
    BACKUP_RESTORE = "backup_restore"
    CLEAN_DATABASE = "clean_database"
    ALTERNATIVE_PATH = "alternative_path"
    ALTERNATIVE_LOCATION = "alternative_location"

@dataclass
class PermissionResult:
    """Dosya erişim izin kontrolü sonucu"""
    can_read: bool
    can_write: bool
    can_create: bool
    permission_level: PermissionLevel
    error_message: Optional[str] = None
    suggested_fix: Optional[str] = None
    
    @property
    def has_full_access(self) -> bool:
        return self.can_read and self.can_write and self.can_create

@dataclass
class ErrorAnalysis:
    """Hata analizi sonucu"""
    error_type: str
    error_code: Optional[str]
    probable_cause: str
    severity: ErrorSeverity
    auto_fixable: bool
    suggested_actions: List[str]
    technical_details: Dict[str, Any]
    timestamp: datetime
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()

@dataclass
class DatabaseStatus:
    """Veritabanı durumu bilgisi"""
    is_connected: bool
    database_path: str
    is_fallback: bool
    fallback_type: Optional[FallbackType]
    last_error: Optional[str]
    connection_attempts: int
    integrity_status: str
    last_check_time: datetime
    
    def __post_init__(self):
        if not self.last_check_time:
            self.last_check_time = datetime.now()

@dataclass
class PathResolutionResult:
    """Yol çözümleme sonucu"""
    resolved_path: str
    is_primary_path: bool
    fallback_level: int  # 0 = primary, 1+ = fallback levels
    permission_result: PermissionResult
    creation_required: bool
    warnings: List[str]

@dataclass
class IntegrityCheckResult:
    """Veritabanı bütünlük kontrolü sonucu"""
    is_valid: bool
    corruption_detected: bool
    error_details: List[str]
    repair_possible: bool
    backup_recommended: bool
    check_timestamp: datetime
    
    def __post_init__(self):
        if not self.check_timestamp:
            self.check_timestamp = datetime.now()

@dataclass
class FallbackResult:
    """Fallback işlem sonucu"""
    success: bool
    fallback_type: FallbackType
    database_path: Optional[str]
    message: str
    warnings: List[str]
    engine: Optional[Any] = None  # SQLAlchemy engine
    
    @property
    def is_temporary(self) -> bool:
        """Geçici veritabanı mı?"""
        return self.fallback_type in [FallbackType.MEMORY_DATABASE, FallbackType.CLEAN_DATABASE]

class DatabaseErrorType(Enum):
    """Veritabanı hata türleri"""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"
    FILE_LOCKED = "file_locked"
    CORRUPTION = "corruption"
    NETWORK_PATH = "network_path"
    ANTIVIRUS_BLOCK = "antivirus_block"
    INVALID_PATH = "invalid_path"
    UNKNOWN = "unknown"

# Türkçe hata mesajları
ERROR_MESSAGES_TR = {
    DatabaseErrorType.FILE_NOT_FOUND: "Veritabanı dosyası bulunamadı",
    DatabaseErrorType.PERMISSION_DENIED: "Veritabanı dosyasına erişim izni yok",
    DatabaseErrorType.DISK_FULL: "Disk alanı yetersiz",
    DatabaseErrorType.FILE_LOCKED: "Veritabanı dosyası başka bir işlem tarafından kullanılıyor",
    DatabaseErrorType.CORRUPTION: "Veritabanı dosyası bozuk",
    DatabaseErrorType.NETWORK_PATH: "Ağ yolunda veritabanı erişim sorunu",
    DatabaseErrorType.ANTIVIRUS_BLOCK: "Antivirüs yazılımı dosya erişimini engelliyor",
    DatabaseErrorType.INVALID_PATH: "Geçersiz dosya yolu",
    DatabaseErrorType.UNKNOWN: "Bilinmeyen veritabanı hatası"
}

# Çözüm önerileri
SOLUTION_SUGGESTIONS_TR = {
    DatabaseErrorType.FILE_NOT_FOUND: [
        "Veritabanı dosyasının doğru konumda olduğunu kontrol edin",
        "Uygulamayı yönetici olarak çalıştırmayı deneyin",
        "Yedekten geri yükleme yapın"
    ],
    DatabaseErrorType.PERMISSION_DENIED: [
        "Uygulamayı yönetici olarak çalıştırın",
        "Dosya ve klasör izinlerini kontrol edin",
        "Antivirüs yazılımında istisna ekleyin",
        "Veritabanını farklı bir konuma taşıyın"
    ],
    DatabaseErrorType.DISK_FULL: [
        "Disk alanı açın",
        "Gereksiz dosyaları silin",
        "Veritabanını başka bir diske taşıyın"
    ],
    DatabaseErrorType.FILE_LOCKED: [
        "Diğer TezgahTakip uygulamalarını kapatın",
        "Bilgisayarı yeniden başlatın",
        "Dosyayı kilitleyen işlemi sonlandırın"
    ],
    DatabaseErrorType.CORRUPTION: [
        "Yedekten geri yükleme yapın",
        "Veritabanı onarım aracını çalıştırın",
        "Yeni veritabanı oluşturun"
    ],
    DatabaseErrorType.NETWORK_PATH: [
        "Ağ bağlantısını kontrol edin",
        "Veritabanını yerel diske kopyalayın",
        "Ağ izinlerini kontrol edin"
    ],
    DatabaseErrorType.ANTIVIRUS_BLOCK: [
        "Antivirüs yazılımında TezgahTakip'i istisna listesine ekleyin",
        "Gerçek zamanlı taramayı geçici olarak kapatın",
        "Farklı bir antivirüs yazılımı deneyin"
    ],
    DatabaseErrorType.INVALID_PATH: [
        "Dosya yolunu kontrol edin",
        "Özel karakterleri kaldırın",
        "Daha kısa bir yol kullanın"
    ],
    DatabaseErrorType.UNKNOWN: [
        "Uygulamayı yeniden başlatın",
        "Sistem yöneticisine başvurun",
        "Log dosyalarını kontrol edin"
    ]
}