#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Exception Handler
Merkezi exception handling ve error reporting sistemi
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
from PyQt5.QtWidgets import QMessageBox, QWidget

class TezgahTakipException(Exception):
    """Base exception class for TezgahTakip"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()

class DatabaseException(TezgahTakipException):
    """Veritabanı ile ilgili hatalar"""
    pass

class ValidationException(TezgahTakipException):
    """Validasyon hataları"""
    pass

class SecurityException(TezgahTakipException):
    """Güvenlik ile ilgili hatalar"""
    pass

class APIException(TezgahTakipException):
    """API ile ilgili hatalar"""
    pass

class ConfigurationException(TezgahTakipException):
    """Konfigürasyon hataları"""
    pass

class ExceptionHandler:
    """Merkezi exception handling sınıfı"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}  # Error frequency tracking
        self.last_errors = []   # Son hataları sakla
        
    def handle_exception(self, exc_type, exc_value, exc_traceback, 
                        context: Optional[str] = None,
                        show_user_message: bool = True,
                        parent_widget: Optional[QWidget] = None):
        """
        Exception'ı handle et
        
        Args:
            exc_type: Exception tipi
            exc_value: Exception değeri
            exc_traceback: Traceback
            context: Hata bağlamı
            show_user_message: Kullanıcıya mesaj göster mi
            parent_widget: Parent widget (dialog için)
        """
        try:
            # Exception bilgilerini topla
            error_info = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value) if exc_value else "Unknown error",
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback),
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            # Error frequency tracking
            error_key = f"{exc_type.__name__}:{str(exc_value)[:100]}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Son hataları sakla (max 50)
            self.last_errors.append(error_info)
            if len(self.last_errors) > 50:
                self.last_errors.pop(0)
            
            # Log'a yaz
            self._log_exception(error_info)
            
            # Kullanıcıya mesaj göster
            if show_user_message:
                self._show_user_message(error_info, parent_widget)
                
        except Exception as e:
            # Exception handler'da hata olursa fallback
            print(f"Exception handler failed: {e}")
            print(f"Original exception: {exc_value}")
    
    def _log_exception(self, error_info: Dict[str, Any]):
        """Exception'ı log'a yaz"""
        try:
            log_message = f"""
EXCEPTION OCCURRED:
Type: {error_info['type']}
Message: {error_info['message']}
Context: {error_info.get('context', 'N/A')}
Timestamp: {error_info['timestamp']}
Traceback:
{''.join(error_info['traceback'])}
"""
            self.logger.error(log_message)
            
        except Exception as e:
            print(f"Logging failed: {e}")
    
    def _show_user_message(self, error_info: Dict[str, Any], parent_widget: Optional[QWidget]):
        """Kullanıcıya hata mesajı göster"""
        try:
            error_type = error_info['type']
            error_message = error_info['message']
            
            # Kullanıcı dostu mesajlar
            user_messages = {
                'DatabaseException': '🗄️ Veritabanı hatası oluştu. Lütfen tekrar deneyin.',
                'ValidationException': '⚠️ Girilen veriler geçersiz. Lütfen kontrol edin.',
                'SecurityException': '🔒 Güvenlik hatası tespit edildi. İşlem iptal edildi.',
                'APIException': '🌐 API bağlantı hatası. İnternet bağlantınızı kontrol edin.',
                'ConfigurationException': '⚙️ Konfigürasyon hatası. Ayarları kontrol edin.',
                'ConnectionError': '🔌 Bağlantı hatası. Lütfen tekrar deneyin.',
                'FileNotFoundError': '📁 Dosya bulunamadı. Dosya yolunu kontrol edin.',
                'PermissionError': '🚫 Yetki hatası. Dosya izinlerini kontrol edin.',
                'MemoryError': '💾 Bellek yetersiz. Uygulamayı yeniden başlatın.',
                'TimeoutError': '⏱️ İşlem zaman aşımına uğradı. Tekrar deneyin.'
            }
            
            user_message = user_messages.get(error_type, f'❌ Beklenmeyen hata: {error_message}')
            
            # Teknik detayları sadece geliştirici modunda göster
            detailed_message = f"{user_message}\n\nTeknik Detay: {error_message}"
            
            # QMessageBox göster
            msg_box = QMessageBox(parent_widget)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Hata")
            msg_box.setText(user_message)
            msg_box.setDetailedText(detailed_message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            
        except Exception as e:
            print(f"User message display failed: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Hata istatistiklerini döndür"""
        return {
            "total_errors": len(self.last_errors),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.last_errors[-10:] if self.last_errors else []
        }
    
    def clear_error_history(self):
        """Hata geçmişini temizle"""
        self.last_errors.clear()
        self.error_counts.clear()

# Decorator fonksiyonları
def handle_exceptions(context: Optional[str] = None, 
                     show_user_message: bool = True,
                     reraise: bool = False):
    """
    Exception handling decorator
    
    Args:
        context: Hata bağlamı
        show_user_message: Kullanıcıya mesaj göster mi
        reraise: Exception'ı tekrar raise et mi
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Parent widget'ı bulmaya çalış
                parent_widget = None
                for arg in args:
                    if isinstance(arg, QWidget):
                        parent_widget = arg
                        break
                
                # Exception'ı handle et
                exception_handler.handle_exception(
                    type(e), e, e.__traceback__,
                    context=context or f"{func.__module__}.{func.__name__}",
                    show_user_message=show_user_message,
                    parent_widget=parent_widget
                )
                
                if reraise:
                    raise
                    
                return None
        return wrapper
    return decorator

def database_operation(func: Callable):
    """Veritabanı işlemleri için özel decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Veritabanı hatalarını özel olarak handle et
            if "database" in str(e).lower() or "sqlite" in str(e).lower():
                raise DatabaseException(f"Veritabanı hatası: {e}")
            else:
                raise
    return wrapper

def validation_required(func: Callable):
    """Validasyon gerektiren işlemler için decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise ValidationException(f"Validasyon hatası: {e}")
        except Exception as e:
            raise
    return wrapper

# Global exception handler instance
exception_handler = ExceptionHandler()

# Global exception hook
def global_exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception hook - yakalanmamış exception'lar için"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Ctrl+C'yi normal şekilde handle et
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    exception_handler.handle_exception(
        exc_type, exc_value, exc_traceback,
        context="Global Exception Hook",
        show_user_message=True
    )

# Global exception hook'u ayarla
sys.excepthook = global_exception_hook