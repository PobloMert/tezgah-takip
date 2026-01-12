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
    
    def run_startup_diagnostics(self):
        """Gelişmiş startup diagnostics ve health checks"""
        try:
            self.splash.showMessage("Kapsamlı sistem tanılaması çalıştırılıyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            diagnostics = {
                'system_info': {},
                'disk_space': {},
                'permissions': {},
                'dependencies': {},
                'database_paths': {},
                'enhanced_components': {},
                'backup_system': {},
                'logging_system': {}
            }
            
            # Sistem bilgileri
            import platform
            diagnostics['system_info'] = {
                'platform': platform.system(),
                'version': platform.version(),
                'architecture': platform.architecture()[0],
                'python_version': platform.python_version(),
                'working_directory': os.getcwd(),
                'user_home': os.path.expanduser('~'),
                'temp_dir': os.path.join(os.getcwd(), 'temp')
            }
            
            # Disk alanı kontrolü - çoklu lokasyon
            import shutil
            locations_to_check = [
                ('Working Directory', os.getcwd()),
                ('User Documents', os.path.expanduser('~/Documents')),
                ('User Home', os.path.expanduser('~')),
                ('Temp Directory', os.path.join(os.getcwd(), 'temp'))
            ]
            
            diagnostics['disk_space'] = {}
            for name, path in locations_to_check:
                try:
                    if os.path.exists(os.path.dirname(path)):
                        total, used, free = shutil.disk_usage(os.path.dirname(path))
                        diagnostics['disk_space'][name] = {
                            'path': path,
                            'total_gb': total / (1024**3),
                            'used_gb': used / (1024**3),
                            'free_gb': free / (1024**3),
                            'usage_percent': (used / total) * 100,
                            'status': 'OK' if free > 1024**3 else 'LOW'  # 1GB threshold
                        }
                except Exception as e:
                    diagnostics['disk_space'][name] = {'error': str(e)}
            
            # Kritik dizinler için gelişmiş izin kontrolü
            critical_paths = [
                ('App Directory', os.getcwd()),
                ('Logs Directory', os.path.join(os.getcwd(), 'logs')),
                ('Backups Directory', os.path.join(os.getcwd(), 'backups')),
                ('Exports Directory', os.path.join(os.getcwd(), 'exports')),
                ('Temp Directory', os.path.join(os.getcwd(), 'temp')),
                ('User Documents', os.path.expanduser('~/Documents')),
                ('User AppData', os.path.expanduser('~/AppData/Local') if platform.system() == 'Windows' else os.path.expanduser('~/.local'))
            ]
            
            for name, path in critical_paths:
                try:
                    os.makedirs(path, exist_ok=True)
                    
                    # Test dosyası ile yazma kontrolü
                    test_file = os.path.join(path, '.tezgah_test_write')
                    can_write = False
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        can_write = True
                    except:
                        pass
                    
                    diagnostics['permissions'][name] = {
                        'path': path,
                        'exists': os.path.exists(path),
                        'readable': os.access(path, os.R_OK),
                        'writable': os.access(path, os.W_OK),
                        'executable': os.access(path, os.X_OK),
                        'write_test': can_write,
                        'status': 'OK' if (os.access(path, os.R_OK) and can_write) else 'PROBLEM'
                    }
                except Exception as e:
                    diagnostics['permissions'][name] = {'error': str(e), 'status': 'ERROR'}
            
            # Gelişmiş bağımlılık kontrolü
            dependencies = {
                'PyQt5': 'GUI framework',
                'sqlalchemy': 'Database ORM',
                'requests': 'HTTP client',
                'sqlite3': 'Database engine',
                'logging': 'Logging system',
                'json': 'JSON processing',
                'datetime': 'Date/time handling',
                'pathlib': 'Path operations',
                'shutil': 'File operations',
                'tempfile': 'Temporary files'
            }
            
            for dep, description in dependencies.items():
                try:
                    module = __import__(dep)
                    version = getattr(module, '__version__', 'Unknown')
                    diagnostics['dependencies'][dep] = {
                        'status': 'OK',
                        'version': version,
                        'description': description
                    }
                except ImportError as e:
                    diagnostics['dependencies'][dep] = {
                        'status': 'MISSING',
                        'error': str(e),
                        'description': description
                    }
            
            # Enhanced Database Manager bileşenleri kontrolü
            enhanced_components = [
                ('DatabasePathResolver', 'database_path_resolver'),
                ('FileAccessValidator', 'file_access_validator'),
                ('FallbackSystem', 'fallback_system'),
                ('DatabaseIntegrityChecker', 'database_integrity_checker'),
                ('AutomaticRetryManager', 'automatic_retry_manager'),
                ('DatabaseMigrationManager', 'database_migration_manager'),
                ('EnhancedDatabaseManager', 'enhanced_database_manager')
            ]
            
            for component_name, module_name in enhanced_components:
                try:
                    module = __import__(module_name)
                    diagnostics['enhanced_components'][component_name] = {
                        'status': 'OK',
                        'module': module_name,
                        'available': True
                    }
                except ImportError as e:
                    diagnostics['enhanced_components'][component_name] = {
                        'status': 'MISSING',
                        'error': str(e),
                        'available': False
                    }
            
            # Veritabanı yolu analizi - gelişmiş
            try:
                from database_path_resolver import DatabasePathResolver
                path_resolver = DatabasePathResolver()
                fallback_paths = path_resolver.get_fallback_paths()
                
                for i, path in enumerate(fallback_paths):
                    accessibility = path_resolver.validate_path_accessibility(path)
                    diagnostics['database_paths'][f'fallback_{i}'] = {
                        'path': path,
                        'accessible': accessibility,
                        'priority': i + 1,
                        'directory_exists': os.path.exists(os.path.dirname(path)),
                        'parent_writable': os.access(os.path.dirname(path), os.W_OK) if os.path.exists(os.path.dirname(path)) else False
                    }
            except Exception as e:
                diagnostics['database_paths']['error'] = str(e)
            
            # Backup sistem kontrolü
            try:
                from advanced_backup_manager import AdvancedBackupManager
                backup_dir = os.path.join(os.getcwd(), 'backups')
                diagnostics['backup_system'] = {
                    'backup_directory': backup_dir,
                    'directory_exists': os.path.exists(backup_dir),
                    'directory_writable': os.access(backup_dir, os.W_OK) if os.path.exists(backup_dir) else False,
                    'manager_available': True
                }
            except ImportError:
                diagnostics['backup_system'] = {
                    'manager_available': False,
                    'error': 'AdvancedBackupManager not found'
                }
            
            # Logging sistem kontrolü
            log_dir = os.path.join(os.getcwd(), 'logs')
            diagnostics['logging_system'] = {
                'log_directory': log_dir,
                'directory_exists': os.path.exists(log_dir),
                'directory_writable': os.access(log_dir, os.W_OK) if os.path.exists(log_dir) else False,
                'current_log_file': f"logs/tezgah_takip_{datetime.now().strftime('%Y%m%d')}.log",
                'handlers_configured': len(logging.getLogger().handlers) > 0
            }
            
            # Detaylı diagnostics logla
            self.logger.info("🔍 Kapsamlı Startup Diagnostics:")
            self.logger.info(f"   Platform: {diagnostics['system_info']['platform']} {diagnostics['system_info']['architecture']}")
            self.logger.info(f"   Python: {diagnostics['system_info']['python_version']}")
            
            # Disk durumu
            for name, disk_info in diagnostics['disk_space'].items():
                if 'error' not in disk_info:
                    status_icon = "✅" if disk_info['status'] == 'OK' else "⚠️"
                    self.logger.info(f"   {status_icon} {name}: {disk_info['free_gb']:.1f} GB free ({disk_info['usage_percent']:.1f}% used)")
            
            # İzin durumu
            permission_issues = [name for name, perm in diagnostics['permissions'].items() if perm.get('status') != 'OK']
            if permission_issues:
                self.logger.warning(f"⚠️ İzin sorunları: {permission_issues}")
            
            # Bağımlılık durumu
            missing_deps = [dep for dep, info in diagnostics['dependencies'].items() if info.get('status') == 'MISSING']
            if missing_deps:
                self.logger.warning(f"⚠️ Eksik bağımlılıklar: {missing_deps}")
            
            # Enhanced bileşenler durumu
            missing_components = [comp for comp, info in diagnostics['enhanced_components'].items() if not info.get('available')]
            if missing_components:
                self.logger.warning(f"⚠️ Eksik enhanced bileşenler: {missing_components}")
            else:
                self.logger.info("✅ Tüm enhanced database bileşenleri mevcut")
            
            # Genel sistem sağlığı değerlendirmesi
            health_score = self._calculate_system_health_score(diagnostics)
            self.logger.info(f"🏥 Sistem sağlık skoru: {health_score}/100")
            
            if health_score < 70:
                self.logger.warning("⚠️ Sistem sağlığı düşük - performans sorunları yaşanabilir")
            elif health_score < 85:
                self.logger.info("ℹ️ Sistem sağlığı orta - bazı optimizasyonlar yapılabilir")
            else:
                self.logger.info("✅ Sistem sağlığı mükemmel")
            
            return diagnostics
            
        except Exception as e:
            self.logger.error(f"❌ Startup diagnostics hatası: {e}")
            return {}
    
    def _calculate_system_health_score(self, diagnostics):
        """Sistem sağlık skoru hesapla (0-100)"""
        score = 100
        
        # Disk alanı kontrolü (-20 puan düşük alan için)
        for name, disk_info in diagnostics.get('disk_space', {}).items():
            if isinstance(disk_info, dict) and disk_info.get('status') == 'LOW':
                score -= 20
                break
        
        # İzin sorunları (-15 puan her sorun için, max -45)
        permission_issues = sum(1 for perm in diagnostics.get('permissions', {}).values() 
                              if isinstance(perm, dict) and perm.get('status') != 'OK')
        score -= min(permission_issues * 15, 45)
        
        # Eksik bağımlılıklar (-10 puan her eksik için, max -30)
        missing_deps = sum(1 for dep in diagnostics.get('dependencies', {}).values()
                          if isinstance(dep, dict) and dep.get('status') == 'MISSING')
        score -= min(missing_deps * 10, 30)
        
        # Eksik enhanced bileşenler (-5 puan her eksik için, max -25)
        missing_components = sum(1 for comp in diagnostics.get('enhanced_components', {}).values()
                               if isinstance(comp, dict) and not comp.get('available'))
        score -= min(missing_components * 5, 25)
        
        return max(0, score)

    def initialize_database(self):
        """Gelişmiş veritabanı başlatma - Enhanced Database Manager ile tam entegrasyon"""
        try:
            self.splash.showMessage("Gelişmiş veritabanı sistemi başlatılıyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            # Enhanced Database Manager'ı oluştur
            from enhanced_database_manager import EnhancedDatabaseManager
            
            # Config'den veritabanı yolunu al
            db_path = None
            try:
                from config_manager import ConfigManager
                config_manager = ConfigManager()
                db_path = config_manager.get("database.path")
                self.logger.info(f"📍 Config'den veritabanı yolu: {db_path}")
            except Exception as config_error:
                self.logger.warning(f"⚠️ Config yüklenemedi, otomatik yol çözümlemesi kullanılacak: {config_error}")
            
            # Notification callback tanımla
            def database_notification_callback(message: str, severity: str = "info", details: dict = None):
                """Database bildirimlerini yakala ve logla"""
                if severity == "error":
                    self.logger.error(f"🔴 DB Notification: {message}")
                elif severity == "warning":
                    self.logger.warning(f"🟡 DB Notification: {message}")
                else:
                    self.logger.info(f"🔵 DB Notification: {message}")
                
                # Splash screen'de göster
                if self.splash and self.splash.isVisible():
                    color = QColor(220, 53, 69) if severity == "error" else QColor(255, 193, 7) if severity == "warning" else QColor(40, 167, 69)
                    self.splash.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, color)
            
            # Enhanced Database Manager ile başlat
            self.enhanced_db_manager = EnhancedDatabaseManager(
                db_path=db_path,
                enable_fallback=True,
                notification_callback=database_notification_callback
            )
            
            # Başlatma öncesi sistem kontrolü
            self.splash.showMessage("Veritabanı sistem kontrolü yapılıyor...", 
                                  Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
            
            # Veritabanı başlatma
            init_success = self.enhanced_db_manager.init_database_with_fallback()
            
            if not init_success:
                raise Exception("Enhanced Database Manager başlatılamadı")
            
            # Veritabanı durumunu kontrol et
            status = self.enhanced_db_manager.get_database_status()
            
            if status.is_connected:
                # Test bağlantısı ve health check
                try:
                    tezgah_count = self.enhanced_db_manager.get_tezgah_count()
                except Exception as e:
                    self.logger.warning(f"⚠️ Tezgah sayısı alınamadı: {e}")
                    tezgah_count = "Bilinmiyor"
                
                # Database health check
                health_status = self.enhanced_db_manager.perform_health_check()
                
                # Başarı mesajı
                if status.is_fallback:
                    fallback_msg = f" (Fallback: {status.fallback_type.value})" if status.fallback_type else " (Fallback aktif)"
                    self.logger.info(f"✅ Veritabanı bağlantısı başarılı{fallback_msg}. Toplam tezgah: {tezgah_count}")
                    
                    # Kullanıcıya fallback bilgisi ver
                    self.splash.showMessage(f"Veritabanı yedek sistemle başlatıldı{fallback_msg}", 
                                          Qt.AlignBottom | Qt.AlignCenter, QColor(255, 193, 7))  # Sarı renk
                    
                    # Fallback durumunu kaydet (ana pencerede gösterilmek üzere)
                    self.fallback_info = {
                        'active': True,
                        'type': status.fallback_type.value if status.fallback_type else 'unknown',
                        'message': f"Veritabanı yedek sistemle çalışıyor{fallback_msg}"
                    }
                else:
                    self.logger.info(f"✅ Veritabanı bağlantısı başarılı. Toplam tezgah: {tezgah_count}")
                    self.fallback_info = {'active': False}
                
                # Health check sonuçları
                if health_status:
                    self.logger.info(f"✅ Database health check: {health_status.get('status', 'OK')}")
                    if health_status.get('warnings'):
                        for warning in health_status['warnings']:
                            self.logger.warning(f"⚠️ DB Warning: {warning}")
                    if health_status.get('recommendations'):
                        for rec in health_status['recommendations']:
                            self.logger.info(f"💡 DB Recommendation: {rec}")
                
                # Backup sistem entegrasyonu
                try:
                    from advanced_backup_manager import AdvancedBackupManager
                    backup_manager = AdvancedBackupManager()
                    
                    # Otomatik backup kontrolü
                    if backup_manager.should_create_automatic_backup():
                        self.splash.showMessage("Otomatik yedekleme kontrol ediliyor...", 
                                              Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
                        
                        backup_result = backup_manager.create_backup(
                            source_path=self.enhanced_db_manager.get_current_database_path(),
                            backup_type="startup_auto"
                        )
                        
                        if backup_result and backup_result.get('success'):
                            self.logger.info(f"✅ Otomatik startup yedeklemesi oluşturuldu: {backup_result.get('backup_path')}")
                        else:
                            self.logger.warning("⚠️ Otomatik startup yedeklemesi başarısız")
                    
                    # Backup sistem durumunu kaydet
                    self.backup_system_available = True
                    
                except ImportError:
                    self.logger.info("ℹ️ Advanced Backup Manager bulunamadı - temel yedekleme kullanılacak")
                    self.backup_system_available = False
                except Exception as backup_error:
                    self.logger.warning(f"⚠️ Backup sistem hatası: {backup_error}")
                    self.backup_system_available = False
                
                # Global referansı ayarla (backward compatibility için)
                self.db_manager = self.enhanced_db_manager
                
                # Başarılı başlatma sonrası temizlik
                self.splash.showMessage("Veritabanı sistemi hazır!", 
                                      Qt.AlignBottom | Qt.AlignCenter, QColor(40, 167, 69))
                
                return True
            else:
                error_msg = status.last_error or "Bilinmeyen veritabanı hatası"
                raise Exception(error_msg)
            
        except Exception as e:
            self.logger.error(f"❌ Gelişmiş veritabanı başlatma hatası: {e}")
            
            # Kullanıcı dostu hata mesajı
            error_details = str(e)
            
            # Türkçe hata mesajları - gelişmiş
            if "permission" in error_details.lower() or "izin" in error_details.lower():
                user_message = (
                    "🔐 Veritabanı Erişim Sorunu\n\n"
                    "Veritabanı dosyasına erişim izni bulunmuyor.\n\n"
                    "💡 Çözüm önerileri:\n"
                    "• Uygulamayı yönetici olarak çalıştırın\n"
                    "• Antivirüs yazılımınızı kontrol edin\n"
                    "• Dosya izinlerini kontrol edin\n"
                    "• Windows Defender'ı kontrol edin\n"
                    "• Klasör şifrelemesini kontrol edin\n\n"
                    f"Teknik detay: {error_details}"
                )
            elif "corrupt" in error_details.lower() or "bozuk" in error_details.lower():
                user_message = (
                    "🗄️ Veritabanı Bozulması\n\n"
                    "Veritabanı dosyası bozulmuş görünüyor.\n\n"
                    "💡 Çözüm önerileri:\n"
                    "• Yedek dosyalarınızı kontrol edin (backups klasörü)\n"
                    "• Uygulamayı yeniden başlatın\n"
                    "• Disk hatası kontrolü yapın (chkdsk)\n"
                    "• Antivirüs taraması yapın\n"
                    "• Teknik destek ile iletişime geçin\n\n"
                    f"Teknik detay: {error_details}"
                )
            elif "not found" in error_details.lower() or "bulunamadı" in error_details.lower():
                user_message = (
                    "📁 Veritabanı Dosyası Bulunamadı\n\n"
                    "Veritabanı dosyası bulunamıyor.\n\n"
                    "💡 Çözüm önerileri:\n"
                    "• İlk kez çalıştırıyorsanız bu normal\n"
                    "• Yeni veritabanı otomatik oluşturulacak\n"
                    "• Yedek dosyalarınızı kontrol edin\n"
                    "• Dosya yolunu kontrol edin\n"
                    "• Ağ bağlantısını kontrol edin (ağ sürücüsü kullanıyorsanız)\n\n"
                    f"Teknik detay: {error_details}"
                )
            elif "disk" in error_details.lower() or "space" in error_details.lower():
                user_message = (
                    "💾 Disk Alanı Sorunu\n\n"
                    "Yetersiz disk alanı nedeniyle veritabanı başlatılamadı.\n\n"
                    "💡 Çözüm önerileri:\n"
                    "• Disk alanı boşaltın\n"
                    "• Geçici dosyaları temizleyin\n"
                    "• Geri dönüşüm kutusunu boşaltın\n"
                    "• Eski yedekleri silin\n"
                    "• Disk temizleme aracını çalıştırın\n\n"
                    f"Teknik detay: {error_details}"
                )
            else:
                user_message = (
                    "❌ Veritabanı Başlatma Hatası\n\n"
                    "Veritabanı sistemi başlatılamadı.\n\n"
                    "💡 Çözüm önerileri:\n"
                    "• Uygulamayı yeniden başlatın\n"
                    "• Bilgisayarı yeniden başlatın\n"
                    "• Disk alanınızı kontrol edin\n"
                    "• Antivirüs yazılımınızı kontrol edin\n"
                    "• Windows güncellemelerini kontrol edin\n"
                    "• Teknik destek ile iletişime geçin\n\n"
                    f"Teknik detay: {error_details}"
                )
            
            from main_window import CustomMessageBox
            CustomMessageBox.critical(None, "Veritabanı Sistemi Hatası", user_message)
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
                ("Sistem tanılaması", self.run_startup_diagnostics),
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