#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Ana Uygulama
AI Güçlü Fabrika Bakım Yönetim Sistemi v2.1.2
"""

import sys
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer, QRect, QSize
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QLinearGradient

# DPI Scaling ayarları - QApplication'dan önce ayarlanmalı
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
if hasattr(Qt, 'AA_DisableWindowContextHelpButton'):
    QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)

# Windows'ta DPI awareness ayarla
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        
        # Windows DPI awareness ayarla
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (ImportError, AttributeError, OSError):
        # Fallback - eski Windows versiyonları için
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

# Kendi modüllerimizi import et
try:
    from main_window import TezgahTakipMainWindow, CustomMessageBox
    from database_models import DatabaseManager
    from api_key_manager import APIKeyManager
    from gemini_ai import GeminiAI
except ImportError as e:
    print(f"❌ Modül import hatası: {e}")
    print("Lütfen tüm dosyaların aynı klasörde olduğundan emin olun.")
    sys.exit(1)

class TezgahTakipApp:
    """Ana uygulama sınıfı"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.splash = None
        
        # Logging ayarla
        self.setup_logging()
        
    # Uygulama bilgileri
        self.app_name = "TezgahTakip"
        self.app_version = "2.1.2"
        self.app_description = "AI Güçlü Fabrika Bakım Yönetim Sistemi"
    
    def setup_logging(self):
        """Gelişmiş logging sistemini ayarla"""
        try:
            # Logs klasörü oluştur
            if not os.path.exists("logs"):
                os.makedirs("logs")
            
            # Log dosyası
            log_file = f"logs/tezgah_takip_{datetime.now().strftime('%Y%m%d')}.log"
            
            # Rotating file handler - 10MB max, 5 backup dosyası
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Root logger konfigürasyonu
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("🚀 TezgahTakip uygulaması başlatılıyor...")
            
        except Exception as e:
            print(f"❌ Logging ayarlama hatası: {e}")
            # Fallback basit logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger(__name__)
    
    def create_splash_screen(self):
        """Responsive splash screen oluştur"""
        try:
            # Ekran boyutunu al
            screen = QApplication.primaryScreen()
            screen_size = screen.size()
            
            # Responsive boyut hesapla
            width = min(700, int(screen_size.width() * 0.5))
            height = min(450, int(screen_size.height() * 0.4))
            
            # Splash screen için pixmap oluştur
            pixmap = QPixmap(width, height)
            pixmap.fill(QColor(25, 25, 25))  # Daha koyu arka plan
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Gradient arka plan
            gradient = QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0, QColor(45, 45, 45))
            gradient.setColorAt(1, QColor(25, 25, 25))
            painter.fillRect(0, 0, width, height, gradient)
            
            # Responsive font boyutları
            title_size = max(24, min(32, width // 22))
            subtitle_size = max(12, min(16, width // 44))
            version_size = max(10, min(14, width // 50))
            copyright_size = max(9, min(11, width // 64))
            
            # Başlık - Merkezi ve büyük
            painter.setPen(QColor(255, 255, 255))
            title_font = QFont("Segoe UI", title_size, QFont.Bold)
            painter.setFont(title_font)
            title_rect = QRect(50, height//3, width-100, 50)
            painter.drawText(title_rect, Qt.AlignCenter, "TezgahTakip")
            
            # Alt başlık
            subtitle_font = QFont("Segoe UI", subtitle_size)
            painter.setFont(subtitle_font)
            painter.setPen(QColor(200, 200, 200))
            subtitle_rect = QRect(50, height//3 + 60, width-100, 30)
            painter.drawText(subtitle_rect, Qt.AlignCenter, "AI Güçlü Fabrika Bakım Yönetim Sistemi")
            
            # Versiyon
            version_font = QFont("Segoe UI", version_size)
            painter.setFont(version_font)
            painter.setPen(QColor(150, 150, 150))
            version_rect = QRect(50, height//3 + 100, width-100, 25)
            painter.drawText(version_rect, Qt.AlignCenter, f"v{self.app_version} - Profesyonel Sürüm")
            
            # Copyright - En altta
            copyright_font = QFont("Segoe UI", copyright_size)
            painter.setFont(copyright_font)
            painter.setPen(QColor(120, 120, 120))
            copyright_rect = QRect(50, height-50, width-100, 25)
            painter.drawText(copyright_rect, Qt.AlignCenter, f"© {datetime.now().year} - Tüm hakları saklıdır")
            
            painter.end()
            
            # Splash screen oluştur
            self.splash = QSplashScreen(pixmap)
            self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            
            # Ekranın ortasında konumlandır
            screen_center = screen.geometry().center()
            splash_rect = self.splash.geometry()
            splash_rect.moveCenter(screen_center)
            self.splash.move(splash_rect.topLeft())
            
            self.splash.show()
            
            # Mesaj göster
            self.splash.showMessage("Sistem başlatılıyor...", Qt.AlignBottom | Qt.AlignCenter, QColor(76, 175, 80))
            
            self.logger.info("✅ Responsive splash screen oluşturuldu")
            
        except Exception as e:
            self.logger.error(f"❌ Splash screen oluşturma hatası: {e}")
            # Fallback basit splash
            self.splash = QSplashScreen(QPixmap(400, 300))
            self.splash.show()
    
    def check_system_requirements(self):
        """Sistem gereksinimlerini kontrol et"""
        try:
            self.splash.showMessage("Sistem gereksinimleri kontrol ediliyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            # Python versiyonu
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
                raise SystemError(f"Python 3.7+ gerekli. Mevcut: {python_version.major}.{python_version.minor}")
            
            # PyQt5 kontrolü
            try:
                from PyQt5.QtCore import QT_VERSION_STR
                self.logger.info(f"✅ PyQt5 versiyonu: {QT_VERSION_STR}")
            except ImportError as e:
                raise ImportError("PyQt5 bulunamadı. Lütfen 'pip install PyQt5' çalıştırın.") from e
            
            # SQLAlchemy kontrolü
            try:
                import sqlalchemy
                self.logger.info(f"✅ SQLAlchemy versiyonu: {sqlalchemy.__version__}")
            except ImportError as e:
                raise ImportError("SQLAlchemy bulunamadı. Lütfen 'pip install sqlalchemy' çalıştırın.") from e
            
            # Requests kontrolü
            try:
                import requests
                self.logger.info(f"✅ Requests versiyonu: {requests.__version__}")
            except ImportError as e:
                raise ImportError("Requests bulunamadı. Lütfen 'pip install requests' çalıştırın.") from e
            
            self.logger.info("✅ Sistem gereksinimleri karşılanıyor")
            return True
            
        except (SystemError, ImportError) as e:
            self.logger.error(f"❌ Sistem gereksinim hatası: {e}")
            from main_window import CustomMessageBox
            CustomMessageBox.critical(None, "Sistem Gereksinim Hatası", 
                               f"Sistem gereksinimleri karşılanmıyor:\n\n{e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Beklenmeyen sistem kontrol hatası: {e}")
            return False
    
    def initialize_database(self):
        """Veritabanını başlat"""
        try:
            self.splash.showMessage("Veritabanı başlatılıyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            # Veritabanı yöneticisini oluştur
            from database_models import DatabaseManager
            db_manager = DatabaseManager()
            
            # Test bağlantısı
            tezgah_count = db_manager.get_tezgah_count()
            self.logger.info(f"✅ Veritabanı bağlantısı başarılı. Toplam tezgah: {tezgah_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Veritabanı başlatma hatası: {e}")
            from main_window import CustomMessageBox
            CustomMessageBox.critical(None, "Veritabanı Hatası", 
                               f"Veritabanı başlatılamadı:\n\n{e}")
            return False
    
    def check_api_configuration(self):
        """API konfigürasyonunu kontrol et"""
        try:
            self.splash.showMessage("API konfigürasyonu kontrol ediliyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            from api_key_manager import APIKeyManager
            from gemini_ai import GeminiAI
            
            api_manager = APIKeyManager()
            
            if api_manager.has_api_key():
                self.logger.info("✅ API anahtarı mevcut")
                
                # API bağlantısını test et
                gemini_ai = GeminiAI()
                success, message = gemini_ai.test_connection()
                
                if success:
                    self.logger.info("✅ Gemini AI bağlantısı başarılı")
                else:
                    self.logger.warning(f"⚠️ Gemini AI bağlantı sorunu: {message}")
            else:
                self.logger.info("ℹ️ API anahtarı bulunamadı - kullanıcıdan istenecek")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ API konfigürasyon hatası: {e}")
            # API hatası kritik değil, uygulama çalışmaya devam edebilir
            return True
    
    def create_main_window(self):
        """Ana pencereyi oluştur"""
        try:
            self.splash.showMessage("Ana pencere oluşturuluyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            # Ana pencereyi oluştur
            from main_window import TezgahTakipMainWindow
            self.main_window = TezgahTakipMainWindow()
            
            self.logger.info("✅ Ana pencere oluşturuldu")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ana pencere oluşturma hatası: {e}")
            from main_window import CustomMessageBox
            CustomMessageBox.critical(None, "Uygulama Hatası", 
                               f"Ana pencere oluşturulamadı:\n\n{e}")
            return False
    
    def show_main_window(self):
        """Ana pencereyi göster"""
        try:
            # Splash screen'i kapat
            if self.splash:
                self.splash.finish(self.main_window)
            
            # Ana pencereyi göster
            self.main_window.show()
            
            # Pencereyi öne getir
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            self.logger.info("✅ Ana pencere gösterildi")
            
        except Exception as e:
            self.logger.error(f"❌ Ana pencere gösterme hatası: {e}")
    
    def setup_exception_handler(self):
        """Global exception handler ayarla"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_msg = f"Beklenmeyen hata:\n{exc_type.__name__}: {exc_value}"
            self.logger.critical(error_msg, exc_info=(exc_type, exc_value, exc_traceback))
            
            CustomMessageBox.critical(None, "Kritik Hata", 
                               f"Beklenmeyen bir hata oluştu:\n\n{error_msg}\n\n"
                               "Lütfen uygulamayı yeniden başlatın.")
        
        sys.excepthook = handle_exception
    
    def run(self):
        """Uygulamayı çalıştır"""
        try:
            # QApplication oluştur
            self.app = QApplication(sys.argv)
            
            # Uygulama bilgilerini ayarla
            self.app.setApplicationName(self.app_name)
            self.app.setApplicationVersion(self.app_version)
            self.app.setOrganizationName("TezgahTakip")
            
            # Exception handler ayarla
            self.setup_exception_handler()
            
            # Splash screen göster
            self.create_splash_screen()
            
            # Başlatma adımları
            steps = [
                ("Sistem gereksinimleri", self.check_system_requirements),
                ("Veritabanı", self.initialize_database),
                ("API konfigürasyonu", self.check_api_configuration),
                ("Ana pencere", self.create_main_window)
            ]
            
            for step_name, step_func in steps:
                self.logger.info(f"🔄 {step_name} kontrol ediliyor...")
                
                if not step_func():
                    self.logger.error(f"❌ {step_name} başarısız!")
                    return 1
                
                # Kısa bekleme (splash screen için)
                self.app.processEvents()
                QTimer.singleShot(500, lambda: None)
                self.app.processEvents()
            
            # Ana pencereyi göster
            self.show_main_window()
            
            # Başarı mesajı
            self.logger.info("🎉 TezgahTakip başarıyla başlatıldı!")
            
            # Uygulamayı çalıştır
            return self.app.exec_()
            
        except Exception as e:
            self.logger.critical(f"❌ Kritik başlatma hatası: {e}")
            
            if self.splash:
                self.splash.close()
            
            CustomMessageBox.critical(None, "Kritik Hata", 
                               f"Uygulama başlatılamadı:\n\n{e}")
            return 1
        
        finally:
            # Temizlik işlemleri
            self.logger.info("🧹 Uygulama kapatılıyor...")
            
            # Timer'ları durdur
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.cleanup_resources()
            
            # Veritabanı bağlantısını kapat
            try:
                from database_models import DatabaseManager
                # Global cleanup
                pass
            except:
                pass

def main():
    """Ana giriş noktası"""
    print("🏭 TezgahTakip - AI Güçlü Fabrika Bakım Yönetim Sistemi v2.1")
    print("=" * 60)
    
    try:
        # Uygulamayı oluştur ve çalıştır
        app = TezgahTakipApp()
        exit_code = app.run()
        
        print(f"Uygulama çıkış kodu: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⚠️ Kullanıcı tarafından iptal edildi")
        return 0
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())