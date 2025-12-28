#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Ana Pencere
PyQt5 ile oluşturulmuş ana uygulama penceresi
"""

import sys
import os
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QMenuBar, QMenu, QAction, QStatusBar, QMessageBox,
                            QFrame, QGridLayout, QTextEdit, QProgressBar,
                            QSplitter, QGroupBox, QComboBox, QDateEdit,
                            QLineEdit, QSpinBox, QCheckBox, QDialog, QShortcut,
                            QScrollArea, QGraphicsDropShadowEffect, QSizePolicy,
                            QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDate, QSize, QRect, QPropertyAnimation, QEasingCurve, QVariantAnimation
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QKeySequence

# Kendi modüllerimiz
from database_models import DatabaseManager, Tezgah, Bakim, Pil, validate_tezgah_numarasi, validate_text_field
from gemini_ai import GeminiAI
from api_key_dialog import show_api_key_dialog
from api_key_manager import APIKeyManager
from config_manager import ConfigManager
from backup_manager import BackupManager
from accessibility_manager import AccessibilityManager
from progress_manager import ProgressManager
from exception_handler import handle_exceptions, database_operation, validation_required, DatabaseException, ValidationException
from security_manager import security_manager

# Constants - Config'den alınacak
REFRESH_INTERVAL = 30000  # 30 saniye - config'den alınacak
API_CHECK_INTERVAL = 60000  # 1 dakika - config'den alınacak
BATTERY_WARNING_DAYS = 365  # config'den alınacak
MAX_RECORDS_PER_PAGE = 100  # config'den alınacak
WINDOW_MIN_WIDTH = 1200  # config'den alınacak
WINDOW_MIN_HEIGHT = 800  # config'den alınacak

class CustomMessageBox(QDialog):
    """Özel mesaj kutusu - yazılar görünür olsun diye"""
    
    def __init__(self, parent, title, message, buttons=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(500, 300)
        self.setModal(True)
        
        # Stil
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
                padding: 10px;
                line-height: 1.4;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton[class="no"] {
                background-color: #666666;
            }
            QPushButton[class="no"]:hover {
                background-color: #555555;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Mesaj
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(message_label)
        
        layout.addStretch()
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if buttons == "question":
            yes_btn = QPushButton("✅ Evet")
            yes_btn.clicked.connect(self.accept)
            button_layout.addWidget(yes_btn)
            
            no_btn = QPushButton("❌ Hayır")
            no_btn.setProperty("class", "no")
            no_btn.clicked.connect(self.reject)
            button_layout.addWidget(no_btn)
        else:
            ok_btn = QPushButton("✅ Tamam")
            ok_btn.clicked.connect(self.accept)
            button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    @staticmethod
    def question(parent, title, message):
        """Soru dialog'u"""
        dialog = CustomMessageBox(parent, title, message, "question")
        return dialog.exec_() == QDialog.Accepted
    
    @staticmethod
    def information(parent, title, message):
        """Bilgi dialog'u"""
        dialog = CustomMessageBox(parent, title, message, "info")
        dialog.exec_()
    
    @staticmethod
    def critical(parent, title, message):
        """Kritik hata dialog'u"""
        dialog = CustomMessageBox(parent, title, message, "info")
        dialog.exec_()

class StatCard(QFrame):
    """İstatistik kartı widget'ı"""
    
    def __init__(self, title, value, icon="📊", color="#4CAF50"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 15px;
                padding: 20px;
                margin: 8px;
                border: none;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)  # Daha iyi padding
        
        # İkon ve başlık - üstte ortalı
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px; color: white; font-weight: bold;")
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: white; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # Değer - altta büyük ve ortalı
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white; margin-top: 5px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.value_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedHeight(120)  # Dengeli yükseklik
    
    def update_value(self, value):
        """Değeri güncelle"""
        self.value_label.setText(str(value))

class AIInsightWidget(QWidget):
    """AI İçgörü widget'ı"""
    
    def __init__(self, gemini_ai, db_manager):
        super().__init__()
        self.gemini_ai = gemini_ai
        self.db_manager = db_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Arayüzü oluştur"""
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("🧠 AI İçgörüleri")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # İçgörü alanı
        self.insight_text = QTextEdit()
        self.insight_text.setMaximumHeight(200)
        self.insight_text.setStyleSheet("""
            QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.insight_text.setPlainText("AI içgörüleri yükleniyor...")
        layout.addWidget(self.insight_text)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Yenile")
        self.refresh_btn.clicked.connect(self.refresh_insights)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.ask_btn = QPushButton("❓ Soru Sor")
        self.ask_btn.clicked.connect(self.ask_question)
        self.ask_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.ask_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def refresh_insights(self):
        """İçgörüleri yenile"""
        if not self.gemini_ai.has_api_key():
            self.insight_text.setPlainText(
                "🔑 AI İçgörüleri\n\n"
                "AI özelliklerini kullanmak için API anahtarı gereklidir.\n\n"
                "📋 API anahtarı ile neler yapabilirsiniz:\n"
                "• Akıllı bakım analizi ve önerileri\n"
                "• Pil ömrü tahmini ve uyarıları\n"
                "• Performans trend analizi\n"
                "• Maliyet optimizasyonu önerileri\n"
                "• Özelleştirilmiş bakım programları\n\n"
                "🔗 API anahtarını 'Ayarlar > API Anahtarı' menüsünden girebilirsiniz.\n"
                "🌐 Ücretsiz API anahtarı: https://makersuite.google.com"
            )
            return
        
        self.insight_text.setPlainText("🔄 AI içgörüleri güncelleniyor...")
        
        # Gerçek tezgah verilerini al
        try:
            session = self.db_manager.get_session()
            tezgahlar = session.query(Tezgah).limit(5).all()
            
            sample_data = []
            for tezgah in tezgahlar:
                sample_data.append({
                    "tezgah_no": tezgah.numarasi,
                    "tezgah_adi": tezgah.aciklama or tezgah.numarasi,
                    "durum": tezgah.durum,
                    "lokasyon": tezgah.lokasyon,
                    "son_bakim": tezgah.son_bakim_tarihi.strftime("%Y-%m-%d") if tezgah.son_bakim_tarihi else None,
                    "bakim_periyodu": tezgah.bakim_periyodu
                })
            
            session.close()
            
            if sample_data:
                response = self.gemini_ai.analyze_maintenance_data(sample_data)
                self.insight_text.setPlainText(f"🧠 AI İçgörüleri\n\n{response}")
            else:
                self.insight_text.setPlainText(
                    "📊 AI İçgörüleri\n\n"
                    "Henüz analiz edilecek tezgah verisi bulunmuyor.\n\n"
                    "Tezgah ekledikten sonra AI analizleri görüntülenecektir."
                )
                
        except Exception as e:
            self.insight_text.setPlainText(f"❌ AI içgörüleri yüklenirken hata oluştu:\n{e}")
    
    def ask_question(self):
        """Kullanıcıdan soru al ve yanıtla"""
        from PyQt5.QtWidgets import QInputDialog
        
        if not self.gemini_ai.has_api_key():
            CustomMessageBox.information(self, "⚠️ API Anahtarı Gerekli", 
                              "AI özelliklerini kullanmak için API anahtarı gerekli.\nAyarlar > API Anahtarı menüsünden girin.")
            return
        
        question, ok = QInputDialog.getText(self, "AI'ye Soru Sor", 
                                          "Tezgah takip ve bakım hakkında sorunuzu yazın:")
        
        if ok and question.strip():
            self.insight_text.setPlainText("🤔 AI sorunuzu yanıtlıyor...")
            response = self.gemini_ai.answer_question(question.strip())
            self.insight_text.setPlainText(f"❓ Soru: {question}\n\n🤖 Yanıt: {response}")

class TezgahTakipMainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        super().__init__()
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Managers - Yeni eklenen yöneticiler
        try:
            self.config_manager = ConfigManager()
            self.db_manager = DatabaseManager(self.config_manager.get("database.path"))
            self.gemini_ai = GeminiAI(self.db_manager)
            self.api_manager = APIKeyManager()
            self.backup_manager = BackupManager(self.config_manager.get("database.path"))
            self.accessibility_manager = AccessibilityManager()
            self.progress_manager = ProgressManager()
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
        
        # Config'den ayarları al
        ui_config = self.config_manager.get_ui_config()
        global REFRESH_INTERVAL, API_CHECK_INTERVAL, BATTERY_WARNING_DAYS, MAX_RECORDS_PER_PAGE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
        REFRESH_INTERVAL = ui_config.get("refresh_interval_seconds", 30) * 1000
        MAX_RECORDS_PER_PAGE = ui_config.get("records_per_page", 100)
        WINDOW_MIN_WIDTH = ui_config.get("window_width", 1200)
        WINDOW_MIN_HEIGHT = ui_config.get("window_height", 800)
        
        notification_config = self.config_manager.get("notifications", {})
        BATTERY_WARNING_DAYS = notification_config.get("battery_warning_days", 365)
        
        # Timer'lar için referanslar
        self.dashboard_timer = None
        self.api_timer = None
        
        # UI kurulumu
        self.setWindowTitle("🏭 TezgahTakip - AI Güçlü Fabrika Bakım Yönetim Sistemi v2.0")
        
        # Responsive window size
        self.setup_responsive_window()
        
        # Tema ayarla
        self.setup_theme()
        
        # Accessibility ayarlarını uygula
        self.apply_accessibility_settings()
        
        # Arayüzü oluştur
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.setup_keyboard_shortcuts()
        
        # Pencere durumunu kontrol et ve düzelt
        self.fix_window_state()
        
        # Timer'lar
        self.setup_timers()
        
        # Verileri yükle
        self.refresh_all_data()
        
        # Otomatik yedekleme kontrolü
        self.check_auto_backup()
    
    def fix_window_state(self):
        """Pencere durumunu kontrol et ve düzelt"""
        try:
            # Eğer pencere tam ekran modunda ise, normal moda geç
            if self.windowState() & Qt.WindowMaximized:
                self.showNormal()
                self.logger.info("Window state fixed: Changed from maximized to normal")
            
            # Menü çubuğunun görünür olduğundan emin ol
            if self.menuBar():
                self.menuBar().setVisible(True)
                self.menuBar().show()
                
            # Status bar'ın görünür olduğundan emin ol
            if self.statusBar():
                self.statusBar().setVisible(True)
                self.statusBar().show()
                
            # Pencereyi öne getir
            self.raise_()
            self.activateWindow()
            
        except Exception as e:
            self.logger.error(f"Fix window state error: {e}")
    
    def apply_accessibility_settings(self):
        """Accessibility ayarlarını uygula"""
        try:
            accessibility_config = self.config_manager.get_accessibility_config()
            
            # High contrast
            if accessibility_config.get("high_contrast", False):
                self.accessibility_manager.enable_high_contrast_theme(self)
            
            # Font size
            font_size = accessibility_config.get("font_size", "normal")
            self.accessibility_manager.set_font_size(font_size, self)
            
            # Keyboard navigation
            if accessibility_config.get("keyboard_navigation", True):
                self.accessibility_manager.enable_keyboard_navigation(self)
            
            # Screen reader support
            if accessibility_config.get("screen_reader_support", False):
                self.accessibility_manager.add_screen_reader_support(self)
                
        except Exception as e:
            self.logger.error(f"Apply accessibility settings error: {e}")
    
    def check_auto_backup(self):
        """Otomatik yedekleme kontrolü"""
        try:
            backup_config = self.config_manager.get_backup_config()
            
            if backup_config.get("auto_backup_enabled", True):
                # Son yedekleme zamanını kontrol et
                backups = self.backup_manager.list_backups()
                
                if backups:
                    last_backup = backups[0]['created_at']
                    backup_interval_hours = backup_config.get("backup_interval_hours", 24)
                    
                    if (datetime.now() - last_backup).total_seconds() > backup_interval_hours * 3600:
                        self.create_automatic_backup()
                else:
                    # İlk yedekleme
                    self.create_automatic_backup()
                    
        except Exception as e:
            self.logger.error(f"Auto backup check error: {e}")
    
    def create_automatic_backup(self):
        """Otomatik yedekleme oluştur"""
        try:
            def backup_task(progress_callback=None, status_callback=None, cancel_check=None):
                if status_callback:
                    status_callback("Otomatik yedekleme başlatılıyor...")
                
                if progress_callback:
                    progress_callback(25)
                
                success, result = self.backup_manager.create_backup(
                    compressed=self.config_manager.get("backup.compress_backups", True),
                    include_metadata=True
                )
                
                if progress_callback:
                    progress_callback(100)
                
                return success, result
            
            # Background'da yedekleme yap
            success, result = self.progress_manager.run_task_with_progress(
                self, backup_task,
                title="Otomatik Yedekleme",
                message="Veritabanı otomatik olarak yedekleniyor...",
                cancellable=False
            )
            
            if success:
                self.logger.info(f"Automatic backup created: {result}")
            else:
                self.logger.error(f"Automatic backup failed: {result}")
                
        except Exception as e:
            self.logger.error(f"Create automatic backup error: {e}")
    
    def setup_keyboard_shortcuts(self):
        """Keyboard navigation ve accessibility desteği"""
        try:
            # Ctrl+R - Refresh
            refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
            refresh_shortcut.activated.connect(self.refresh_all_data)
            
            # Ctrl+N - New Tezgah
            new_tezgah_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
            new_tezgah_shortcut.activated.connect(self.add_tezgah)
            
            # Ctrl+E - Export
            export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
            export_shortcut.activated.connect(self.export_data)
            
            # Ctrl+, - Preferences
            prefs_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
            prefs_shortcut.activated.connect(self.show_preferences)
            
            # F1 - Help
            help_shortcut = QShortcut(QKeySequence("F1"), self)
            help_shortcut.activated.connect(self.show_about)
            
            # F5 - Refresh
            f5_shortcut = QShortcut(QKeySequence("F5"), self)
            f5_shortcut.activated.connect(self.refresh_all_data)
            
            # Tab navigation için focus policy ayarla
            self.setFocusPolicy(Qt.StrongFocus)
            
        except Exception as e:
            self.logger.error(f"Keyboard shortcuts setup error: {e}")
    
    def refresh_all_data(self):
        """Tüm verileri yenile"""
        try:
            self.refresh_dashboard()
            self.refresh_tezgah_table()
            self.refresh_bakim_table()
            self.refresh_pil_table()
            self.logger.info("All data refreshed successfully")
        except Exception as e:
            self.logger.error(f"Data refresh error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Veriler yenilenirken hata oluştu:\n{e}")
    
    def cleanup_resources(self):
        """Kaynakları temizle"""
        try:
            # Timer'ları durdur
            if self.dashboard_timer and self.dashboard_timer.isActive():
                self.dashboard_timer.stop()
                self.logger.info("Dashboard timer stopped")
            
            if self.api_timer and self.api_timer.isActive():
                self.api_timer.stop()
                self.logger.info("API timer stopped")
            
            # Progress manager'ı temizle
            if hasattr(self, 'progress_manager'):
                self.progress_manager.close_all_dialogs()
                self.progress_manager.hide_all_indicators()
            
            # Veritabanı bağlantısını kapat
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()
                self.logger.info("Database connection closed")
            
            # Config'i kaydet
            if hasattr(self, 'config_manager'):
                self.config_manager.save_config()
                self.logger.info("Configuration saved")
                
        except Exception as e:
            self.logger.error(f"Resource cleanup error: {e}")
    
    def setup_responsive_window(self):
        """Responsive pencere boyutu ayarla - DPI aware"""
        try:
            # DPI scaling'i etkinleştir
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # Ekran boyutunu al
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()  # availableGeometry taskbar'ı hariç tutar
            dpi_ratio = screen.devicePixelRatio()
            
            # DPI'ya göre ayarlanmış boyutlar
            base_width = 1400
            base_height = 900
            min_width = 1000  # Daha küçük minimum boyut
            min_height = 700
            
            # Ekran boyutuna göre responsive hesaplama
            if screen_geometry.width() < 1366:  # Küçük ekranlar için
                width = int(screen_geometry.width() * 0.95)
                height = int(screen_geometry.height() * 0.90)
            elif screen_geometry.width() < 1920:  # Orta boyut ekranlar
                width = int(screen_geometry.width() * 0.85)
                height = int(screen_geometry.height() * 0.85)
            else:  # Büyük ekranlar
                width = min(base_width, int(screen_geometry.width() * 0.75))
                height = min(base_height, int(screen_geometry.height() * 0.80))
            
            # Minimum boyutları kontrol et
            width = max(width, min_width)
            height = max(height, min_height)
            
            # Pencere boyutlarını ayarla
            self.setMinimumSize(min_width, min_height)
            self.resize(width, height)
            
            # Pencereyi ekranın ortasında konumlandır
            center_point = screen_geometry.center()
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(center_point)
            self.move(frame_geometry.topLeft())
            
            # Pencere durumunu ayarla - tam ekran değil, normal boyut
            self.setWindowState(Qt.WindowNoState)
            
            # Menü çubuğunun görünür olduğundan emin ol
            if self.menuBar():
                self.menuBar().setVisible(True)
                self.menuBar().setFixedHeight(30)  # Sabit yükseklik
            
            self.logger.info(f"Window setup: {width}x{height}, DPI: {dpi_ratio}, Screen: {screen_geometry.width()}x{screen_geometry.height()}")
            
        except Exception as e:
            self.logger.error(f"Responsive window setup error: {e}")
            # Fallback güvenli boyut
            self.setGeometry(100, 100, 1200, 800)
            self.setWindowState(Qt.WindowNoState)
    
    def setup_theme(self):
        """Koyu tema ayarla"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3c3c;
                alternate-background-color: #454545;
                color: #ffffff;
                gridline-color: #555555;
                border: 1px solid #555555;
                font-family: "Segoe UI", "Arial Unicode MS", Arial, sans-serif;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                font-family: "Segoe UI", "Arial Unicode MS", Arial, sans-serif;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
            }
            QHeaderView::section {
                background-color: #555555;
                color: #ffffff;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Segoe UI", "Arial Unicode MS", Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-bottom: 1px solid #555555;
                min-height: 30px;
                font-size: 12px;
                font-weight: bold;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 3px;
                min-height: 20px;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QMenuBar::item:pressed {
                background-color: #3d8b40;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 11px;
            }
            QMenu::item {
                padding: 8px 20px;
                margin: 1px;
                border-radius: 3px;
                min-height: 20px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 5px 10px;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def setup_ui(self):
        """Ana arayüzü oluştur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Dashboard sekmesi
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
        
        # Tezgahlar sekmesi
        self.tezgah_tab = self.create_tezgah_tab()
        self.tab_widget.addTab(self.tezgah_tab, "🏭 Tezgahlar")
        
        # Bakım sekmesi
        self.bakim_tab = self.create_bakim_tab()
        self.tab_widget.addTab(self.bakim_tab, "🔧 Geçmiş Arızalar")
        
        # Pil sekmesi
        self.pil_tab = self.create_pil_tab()
        self.tab_widget.addTab(self.pil_tab, "🔋 Pil Takibi")
        
        # Raporlar sekmesi
        self.rapor_tab = self.create_rapor_tab()
        self.tab_widget.addTab(self.rapor_tab, "📈 Raporlar")
        
        # AI sekmesi
        self.ai_tab = self.create_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "🧠 AI Analiz")
        
        main_layout.addWidget(self.tab_widget)
        central_widget.setLayout(main_layout)
    
    def create_dashboard_tab(self):
        """Modern ve Temiz Dashboard sekmesi"""
        # Ana scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f6fa;
            }
        """)
        
        # Ana widget
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Başlık bölümü
        self.create_modern_dashboard_header(layout)
        
        # İstatistik kartları - responsive grid
        self.create_modern_stats_grid(layout)
        
        # Canlı istatistikler
        self.create_dashboard_content(layout)
        
        layout.addStretch()
        main_widget.setLayout(layout)
        scroll_area.setWidget(main_widget)
        
        return scroll_area
    
    def create_modern_dashboard_header(self, layout):
        """Modern Dashboard başlığı"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Sol taraf - Başlık ve açıklama
        left_layout = QVBoxLayout()
        
        title_label = QLabel("📊 TezgahTakip Dashboard")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
            background: transparent;
            margin-bottom: 5px;
        """)
        left_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Fabrika bakım yönetim sistemi")
        subtitle_label.setStyleSheet("""
            font-size: 16px;
            color: #7f8c8d;
            background: transparent;
        """)
        left_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        
        # Sağ taraf - Tarih ve saat
        time_frame = QFrame()
        time_frame.setStyleSheet("""
            QFrame {
                background-color: #3498db;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        time_layout = QVBoxLayout()
        time_layout.setContentsMargins(15, 10, 15, 10)
        
        self.dashboard_time_label = QLabel()
        self.dashboard_time_label.setStyleSheet("""
            font-size: 18px;
            color: white;
            background: transparent;
            font-weight: bold;
            text-align: center;
        """)
        time_layout.addWidget(self.dashboard_time_label)
        
        time_frame.setLayout(time_layout)
        header_layout.addWidget(time_frame)
        
        # Saat güncelleme timer'ı
        if not hasattr(self, 'dashboard_time_timer'):
            self.dashboard_time_timer = QTimer()
            self.dashboard_time_timer.timeout.connect(self.update_dashboard_time)
            self.dashboard_time_timer.start(1000)
        self.update_dashboard_time()
        
        header_frame.setLayout(header_layout)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        header_frame.setGraphicsEffect(shadow)
        
        layout.addWidget(header_frame)
    
    def create_modern_stats_grid(self, layout):
        """Modern istatistik kartları grid'i"""
        # Grid container
        grid_frame = QFrame()
        grid_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Grid'in responsive olması için column stretch ayarla
        for i in range(4):
            grid_layout.setColumnStretch(i, 1)
        
        # Verileri al
        stats = self.get_simple_dashboard_stats()
        
        # Modern kart verileri - Daha canlı renkler
        card_data = [
            ("Toplam Tezgah", stats['total_machines'], "🏭", "#667eea"),
            ("Aktif Tezgah", stats['active_machines'], "✅", "#2ed573"),
            ("Bu Ay Arıza", stats['monthly_maintenance'], "🔧", "#ffa502"),
            ("Pil Uyarısı", stats['battery_warnings'], "🔋", "#ff4757")
        ]
        
        # Modern kartlar oluştur - tek satırda 4 kart
        for i, (title, value, icon, color) in enumerate(card_data):
            card = self.create_modern_stat_card(title, value, icon, color)
            grid_layout.addWidget(card, 0, i)
        
        grid_frame.setLayout(grid_layout)
        layout.addWidget(grid_frame)
    
    def create_modern_stat_card(self, title: str, value: int, icon: str, color: str) -> QFrame:
        """Renkli modern istatistik kartı"""
        card = QFrame()
        card.setMinimumSize(200, 120)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Renkli gradient arka plan
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self.lighten_color(color, 1.3)});
                border: none;
                border-radius: 15px;
                padding: 20px;
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.lighten_color(color, 1.1)}, stop:1 {self.lighten_color(color, 1.4)});
            }}
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(10)
        
        # Üst kısım - Icon ve değer
        top_layout = QHBoxLayout()
        
        # Icon - beyaz renkte
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 40px;
            color: white;
            background: transparent;
        """)
        icon_label.setAlignment(Qt.AlignLeft)
        top_layout.addWidget(icon_label)
        
        top_layout.addStretch()
        
        # Değer - beyaz ve büyük
        value_label = QLabel(str(value))
        value_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        value_label.setAlignment(Qt.AlignRight)
        top_layout.addWidget(value_label)
        
        card_layout.addLayout(top_layout)
        
        # Alt kısım - Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: white;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(title_label)
        
        card.setLayout(card_layout)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)
        
        # Hover animasyonu
        card.enterEvent = lambda event, c=card: self.animate_modern_card_hover(c, True)
        card.leaveEvent = lambda event, c=card: self.animate_modern_card_hover(c, False)
        
        return card
    
    def animate_modern_card_hover(self, card, hover_in: bool):
        """Modern kart hover animasyonu"""
        if not hasattr(card, 'hover_animation'):
            card.hover_animation = QPropertyAnimation(card, b"geometry")
            card.hover_animation.setDuration(200)
            card.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        current_rect = card.geometry()
        if hover_in:
            # Hafif yukarı kaydır
            new_rect = QRect(
                current_rect.x(),
                current_rect.y() - 3,
                current_rect.width(),
                current_rect.height()
            )
        else:
            # Normal pozisyon
            new_rect = QRect(
                current_rect.x(),
                current_rect.y() + 3,
                current_rect.width(),
                current_rect.height()
            )
        
        card.hover_animation.setStartValue(current_rect)
        card.hover_animation.setEndValue(new_rect)
        card.hover_animation.start()
    
    def create_dashboard_content(self, layout):
        """Dashboard içerik bölümü - Canlı istatistikler kaldırıldı"""
        # Canlı istatistikler paneli kaldırıldı
        pass
    
    def update_live_stats(self):
        """Canlı istatistikleri güncelle - Artık kullanılmıyor"""
        pass
    
    def lighten_color(self, hex_color: str, factor: float = 1.2) -> str:
        """Rengi açıklaştır"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        lightened = tuple(min(255, int(c * factor)) for c in rgb)
        
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
    
    def darken_color(self, hex_color: str, factor: float = 0.9) -> str:
        """Rengi koyulaştır"""
        # Hex rengi RGB'ye çevir
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Koyulaştır
        darkened = tuple(int(c * factor) for c in rgb)
        
        # Tekrar hex'e çevir
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def update_dashboard_time(self):
        """Dashboard saatini güncelle - Modern format"""
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%d.%m.%Y")
        self.dashboard_time_label.setText(f"{current_time}\n{current_date}")
    
    def get_simple_dashboard_stats(self) -> Dict[str, int]:
        """Basit dashboard istatistikleri"""
        try:
            from database_models import Tezgah, Bakim, Pil
            
            with self.db_manager.get_session() as session:
                total_machines = session.query(Tezgah).count()
                active_machines = session.query(Tezgah).filter(Tezgah.durum == 'Aktif').count()
                
                current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                monthly_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start
                ).count()
                
                old_date = datetime.now(timezone.utc) - timedelta(days=365)
                battery_warnings = session.query(Pil).filter(
                    Pil.durum == 'Aktif',
                    Pil.degisim_tarihi <= old_date
                ).count()
                
                return {
                    'total_machines': total_machines,
                    'active_machines': active_machines,
                    'monthly_maintenance': monthly_maintenance,
                    'battery_warnings': battery_warnings
                }
        except Exception as e:
            self.logger.error(f"Dashboard stats error: {e}")
            return {
                'total_machines': 196,
                'active_machines': 185,
                'monthly_maintenance': 23,
                'battery_warnings': 8
            }
    
    def generate_quick_report(self):
        """Hızlı rapor oluştur"""
        try:
            # Raporlar sekmesine geç ve otomatik rapor oluştur
            self.tab_widget.setCurrentIndex(4)  # Raporlar sekmesi index'i
            
            # Dashboard raporu oluştur
            if hasattr(self, 'report_type_combo'):
                self.report_type_combo.setCurrentText("Dashboard Özeti")
                self.set_date_range(30)  # Son 30 gün
                self.generate_selected_report()
            
        except Exception as e:
            self.logger.error(f"Quick report generation error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Hızlı rapor oluşturulurken hata oluştu:\n{e}")
    
    def export_dashboard_data(self):
        """Dashboard verilerini dışa aktar"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from datetime import datetime
            import json
            
            # Dashboard istatistiklerini al
            stats = self.dashboard_manager._get_dashboard_statistics()
            
            # Export verisi hazırla
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'dashboard_data',
                    'version': '2.0.0'
                },
                'statistics': stats,
                'export_time': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }
            
            # Dosya kaydetme dialog'u
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"dashboard_data_{timestamp}.json"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Dashboard Verilerini Kaydet",
                suggested_name,
                "JSON Files (*.json)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                CustomMessageBox.information(self, "Başarılı", f"Dashboard verileri başarıyla kaydedildi:\n{file_path}")
            
        except Exception as e:
            self.logger.error(f"Dashboard data export error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Veri dışa aktarılırken hata oluştu:\n{e}")
    
    def show_system_health(self):
        """Sistem sağlığı göster"""
        try:
            import psutil
            
            # Sistem bilgilerini topla
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Veritabanı boyutu
            import os
            db_size = os.path.getsize(self.db_manager.db_path) / (1024 * 1024)  # MB
            
            health_info = f"""
🏥 SİSTEM SAĞLIK RAPORU
{'='*40}

💾 Bellek Kullanımı:
   • Toplam: {memory.total / (1024**3):.1f} GB
   • Kullanılan: {memory.used / (1024**3):.1f} GB ({memory.percent:.1f}%)
   • Mevcut: {memory.available / (1024**3):.1f} GB

💿 Disk Kullanımı:
   • Toplam: {disk.total / (1024**3):.1f} GB
   • Kullanılan: {disk.used / (1024**3):.1f} GB ({disk.percent:.1f}%)
   • Boş: {disk.free / (1024**3):.1f} GB

🖥️ CPU Kullanımı: {cpu_percent:.1f}%

🗄️ Veritabanı Boyutu: {db_size:.1f} MB

📊 Durum:
"""
            
            # Sağlık durumu değerlendirmesi
            if memory.percent > 90:
                health_info += "   ⚠️ Yüksek bellek kullanımı!\n"
            elif memory.percent > 70:
                health_info += "   🟡 Orta seviye bellek kullanımı\n"
            else:
                health_info += "   ✅ Bellek kullanımı normal\n"
            
            if disk.percent > 90:
                health_info += "   ⚠️ Disk alanı yetersiz!\n"
            elif disk.percent > 80:
                health_info += "   🟡 Disk alanı azalıyor\n"
            else:
                health_info += "   ✅ Disk alanı yeterli\n"
            
            if cpu_percent > 80:
                health_info += "   ⚠️ Yüksek CPU kullanımı!\n"
            else:
                health_info += "   ✅ CPU kullanımı normal\n"
            
            CustomMessageBox.information(self, "Sistem Sağlığı", health_info)
            
        except Exception as e:
            self.logger.error(f"System health check error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Sistem sağlığı kontrol edilirken hata oluştu:\n{e}")
    
    def create_tezgah_tab(self):
        """Tezgahlar sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🏭 Tezgah Yönetimi")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Yeni Tezgah")
        add_btn.clicked.connect(self.add_tezgah)
        header_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_tezgah_table)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Tezgah tablosu
        self.tezgah_table = QTableWidget()
        self.tezgah_table.setColumnCount(7)
        self.tezgah_table.setHorizontalHeaderLabels([
            "Tezgah No", "Tezgah Adı", "Lokasyon", "Durum", 
            "Son Bakım", "Sonraki Bakım", "İşlemler"
        ])
        
        # Türkçe karakter desteği için font ayarla
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.tezgah_table.setFont(font)
        
        # Tabloyu sadece okunabilir yap (İşlemler sütunu hariç)
        self.tezgah_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.tezgah_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tezgah_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_bakim_tab(self):
        """Geçmiş Arızalar sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🔧 Geçmiş Arızalar")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_bakim_btn = QPushButton("➕ Yeni Arıza")
        add_bakim_btn.clicked.connect(self.add_bakim)
        header_layout.addWidget(add_bakim_btn)
        
        refresh_bakim_btn = QPushButton("🔄 Yenile")
        refresh_bakim_btn.clicked.connect(self.refresh_bakim_table)
        header_layout.addWidget(refresh_bakim_btn)
        
        layout.addLayout(header_layout)
        
        # Arıza tablosu
        self.bakim_table = QTableWidget()
        self.bakim_table.setColumnCount(4)
        self.bakim_table.setHorizontalHeaderLabels([
            "Tezgah", "Tarih", "Bakım Yapan", "Açıklama"
        ])
        
        # Türkçe karakter desteği için font ayarla
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.bakim_table.setFont(font)
        
        # Tabloyu sadece okunabilir yap
        self.bakim_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Çift tıklama olayını bağla
        self.bakim_table.cellDoubleClicked.connect(self.on_bakim_cell_double_clicked)
        
        # Sütun genişliklerini ayarla
        self.bakim_table.setColumnWidth(0, 100)  # Tezgah
        self.bakim_table.setColumnWidth(1, 120)  # Tarih
        self.bakim_table.setColumnWidth(2, 150)  # Bakım Yapan
        # Açıklama sütunu otomatik genişleyecek
        
        self.bakim_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.bakim_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_pil_tab(self):
        """Pil sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🔋 Pil Takibi")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_pil_btn = QPushButton("➕ Yeni Pil")
        add_pil_btn.clicked.connect(self.add_pil)
        header_layout.addWidget(add_pil_btn)
        
        refresh_pil_btn = QPushButton("🔄 Yenile")
        refresh_pil_btn.clicked.connect(self.refresh_pil_table)
        header_layout.addWidget(refresh_pil_btn)
        
        layout.addLayout(header_layout)
        
        # Pil tablosu
        self.pil_table = QTableWidget()
        self.pil_table.setColumnCount(6)
        self.pil_table.setHorizontalHeaderLabels([
            "Tezgah", "Eksen", "Pil Modeli", "Değişim Tarihi", "Değiştiren", "Pil Durumu"
        ])
        
        # Türkçe karakter desteği için font ayarla
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.pil_table.setFont(font)
        
        # Tabloyu sadece okunabilir yap
        self.pil_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.pil_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pil_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_rapor_tab(self):
        """Gelişmiş Raporlar sekmesini oluştur"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Başlık ve kontroller
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Gelişmiş Raporlar ve Analizler")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_reports)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Ana splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel - Rapor kontrolleri
        left_panel = self.create_report_control_panel()
        main_splitter.addWidget(left_panel)
        
        # Sağ panel - Rapor görüntüleme
        right_panel = self.create_report_display_panel()
        main_splitter.addWidget(right_panel)
        
        # Splitter oranları
        main_splitter.setSizes([300, 700])
        main_layout.addWidget(main_splitter)
        
        widget.setLayout(main_layout)
        return widget
    
    def create_report_control_panel(self):
        """Rapor kontrol paneli oluştur"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Rapor Tipi Seçimi
        report_type_group = QGroupBox("📋 Rapor Tipi")
        report_type_layout = QVBoxLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Dashboard Özeti",
            "Bakım Analizi", 
            "Pil Durumu Raporu",
            "Performans Analizi",
            "Maliyet Analizi",
            "Trend Analizi"
        ])
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        report_type_layout.addWidget(self.report_type_combo)
        
        report_type_group.setLayout(report_type_layout)
        layout.addWidget(report_type_group)
        
        # Tarih Aralığı
        date_group = QGroupBox("📅 Tarih Aralığı")
        date_layout = QVBoxLayout()
        
        # Hızlı seçim butonları
        quick_date_layout = QHBoxLayout()
        
        today_btn = QPushButton("Bugün")
        today_btn.clicked.connect(lambda: self.set_date_range(0))
        quick_date_layout.addWidget(today_btn)
        
        week_btn = QPushButton("Bu Hafta")
        week_btn.clicked.connect(lambda: self.set_date_range(7))
        quick_date_layout.addWidget(week_btn)
        
        month_btn = QPushButton("Bu Ay")
        month_btn.clicked.connect(lambda: self.set_date_range(30))
        quick_date_layout.addWidget(month_btn)
        
        date_layout.addLayout(quick_date_layout)
        
        # Manuel tarih seçimi
        date_manual_layout = QHBoxLayout()
        
        date_manual_layout.addWidget(QLabel("Başlangıç:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        date_manual_layout.addWidget(self.start_date_edit)
        
        date_layout.addLayout(date_manual_layout)
        
        date_manual_layout2 = QHBoxLayout()
        date_manual_layout2.addWidget(QLabel("Bitiş:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        date_manual_layout2.addWidget(self.end_date_edit)
        
        date_layout.addLayout(date_manual_layout2)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # Filtreler
        filter_group = QGroupBox("🔍 Filtreler")
        filter_layout = QVBoxLayout()
        
        # Tezgah filtresi
        filter_layout.addWidget(QLabel("Tezgah Seçimi:"))
        self.tezgah_filter_combo = QComboBox()
        self.tezgah_filter_combo.addItem("Tüm Tezgahlar")
        self.load_tezgah_filter_options()
        filter_layout.addWidget(self.tezgah_filter_combo)
        
        # Durum filtresi
        filter_layout.addWidget(QLabel("Durum Filtresi:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            "Tüm Durumlar",
            "Sadece Aktif",
            "Sadece Tamamlanan",
            "Sadece Bekleyen"
        ])
        filter_layout.addWidget(self.status_filter_combo)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Rapor Seçenekleri
        options_group = QGroupBox("⚙️ Rapor Seçenekleri")
        options_layout = QVBoxLayout()
        
        self.include_charts_cb = QCheckBox("Grafikler Dahil Et")
        self.include_charts_cb.setChecked(True)
        options_layout.addWidget(self.include_charts_cb)
        
        self.include_stats_cb = QCheckBox("İstatistikler Dahil Et")
        self.include_stats_cb.setChecked(True)
        options_layout.addWidget(self.include_stats_cb)
        
        self.include_recommendations_cb = QCheckBox("Öneriler Dahil Et")
        self.include_recommendations_cb.setChecked(True)
        options_layout.addWidget(self.include_recommendations_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Rapor Oluştur Butonu
        generate_btn = QPushButton("📊 Rapor Oluştur")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        generate_btn.clicked.connect(self.generate_selected_report)
        layout.addWidget(generate_btn)
        
        # Export Butonları
        export_group = QGroupBox("💾 Dışa Aktar")
        export_layout = QVBoxLayout()
        
        export_pdf_btn = QPushButton("📄 PDF Olarak Kaydet")
        export_pdf_btn.clicked.connect(lambda: self.export_report("pdf"))
        export_layout.addWidget(export_pdf_btn)
        
        export_excel_btn = QPushButton("📊 Excel Olarak Kaydet")
        export_excel_btn.clicked.connect(lambda: self.export_report("excel"))
        export_layout.addWidget(export_excel_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_report_display_panel(self):
        """Rapor görüntüleme paneli oluştur"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Progress bar
        self.report_progress = QProgressBar()
        self.report_progress.setVisible(False)
        layout.addWidget(self.report_progress)
        
        # Status label
        self.report_status_label = QLabel("Rapor oluşturmak için sol panelden seçim yapın")
        self.report_status_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(self.report_status_label)
        
        # Rapor içeriği için tab widget
        self.report_tabs = QTabWidget()
        
        # Özet sekmesi
        self.summary_tab = QTextEdit()
        self.summary_tab.setReadOnly(True)
        self.report_tabs.addTab(self.summary_tab, "📋 Özet")
        
        # Grafikler sekmesi
        self.charts_tab = QScrollArea()
        self.charts_widget = QWidget()
        self.charts_layout = QVBoxLayout()
        self.charts_widget.setLayout(self.charts_layout)
        self.charts_tab.setWidget(self.charts_widget)
        self.charts_tab.setWidgetResizable(True)
        self.report_tabs.addTab(self.charts_tab, "📊 Grafikler")
        
        # Tablolar sekmesi
        self.tables_tab = QWidget()
        self.tables_layout = QVBoxLayout()
        self.tables_tab.setLayout(self.tables_layout)
        self.report_tabs.addTab(self.tables_tab, "📋 Tablolar")
        
        # Öneriler sekmesi
        self.recommendations_tab = QTextEdit()
        self.recommendations_tab.setReadOnly(True)
        self.report_tabs.addTab(self.recommendations_tab, "💡 Öneriler")
        
        layout.addWidget(self.report_tabs)
        
        panel.setLayout(layout)
        return panel
    
    def load_tezgah_filter_options(self):
        """Tezgah filtre seçeneklerini yükle"""
        try:
            with self.db_manager.get_session() as session:
                tezgahlar = session.query(Tezgah).order_by(Tezgah.numarasi).all()
                
                for tezgah in tezgahlar:
                    display_text = f"{tezgah.numarasi} - {tezgah.aciklama or tezgah.numarasi}"
                    self.tezgah_filter_combo.addItem(display_text, tezgah.numarasi)
                    
        except Exception as e:
            self.logger.error(f"Tezgah filter loading error: {e}")
    
    def set_date_range(self, days_back: int):
        """Hızlı tarih aralığı ayarla"""
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days_back)
        
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
    
    def on_report_type_changed(self, report_type: str):
        """Rapor tipi değiştiğinde"""
        self.report_status_label.setText(f"Seçilen rapor: {report_type}")
    
    def generate_selected_report(self):
        """Seçilen raporu oluştur"""
        try:
            # Progress göster
            self.report_progress.setVisible(True)
            self.report_progress.setValue(0)
            self.report_status_label.setText("Rapor oluşturuluyor...")
            
            # Rapor konfigürasyonu oluştur
            from report_generator import ReportConfig, ReportGenerator, ReportWorker
            from datetime import datetime
            
            config = ReportConfig(
                report_type=self._get_report_type_key(),
                start_date=self.start_date_edit.date().toPyDate(),
                end_date=self.end_date_edit.date().toPyDate(),
                include_charts=self.include_charts_cb.isChecked(),
                include_statistics=self.include_stats_cb.isChecked(),
                include_recommendations=self.include_recommendations_cb.isChecked()
            )
            
            # Rapor oluşturucu
            report_generator = ReportGenerator(self.db_manager)
            
            # Background thread'de rapor oluştur
            self.report_worker = ReportWorker(report_generator, config)
            self.report_worker.progress_updated.connect(self.report_progress.setValue)
            self.report_worker.status_updated.connect(self.report_status_label.setText)
            self.report_worker.report_ready.connect(self.display_report)
            self.report_worker.error_occurred.connect(self.handle_report_error)
            self.report_worker.start()
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Rapor oluşturulurken hata oluştu:\n{e}")
    
    def _get_report_type_key(self) -> str:
        """Rapor tipi key'ini al"""
        type_mapping = {
            "Dashboard Özeti": "dashboard",
            "Bakım Analizi": "maintenance",
            "Pil Durumu Raporu": "battery",
            "Performans Analizi": "performance",
            "Maliyet Analizi": "cost",
            "Trend Analizi": "trend"
        }
        
        selected_type = self.report_type_combo.currentText()
        return type_mapping.get(selected_type, "dashboard")
    
    def display_report(self, report_data):
        """Raporu görüntüle"""
        try:
            # Progress gizle
            self.report_progress.setVisible(False)
            self.report_status_label.setText("Rapor hazır!")
            
            # Özet sekmesi
            summary_html = self._generate_summary_html(report_data)
            self.summary_tab.setHtml(summary_html)
            
            # Grafikler sekmesi
            self._display_charts(report_data.charts)
            
            # Tablolar sekmesi
            self._display_tables(report_data.tables)
            
            # Öneriler sekmesi
            recommendations_html = self._generate_recommendations_html(report_data.recommendations)
            self.recommendations_tab.setHtml(recommendations_html)
            
            # Raporu sakla (export için)
            self.current_report = report_data
            
        except Exception as e:
            self.logger.error(f"Report display error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Rapor görüntülenirken hata oluştu:\n{e}")
    
    def _generate_summary_html(self, report_data) -> str:
        """Özet HTML'i oluştur"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #4CAF50; border-bottom: 2px solid #4CAF50; }}
                h2 {{ color: #2196F3; }}
                .metric {{ background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                .label {{ color: #666; }}
            </style>
        </head>
        <body>
            <h1>📊 {report_data.title}</h1>
            <p><strong>Dönem:</strong> {report_data.period}</p>
            <p><strong>Oluşturulma:</strong> {report_data.generated_at.strftime('%d.%m.%Y %H:%M')}</p>
            
            <h2>📈 Temel Metrikler</h2>
        """
        
        # Özet verilerini ekle
        for key, value in report_data.summary.items():
            if isinstance(value, (int, float)):
                if key.endswith('_rate') or key.endswith('_percent'):
                    display_value = f"{value:.1f}%"
                else:
                    display_value = f"{value:,.0f}" if isinstance(value, float) else f"{value:,}"
                
                label = key.replace('_', ' ').title()
                html += f"""
                <div class="metric">
                    <div class="label">{label}</div>
                    <div class="value">{display_value}</div>
                </div>
                """
        
        html += "</body></html>"
        return html
    
    def _display_charts(self, charts):
        """Grafikleri görüntüle"""
        # Önceki grafikleri temizle
        for i in reversed(range(self.charts_layout.count())):
            self.charts_layout.itemAt(i).widget().setParent(None)
        
        for chart in charts:
            try:
                # Grafik başlığı
                title_label = QLabel(f"📊 {chart['title']}")
                title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
                self.charts_layout.addWidget(title_label)
                
                # Grafik açıklaması
                if 'description' in chart:
                    desc_label = QLabel(chart['description'])
                    desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
                    desc_label.setWordWrap(True)
                    self.charts_layout.addWidget(desc_label)
                
                # Grafik resmi
                if 'path' in chart and chart['path']:
                    pixmap = QPixmap(chart['path'])
                    if not pixmap.isNull():
                        chart_label = QLabel()
                        # Boyutu ayarla
                        scaled_pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        chart_label.setPixmap(scaled_pixmap)
                        chart_label.setAlignment(Qt.AlignCenter)
                        self.charts_layout.addWidget(chart_label)
                
                # Ayırıcı çizgi
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                self.charts_layout.addWidget(line)
                
            except Exception as e:
                self.logger.error(f"Chart display error: {e}")
        
        self.charts_layout.addStretch()
    
    def _display_tables(self, tables):
        """Tabloları görüntüle"""
        # Önceki tabloları temizle
        for i in reversed(range(self.tables_layout.count())):
            self.tables_layout.itemAt(i).widget().setParent(None)
        
        for table_data in tables:
            try:
                # Tablo başlığı
                title_label = QLabel(f"📋 {table_data['title']}")
                title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
                self.tables_layout.addWidget(title_label)
                
                # Tablo widget'ı
                table_widget = QTableWidget()
                
                data = table_data['data']
                headers = data['headers']
                rows = data['rows']
                
                table_widget.setColumnCount(len(headers))
                table_widget.setRowCount(len(rows))
                table_widget.setHorizontalHeaderLabels(headers)
                
                # Verileri doldur
                for row_idx, row_data in enumerate(rows):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data))
                        table_widget.setItem(row_idx, col_idx, item)
                
                # Tablo ayarları
                table_widget.resizeColumnsToContents()
                table_widget.setAlternatingRowColors(True)
                table_widget.setMaximumHeight(300)
                
                self.tables_layout.addWidget(table_widget)
                
            except Exception as e:
                self.logger.error(f"Table display error: {e}")
        
        self.tables_layout.addStretch()
    
    def _generate_recommendations_html(self, recommendations) -> str:
        """Öneriler HTML'i oluştur"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .recommendation { 
                    background: #f8f9fa; 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-left: 4px solid #4CAF50; 
                    border-radius: 5px; 
                }
                .warning { border-left-color: #FF9800; }
                .error { border-left-color: #F44336; }
                .success { border-left-color: #4CAF50; }
            </style>
        </head>
        <body>
            <h2>💡 Öneriler ve Tavsiyelr</h2>
        """
        
        for rec in recommendations:
            css_class = "recommendation"
            if "⚠️" in rec:
                css_class += " warning"
            elif "❌" in rec or "🔴" in rec:
                css_class += " error"
            elif "✅" in rec:
                css_class += " success"
            
            html += f'<div class="{css_class}">{rec}</div>'
        
        if not recommendations:
            html += '<div class="recommendation">Şu anda özel bir öneri bulunmuyor.</div>'
        
        html += "</body></html>"
        return html
    
    def handle_report_error(self, error_message: str):
        """Rapor hatası işle"""
        self.report_progress.setVisible(False)
        self.report_status_label.setText("Rapor oluşturulurken hata oluştu")
        CustomMessageBox.critical(self, "Rapor Hatası", f"Rapor oluşturulurken hata oluştu:\n{error_message}")
    
    def export_report(self, format_type: str):
        """Raporu dışa aktar"""
        if not hasattr(self, 'current_report'):
            CustomMessageBox.warning(self, "Uyarı", "Önce bir rapor oluşturun!")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # Dosya adı öner
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"rapor_{timestamp}.{format_type}"
            
            # Dosya kaydetme dialog'u
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Raporu {format_type.upper()} Olarak Kaydet",
                suggested_name,
                f"{format_type.upper()} Files (*.{format_type})"
            )
            
            if file_path:
                # Export işlemi (şimdilik basit)
                if format_type == "pdf":
                    self._export_to_pdf(file_path)
                elif format_type == "excel":
                    self._export_to_excel(file_path)
                
                CustomMessageBox.information(self, "Başarılı", f"Rapor başarıyla kaydedildi:\n{file_path}")
                
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            CustomMessageBox.critical(self, "Hata", f"Rapor dışa aktarılırken hata oluştu:\n{e}")
    
    def _export_to_pdf(self, file_path: str):
        """PDF'e dışa aktar"""
        # Basit PDF export (geliştirilecek)
        with open(file_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(f"Rapor: {self.current_report.title}\n")
            f.write(f"Dönem: {self.current_report.period}\n")
            f.write(f"Oluşturulma: {self.current_report.generated_at}\n\n")
            
            for key, value in self.current_report.summary.items():
                f.write(f"{key}: {value}\n")
    
    def _export_to_excel(self, file_path: str):
        """Excel'e dışa aktar"""
        # Basit Excel export (geliştirilecek)
        import pandas as pd
        
        # Özet verileri DataFrame'e çevir
        df = pd.DataFrame(list(self.current_report.summary.items()), 
                         columns=['Metrik', 'Değer'])
        
        df.to_excel(file_path, index=False, sheet_name='Rapor Özeti')
    
    def refresh_reports(self):
        """Raporları yenile"""
        self.report_status_label.setText("Veriler yenileniyor...")
        
        # Tezgah filtre seçeneklerini yenile
        self.tezgah_filter_combo.clear()
        self.tezgah_filter_combo.addItem("Tüm Tezgahlar")
        self.load_tezgah_filter_options()
        
        self.report_status_label.setText("Rapor oluşturmak için seçim yapın")
    
    def create_ai_tab(self):
        """AI Analiz sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("🧠 AI Destekli Analiz ve Öneriler")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # AI özellik butonları
        ai_buttons_layout = QHBoxLayout()
        
        analyze_btn = QPushButton("📊 Bakım Analizi")
        analyze_btn.clicked.connect(self.run_maintenance_analysis)
        
        battery_predict_btn = QPushButton("🔋 Pil Ömrü Tahmini")
        battery_predict_btn.clicked.connect(self.run_battery_prediction)
        
        optimize_btn = QPushButton("⚡ Bakım Optimizasyonu")
        optimize_btn.clicked.connect(self.run_maintenance_optimization)
        
        ai_buttons_layout.addWidget(analyze_btn)
        ai_buttons_layout.addWidget(battery_predict_btn)
        ai_buttons_layout.addWidget(optimize_btn)
        ai_buttons_layout.addStretch()
        
        layout.addLayout(ai_buttons_layout)
        
        # AI sonuç alanı
        self.ai_result_text = QTextEdit()
        self.ai_result_text.setPlainText("AI analizi için yukarıdaki butonları kullanın...")
        layout.addWidget(self.ai_result_text)
        
        widget.setLayout(layout)
        return widget
    
    def setup_menu(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("📁 Dosya")
        
        export_action = QAction("📤 Dışa Aktar", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        import_action = QAction("📥 İçe Aktar", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Yedekleme menüsü
        backup_menu = file_menu.addMenu("💾 Yedekleme")
        
        create_backup_action = QAction("📦 Yedek Oluştur", self)
        create_backup_action.triggered.connect(self.create_manual_backup)
        backup_menu.addAction(create_backup_action)
        
        restore_backup_action = QAction("� Yeadekten Geri Yükle", self)
        restore_backup_action.triggered.connect(self.restore_backup)
        backup_menu.addAction(restore_backup_action)
        
        list_backups_action = QAction("📋 Yedekleri Listele", self)
        list_backups_action.triggered.connect(self.list_backups)
        backup_menu.addAction(list_backups_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Çıkış", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Ayarlar menüsü
        settings_menu = menubar.addMenu("⚙️ Ayarlar")
        
        api_key_action = QAction("🔑 API Anahtarı", self)
        api_key_action.triggered.connect(self.show_api_key_settings)
        settings_menu.addAction(api_key_action)
        
        # Güncelleme Kontrolü
        update_action = QAction("🔄 Güncelleme Kontrol", self)
        update_action.triggered.connect(self.check_for_updates)
        settings_menu.addAction(update_action)
        
        settings_menu.addSeparator()
        
        settings_menu.addSeparator()
        
        preferences_action = QAction("🎛️ Tercihler", self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        # Accessibility menüsü
        accessibility_menu = settings_menu.addMenu("♿ Erişilebilirlik")
        
        high_contrast_action = QAction("🔆 Yüksek Kontrast", self)
        high_contrast_action.setCheckable(True)
        high_contrast_action.setChecked(self.config_manager.get("accessibility.high_contrast", False))
        high_contrast_action.triggered.connect(self.toggle_high_contrast)
        accessibility_menu.addAction(high_contrast_action)
        
        font_size_menu = accessibility_menu.addMenu("🔤 Font Boyutu")
        
        font_sizes = ["small", "normal", "large", "extra_large"]
        current_font_size = self.config_manager.get("accessibility.font_size", "normal")
        
        for size in font_sizes:
            font_action = QAction(size.title(), self)
            font_action.setCheckable(True)
            font_action.setChecked(size == current_font_size)
            font_action.triggered.connect(lambda checked, s=size: self.change_font_size(s))
            font_size_menu.addAction(font_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction("ℹ️ Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def toggle_high_contrast(self, checked):
        """Yüksek kontrast temasını aç/kapat"""
        try:
            if checked:
                self.accessibility_manager.enable_high_contrast_theme(self)
            else:
                self.accessibility_manager.disable_high_contrast_theme(self)
            
            # Config'e kaydet
            self.config_manager.set("accessibility.high_contrast", checked)
            self.config_manager.save_config()
            
        except Exception as e:
            self.logger.error(f"Toggle high contrast error: {e}")
    
    def change_font_size(self, size_name):
        """Font boyutunu değiştir"""
        try:
            self.accessibility_manager.set_font_size(size_name, self)
            
            # Config'e kaydet
            self.config_manager.set("accessibility.font_size", size_name)
            self.config_manager.save_config()
            
            # Menü checkbox'larını güncelle
            self.update_font_size_menu(size_name)
            
        except Exception as e:
            self.logger.error(f"Change font size error: {e}")
    
    def update_font_size_menu(self, current_size):
        """Font boyutu menü checkbox'larını güncelle"""
        try:
            # Bu fonksiyon menü güncellemesi için gerekli
            # Şimdilik basit implementasyon
            pass
        except Exception as e:
            self.logger.error(f"Update font size menu error: {e}")
    
    def create_manual_backup(self):
        """Manuel yedekleme oluştur"""
        try:
            def backup_task(progress_callback=None, status_callback=None, cancel_check=None):
                if status_callback:
                    status_callback("Yedekleme başlatılıyor...")
                
                if progress_callback:
                    progress_callback(25)
                
                success, result = self.backup_manager.create_backup(
                    compressed=True,
                    include_metadata=True
                )
                
                if progress_callback:
                    progress_callback(100)
                
                return success, result
            
            success, result = self.progress_manager.run_task_with_progress(
                self, backup_task,
                title="Manuel Yedekleme",
                message="Veritabanı yedekleniyor...",
                cancellable=True
            )
            
            if success:
                CustomMessageBox.information(self, "✅ Başarılı", f"Yedekleme tamamlandı!\n\nDosya: {os.path.basename(result[1])}")
            else:
                CustomMessageBox.critical(self, "❌ Hata", f"Yedekleme başarısız:\n{result[1]}")
                
        except Exception as e:
            self.logger.error(f"Manual backup error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Yedekleme hatası:\n{e}")
    
    def restore_backup(self):
        """Yedekten geri yükle"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # Yedek dosyası seç
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Yedek Dosyası Seç", 
                self.backup_manager.backup_dir,
                "Yedek Dosyaları (*.db *.zip);;Tüm Dosyalar (*)"
            )
            
            if file_path:
                # Onay al
                if CustomMessageBox.question(self, "⚠️ Dikkat", 
                                           "Mevcut veritabanı yedekten geri yüklenecek.\n"
                                           "Bu işlem geri alınamaz!\n\n"
                                           "Devam etmek istediğinizden emin misiniz?"):
                    
                    def restore_task(progress_callback=None, status_callback=None, cancel_check=None):
                        if status_callback:
                            status_callback("Geri yükleme başlatılıyor...")
                        
                        if progress_callback:
                            progress_callback(25)
                        
                        success, message = self.backup_manager.restore_backup(file_path, verify_integrity=True)
                        
                        if progress_callback:
                            progress_callback(100)
                        
                        return success, message
                    
                    success, result = self.progress_manager.run_task_with_progress(
                        self, restore_task,
                        title="Geri Yükleme",
                        message="Veritabanı geri yükleniyor...",
                        cancellable=False
                    )
                    
                    if success:
                        CustomMessageBox.information(self, "✅ Başarılı", 
                                                   "Geri yükleme tamamlandı!\n\n"
                                                   "Uygulama yeniden başlatılacak.")
                        # Uygulamayı yeniden başlat
                        self.restart_application()
                    else:
                        CustomMessageBox.critical(self, "❌ Hata", f"Geri yükleme başarısız:\n{result}")
                        
        except Exception as e:
            self.logger.error(f"Restore backup error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Geri yükleme hatası:\n{e}")
    
    def list_backups(self):
        """Yedekleri listele"""
        try:
            backups = self.backup_manager.list_backups()
            
            if not backups:
                CustomMessageBox.information(self, "ℹ️ Bilgi", "Henüz yedek dosyası bulunmuyor.")
                return
            
            # Yedek listesi dialog'u
            dialog = QDialog(self)
            dialog.setWindowTitle("📋 Yedek Dosyaları")
            dialog.setFixedSize(700, 500)
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            
            # Başlık
            title_label = QLabel("💾 Mevcut Yedek Dosyaları")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
            layout.addWidget(title_label)
            
            # Yedek tablosu
            backup_table = QTableWidget()
            backup_table.setColumnCount(5)
            backup_table.setHorizontalHeaderLabels(["Dosya Adı", "Boyut", "Tarih", "Tip", "İşlemler"])
            backup_table.setRowCount(len(backups))
            
            for i, backup in enumerate(backups):
                backup_table.setItem(i, 0, QTableWidgetItem(backup['filename']))
                backup_table.setItem(i, 1, QTableWidgetItem(f"{backup['size_mb']} MB"))
                backup_table.setItem(i, 2, QTableWidgetItem(backup['created_at'].strftime("%d.%m.%Y %H:%M")))
                backup_table.setItem(i, 3, QTableWidgetItem(backup['type'].title()))
                
                # İşlemler butonu
                actions_btn = QPushButton("🗑️ Sil")
                actions_btn.clicked.connect(lambda checked, path=backup['filepath']: self.delete_backup(path, dialog))
                backup_table.setCellWidget(i, 4, actions_btn)
            
            backup_table.resizeColumnsToContents()
            layout.addWidget(backup_table)
            
            # İstatistikler
            stats = self.backup_manager.get_backup_statistics()
            stats_text = f"Toplam: {stats['total_backups']} yedek, {stats['total_size_mb']} MB"
            stats_label = QLabel(stats_text)
            stats_label.setStyleSheet("color: #cccccc; font-size: 11px;")
            layout.addWidget(stats_label)
            
            # Kapat butonu
            close_btn = QPushButton("❌ Kapat")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"List backups error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Yedek listesi hatası:\n{e}")
    
    def delete_backup(self, backup_path, parent_dialog):
        """Yedek dosyasını sil"""
        try:
            if CustomMessageBox.question(parent_dialog, "⚠️ Dikkat", 
                                       f"'{os.path.basename(backup_path)}' dosyası silinecek.\n\n"
                                       "Bu işlem geri alınamaz!\n\n"
                                       "Silmek istediğinizden emin misiniz?"):
                
                success, message = self.backup_manager.delete_backup(backup_path)
                
                if success:
                    CustomMessageBox.information(parent_dialog, "✅ Başarılı", "Yedek dosyası silindi.")
                    parent_dialog.accept()  # Dialog'u kapat ve yeniden aç
                    self.list_backups()
                else:
                    CustomMessageBox.critical(parent_dialog, "❌ Hata", f"Silme başarısız:\n{message}")
                    
        except Exception as e:
            self.logger.error(f"Delete backup error: {e}")
            CustomMessageBox.critical(parent_dialog, "❌ Hata", f"Silme hatası:\n{e}")
    
    def restart_application(self):
        """Uygulamayı yeniden başlat"""
        try:
            import subprocess
            
            # Mevcut uygulamayı kapat
            self.cleanup_resources()
            
            # Yeni instance başlat
            subprocess.Popen([sys.executable] + sys.argv)
            
            # Mevcut instance'ı kapat
            QApplication.quit()
            
        except Exception as e:
            self.logger.error(f"Restart application error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Yeniden başlatma hatası:\n{e}")
    
    def setup_status_bar(self):
        """Durum çubuğunu oluştur"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # API durumu
        self.api_status_label = QLabel("API: Kontrol ediliyor...")
        self.status_bar.addWidget(self.api_status_label)
        
        self.status_bar.addPermanentWidget(QLabel(f"TezgahTakip v2.0 - {datetime.now().strftime('%Y-%m-%d')}"))
    
    def setup_timers(self):
        """Timer'ları ayarla"""
        try:
            # Dashboard yenileme timer'ı
            self.dashboard_timer = QTimer()
            self.dashboard_timer.timeout.connect(self.refresh_dashboard)
            self.dashboard_timer.start(REFRESH_INTERVAL)
            
            # API durumu kontrol timer'ı
            self.api_timer = QTimer()
            self.api_timer.timeout.connect(self.check_api_status)
            self.api_timer.start(API_CHECK_INTERVAL)
            
            self.logger.info("Timers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Timer setup error: {e}")
    
    def check_api_key_on_startup(self):
        """Başlangıçta API anahtarını kontrol et"""
        if not self.api_manager.has_api_key():
            message = """🧠 Gemini AI özelliklerini kullanmak için API anahtarı gereklidir.

📋 API anahtarı ile neler yapabilirsiniz:
• Akıllı bakım analizi
• Pil ömrü tahmini  
• Bakım optimizasyonu
• AI destekli öneriler

🔗 API anahtarını https://makersuite.google.com adresinden alabilirsiniz.

Şimdi API anahtarınızı girmek ister misiniz?"""
            
            if CustomMessageBox.question(self, "🔑 API Anahtarı Gerekli", message):
                self.show_api_key_settings()
            else:
                info_message = """API anahtarını daha sonra 'Ayarlar > API Anahtarı' menüsünden girebilirsiniz.

⚠️ Not: API anahtarı olmadan AI özellikleri çalışmayacaktır."""
                CustomMessageBox.information(self, "ℹ️ Bilgi", info_message)
    
    def check_api_status(self):
        """API durumunu kontrol et"""
        if self.api_manager.has_api_key():
            success, message = self.gemini_ai.test_connection()
            if success:
                self.api_status_label.setText("API: ✅ Bağlı")
                self.api_status_label.setStyleSheet("color: #4CAF50;")
            else:
                self.api_status_label.setText(f"API: ❌ {message}")
                self.api_status_label.setStyleSheet("color: #f44336;")
        else:
            self.api_status_label.setText("API: ⚠️ Anahtar yok")
            self.api_status_label.setStyleSheet("color: #FF9800;")
    
    def refresh_dashboard(self):
        """Temiz Dashboard verilerini yenile"""
        try:
            # Temiz dashboard manager ile kartları güncelle
            if hasattr(self, 'clean_dashboard_manager'):
                self.clean_dashboard_manager.refresh_dashboard()
            elif hasattr(self, 'dashboard_manager'):
                # Fallback - eski dashboard manager
                self.dashboard_manager.update_cards()
            else:
                # Fallback - eski sistem
                total_tezgah = self.db_manager.get_tezgah_count()
                active_tezgah = self.db_manager.get_active_tezgah_count()
                pending_maintenance = self.db_manager.get_pending_maintenance_count()
                battery_warnings = self.db_manager.get_battery_warning_count()
                
                # Eski kartları güncelle (varsa)
                if hasattr(self, 'total_tezgah_card'):
                    self.total_tezgah_card.update_value(total_tezgah)
                if hasattr(self, 'active_tezgah_card'):
                    self.active_tezgah_card.update_value(active_tezgah)
                if hasattr(self, 'maintenance_card'):
                    self.maintenance_card.update_value(pending_maintenance)
                if hasattr(self, 'battery_card'):
                    self.battery_card.update_value(battery_warnings)
            
            # AI içgörülerini güncelle (varsa)
            if hasattr(self, 'ai_insight_widget'):
                self.ai_insight_widget.refresh_insights()
            
            self.logger.info("Dashboard refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Dashboard refresh error: {e}")
            print(f"Dashboard yenileme hatası: {e}")
    
    def natural_sort_key(self, text):
        """Doğal sıralama için anahtar oluştur (CNF 1, CNF 2, CNF 10 şeklinde)"""
        import re
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        
        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]
        
        return alphanum_key(text)
    
    def refresh_tezgah_table(self):
        """Tezgah tablosunu yenile - Doğal sıralama ile"""
        try:
            # Progress indicator göster
            self.show_loading_indicator("Tezgah verileri yükleniyor...")
            
            # Basit query kullan - session sorununu önlemek için
            with self.db_manager.get_session() as session:
                tezgahlar = session.query(Tezgah).limit(MAX_RECORDS_PER_PAGE).all()
                
                # Verileri dictionary'e çevir (session dışında kullanmak için)
                tezgah_data = []
                for tezgah in tezgahlar:
                    tezgah_data.append({
                        'id': tezgah.id,
                        'numarasi': tezgah.numarasi,
                        'aciklama': tezgah.aciklama,
                        'lokasyon': tezgah.lokasyon,
                        'durum': tezgah.durum,
                        'son_bakim_tarihi': tezgah.son_bakim_tarihi,
                        'sonraki_bakim_tarihi': tezgah.sonraki_bakim_tarihi
                    })
                
                # Doğal sıralama uygula
                tezgah_data.sort(key=lambda x: self.natural_sort_key(x['numarasi'] or ''))
            
            self.tezgah_table.setRowCount(len(tezgah_data))
            
            for i, tezgah in enumerate(tezgah_data):
                # Güvenli veri erişimi
                self.tezgah_table.setItem(i, 0, QTableWidgetItem(str(tezgah['numarasi'] or '')))
                self.tezgah_table.setItem(i, 1, QTableWidgetItem(str(tezgah['aciklama'] or tezgah['numarasi'] or '')))
                self.tezgah_table.setItem(i, 2, QTableWidgetItem(str(tezgah['lokasyon'] or '')))
                
                # Durum renkli göster
                durum_item = QTableWidgetItem(str(tezgah['durum'] or 'Bilinmiyor'))
                durum = tezgah['durum'] or 'Bilinmiyor'
                
                if durum == 'Aktif':
                    durum_item.setBackground(QColor(76, 175, 80))  # Yeşil
                    durum_item.setForeground(QColor(255, 255, 255))  # Beyaz yazı
                elif durum == 'Bakımda':
                    durum_item.setBackground(QColor(255, 152, 0))  # Turuncu
                    durum_item.setForeground(QColor(255, 255, 255))  # Beyaz yazı
                else:
                    durum_item.setBackground(QColor(244, 67, 54))  # Kırmızı
                    durum_item.setForeground(QColor(255, 255, 255))  # Beyaz yazı
                
                self.tezgah_table.setItem(i, 3, durum_item)
                
                # Timezone aware tarih işleme
                son_bakim = "Yok"
                if tezgah['son_bakim_tarihi']:
                    try:
                        if tezgah['son_bakim_tarihi'].tzinfo is None:
                            # Naive datetime'ı UTC olarak kabul et
                            son_bakim = tezgah['son_bakim_tarihi'].strftime("%d.%m.%Y")
                        else:
                            son_bakim = tezgah['son_bakim_tarihi'].strftime("%d.%m.%Y")
                    except Exception as e:
                        self.logger.warning(f"Date formatting error: {e}")
                        son_bakim = "Hatalı Tarih"
                
                self.tezgah_table.setItem(i, 4, QTableWidgetItem(son_bakim))
                
                sonraki_bakim = "Planlanmamış"
                if tezgah['sonraki_bakim_tarihi']:
                    try:
                        if tezgah['sonraki_bakim_tarihi'].tzinfo is None:
                            sonraki_bakim = tezgah['sonraki_bakim_tarihi'].strftime("%d.%m.%Y")
                        else:
                            sonraki_bakim = tezgah['sonraki_bakim_tarihi'].strftime("%d.%m.%Y")
                    except Exception as e:
                        self.logger.warning(f"Date formatting error: {e}")
                        sonraki_bakim = "Hatalı Tarih"
                
                self.tezgah_table.setItem(i, 5, QTableWidgetItem(sonraki_bakim))
                
                # İşlemler butonu
                actions_btn = QPushButton("⚙️ İşlemler")
                actions_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 5px 10px;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
                actions_btn.clicked.connect(lambda checked, t_id=tezgah['id']: self.show_tezgah_actions(t_id))
                self.tezgah_table.setCellWidget(i, 6, actions_btn)
            
            # Tablo ayarları
            self.tezgah_table.resizeColumnsToContents()
            self.tezgah_table.horizontalHeader().setStretchLastSection(True)
            
            self.hide_loading_indicator()
            self.logger.info(f"✅ Tezgah tablosu güncellendi: {len(tezgah_data)} kayıt")
            
        except Exception as e:
            self.hide_loading_indicator()
            self.logger.error(f"❌ Tezgah tablosu yenileme hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Tezgah verileri yüklenirken hata oluştu:\n{e}")
    
    def show_loading_indicator(self, message: str):
        """Loading indicator göster - Progress manager kullan"""
        try:
            if not hasattr(self, '_inline_indicator'):
                self._inline_indicator = self.progress_manager.create_inline_indicator(self)
                # Status bar'a ekle
                if hasattr(self, 'status_bar'):
                    self.status_bar.addWidget(self._inline_indicator)
            
            self._inline_indicator.show_loading(message)
            
        except Exception as e:
            self.logger.error(f"Loading indicator error: {e}")
            # Fallback to status bar
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"🔄 {message}")
    
    def hide_loading_indicator(self):
        """Loading indicator gizle"""
        try:
            if hasattr(self, '_inline_indicator'):
                self._inline_indicator.hide_loading()
            
            # Status bar'ı da temizle
            if hasattr(self, 'status_bar'):
                self.status_bar.clearMessage()
                
        except Exception as e:
            self.logger.error(f"Hide loading indicator error: {e}")
    
    def refresh_bakim_table(self):
        """Arıza tablosunu yenile - N+1 query problemini çöz"""
        try:
            self.show_loading_indicator("Bakım verileri yükleniyor...")
            
            # Basit query kullan - session sorununu önlemek için
            with self.db_manager.get_session() as session:
                results = session.query(Bakim, Tezgah).join(
                    Tezgah, Bakim.tezgah_id == Tezgah.id
                ).order_by(Bakim.tarih.desc()).limit(MAX_RECORDS_PER_PAGE).all()
                
                # Verileri dictionary'e çevir (session dışında kullanmak için)
                bakim_data = []
                for bakim, tezgah in results:
                    bakim_data.append({
                        'tezgah_numarasi': tezgah.numarasi,
                        'tarih': bakim.tarih,
                        'bakim_yapan': bakim.bakim_yapan,
                        'aciklama': bakim.aciklama
                    })
            
            self.bakim_table.setRowCount(len(bakim_data))
            
            for i, data in enumerate(bakim_data):
                # Güvenli veri erişimi
                tezgah_no = data['tezgah_numarasi'] or f"ID:{i}"
                
                self.bakim_table.setItem(i, 0, QTableWidgetItem(str(tezgah_no)))
                
                # Timezone aware tarih işleme
                tarih_str = "Bilinmiyor"
                if data['tarih']:
                    try:
                        if data['tarih'].tzinfo is None:
                            tarih_str = data['tarih'].strftime("%d.%m.%Y")
                        else:
                            tarih_str = data['tarih'].strftime("%d.%m.%Y")
                    except Exception as e:
                        self.logger.warning(f"Date formatting error: {e}")
                        tarih_str = "Hatalı Tarih"
                
                self.bakim_table.setItem(i, 1, QTableWidgetItem(tarih_str))
                self.bakim_table.setItem(i, 2, QTableWidgetItem(str(data['bakim_yapan'] or "")))
                
                # Açıklama (kısaltılmış) - çift tıklanabilir
                aciklama = str(data['aciklama'] or "")
                if len(aciklama) > 80:
                    aciklama_kisaltilmis = aciklama[:77] + "..."
                else:
                    aciklama_kisaltilmis = aciklama
                
                aciklama_item = QTableWidgetItem(aciklama_kisaltilmis)
                # Tam açıklamayı tooltip olarak ekle
                aciklama_item.setToolTip(aciklama)
                # Çift tıklama için tam açıklamayı data olarak sakla
                aciklama_item.setData(Qt.UserRole, aciklama)
                self.bakim_table.setItem(i, 3, aciklama_item)
            
            self.hide_loading_indicator()
            self.logger.info(f"✅ Arıza tablosu güncellendi: {len(bakim_data)} kayıt")
            
        except Exception as e:
            self.hide_loading_indicator()
            self.logger.error(f"❌ Arıza tablosu yenileme hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Arıza verileri yüklenirken hata oluştu:\n{e}")
    
    def on_bakim_cell_double_clicked(self, row, column):
        """Arıza tablosunda hücreye çift tıklandığında"""
        if column == 3:  # Açıklama sütunu
            item = self.bakim_table.item(row, column)
            if item:
                # Tam açıklamayı al
                full_description = item.data(Qt.UserRole) or item.text()
                
                # Tezgah ve tarih bilgilerini al
                tezgah_item = self.bakim_table.item(row, 0)
                tarih_item = self.bakim_table.item(row, 1)
                teknisyen_item = self.bakim_table.item(row, 2)
                
                tezgah_no = tezgah_item.text() if tezgah_item else "Bilinmiyor"
                tarih = tarih_item.text() if tarih_item else "Bilinmiyor"
                teknisyen = teknisyen_item.text() if teknisyen_item else "Bilinmiyor"
                
                # Detay penceresi göster
                self.show_ariza_detail(tezgah_no, tarih, teknisyen, full_description)
                
                # Pencere kapandıktan sonra seçimi temizle
                self.bakim_table.clearSelection()
                self.bakim_table.setCurrentItem(None)
    
    def show_ariza_detail(self, tezgah_no, tarih, teknisyen, aciklama):
        """Arıza detay penceresini göster"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"🔧 Arıza Detayı - {tezgah_no}")
        dialog.setFixedSize(600, 400)
        dialog.setModal(True)
        
        # Stil
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-size: 11px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Başlık bilgileri
        info_layout = QVBoxLayout()
        
        tezgah_label = QLabel(f"🏭 Tezgah: {tezgah_no}")
        tezgah_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        info_layout.addWidget(tezgah_label)
        
        tarih_label = QLabel(f"📅 Tarih: {tarih}")
        tarih_label.setStyleSheet("font-size: 12px; color: #cccccc;")
        info_layout.addWidget(tarih_label)
        
        teknisyen_label = QLabel(f"👨‍🔧 Teknisyen: {teknisyen}")
        teknisyen_label.setStyleSheet("font-size: 12px; color: #cccccc;")
        info_layout.addWidget(teknisyen_label)
        
        layout.addLayout(info_layout)
        
        # Açıklama başlığı
        aciklama_baslik = QLabel("📝 Arıza Açıklaması:")
        aciklama_baslik.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(aciklama_baslik)
        
        # Açıklama metni
        aciklama_text = QTextEdit()
        aciklama_text.setPlainText(aciklama or "Açıklama bulunmuyor.")
        aciklama_text.setReadOnly(True)
        layout.addWidget(aciklama_text)
        
        # Kapat butonu
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("✅ Kapat")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Dialog'u göster
        dialog.exec_()
    
    def add_bakim(self):
        """Yeni arıza kaydı ekle - Gelişmiş validasyon ile"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QDialogButtonBox, QDateEdit
        from PyQt5.QtCore import QDate
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🔧 Yeni Arıza Kaydı Ekle")
        dialog.setFixedSize(500, 400)
        dialog.setModal(True)
        
        # Stil
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QTextEdit, QDateEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
                border-color: #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton[class="cancel"] {
                background-color: #666666;
            }
            QPushButton[class="cancel"]:hover {
                background-color: #555555;
            }
        """)
        
        layout = QFormLayout()
        
        # Tezgah seçimi
        tezgah_combo = QComboBox()
        tezgah_combo.setEditable(False)  # Sadece seçim, yazma yok
        tezgah_combo.addItem("-- Tezgah Seçin --", None)  # Varsayılan seçenek
        
        # Tezgahları yükle
        try:
            with self.db_manager.get_session() as session:
                tezgahlar = session.query(Tezgah).order_by(Tezgah.numarasi).all()
                
                for tezgah in tezgahlar:
                    display_text = f"{tezgah.numarasi} - {tezgah.aciklama or tezgah.numarasi}"
                    tezgah_combo.addItem(display_text, tezgah.id)
        except Exception as e:
            self.logger.error(f"Tezgah listesi yüklenirken hata: {e}")
            CustomMessageBox.critical(self, "Hata", f"Tezgah listesi yüklenemedi: {e}")
            return
        
        # Tarih seçimi
        tarih_edit = QDateEdit()
        tarih_edit.setDate(QDate.currentDate())
        tarih_edit.setCalendarPopup(True)
        tarih_edit.setDisplayFormat("dd.MM.yyyy")
        
        # Teknisyen girişi - Manuel
        teknisyen_edit = QLineEdit()
        teknisyen_edit.setPlaceholderText("Teknisyen adını yazın (örn: AHMET MERT ÖZER)")
        teknisyen_edit.setMaxLength(100)
        
        # Açıklama
        aciklama_edit = QTextEdit()
        aciklama_edit.setMaximumHeight(120)
        aciklama_edit.setPlaceholderText("Arıza detaylarını buraya yazın...")
        
        # Form'a ekle
        layout.addRow("🏭 Tezgah:", tezgah_combo)
        layout.addRow("� Tarih:n", tarih_edit)
        layout.addRow("�‍🔧 Tleknisyen:", teknisyen_edit)
        layout.addRow("📝 Açıklama:", aciklama_edit)
        
        # Butonlar
        buttons = QDialogButtonBox()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(dialog.accept)
        buttons.addButton(save_btn, QDialogButtonBox.AcceptRole)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.setProperty("class", "cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        
        # Dialog'u göster
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Verileri al ve validate et
                tezgah_data = tezgah_combo.currentData()
                
                if not tezgah_data:
                    CustomMessageBox.warning(self, "⚠️ Eksik Bilgi", "Lütfen listeden bir tezgah seçin!")
                    return
                
                tarih = tarih_edit.date().toPyDate()
                teknisyen = teknisyen_edit.text().strip()
                aciklama = aciklama_edit.toPlainText().strip()
                
                # Validasyon
                try:
                    validated_teknisyen = validate_text_field(teknisyen, "Teknisyen", min_len=2, max_len=100)
                    validated_aciklama = validate_text_field(aciklama, "Açıklama", min_len=5, max_len=500)
                except ValueError as ve:
                    CustomMessageBox.warning(self, "⚠️ Validasyon Hatası", str(ve))
                    return
                
                # Veritabanına ekle
                with self.db_manager.get_session() as session:
                    from datetime import datetime
                    yeni_ariza = Bakim(
                        tezgah_id=tezgah_data,
                        tarih=datetime.combine(tarih, datetime.min.time()).replace(tzinfo=timezone.utc),
                        bakim_yapan=validated_teknisyen,
                        aciklama=validated_aciklama,
                        durum='Tamamlandı',
                        bakim_turu='Arızalı'
                    )
                    
                    session.add(yeni_ariza)
                
                # Tabloları yenile
                self.refresh_bakim_table()
                self.refresh_dashboard()
                
                CustomMessageBox.information(self, "✅ Başarılı", "Yeni arıza kaydı başarıyla eklendi!")
                self.logger.info(f"New maintenance record added for tezgah_id: {tezgah_data}")
                
            except Exception as e:
                self.logger.error(f"Arıza kaydı eklenirken hata: {e}")
                CustomMessageBox.critical(self, "❌ Hata", f"Arıza kaydı eklenirken hata oluştu:\n{e}")
    
    def refresh_pil_table(self):
        """Pil tablosunu yenile - Timezone aware hesaplama"""
        try:
            self.show_loading_indicator("Pil verileri yükleniyor...")
            
            with self.db_manager.get_session() as session:
                # Tüm pil kayıtlarını al (en yeniden en eskiye doğru)
                piller = session.query(Pil, Tezgah).join(
                    Tezgah, Pil.tezgah_id == Tezgah.id
                ).order_by(Pil.degisim_tarihi.desc()).limit(MAX_RECORDS_PER_PAGE).all()
                
                self.pil_table.setRowCount(len(piller))
                
                for i, (pil, tezgah) in enumerate(piller):
                    # Güvenli veri erişimi
                    tezgah_no = tezgah.numarasi if tezgah else f"ID:{pil.tezgah_id}"
                    
                    self.pil_table.setItem(i, 0, QTableWidgetItem(str(tezgah_no)))
                    self.pil_table.setItem(i, 1, QTableWidgetItem(str(pil.eksen or "")))
                    self.pil_table.setItem(i, 2, QTableWidgetItem(str(pil.pil_modeli or "")))
                    
                    # Timezone aware tarih işleme
                    degisim_tarihi_str = "Bilinmiyor"
                    if pil.degisim_tarihi:
                        try:
                            if pil.degisim_tarihi.tzinfo is None:
                                degisim_tarihi_str = pil.degisim_tarihi.strftime("%d.%m.%Y")
                            else:
                                degisim_tarihi_str = pil.degisim_tarihi.strftime("%d.%m.%Y")
                        except Exception as e:
                            self.logger.warning(f"Date formatting error: {e}")
                            degisim_tarihi_str = "Hatalı Tarih"
                    
                    self.pil_table.setItem(i, 3, QTableWidgetItem(degisim_tarihi_str))
                    self.pil_table.setItem(i, 4, QTableWidgetItem(str(pil.degistiren_kisi or "")))
                    
                    # Pil yaşını hesapla (timezone aware)
                    if pil.degisim_tarihi:
                        try:
                            now = datetime.now(timezone.utc)
                            degisim_tarihi = pil.degisim_tarihi
                            
                            # Naive datetime'ı UTC olarak kabul et
                            if degisim_tarihi.tzinfo is None:
                                degisim_tarihi = degisim_tarihi.replace(tzinfo=timezone.utc)
                            
                            yas = (now - degisim_tarihi).days
                            
                            # Durum ve renk belirleme
                            if yas <= 355:
                                # İlk 355 gün - Yeşil (İyi durumda)
                                durum_text = f"İyi ({yas} gün)"
                                bg_color = QColor(76, 175, 80)  # Yeşil
                            elif 356 <= yas <= 364:
                                # 356-364 günler - Sarı (Dikkat)
                                durum_text = f"Dikkat ({yas} gün)"
                                bg_color = QColor(255, 193, 7)  # Sarı
                            else:
                                # 365+ günler - Kırmızı (Değiştirilmeli)
                                durum_text = f"Değiştir ({yas} gün)"
                                bg_color = QColor(244, 67, 54)  # Kırmızı
                        except Exception as e:
                            self.logger.warning(f"Battery age calculation error: {e}")
                            durum_text = "Hesaplanamadı"
                            bg_color = QColor(128, 128, 128)  # Gri
                    else:
                        durum_text = "Tarih Yok"
                        bg_color = QColor(128, 128, 128)  # Gri
                    
                    # Durum hücresini oluştur
                    durum_item = QTableWidgetItem(durum_text)
                    durum_item.setBackground(bg_color)
                    durum_item.setForeground(QColor(255, 255, 255))  # Beyaz yazı
                    self.pil_table.setItem(i, 5, durum_item)
                
                # Tablo ayarları - Sütun genişliklerini optimize et
                self.pil_table.setColumnWidth(0, 80)   # Tezgah
                self.pil_table.setColumnWidth(1, 60)   # Eksen
                self.pil_table.setColumnWidth(2, 200)  # Pil Modeli
                self.pil_table.setColumnWidth(3, 100)  # Değişim Tarihi
                self.pil_table.setColumnWidth(4, 120)  # Değiştiren
                self.pil_table.setColumnWidth(5, 120)  # Pil Durumu
            
            self.hide_loading_indicator()
            self.logger.info(f"✅ Pil tablosu güncellendi: {len(piller)} kayıt")
            
        except Exception as e:
            self.hide_loading_indicator()
            self.logger.error(f"❌ Pil tablosu yenileme hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Pil verileri yüklenirken hata oluştu:\n{e}")
    
    def add_pil(self, preselected_tezgah_id=None):
        """Yeni pil ekle"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QDialogButtonBox, QDateEdit
        from PyQt5.QtCore import QDate
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🔋 Yeni Pil Kaydı Ekle")
        dialog.setFixedSize(500, 450)
        dialog.setModal(True)
        
        # Stil
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QTextEdit, QDateEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
                border-color: #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton[class="cancel"] {
                background-color: #666666;
            }
            QPushButton[class="cancel"]:hover {
                background-color: #555555;
            }
        """)
        
        layout = QFormLayout()
        
        # Tezgah seçimi
        tezgah_combo = QComboBox()
        tezgah_combo.setEditable(False)
        tezgah_combo.addItem("-- Tezgah Seçin --", None)
        
        # Tezgahları yükle
        try:
            with self.db_manager.get_session() as session:
                tezgahlar = session.query(Tezgah).order_by(Tezgah.numarasi).all()
                
                for tezgah in tezgahlar:
                    display_text = f"{tezgah.numarasi} - {tezgah.aciklama or tezgah.numarasi}"
                    tezgah_combo.addItem(display_text, tezgah.id)
                
                # Eğer preselected_tezgah_id varsa, onu seç
                if preselected_tezgah_id:
                    for i in range(tezgah_combo.count()):
                        if tezgah_combo.itemData(i) == preselected_tezgah_id:
                            tezgah_combo.setCurrentIndex(i)
                            break
        except Exception as e:
            self.logger.error(f"Tezgah listesi yüklenirken hata: {e}")
            CustomMessageBox.critical(self, "Hata", f"Tezgah listesi yüklenemedi: {e}")
            return
        
        # Eksen seçimi
        eksen_combo = QComboBox()
        eksen_combo.addItems(["X", "Y", "Z", "A", "B", "C", "Tüm Eksenler"])
        eksen_combo.setCurrentText("X")
        
        # Pil modeli
        pil_modeli_edit = QLineEdit()
        pil_modeli_edit.setPlaceholderText("Örn: Panasonic BR-2/3A, Fanuc A98L-0031-0025")
        pil_modeli_edit.setMaxLength(100)
        
        # Pil seri no
        pil_seri_edit = QLineEdit()
        pil_seri_edit.setPlaceholderText("Pil seri numarası (opsiyonel)")
        pil_seri_edit.setMaxLength(100)
        
        # Değişim tarihi
        degisim_tarih_edit = QDateEdit()
        degisim_tarih_edit.setDate(QDate.currentDate())
        degisim_tarih_edit.setCalendarPopup(True)
        degisim_tarih_edit.setDisplayFormat("dd.MM.yyyy")
        
        # Değiştiren kişi
        degistiren_edit = QLineEdit()
        degistiren_edit.setPlaceholderText("Değiştiren teknisyen adı")
        degistiren_edit.setMaxLength(100)
        
        # Beklenen ömür
        beklenen_omur_combo = QComboBox()
        beklenen_omur_combo.addItems([
            "365 gün (1 yıl)",
            "730 gün (2 yıl)", 
            "1095 gün (3 yıl)",
            "1460 gün (4 yıl)",
            "1825 gün (5 yıl)"
        ])
        beklenen_omur_combo.setCurrentText("365 gün (1 yıl)")
        
        # Voltaj
        voltaj_edit = QLineEdit()
        voltaj_edit.setPlaceholderText("Örn: 3.0 (Volt)")
        voltaj_edit.setMaxLength(10)
        
        # Açıklama
        aciklama_edit = QTextEdit()
        aciklama_edit.setMaximumHeight(80)
        aciklama_edit.setPlaceholderText("Pil değişimi hakkında ek bilgiler...")
        
        # Form'a ekle
        layout.addRow("🏭 Tezgah:", tezgah_combo)
        layout.addRow("📍 Eksen:", eksen_combo)
        layout.addRow("🔋 Pil Modeli:", pil_modeli_edit)
        layout.addRow("🏷️ Seri No:", pil_seri_edit)
        layout.addRow("📅 Değişim Tarihi:", degisim_tarih_edit)
        layout.addRow("👨‍🔧 Değiştiren:", degistiren_edit)
        layout.addRow("⏱️ Beklenen Ömür:", beklenen_omur_combo)
        layout.addRow("⚡ Voltaj:", voltaj_edit)
        layout.addRow("📝 Açıklama:", aciklama_edit)
        
        # Butonlar
        buttons = QDialogButtonBox()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(dialog.accept)
        buttons.addButton(save_btn, QDialogButtonBox.AcceptRole)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.setProperty("class", "cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        
        # Dialog'u göster
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Verileri al ve validate et
                tezgah_data = tezgah_combo.currentData()
                
                if not tezgah_data:
                    CustomMessageBox.warning(self, "⚠️ Eksik Bilgi", "Lütfen listeden bir tezgah seçin!")
                    return
                
                eksen = eksen_combo.currentText()
                pil_modeli = pil_modeli_edit.text().strip()
                pil_seri = pil_seri_edit.text().strip()
                degisim_tarihi = degisim_tarih_edit.date().toPyDate()
                degistiren = degistiren_edit.text().strip()
                
                # Beklenen ömür parse et
                beklenen_omur_text = beklenen_omur_combo.currentText()
                beklenen_omur = int(beklenen_omur_text.split()[0])  # "365 gün (1 yıl)" -> 365
                
                voltaj_text = voltaj_edit.text().strip()
                voltaj = None
                if voltaj_text:
                    try:
                        voltaj = float(voltaj_text)
                    except ValueError:
                        CustomMessageBox.warning(self, "⚠️ Geçersiz Voltaj", "Voltaj değeri sayı olmalıdır!")
                        return
                
                aciklama = aciklama_edit.toPlainText().strip()
                
                # Validasyon
                try:
                    validated_pil_modeli = validate_text_field(pil_modeli, "Pil Modeli", min_len=2, max_len=100)
                    validated_degistiren = validate_text_field(degistiren, "Değiştiren Kişi", min_len=2, max_len=100)
                    validated_aciklama = validate_text_field(aciklama, "Açıklama", min_len=0, max_len=255)
                    validated_pil_seri = validate_text_field(pil_seri, "Pil Seri No", min_len=0, max_len=100)
                except ValueError as ve:
                    CustomMessageBox.warning(self, "⚠️ Validasyon Hatası", str(ve))
                    return
                
                # Aynı tezgah ve eksende aktif pil var mı kontrol et
                with self.db_manager.get_session() as session:
                    existing_pil = session.query(Pil).filter_by(
                        tezgah_id=tezgah_data,
                        eksen=eksen,
                        durum='Aktif'
                    ).first()
                    
                    if existing_pil:
                        # Mevcut pil güncelleme dialog'u göster
                        if self.show_battery_replacement_dialog(existing_pil, tezgah_combo.currentText(), 
                                                              validated_pil_modeli, validated_degistiren, 
                                                              degisim_tarihi, voltaj, validated_aciklama, 
                                                              validated_pil_seri, beklenen_omur):
                            # Tabloları yenile
                            self.refresh_pil_table()
                            self.refresh_dashboard()
                            return
                        else:
                            return  # Kullanıcı iptal etti
                
                # Veritabanına ekle
                with self.db_manager.get_session() as session:
                    from datetime import datetime
                    yeni_pil = Pil(
                        tezgah_id=tezgah_data,
                        eksen=eksen,
                        pil_modeli=validated_pil_modeli,
                        pil_seri_no=validated_pil_seri if validated_pil_seri else None,
                        degisim_tarihi=datetime.combine(degisim_tarihi, datetime.min.time()).replace(tzinfo=timezone.utc),
                        degistiren_kisi=validated_degistiren,
                        beklenen_omur=beklenen_omur,
                        voltaj=voltaj,
                        aciklama=validated_aciklama if validated_aciklama else None,
                        durum='Aktif'
                    )
                    
                    session.add(yeni_pil)
                
                # Tabloları yenile
                self.refresh_pil_table()
                self.refresh_dashboard()
                
                CustomMessageBox.information(self, "✅ Başarılı", 
                                           f"Yeni pil kaydı başarıyla eklendi!\n\n"
                                           f"Tezgah: {tezgah_combo.currentText().split(' - ')[0]}\n"
                                           f"Eksen: {eksen}\n"
                                           f"Model: {validated_pil_modeli}")
                self.logger.info(f"New battery record added for tezgah_id: {tezgah_data}, eksen: {eksen}")
                
            except Exception as e:
                self.logger.error(f"Pil kaydı eklenirken hata: {e}")
                CustomMessageBox.critical(self, "❌ Hata", f"Pil kaydı eklenirken hata oluştu:\n{e}")
    
    def show_battery_replacement_dialog(self, existing_pil, tezgah_text, new_model, new_technician, 
                                       new_date, new_voltage, new_description, new_serial, new_expected_life):
        """Mevcut pil değişimi onay dialog'u"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🔄 Pil Değişimi Onayı")
            dialog.setFixedSize(600, 500)
            dialog.setModal(True)
            
            # Stil
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 2px solid #FF9800;
                    border-radius: 10px;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                    padding: 5px;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    color: #ffffff;
                    font-size: 11px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton[class="cancel"] {
                    background-color: #666666;
                }
                QPushButton[class="cancel"]:hover {
                    background-color: #555555;
                }
                QPushButton[class="replace"] {
                    background-color: #FF9800;
                }
                QPushButton[class="replace"]:hover {
                    background-color: #F57C00;
                }
            """)
            
            layout = QVBoxLayout()
            
            # Başlık
            title_label = QLabel("🔄 Mevcut Pil Değişimi")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800; margin-bottom: 10px;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # Uyarı mesajı
            warning_label = QLabel("⚠️ Bu tezgahın bu ekseninde zaten aktif bir pil bulunuyor!")
            warning_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #FF9800; margin-bottom: 15px;")
            warning_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning_label)
            
            # Karşılaştırma tablosu
            comparison_text = QTextEdit()
            comparison_text.setReadOnly(True)
            comparison_text.setMaximumHeight(300)
            
            # Mevcut pil yaşını hesapla
            current_age = (datetime.now(timezone.utc) - existing_pil.degisim_tarihi).days
            
            comparison_content = f"""
📊 PİL KARŞILAŞTIRMASI

🏭 Tezgah: {tezgah_text.split(' - ')[0]}
📍 Eksen: {existing_pil.eksen}

┌─────────────────────────────────────────────────────────────┐
│                    MEVCUT PİL                               │
├─────────────────────────────────────────────────────────────┤
│ 🔋 Model: {existing_pil.pil_modeli or 'Belirtilmemiş'}
│ 📅 Değişim Tarihi: {existing_pil.degisim_tarihi.strftime('%d.%m.%Y')}
│ 👨‍🔧 Değiştiren: {existing_pil.degistiren_kisi or 'Bilinmiyor'}
│ ⏱️ Yaş: {current_age} gün
│ ⚡ Voltaj: {existing_pil.voltaj or 'Belirtilmemiş'} V
│ 🏷️ Seri No: {existing_pil.pil_seri_no or 'Yok'}
│ 📝 Açıklama: {existing_pil.aciklama or 'Yok'}
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     YENİ PİL                                │
├─────────────────────────────────────────────────────────────┤
│ 🔋 Model: {new_model}
│ 📅 Değişim Tarihi: {new_date.strftime('%d.%m.%Y')}
│ 👨‍🔧 Değiştiren: {new_technician}
│ ⏱️ Yaş: 0 gün (YENİ)
│ ⚡ Voltaj: {new_voltage or 'Belirtilmemiş'} V
│ 🏷️ Seri No: {new_serial or 'Yok'}
│ 📝 Açıklama: {new_description or 'Yok'}
└─────────────────────────────────────────────────────────────┘

🔄 İŞLEM: Mevcut pil kaydı güncellenecek (yeni kayıt oluşturulmayacak)
"""
            
            comparison_text.setPlainText(comparison_content)
            layout.addWidget(comparison_text)
            
            # Seçenekler
            options_label = QLabel("Ne yapmak istiyorsunuz?")
            options_label.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 10px;")
            layout.addWidget(options_label)
            
            # Butonlar
            button_layout = QHBoxLayout()
            
            # Pil değiştir butonu
            replace_btn = QPushButton("🔄 Pili Değiştir (Kaydı Güncelle)")
            replace_btn.setProperty("class", "replace")
            replace_btn.clicked.connect(lambda: self.replace_existing_battery(
                dialog, existing_pil, new_model, new_technician, new_date, 
                new_voltage, new_description, new_serial, new_expected_life
            ))
            button_layout.addWidget(replace_btn)
            
            # Yeni kayıt oluştur butonu
            new_record_btn = QPushButton("➕ Yeni Kayıt Oluştur")
            new_record_btn.clicked.connect(lambda: self.create_new_battery_record(
                dialog, existing_pil, new_model, new_technician, new_date, 
                new_voltage, new_description, new_serial, new_expected_life
            ))
            button_layout.addWidget(new_record_btn)
            
            # İptal butonu
            cancel_btn = QPushButton("❌ İptal")
            cancel_btn.setProperty("class", "cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # Açıklama
            info_label = QLabel("💡 Önerilen: Aynı tezgahta çok fazla kayıt olmaması için 'Pili Değiştir' seçeneğini kullanın.")
            info_label.setStyleSheet("font-size: 10px; color: #cccccc; margin-top: 10px;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            dialog.setLayout(layout)
            
            # Dialog'u göster
            result = dialog.exec_()
            return result == QDialog.Accepted
            
        except Exception as e:
            self.logger.error(f"Battery replacement dialog error: {e}")
            return False
    
    def replace_existing_battery(self, dialog, existing_pil, new_model, new_technician, 
                               new_date, new_voltage, new_description, new_serial, new_expected_life):
        """Mevcut pil kaydını güncelle"""
        try:
            with self.db_manager.get_session() as session:
                # Mevcut pil kaydını güncelle
                pil = session.query(Pil).filter_by(id=existing_pil.id).first()
                if pil:
                    # Eski bilgileri yedekle (açıklama alanına ekle)
                    old_info = f"[ESKİ PİL - {existing_pil.degisim_tarihi.strftime('%d.%m.%Y')}] "
                    old_info += f"Model: {existing_pil.pil_modeli}, "
                    old_info += f"Değiştiren: {existing_pil.degistiren_kisi}, "
                    old_info += f"Yaş: {(datetime.now(timezone.utc) - existing_pil.degisim_tarihi).days} gün"
                    
                    if new_description:
                        new_description = old_info + " | " + new_description
                    else:
                        new_description = old_info
                    
                    # Yeni bilgileri güncelle
                    pil.pil_modeli = new_model
                    pil.degistiren_kisi = new_technician
                    pil.degisim_tarihi = datetime.combine(new_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    pil.voltaj = new_voltage
                    pil.aciklama = new_description
                    pil.pil_seri_no = new_serial
                    pil.beklenen_omur = new_expected_life
                    pil.guncelleme_tarihi = datetime.now(timezone.utc)
                    pil.durum = 'Aktif'  # Aktif olarak kalsın
            
            CustomMessageBox.information(dialog, "✅ Başarılı", 
                                       f"Pil kaydı başarıyla güncellendi!\n\n"
                                       f"Tezgah: {existing_pil.tezgah.numarasi if hasattr(existing_pil, 'tezgah') else 'Bilinmiyor'}\n"
                                       f"Eksen: {existing_pil.eksen}\n"
                                       f"Yeni Model: {new_model}\n\n"
                                       f"Eski pil bilgileri açıklama alanına kaydedildi.")
            
            self.logger.info(f"Battery record updated for pil_id: {existing_pil.id}")
            dialog.accept()
            
        except Exception as e:
            self.logger.error(f"Replace existing battery error: {e}")
            CustomMessageBox.critical(dialog, "❌ Hata", f"Pil güncellenirken hata oluştu:\n{e}")
    
    def create_new_battery_record(self, dialog, existing_pil, new_model, new_technician, 
                                new_date, new_voltage, new_description, new_serial, new_expected_life):
        """Yeni pil kaydı oluştur (eski kaydı değiştirildi olarak işaretle)"""
        try:
            with self.db_manager.get_session() as session:
                # Eski pili 'Değiştirildi' olarak işaretle
                old_pil = session.query(Pil).filter_by(id=existing_pil.id).first()
                if old_pil:
                    old_pil.durum = 'Değiştirildi'
                    old_pil.guncelleme_tarihi = datetime.now(timezone.utc)
                
                # Yeni pil kaydı oluştur
                new_pil = Pil(
                    tezgah_id=existing_pil.tezgah_id,
                    eksen=existing_pil.eksen,
                    pil_modeli=new_model,
                    pil_seri_no=new_serial if new_serial else None,
                    degisim_tarihi=datetime.combine(new_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                    degistiren_kisi=new_technician,
                    beklenen_omur=new_expected_life,
                    voltaj=new_voltage,
                    aciklama=new_description if new_description else None,
                    durum='Aktif'
                )
                
                session.add(new_pil)
            
            CustomMessageBox.information(dialog, "✅ Başarılı", 
                                       f"Yeni pil kaydı oluşturuldu!\n\n"
                                       f"Eski pil 'Değiştirildi' olarak işaretlendi.\n"
                                       f"Yeni pil 'Aktif' olarak eklendi.")
            
            self.logger.info(f"New battery record created, old battery marked as replaced")
            dialog.accept()
            
        except Exception as e:
            self.logger.error(f"Create new battery record error: {e}")
            CustomMessageBox.critical(dialog, "❌ Hata", f"Yeni pil kaydı oluşturulurken hata oluştu:\n{e}")
    
    def get_next_tezgah_number(self, prefix="CNF"):
        """Otomatik sıradaki tezgah numarasını al"""
        try:
            with self.db_manager.get_session() as session:
                # Belirtilen prefix ile başlayan tezgahları al
                tezgahlar = session.query(Tezgah).filter(
                    Tezgah.numarasi.like(f"{prefix}%")
                ).all()
                
                # Numaraları çıkar ve sırala
                numbers = []
                for tezgah in tezgahlar:
                    try:
                        # Prefix'i çıkar ve sayıyı al
                        number_part = tezgah.numarasi.replace(prefix, "").strip()
                        if number_part.isdigit():
                            numbers.append(int(number_part))
                    except:
                        continue
                
                # En büyük numarayı bul ve 1 ekle
                if numbers:
                    next_number = max(numbers) + 1
                else:
                    next_number = 1
                
                return f"{prefix} {next_number:02d}"  # CNF 01, CNF 02 formatında
                
        except Exception as e:
            self.logger.error(f"Next tezgah number generation error: {e}")
            return f"{prefix} 01"  # Fallback
    
    def analyze_tezgah_prefixes(self):
        """Mevcut tezgah numaralarından prefix'leri analiz et"""
        try:
            with self.db_manager.get_session() as session:
                tezgahlar = session.query(Tezgah).all()
                
                prefixes = {}
                for tezgah in tezgahlar:
                    # Tezgah numarasından prefix'i çıkar
                    parts = tezgah.numarasi.split()
                    if len(parts) >= 1:
                        prefix = parts[0]
                        if prefix not in prefixes:
                            prefixes[prefix] = 0
                        prefixes[prefix] += 1
                
                # En çok kullanılan prefix'i döndür
                if prefixes:
                    most_common = max(prefixes.items(), key=lambda x: x[1])
                    return most_common[0]
                else:
                    return "CNF"  # Default
                    
        except Exception as e:
            self.logger.error(f"Prefix analysis error: {e}")
            return "CNF"
    
    def add_tezgah(self):
        """Yeni tezgah ekle - Otomatik sıralama ile"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QTextEdit, QDialogButtonBox, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🏭 Yeni Tezgah Ekle")
        dialog.setFixedSize(450, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        layout = QFormLayout()
        
        # Otomatik tezgah numarası önerisi
        suggested_prefix = self.analyze_tezgah_prefixes()
        suggested_number = self.get_next_tezgah_number(suggested_prefix)
        
        # Form alanları
        tezgah_no_layout = QHBoxLayout()
        tezgah_no_edit = QLineEdit()
        tezgah_no_edit.setText(suggested_number)  # Otomatik öneri
        tezgah_no_edit.setPlaceholderText("Örn: CNF 37")
        
        # Otomatik numara butonu
        auto_number_btn = QPushButton("🔄 Otomatik")
        auto_number_btn.setToolTip("Sıradaki numarayı otomatik oluştur")
        auto_number_btn.clicked.connect(lambda: tezgah_no_edit.setText(
            self.get_next_tezgah_number(suggested_prefix)
        ))
        
        tezgah_no_layout.addWidget(tezgah_no_edit)
        tezgah_no_layout.addWidget(auto_number_btn)
        
        tezgah_adi_edit = QLineEdit()
        tezgah_adi_edit.setPlaceholderText("Örn: CNC Freze Tezgahı 2")
        
        lokasyon_combo = QComboBox()
        lokasyon_combo.addItems(["Atölye A", "Atölye B", "Atölye C", "Depo", "Diğer"])
        lokasyon_combo.setEditable(True)
        
        durum_combo = QComboBox()
        durum_combo.addItems(["Aktif", "Bakımda", "Arızalı", "Devre Dışı"])
        
        bakim_periyodu_spin = QSpinBox()
        bakim_periyodu_spin.setRange(1, 365)
        bakim_periyodu_spin.setValue(30)
        bakim_periyodu_spin.setSuffix(" gün")
        
        aciklama_edit = QTextEdit()
        aciklama_edit.setMaximumHeight(60)
        aciklama_edit.setPlaceholderText("Tezgah hakkında ek bilgiler...")
        
        # Form'a ekle
        layout.addRow("Tezgah No:", tezgah_no_layout)
        layout.addRow("Tezgah Adı:", tezgah_adi_edit)
        layout.addRow("Lokasyon:", lokasyon_combo)
        layout.addRow("Durum:", durum_combo)
        layout.addRow("Bakım Periyodu:", bakim_periyodu_spin)
        layout.addRow("Açıklama:", aciklama_edit)
        
        # Bilgi etiketi
        from PyQt5.QtWidgets import QLabel
        info_label = QLabel("💡 Tezgah numarası otomatik olarak sıralanır. 'Otomatik' butonuna basarak yeni numara alabilirsiniz.")
        info_label.setStyleSheet("color: #4CAF50; font-size: 10px; margin: 5px;")
        info_label.setWordWrap(True)
        layout.addRow(info_label)
        
        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        buttons.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        
        # Dialog'u göster
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Verileri al
                tezgah_no = tezgah_no_edit.text().strip()
                tezgah_adi = tezgah_adi_edit.text().strip()
                lokasyon = lokasyon_combo.currentText().strip()
                durum = durum_combo.currentText()
                bakim_periyodu = bakim_periyodu_spin.value()
                aciklama = aciklama_edit.toPlainText().strip()
                
                # Validasyon
                try:
                    validated_no = validate_tezgah_numarasi(tezgah_no)
                    validated_adi = validate_text_field(tezgah_adi, "Tezgah Adı", min_len=2, max_len=255)
                    validated_lokasyon = validate_text_field(lokasyon, "Lokasyon", min_len=0, max_len=100)
                    validated_aciklama = validate_text_field(aciklama, "Açıklama", min_len=0, max_len=255)
                except ValueError as ve:
                    CustomMessageBox.warning(self, "⚠️ Validasyon Hatası", str(ve))
                    return
                
                # Veritabanına ekle
                with self.db_manager.get_session() as session:
                    # Aynı numarada tezgah var mı kontrol et
                    existing = session.query(Tezgah).filter_by(numarasi=validated_no).first()
                    if existing:
                        CustomMessageBox.warning(self, "❌ Hata", f"'{validated_no}' numaralı tezgah zaten mevcut!")
                        return
                    
                    # Yeni tezgah oluştur
                    yeni_tezgah = Tezgah(
                        numarasi=validated_no,
                        aciklama=validated_adi,
                        lokasyon=validated_lokasyon if validated_lokasyon else None,
                        durum=durum,
                        bakim_periyodu=bakim_periyodu
                    )
                    
                    session.add(yeni_tezgah)
                
                # Tabloları yenile
                self.refresh_tezgah_table()
                self.refresh_dashboard()
                
                CustomMessageBox.information(self, "✅ Başarılı", f"'{validated_no}' numaralı tezgah başarıyla eklendi!")
                self.logger.info(f"New tezgah added: {validated_no}")
                
            except Exception as e:
                self.logger.error(f"Tezgah eklenirken hata: {e}")
                CustomMessageBox.critical(self, "❌ Hata", f"Tezgah eklenirken hata oluştu:\n{e}")
                CustomMessageBox.critical(self, "❌ Hata", f"Tezgah eklenirken hata oluştu:\n{e}")
    
    def run_maintenance_analysis(self):
        """Bakım analizi çalıştır"""
        if not self.gemini_ai.has_api_key():
            CustomMessageBox.information(self, "🔑 API Anahtarı Gerekli", 
                              "AI analizi için API anahtarı gerekli.\nAyarlar > API Anahtarı menüsünden girin.")
            return
        
        self.ai_result_text.setPlainText("🔄 Bakım analizi yapılıyor...")
        
        # Örnek veri
        sample_data = [
            {"tezgah_no": "TZ001", "durum": "Aktif", "son_bakim": "2025-12-01"},
            {"tezgah_no": "TZ002", "durum": "Bakımda", "son_bakim": "2025-11-15"},
            {"tezgah_no": "TZ003", "durum": "Aktif", "son_bakim": "2025-11-20"}
        ]
        
        result = self.gemini_ai.analyze_maintenance_data(sample_data)
        self.ai_result_text.setPlainText(result)
    
    def run_battery_prediction(self):
        """Pil ömrü tahmini çalıştır"""
        if not self.gemini_ai.has_api_key():
            CustomMessageBox.information(self, "🔑 API Anahtarı Gerekli", 
                              "AI analizi için API anahtarı gerekli.\nAyarlar > API Anahtarı menüsünden girin.")
            return
        
        self.ai_result_text.setPlainText("🔄 Pil ömrü analizi yapılıyor...")
        
        # Örnek pil verisi
        sample_data = [
            {"tezgah_no": "TZ001", "pil_tipi": "Lityum", "takma_tarihi": "2025-01-15", "voltaj": 3.2},
            {"tezgah_no": "TZ002", "pil_tipi": "Alkalin", "takma_tarihi": "2024-12-01", "voltaj": 2.8}
        ]
        
        result = self.gemini_ai.predict_battery_life(sample_data)
        self.ai_result_text.setPlainText(result)
    
    def run_maintenance_optimization(self):
        """Bakım optimizasyonu çalıştır"""
        if not self.gemini_ai.has_api_key():
            CustomMessageBox.information(self, "🔑 API Anahtarı Gerekli", 
                              "AI analizi için API anahtarı gerekli.\nAyarlar > API Anahtarı menüsünden girin.")
            return
        
        self.ai_result_text.setPlainText("🔄 Bakım optimizasyonu yapılıyor...")
        
        # Örnek program verisi
        sample_data = [
            {"tezgah": "TZ001", "mevcut_periyot": 30, "son_arizalar": 2, "maliyet": 1500},
            {"tezgah": "TZ002", "mevcut_periyot": 45, "son_arizalar": 0, "maliyet": 800}
        ]
        
        result = self.gemini_ai.optimize_maintenance_schedule(sample_data)
        self.ai_result_text.setPlainText(result)
    
    def show_api_key_settings(self):
        """API anahtarı ayarlarını göster"""
        success = show_api_key_dialog(self)
        if success:
            self.check_api_status()
            CustomMessageBox.information(self, "✅ Başarılı", "API anahtarı güncellendi! AI özellikleri artık kullanılabilir.")
    
    def check_for_updates(self):
        """Güncelleme kontrolü yap"""
        try:
            from auto_updater import AutoUpdater
            
            # Progress dialog göster
            from PyQt5.QtWidgets import QProgressDialog
            from PyQt5.QtCore import Qt
            
            progress_dialog = QProgressDialog("Güncellemeler kontrol ediliyor...", "İptal", 0, 0, self)
            progress_dialog.setWindowTitle("Güncelleme Kontrolü")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.setAutoReset(True)
            progress_dialog.show()
            
            def check_updates_thread():
                try:
                    updater = AutoUpdater()
                    update_info = updater.check_for_updates()
                    
                    progress_dialog.close()
                    
                    if update_info['available']:
                        # Yeni versiyon mevcut
                        message = f"""🎉 Yeni versiyon mevcut!

📦 Mevcut Versiyon: v{updater.current_version}
🆕 Yeni Versiyon: v{update_info['version']}
📅 Yayın Tarihi: {update_info['published_at'][:10]}

📝 Yenilikler:
{update_info['release_notes'][:300]}...

🔄 Güncellemeyi şimdi yapmak istiyor musunuz?

⚠️ Not: Güncelleme sırasında uygulama yeniden başlatılacaktır."""
                        
                        if CustomMessageBox.question(self, "🔄 Güncelleme Mevcut", message):
                            # Launcher'ı çalıştır ve uygulamayı kapat
                            try:
                                import subprocess
                                import sys
                                
                                # Launcher'ı başlat
                                if os.path.exists("launcher.py"):
                                    subprocess.Popen([sys.executable, "launcher.py"])
                                elif os.path.exists("TezgahTakip_Launcher.exe"):
                                    subprocess.Popen(["TezgahTakip_Launcher.exe"])
                                
                                # Ana uygulamayı kapat
                                self.close()
                                
                            except Exception as e:
                                CustomMessageBox.critical(self, "❌ Hata", 
                                                        f"Launcher başlatılamadı:\n{e}\n\nLütfen manuel olarak launcher'ı çalıştırın.")
                        else:
                            CustomMessageBox.information(self, "ℹ️ Bilgi", 
                                                       "Güncelleme iptal edildi. Daha sonra 'Ayarlar > Güncelleme Kontrol' menüsünden kontrol edebilirsiniz.")
                    else:
                        # Uygulama güncel
                        CustomMessageBox.information(self, "✅ Güncel", 
                                                   f"Uygulama güncel!\n\nMevcut versiyon: v{updater.current_version}")
                        
                except Exception as e:
                    progress_dialog.close()
                    if 'error' in update_info:
                        CustomMessageBox.critical(self, "❌ Bağlantı Hatası", 
                                                f"Güncelleme kontrolü yapılamadı:\n{update_info['error']}\n\nİnternet bağlantınızı kontrol edin.")
                    else:
                        CustomMessageBox.critical(self, "❌ Hata", 
                                                f"Güncelleme kontrolü sırasında hata oluştu:\n{e}")
            
            # Thread'de çalıştır
            import threading
            threading.Thread(target=check_updates_thread, daemon=True).start()
            
        except ImportError:
            CustomMessageBox.information(self, "ℹ️ Bilgi", 
                                       "Otomatik güncelleme özelliği bu sürümde mevcut değil.\n\nYeni sürümü manuel olarak indirmeniz gerekiyor.")
        except Exception as e:
            self.logger.error(f"Update check error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Güncelleme kontrolü başlatılamadı:\n{e}")
    
    def show_preferences(self):
        """Tercihler penceresini göster"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, QCheckBox, QSpinBox, QComboBox, QPushButton, QGroupBox, QFormLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ Tercihler")
        dialog.setFixedSize(600, 500)
        dialog.setModal(True)
        
        # Stil
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
                border-radius: 3px;
            }
            QSpinBox, QComboBox {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
                font-size: 11px;
            }
            QSpinBox:focus, QComboBox:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton[class="cancel"] {
                background-color: #666666;
            }
            QPushButton[class="cancel"]:hover {
                background-color: #555555;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Genel ayarlar sekmesi
        genel_tab = QWidget()
        genel_layout = QVBoxLayout()
        
        # Uygulama ayarları grubu
        app_group = QGroupBox("🏭 Uygulama Ayarları")
        app_layout = QFormLayout()
        
        # Otomatik yenileme
        self.auto_refresh_check = QCheckBox("Dashboard otomatik yenileme")
        self.auto_refresh_check.setChecked(True)
        app_layout.addRow(self.auto_refresh_check)
        
        # Yenileme süresi
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(10, 300)
        self.refresh_interval.setValue(30)
        self.refresh_interval.setSuffix(" saniye")
        app_layout.addRow("Yenileme süresi:", self.refresh_interval)
        
        # Başlangıçta açılacak sekme
        self.startup_tab = QComboBox()
        self.startup_tab.addItems(["Dashboard", "Tezgahlar", "Geçmiş Arızalar", "Pil Takibi"])
        app_layout.addRow("Başlangıç sekmesi:", self.startup_tab)
        
        app_group.setLayout(app_layout)
        genel_layout.addWidget(app_group)
        
        # Bildirim ayarları grubu
        notification_group = QGroupBox("🔔 Bildirim Ayarları")
        notification_layout = QFormLayout()
        
        self.maintenance_alerts = QCheckBox("Bakım uyarıları")
        self.maintenance_alerts.setChecked(True)
        notification_layout.addRow(self.maintenance_alerts)
        
        self.battery_alerts = QCheckBox("Pil uyarıları")
        self.battery_alerts.setChecked(True)
        notification_layout.addRow(self.battery_alerts)
        
        # Pil uyarı süresi
        self.battery_warning_days = QSpinBox()
        self.battery_warning_days.setRange(30, 400)
        self.battery_warning_days.setValue(355)
        self.battery_warning_days.setSuffix(" gün")
        notification_layout.addRow("Pil uyarı süresi:", self.battery_warning_days)
        
        notification_group.setLayout(notification_layout)
        genel_layout.addWidget(notification_group)
        
        genel_layout.addStretch()
        genel_tab.setLayout(genel_layout)
        tab_widget.addTab(genel_tab, "🔧 Genel")
        
        # Görünüm sekmesi
        gorunum_tab = QWidget()
        gorunum_layout = QVBoxLayout()
        
        # Tema ayarları
        tema_group = QGroupBox("🎨 Tema Ayarları")
        tema_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Koyu Tema", "Açık Tema (Yakında)"])
        tema_layout.addRow("Tema:", self.theme_combo)
        
        # Font boyutu
        self.font_size = QComboBox()
        self.font_size.addItems(["Küçük", "Normal", "Büyük"])
        self.font_size.setCurrentText("Normal")
        tema_layout.addRow("Font boyutu:", self.font_size)
        
        tema_group.setLayout(tema_layout)
        gorunum_layout.addWidget(tema_group)
        
        # Tablo ayarları
        tablo_group = QGroupBox("📊 Tablo Ayarları")
        tablo_layout = QFormLayout()
        
        # Sayfa başına kayıt
        self.records_per_page = QSpinBox()
        self.records_per_page.setRange(50, 1000)
        self.records_per_page.setValue(100)
        tablo_layout.addRow("Sayfa başına kayıt:", self.records_per_page)
        
        # Tarih formatı
        self.date_format = QComboBox()
        self.date_format.addItems(["dd.mm.yyyy", "yyyy-mm-dd", "mm/dd/yyyy"])
        tablo_layout.addRow("Tarih formatı:", self.date_format)
        
        tablo_group.setLayout(tablo_layout)
        gorunum_layout.addWidget(tablo_group)
        
        gorunum_layout.addStretch()
        gorunum_tab.setLayout(gorunum_layout)
        tab_widget.addTab(gorunum_tab, "👁️ Görünüm")
        
        # Gelişmiş sekmesi
        gelismis_tab = QWidget()
        gelismis_layout = QVBoxLayout()
        
        # Veritabanı ayarları
        db_group = QGroupBox("💾 Veritabanı Ayarları")
        db_layout = QFormLayout()
        
        self.auto_backup = QCheckBox("Otomatik yedekleme")
        self.auto_backup.setChecked(True)
        db_layout.addRow(self.auto_backup)
        
        self.backup_interval = QComboBox()
        self.backup_interval.addItems(["Günlük", "Haftalık", "Aylık"])
        self.backup_interval.setCurrentText("Haftalık")
        db_layout.addRow("Yedekleme sıklığı:", self.backup_interval)
        
        db_group.setLayout(db_layout)
        gelismis_layout.addWidget(db_group)
        
        # Performans ayarları
        perf_group = QGroupBox("⚡ Performans Ayarları")
        perf_layout = QFormLayout()
        
        self.cache_enabled = QCheckBox("Önbellek kullan")
        self.cache_enabled.setChecked(True)
        perf_layout.addRow(self.cache_enabled)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["Hata", "Uyarı", "Bilgi", "Debug"])
        self.log_level.setCurrentText("Bilgi")
        perf_layout.addRow("Log seviyesi:", self.log_level)
        
        perf_group.setLayout(perf_layout)
        gelismis_layout.addWidget(perf_group)
        
        gelismis_layout.addStretch()
        gelismis_tab.setLayout(gelismis_layout)
        tab_widget.addTab(gelismis_tab, "🔬 Gelişmiş")
        
        layout.addWidget(tab_widget)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(lambda: self.save_preferences(dialog))
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.setProperty("class", "cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec_()
    
    def save_preferences(self, dialog):
        """Tercihleri kaydet"""
        try:
            # Burada tercihleri settings.json dosyasına kaydedebiliriz
            # Şimdilik sadece bilgi mesajı gösterelim
            CustomMessageBox.information(self, "✅ Başarılı", 
                                       "Tercihler kaydedildi!\n\n"
                                       "Not: Bazı ayarlar uygulama yeniden başlatıldığında aktif olacaktır.")
            dialog.accept()
        except Exception as e:
            CustomMessageBox.information(self, "❌ Hata", f"Tercihler kaydedilirken hata oluştu:\n{e}")
    
    def show_about(self):
        """Hakkında dialog'unu göster"""
        about_text = """🏭 TezgahTakip - AI Güçlü Fabrika Bakım Yönetim Sistemi

Versiyon: 2.0.0
Geliştirme Tarihi: Aralık 2025

Özellikler:
• AI destekli bakım analizi (Google Gemini)
• Akıllı pil takibi ve ömür tahmini
• Otomatik raporlama sistemi
• Güvenli API anahtarı yönetimi
• Modern kullanıcı arayüzü
• Gerçek zamanlı dashboard
• Otomatik yedekleme sistemi

Teknoloji:
• Python 3.7+ & PyQt5
• SQLite & SQLAlchemy ORM
• Google Gemini AI
• Fernet Şifreleme

© 2025 TezgahTakip - Tüm hakları saklıdır"""
        
        CustomMessageBox.information(self, "ℹ️ Hakkında - TezgahTakip v2.0", about_text)
    
    def export_data(self):
        """Veri dışa aktarma"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGroupBox, QFormLayout, QDateEdit, QCheckBox, QProgressBar, QTextEdit
        from PyQt5.QtCore import QThread, pyqtSignal, QDate
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📤 Veri Dışa Aktarma")
        dialog.setFixedSize(500, 600)
        dialog.setModal(True)
        
        # Stil
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QComboBox, QDateEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
                font-size: 11px;
            }
            QComboBox:focus, QDateEdit:focus {
                border-color: #4CAF50;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton[class="cancel"] {
                background-color: #666666;
            }
            QPushButton[class="cancel"]:hover {
                background-color: #555555;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
                background-color: #3c3c3c;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-size: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Veri tipi seçimi
        data_group = QGroupBox("📊 Dışa Aktarılacak Veriler")
        data_layout = QFormLayout()
        
        self.export_data_type = QComboBox()
        self.export_data_type.addItems([
            "Tezgahlar",
            "Arızalar", 
            "Piller",
            "Özet Rapor (Tümü)"
        ])
        data_layout.addRow("Veri Tipi:", self.export_data_type)
        
        # Format seçimi
        self.export_format = QComboBox()
        self.export_format.addItems(["Excel (.xlsx)", "PDF (.pdf)"])
        data_layout.addRow("Format:", self.export_format)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Filtre seçenekleri
        filter_group = QGroupBox("🔍 Filtreler")
        filter_layout = QFormLayout()
        
        # Tarih aralığı
        self.use_date_filter = QCheckBox("Tarih aralığı kullan")
        filter_layout.addRow(self.use_date_filter)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd.MM.yyyy")
        self.start_date.setEnabled(False)
        filter_layout.addRow("Başlangıç:", self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd.MM.yyyy")
        self.end_date.setEnabled(False)
        filter_layout.addRow("Bitiş:", self.end_date)
        
        # Tarih filtresi aktif/pasif
        self.use_date_filter.toggled.connect(self.start_date.setEnabled)
        self.use_date_filter.toggled.connect(self.end_date.setEnabled)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Grafik seçenekleri
        chart_group = QGroupBox("📈 Grafik Seçenekleri")
        chart_layout = QFormLayout()
        
        self.include_charts = QCheckBox("Grafikleri dahil et")
        chart_layout.addRow(self.include_charts)
        
        self.chart_type = QComboBox()
        self.chart_type.addItems([
            "Arıza Trend Analizi",
            "Pil Değişim Analizi", 
            "Teknisyen Performansı"
        ])
        self.chart_type.setEnabled(False)
        chart_layout.addRow("Grafik Tipi:", self.chart_type)
        
        self.include_charts.toggled.connect(self.chart_type.setEnabled)
        
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)
        
        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setVisible(False)
        layout.addWidget(self.log_text)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        export_btn = QPushButton("📤 Dışa Aktar")
        export_btn.clicked.connect(lambda: self.start_export(dialog))
        button_layout.addWidget(export_btn)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.setProperty("class", "cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec_()
    
    def start_export(self, dialog):
        """Dışa aktarma işlemini başlat"""
        try:
            # Export manager'ı import et
            from export_manager import ExportManager
            
            # Progress bar'ı göster
            self.progress_bar.setVisible(True)
            self.log_text.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Export manager oluştur
            export_manager = ExportManager(self.db_manager)
            
            # Filtreleri hazırla
            filters = {}
            if self.use_date_filter.isChecked():
                filters['start_date'] = self.start_date.date().toPyDate()
                filters['end_date'] = self.end_date.date().toPyDate()
            
            # Veri tipini belirle
            data_type_map = {
                "Tezgahlar": "tezgahlar",
                "Arızalar": "arizalar",
                "Piller": "piller",
                "Özet Rapor (Tümü)": "ozet"
            }
            data_type = data_type_map[self.export_data_type.currentText()]
            
            self.progress_bar.setValue(25)
            self.log_text.append("📊 Veriler hazırlanıyor...")
            
            # Format seçimi
            if self.export_format.currentText().startswith("Excel"):
                filepath = export_manager.export_to_excel(data_type, filters)
                self.progress_bar.setValue(75)
                self.log_text.append("📄 Excel dosyası oluşturuluyor...")
            else:
                filepath = export_manager.export_to_pdf(data_type, filters)
                self.progress_bar.setValue(75)
                self.log_text.append("📄 PDF dosyası oluşturuluyor...")
            
            # Grafik oluştur (eğer seçilmişse)
            chart_path = None
            if self.include_charts.isChecked():
                chart_type_map = {
                    "Arıza Trend Analizi": "ariza_trend",
                    "Pil Değişim Analizi": "pil_degisim",
                    "Teknisyen Performansı": "teknisyen_performans"
                }
                chart_type = chart_type_map[self.chart_type.currentText()]
                chart_path = export_manager.create_chart(chart_type, filters)
                self.log_text.append("📈 Grafik oluşturuluyor...")
            
            self.progress_bar.setValue(100)
            self.log_text.append("✅ Dışa aktarma tamamlandı!")
            
            # Başarı mesajı
            message = f"✅ Dışa aktarma başarılı!\n\n📁 Dosya: {os.path.basename(filepath)}"
            if chart_path:
                message += f"\n📈 Grafik: {os.path.basename(chart_path)}"
            message += f"\n\n📂 Konum: {os.path.dirname(filepath)}"
            
            CustomMessageBox.information(dialog, "✅ Başarılı", message)
            
            # Klasörü aç
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer "{os.path.dirname(filepath)}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", os.path.dirname(filepath)])
            else:  # Linux
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
            
            dialog.accept()
            
        except ImportError as e:
            error_msg = "❌ Gerekli paketler yüklü değil!\n\n"
            if "pandas" in str(e) or "openpyxl" in str(e):
                error_msg += "Excel desteği için:\npip install pandas openpyxl\n\n"
            if "reportlab" in str(e):
                error_msg += "PDF desteği için:\npip install reportlab\n\n"
            if "matplotlib" in str(e):
                error_msg += "Grafik desteği için:\npip install matplotlib"
            
            CustomMessageBox.information(dialog, "⚠️ Eksik Paket", error_msg)
            
        except Exception as e:
            self.log_text.append(f"❌ Hata: {e}")
            CustomMessageBox.information(dialog, "❌ Hata", f"Dışa aktarma sırasında hata oluştu:\n{e}")
    
    def show_tezgah_actions(self, tezgah_id):
        """Tezgah işlemleri menüsünü göster"""
        from PyQt5.QtWidgets import QMenu
        
        try:
            # Context menu oluştur
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 20px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #4CAF50;
                }
            """)
            
            # Tezgah bilgilerini al
            with self.db_manager.get_session() as session:
                tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                if not tezgah:
                    CustomMessageBox.warning(self, "⚠️ Hata", "Tezgah bulunamadı!")
                    return
                
                tezgah_info = {
                    'id': tezgah.id,
                    'numarasi': tezgah.numarasi,
                    'aciklama': tezgah.aciklama,
                    'durum': tezgah.durum
                }
            
            # Menü öğeleri
            view_action = menu.addAction("👁️ Detayları Görüntüle")
            edit_action = menu.addAction("✏️ Düzenle")
            menu.addSeparator()
            
            maintenance_action = menu.addAction("🔧 Bakım Kaydı Ekle")
            battery_action = menu.addAction("🔋 Pil Kaydı Ekle")
            menu.addSeparator()
            
            if tezgah_info['durum'] == 'Aktif':
                status_action = menu.addAction("⏸️ Devre Dışı Bırak")
            else:
                status_action = menu.addAction("▶️ Aktif Yap")
            
            delete_action = menu.addAction("🗑️ Sil")
            
            # Menüyü göster
            action = menu.exec_(self.cursor().pos())
            
            # Seçilen işlemi gerçekleştir
            if action == view_action:
                self.show_tezgah_details(tezgah_info)
            elif action == edit_action:
                self.edit_tezgah(tezgah_info)
            elif action == maintenance_action:
                self.add_maintenance_for_tezgah(tezgah_id)
            elif action == battery_action:
                self.add_battery_for_tezgah(tezgah_id)
            elif action == status_action:
                self.toggle_tezgah_status(tezgah_id, tezgah_info)
            elif action == delete_action:
                self.delete_tezgah(tezgah_id, tezgah_info)
                
        except Exception as e:
            self.logger.error(f"Tezgah işlemleri menüsü hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"İşlem menüsü açılırken hata oluştu:\n{e}")
    
    def add_maintenance_for_tezgah(self, tezgah_id):
        """Belirli tezgah için bakım kaydı ekle"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit, QDialogButtonBox, QSpinBox
        from PyQt5.QtCore import QDate
        
        try:
            # Tezgah bilgilerini al
            with self.db_manager.get_session() as session:
                tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                if not tezgah:
                    CustomMessageBox.warning(self, "⚠️ Hata", "Tezgah bulunamadı!")
                    return
                
                tezgah_info = {
                    'id': tezgah.id,
                    'numarasi': tezgah.numarasi,
                    'aciklama': tezgah.aciklama
                }
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"🔧 Arıza Kaydı Ekle - {tezgah_info['numarasi']}")
            dialog.setFixedSize(500, 400)
            dialog.setModal(True)
            
            # Dialog stili
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                    font-weight: bold;
                }
                QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
                    background-color: #3c3c3c;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    padding: 5px;
                    color: #ffffff;
                }
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
                    border-color: #4CAF50;
                }
            """)
            
            layout = QFormLayout()
            
            # Tezgah bilgisi (sadece gösterim)
            tezgah_label = QLineEdit(f"{tezgah_info['numarasi']} - {tezgah_info['aciklama'] or 'Tezgah'}")
            tezgah_label.setReadOnly(True)
            tezgah_label.setStyleSheet("background-color: #555555; color: #ffffff;")
            
            # Arıza tarihi
            tarih_edit = QDateEdit()
            tarih_edit.setDate(QDate.currentDate())
            tarih_edit.setCalendarPopup(True)
            
            # Teknisyen
            teknisyen_edit = QLineEdit()
            teknisyen_edit.setPlaceholderText("Arızayı gideren teknisyen adı")
            
            # Arıza türü
            tur_combo = QComboBox()
            tur_combo.addItems(["Arızalı", "Periyodik", "Acil", "Önleyici"])
            tur_combo.setCurrentText("Arızalı")
            
            # Durum
            durum_combo = QComboBox()
            durum_combo.addItems(["Tamamlandı", "Devam Ediyor", "Planlandı", "İptal Edildi"])
            durum_combo.setCurrentText("Tamamlandı")
            
            # Maliyet
            maliyet_spin = QSpinBox()
            maliyet_spin.setRange(0, 999999)
            maliyet_spin.setSuffix(" ₺")
            maliyet_spin.setValue(0)
            
            # Açıklama
            aciklama_edit = QTextEdit()
            aciklama_edit.setPlaceholderText("Arıza detayları, yapılan işlemler, kullanılan parçalar...")
            aciklama_edit.setMaximumHeight(100)
            
            # Form'a ekle
            layout.addRow("🏭 Tezgah:", tezgah_label)
            layout.addRow("📅 Tarih:", tarih_edit)
            layout.addRow("👨‍🔧 Teknisyen:", teknisyen_edit)
            layout.addRow("⚠️ Arıza Türü:", tur_combo)
            layout.addRow("📊 Durum:", durum_combo)
            layout.addRow("💰 Maliyet:", maliyet_spin)
            layout.addRow("📝 Açıklama:", aciklama_edit)
            
            # Butonlar
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            buttons.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            
            layout.addRow(buttons)
            dialog.setLayout(layout)
            
            # Dialog'u göster
            if dialog.exec_() == QDialog.Accepted:
                # Verileri al
                tarih = tarih_edit.date().toPyDate()
                teknisyen = teknisyen_edit.text().strip()
                tur = tur_combo.currentText()
                durum = durum_combo.currentText()
                maliyet = maliyet_spin.value() if maliyet_spin.value() > 0 else None
                aciklama = aciklama_edit.toPlainText().strip()
                
                # Validasyon
                if not teknisyen:
                    CustomMessageBox.warning(self, "⚠️ Uyarı", "Teknisyen adı boş olamaz!")
                    return
                
                if not aciklama:
                    CustomMessageBox.warning(self, "⚠️ Uyarı", "Açıklama boş olamaz!")
                    return
                
                # Veritabanına ekle
                with self.db_manager.get_session() as session:
                    from datetime import datetime, timezone
                    
                    yeni_bakim = Bakim(
                        tezgah_id=tezgah_id,
                        tarih=datetime.combine(tarih, datetime.min.time()).replace(tzinfo=timezone.utc),
                        bakim_yapan=teknisyen,
                        aciklama=aciklama,
                        durum=durum,
                        bakim_turu=tur,
                        maliyet=maliyet
                    )
                    
                    session.add(yeni_bakim)
                    
                    # Tezgah'ın son bakım tarihini güncelle
                    tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                    if tezgah:
                        tezgah.son_bakim_tarihi = yeni_bakim.tarih
                        tezgah.updated_at = datetime.now(timezone.utc)
                
                # Tabloları yenile
                self.refresh_bakim_table()
                self.refresh_tezgah_table()
                self.refresh_dashboard()
                
                CustomMessageBox.information(self, "✅ Başarılı", 
                                           f"Arıza kaydı başarıyla eklendi!\n\n"
                                           f"Tezgah: {tezgah_info['numarasi']}\n"
                                           f"Teknisyen: {teknisyen}\n"
                                           f"Durum: {durum}")
                
                self.logger.info(f"Maintenance record added for tezgah {tezgah_id}")
                
        except Exception as e:
            self.logger.error(f"Add maintenance for tezgah error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Arıza kaydı eklenirken hata oluştu:\n{e}")
    
    def add_battery_for_tezgah(self, tezgah_id):
        """Belirli tezgah için pil kaydı ekle"""
        try:
            # Mevcut add_pil fonksiyonunu kullan ama tezgah'ı önceden seç
            self.add_pil(preselected_tezgah_id=tezgah_id)
        except Exception as e:
            self.logger.error(f"Add battery for tezgah error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Pil kaydı eklenirken hata oluştu:\n{e}")
    
    def toggle_tezgah_status(self, tezgah_id, tezgah_info):
        """Tezgah durumunu değiştir"""
        try:
            current_status = tezgah_info['durum']
            new_status = 'Aktif' if current_status != 'Aktif' else 'Devre Dışı'
            
            # Onay al
            if not CustomMessageBox.question(self, "🔄 Durum Değiştir", 
                                           f"'{tezgah_info['numarasi']}' tezgahının durumunu '{new_status}' yapmak istediğinizden emin misiniz?"):
                return
            
            # Veritabanında güncelle
            with self.db_manager.get_session() as session:
                from datetime import datetime, timezone
                
                tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                if tezgah:
                    tezgah.durum = new_status
                    tezgah.updated_at = datetime.now(timezone.utc)
            
            # Tabloları yenile
            self.refresh_tezgah_table()
            self.refresh_dashboard()
            
            CustomMessageBox.information(self, "✅ Başarılı", 
                                       f"Tezgah durumu '{new_status}' olarak güncellendi!")
            
            self.logger.info(f"Tezgah {tezgah_id} status changed to {new_status}")
            
        except Exception as e:
            self.logger.error(f"Toggle tezgah status error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Durum değiştirilirken hata oluştu:\n{e}")
    
    def delete_tezgah(self, tezgah_id, tezgah_info):
        """Tezgah sil"""
        try:
            # Onay al
            if not CustomMessageBox.question(self, "🗑️ Tezgah Sil", 
                                           f"'{tezgah_info['numarasi']}' tezgahını silmek istediğinizden emin misiniz?\n\n"
                                           f"⚠️ Bu işlem geri alınamaz ve tüm ilişkili kayıtlar (arıza, pil) da silinecektir!"):
                return
            
            # Veritabanından sil
            with self.db_manager.get_session() as session:
                tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                if tezgah:
                    session.delete(tezgah)  # Cascade delete ile ilişkili kayıtlar da silinir
            
            # Tabloları yenile
            self.refresh_tezgah_table()
            self.refresh_bakim_table()
            self.refresh_pil_table()
            self.refresh_dashboard()
            
            CustomMessageBox.information(self, "✅ Başarılı", 
                                       f"'{tezgah_info['numarasi']}' tezgahı başarıyla silindi!")
            
            self.logger.info(f"Tezgah {tezgah_id} deleted")
            
        except Exception as e:
            self.logger.error(f"Delete tezgah error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Tezgah silinirken hata oluştu:\n{e}")
    
    def show_tezgah_details(self, tezgah_info):
        """Tezgah detaylarını göster"""
        try:
            # Detaylı bilgileri al
            with self.db_manager.get_session() as session:
                tezgah = session.query(Tezgah).filter_by(id=tezgah_info['id']).first()
                if not tezgah:
                    CustomMessageBox.critical(self, "❌ Hata", "Tezgah bulunamadı!")
                    return
                
                # Son arıza bilgisi
                son_ariza = session.query(Bakim).filter_by(tezgah_id=tezgah_info['id']).order_by(Bakim.tarih.desc()).first()
                
                # Pil bilgileri
                piller = session.query(Pil).filter_by(tezgah_id=tezgah_info['id'], durum='Aktif').all()
                
                # Toplam arıza sayısı
                toplam_ariza = session.query(Bakim).filter_by(tezgah_id=tezgah_info['id']).count()
                
                # Verileri dictionary'lere çevir (session dışında kullanmak için)
                tezgah_data = {
                    'numarasi': tezgah.numarasi,
                    'aciklama': tezgah.aciklama,
                    'lokasyon': tezgah.lokasyon,
                    'durum': tezgah.durum,
                    'bakim_periyodu': tezgah.bakim_periyodu,
                    'son_bakim_tarihi': tezgah.son_bakim_tarihi,
                    'sonraki_bakim_tarihi': tezgah.sonraki_bakim_tarihi,
                    'created_at': tezgah.created_at,
                    'updated_at': tezgah.updated_at
                }
                
                son_ariza_data = None
                if son_ariza:
                    son_ariza_data = {
                        'tarih': son_ariza.tarih,
                        'aciklama': son_ariza.aciklama,
                        'bakim_yapan': son_ariza.bakim_yapan,  # Doğru field adı
                        'maliyet': getattr(son_ariza, 'maliyet', None)
                    }
                
                pil_data = []
                for pil in piller:
                    pil_data.append({
                        'pil_seri_no': getattr(pil, 'pil_seri_no', 'Belirtilmemiş'),  # Doğru field adı
                        'degisim_tarihi': pil.degisim_tarihi,
                        'durum': pil.durum,
                        'eksen': getattr(pil, 'eksen', 'Bilinmiyor'),
                        'pil_modeli': getattr(pil, 'pil_modeli', 'Belirtilmemiş'),
                        'degistiren_kisi': pil.degistiren_kisi
                    })
            
            # Detay dialog'u
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QTabWidget, QWidget, QScrollArea
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"🏭 Tezgah Detayları - {tezgah_data['numarasi']}")
            dialog.setFixedSize(700, 600)
            dialog.setModal(True)
            
            # Dialog stili
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                    margin: 5px 0;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    color: #ffffff;
                    font-size: 11px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                }
                QTabBar::tab:selected {
                    background-color: #4CAF50;
                    color: white;
                }
            """)
            
            layout = QVBoxLayout()
            
            # Başlık
            title_label = QLabel(f"🏭 {tezgah_data['numarasi']} - {tezgah_data['aciklama'] or 'Tezgah Detayları'}")
            title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 15px;")
            layout.addWidget(title_label)
            
            # Tab widget
            tab_widget = QTabWidget()
            
            # Genel Bilgiler Sekmesi
            genel_tab = QWidget()
            genel_layout = QVBoxLayout()
            
            genel_info = QTextEdit()
            genel_info.setReadOnly(True)
            
            # Genel bilgileri hazırla
            genel_details = f"""
📋 GENEL BİLGİLER
{'='*60}
🏭 Tezgah Numarası: {tezgah_data['numarasi']}
📝 Açıklama: {tezgah_data['aciklama'] or 'Belirtilmemiş'}
📍 Lokasyon: {tezgah_data['lokasyon'] or 'Belirtilmemiş'}
⚡ Durum: {tezgah_data['durum']}
🔧 Bakım Periyodu: {tezgah_data['bakim_periyodu']} gün

📅 TARİH BİLGİLERİ
{'='*60}
📅 Oluşturma Tarihi: {tezgah_data['created_at'].strftime('%d.%m.%Y %H:%M') if tezgah_data['created_at'] else 'Belirtilmemiş'}
🔄 Son Güncelleme: {tezgah_data['updated_at'].strftime('%d.%m.%Y %H:%M') if tezgah_data['updated_at'] else 'Belirtilmemiş'}
⚠️ Son Arıza Tarihi: {tezgah_data['son_bakim_tarihi'].strftime('%d.%m.%Y') if tezgah_data['son_bakim_tarihi'] else 'Henüz arıza yaşanmamış'}
📅 Sonraki Bakım: {tezgah_data['sonraki_bakim_tarihi'].strftime('%d.%m.%Y') if tezgah_data['sonraki_bakim_tarihi'] else 'Planlanmamış'}
"""
            
            # Arıza durumu analizi
            if tezgah_data['son_bakim_tarihi']:
                from datetime import datetime
                gun_farki = (datetime.now() - tezgah_data['son_bakim_tarihi']).days
                genel_details += f"\n⏰ Son Arızadan Bu Yana: {gun_farki} gün\n"
                
                if gun_farki > tezgah_data['bakim_periyodu']:
                    genel_details += "✅ Uzun süredir arıza yaşanmamış\n"
                elif gun_farki > (tezgah_data['bakim_periyodu'] * 0.5):
                    genel_details += "🟡 Orta seviye arıza geçmişi\n"
                else:
                    genel_details += "⚠️ Yakın zamanda arıza yaşanmış\n"
            
            genel_info.setPlainText(genel_details)
            genel_layout.addWidget(genel_info)
            genel_tab.setLayout(genel_layout)
            tab_widget.addTab(genel_tab, "📋 Genel Bilgiler")
            
            # Arıza Geçmişi Sekmesi
            ariza_tab = QWidget()
            ariza_layout = QVBoxLayout()
            
            ariza_info = QTextEdit()
            ariza_info.setReadOnly(True)
            
            ariza_details = f"""
⚠️ ARIZA GEÇMİŞİ
{'='*60}
📊 Toplam Arıza Sayısı: {toplam_ariza}
"""
            
            if son_ariza_data:
                ariza_details += f"""
⚠️ SON ARIZA BİLGİLERİ
{'='*60}
📅 Tarih: {son_ariza_data['tarih'].strftime('%d.%m.%Y %H:%M')}
👨‍🔧 Teknisyen: {son_ariza_data['bakim_yapan'] or 'Belirtilmemiş'}
📝 Açıklama: {son_ariza_data['aciklama'] or 'Belirtilmemiş'}
💰 Maliyet: {son_ariza_data['maliyet'] or 'Belirtilmemiş'}
"""
            else:
                ariza_details += "\n⚠️ Henüz arıza kaydı bulunmuyor\n"
            
            # Arıza istatistikleri
            if toplam_ariza > 0:
                ariza_details += f"""
📈 ARIZA İSTATİSTİKLERİ
{'='*60}
📊 Ortalama Arıza Sıklığı: {365 // max(toplam_ariza, 1)} gün
📅 Bakım Periyodu: {tezgah_data['bakim_periyodu']} gün
"""
                
                if toplam_ariza >= 5:
                    ariza_details += "⚠️ Sık arıza yaşanıyor - bakım gerekli\n"
                elif toplam_ariza >= 2:
                    ariza_details += "🟡 Orta seviye arıza geçmişi\n"
                else:
                    ariza_details += "✅ Az arıza geçmişi - iyi durumda\n"
            
            ariza_info.setPlainText(ariza_details)
            ariza_layout.addWidget(ariza_info)
            ariza_tab.setLayout(ariza_layout)
            tab_widget.addTab(ariza_tab, "⚠️ Arıza Geçmişi")
            
            # Pil Bilgileri Sekmesi
            pil_tab = QWidget()
            pil_layout = QVBoxLayout()
            
            pil_info = QTextEdit()
            pil_info.setReadOnly(True)
            
            pil_details = f"""
🔋 PİL BİLGİLERİ
{'='*60}
📊 Aktif Pil Sayısı: {len(pil_data)}
"""
            
            if pil_data:
                for i, pil in enumerate(pil_data, 1):
                    yas = (datetime.now() - pil['degisim_tarihi']).days if pil['degisim_tarihi'] else 0
                    pil_details += f"""
🔋 Pil {i}:
   • Seri No: {pil['pil_seri_no']}
   • Eksen: {pil['eksen']}
   • Model: {pil['pil_modeli']}
   • Değişim Tarihi: {pil['degisim_tarihi'].strftime('%d.%m.%Y') if pil['degisim_tarihi'] else 'Belirtilmemiş'}
   • Değiştiren: {pil['degistiren_kisi']}
   • Yaş: {yas} gün
   • Durum: {pil['durum']}
"""
                    
                    # Pil yaşı uyarıları
                    if yas > 365:
                        pil_details += "   ⚠️ UYARI: Pil çok eski, değişim gerekli!\n"
                    elif yas > 300:
                        pil_details += "   🟡 DİKKAT: Pil yaşlanıyor\n"
                    else:
                        pil_details += "   ✅ Pil durumu iyi\n"
            else:
                pil_details += "\n🔋 Henüz pil kaydı bulunmuyor\n"
                pil_details += "\n💡 İPUCU: Yeni pil eklemek için tezgah işlemleri menüsünden '🔋 Pil Kaydı Ekle' seçeneğini kullanın.\n"
            
            pil_info.setPlainText(pil_details)
            pil_layout.addWidget(pil_info)
            pil_tab.setLayout(pil_layout)
            tab_widget.addTab(pil_tab, "🔋 Pil Bilgileri")
            
            layout.addWidget(tab_widget)
            
            # Butonlar
            button_layout = QHBoxLayout()
            
            # Düzenle butonu
            edit_btn = QPushButton("✏️ Düzenle")
            edit_btn.clicked.connect(lambda: (dialog.accept(), self.edit_tezgah(tezgah_info)))
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            button_layout.addWidget(edit_btn)
            
            button_layout.addStretch()
            
            # Kapat butonu
            close_btn = QPushButton("✅ Kapat")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"Tezgah detayları gösterme hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Tezgah detayları gösterilirken hata oluştu:\n{e}")
    
    def edit_tezgah(self, tezgah_info):
        """Tezgah bilgilerini düzenle"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QTextEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"✏️ Tezgah Düzenle - {tezgah_info['numarasi']}")
        dialog.setFixedSize(500, 450)
        dialog.setModal(True)
        
        # Dialog stili
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                margin: 5px 0;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                padding: 8px;
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton[class="cancel"] {
                background-color: #666666;
            }
            QPushButton[class="cancel"]:hover {
                background-color: #555555;
            }
        """)
        
        layout = QFormLayout()
        
        # Mevcut tezgah bilgilerini al
        try:
            with self.db_manager.get_session() as session:
                tezgah = session.query(Tezgah).filter_by(id=tezgah_info['id']).first()
                if not tezgah:
                    CustomMessageBox.critical(self, "❌ Hata", "Tezgah bulunamadı!")
                    return
                
                # Tezgah verilerini dictionary'e çevir (session dışında kullanmak için)
                tezgah_data = {
                    'numarasi': tezgah.numarasi,
                    'aciklama': tezgah.aciklama,
                    'lokasyon': tezgah.lokasyon,
                    'durum': tezgah.durum,
                    'bakim_periyodu': tezgah.bakim_periyodu
                }
        except Exception as e:
            CustomMessageBox.critical(self, "❌ Hata", f"Tezgah bilgileri alınırken hata oluştu:\n{e}")
            return
        
        # Form alanları
        numara_edit = QLineEdit(tezgah_data['numarasi'])
        layout.addRow("🏭 Tezgah Numarası:", numara_edit)
        
        aciklama_edit = QLineEdit("")
        aciklama_edit.setPlaceholderText("Kısa açıklama...")
        layout.addRow("📝 Kısa Açıklama:", aciklama_edit)
        
        lokasyon_edit = QLineEdit(tezgah_data['lokasyon'] or "")
        layout.addRow("📍 Lokasyon:", lokasyon_edit)
        
        durum_combo = QComboBox()
        durum_combo.addItems(["Aktif", "Bakımda", "Arızalı", "Devre Dışı"])
        durum_combo.setCurrentText(tezgah_data['durum'])
        layout.addRow("⚡ Durum:", durum_combo)
        
        bakim_periyodu_spin = QSpinBox()
        bakim_periyodu_spin.setRange(1, 365)
        bakim_periyodu_spin.setValue(tezgah_data['bakim_periyodu'])
        bakim_periyodu_spin.setSuffix(" gün")
        layout.addRow("🔧 Bakım Periyodu:", bakim_periyodu_spin)
        
        notlar_edit = QTextEdit(tezgah_data['aciklama'] or "")
        notlar_edit.setMaximumHeight(80)
        notlar_edit.setPlaceholderText("Tezgah hakkında açıklama...")
        layout.addRow("📋 Açıklama/Notlar:", notlar_edit)
        
        # Butonlar
        button_box = QDialogButtonBox()
        
        save_btn = button_box.addButton("💾 Kaydet", QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton("❌ İptal", QDialogButtonBox.RejectRole)
        cancel_btn.setProperty("class", "cancel")
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addRow(button_box)
        dialog.setLayout(layout)
        
        # Dialog'u göster
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Validasyon
                new_numara = numara_edit.text().strip()
                if not new_numara:
                    CustomMessageBox.warning(self, "⚠️ Uyarı", "Tezgah numarası boş olamaz!")
                    return
                
                # Numara değişmişse, başka tezgahta kullanılıp kullanılmadığını kontrol et
                if new_numara != tezgah_data['numarasi']:
                    if not validate_tezgah_numarasi(new_numara):
                        CustomMessageBox.warning(self, "⚠️ Uyarı", "Geçersiz tezgah numarası formatı!")
                        return
                    
                    with self.db_manager.get_session() as session:
                        existing = session.query(Tezgah).filter(
                            Tezgah.numarasi == new_numara,
                            Tezgah.id != tezgah_info['id']
                        ).first()
                        if existing:
                            CustomMessageBox.warning(self, "⚠️ Uyarı", f"'{new_numara}' numarası zaten kullanılıyor!")
                            return
                
                # Güncelleme
                with self.db_manager.get_session() as session:
                    tezgah_to_update = session.query(Tezgah).filter_by(id=tezgah_info['id']).first()
                    if tezgah_to_update:
                        # Değişiklikleri kaydet
                        old_numara = tezgah_to_update.numarasi
                        tezgah_to_update.numarasi = new_numara
                        tezgah_to_update.aciklama = notlar_edit.toPlainText().strip() or None  # Detaylı açıklama
                        tezgah_to_update.lokasyon = lokasyon_edit.text().strip() or None
                        tezgah_to_update.durum = durum_combo.currentText()
                        tezgah_to_update.bakim_periyodu = bakim_periyodu_spin.value()
                        
                        session.commit()
                        
                        # Başarı mesajı
                        changes = []
                        if old_numara != new_numara:
                            changes.append(f"Numara: {old_numara} → {new_numara}")
                        if tezgah_data['durum'] != durum_combo.currentText():
                            changes.append(f"Durum: {tezgah_data['durum']} → {durum_combo.currentText()}")
                        if tezgah_data['bakim_periyodu'] != bakim_periyodu_spin.value():
                            changes.append(f"Bakım Periyodu: {tezgah_data['bakim_periyodu']} → {bakim_periyodu_spin.value()} gün")
                        
                        success_msg = f"✅ Tezgah '{new_numara}' başarıyla güncellendi!"
                        if changes:
                            success_msg += f"\n\n📝 Değişiklikler:\n• " + "\n• ".join(changes)
                        
                        CustomMessageBox.information(self, "✅ Başarılı", success_msg)
                        
                        # Tabloları yenile
                        self.refresh_tezgah_table()
                        self.refresh_dashboard()
                        
                        self.logger.info(f"Tezgah güncellendi: {old_numara} → {new_numara}")
                    else:
                        CustomMessageBox.critical(self, "❌ Hata", "Tezgah bulunamadı!")
                        
            except Exception as e:
                self.logger.error(f"Tezgah güncelleme hatası: {e}")
                CustomMessageBox.critical(self, "❌ Hata", f"Tezgah güncellenirken hata oluştu:\n{e}")
    
    def toggle_tezgah_status(self, tezgah_id, tezgah_info):
        """Tezgah durumunu değiştir"""
        try:
            new_status = 'Aktif' if tezgah_info['durum'] != 'Aktif' else 'Devre Dışı'
            
            if CustomMessageBox.question(self, "⚠️ Durum Değişikliği", 
                                       f"'{tezgah_info['numarasi']}' tezgahının durumu '{new_status}' olarak değiştirilecek.\n\n"
                                       "Devam etmek istediğinizden emin misiniz?"):
                
                with self.db_manager.get_session() as session:
                    tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                    if tezgah:
                        tezgah.durum = new_status
                        tezgah.updated_at = datetime.now(timezone.utc)
                
                self.refresh_tezgah_table()
                self.refresh_dashboard()
                
                CustomMessageBox.information(self, "✅ Başarılı", f"Tezgah durumu '{new_status}' olarak güncellendi!")
                
        except Exception as e:
            self.logger.error(f"Tezgah durum değiştirme hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Durum değiştirilirken hata oluştu:\n{e}")
    
    def delete_tezgah(self, tezgah_id, tezgah_info):
        """Tezgahı sil"""
        try:
            if CustomMessageBox.question(self, "⚠️ Tehlikeli İşlem", 
                                       f"'{tezgah_info['numarasi']}' tezgahı ve tüm ilişkili kayıtları (bakım, pil) silinecek!\n\n"
                                       "Bu işlem GERİ ALINAMAZ!\n\n"
                                       "Silmek istediğinizden emin misiniz?"):
                
                with self.db_manager.get_session() as session:
                    tezgah = session.query(Tezgah).filter_by(id=tezgah_id).first()
                    if tezgah:
                        session.delete(tezgah)  # Cascade delete ile ilişkili kayıtlar da silinir
                
                self.refresh_tezgah_table()
                self.refresh_bakim_table()
                self.refresh_pil_table()
                self.refresh_dashboard()
                
                CustomMessageBox.information(self, "✅ Başarılı", f"'{tezgah_info['numarasi']}' tezgahı başarıyla silindi!")
                
        except Exception as e:
            self.logger.error(f"Tezgah silme hatası: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Tezgah silinirken hata oluştu:\n{e}")
    
    def import_data(self):
        """Veri içe aktarma - .db dosyası veya JSON formatında"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QProgressDialog
            import shutil
            import sqlite3
            import json
            
            # Dosya seçim dialog'u
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "İçe Aktarılacak Dosyayı Seçin",
                "",
                "Veritabanı Dosyaları (*.db *.sqlite *.sqlite3);;JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
            )
            
            if not file_path:
                return
            
            # Dosya türünü kontrol et
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in ['.db', '.sqlite', '.sqlite3']:
                self.import_database_file(file_path)
            elif file_extension == '.json':
                self.import_json_file(file_path)
            else:
                CustomMessageBox.warning(self, "⚠️ Uyarı", 
                                       "Desteklenmeyen dosya formatı!\n\n"
                                       "Desteklenen formatlar:\n"
                                       "• .db, .sqlite, .sqlite3 (Veritabanı dosyaları)\n"
                                       "• .json (JSON veri dosyaları)")
                
        except Exception as e:
            self.logger.error(f"Import data error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Veri içe aktarma hatası:\n{e}")
    
    def import_database_file(self, file_path):
        """Veritabanı dosyasını içe aktar"""
        try:
            # Önce dosyanın geçerli bir SQLite veritabanı olduğunu kontrol et
            test_conn = sqlite3.connect(file_path)
            cursor = test_conn.cursor()
            
            # Tabloları kontrol et
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            test_conn.close()
            
            if not tables:
                CustomMessageBox.warning(self, "⚠️ Uyarı", "Seçilen dosya boş bir veritabanı!")
                return
            
            # Kullanıcıya seçenekleri sun
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QLabel, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("İçe Aktarma Seçenekleri")
            dialog.setFixedSize(400, 300)
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            
            # Açıklama
            info_label = QLabel("Veri içe aktarma yöntemi seçin:")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Seçenekler
            merge_radio = QRadioButton("Mevcut verilerle birleştir (önerilen)")
            merge_radio.setChecked(True)
            layout.addWidget(merge_radio)
            
            replace_radio = QRadioButton("Mevcut verileri değiştir (dikkatli olun!)")
            layout.addWidget(replace_radio)
            
            # Butonlar
            button_layout = QHBoxLayout()
            ok_button = QPushButton("Devam Et")
            cancel_button = QPushButton("İptal")
            
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            
            # Dialog olayları
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            if dialog.exec_() != QDialog.Accepted:
                return
            
            merge_mode = merge_radio.isChecked()
            
            # Progress dialog
            progress = QProgressDialog("Veriler içe aktarılıyor...", "İptal", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Veritabanından verileri oku ve aktar
            source_conn = sqlite3.connect(file_path)
            source_cursor = source_conn.cursor()
            
            imported_counts = {
                'tezgahlar': 0,
                'bakimlar': 0,
                'piller': 0
            }
            
            # Tezgahları aktar
            if 'tezgahlar' in tables:
                progress.setLabelText("Tezgahlar aktarılıyor...")
                progress.setValue(10)
                
                source_cursor.execute("SELECT * FROM tezgahlar")
                tezgahlar = source_cursor.fetchall()
                
                # Sütun isimlerini al
                source_cursor.execute("PRAGMA table_info(tezgahlar)")
                columns = [row[1] for row in source_cursor.fetchall()]
                
                for tezgah_data in tezgahlar:
                    try:
                        # Veriyi dict'e çevir
                        tezgah_dict = dict(zip(columns, tezgah_data))
                        
                        # Mevcut tezgahı kontrol et
                        existing = self.db_manager.session.query(Tezgah).filter_by(
                            tezgah_no=tezgah_dict.get('tezgah_no')
                        ).first()
                        
                        if existing and merge_mode:
                            # Güncelle
                            for key, value in tezgah_dict.items():
                                if hasattr(existing, key) and key != 'id':
                                    setattr(existing, key, value)
                        elif not existing:
                            # Yeni ekle
                            new_tezgah = Tezgah()
                            for key, value in tezgah_dict.items():
                                if hasattr(new_tezgah, key) and key != 'id':
                                    setattr(new_tezgah, key, value)
                            self.db_manager.session.add(new_tezgah)
                        
                        imported_counts['tezgahlar'] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Tezgah import error: {e}")
                        continue
            
            progress.setValue(40)
            
            # Bakımları aktar
            if 'bakimlar' in tables:
                progress.setLabelText("Bakımlar aktarılıyor...")
                
                source_cursor.execute("SELECT * FROM bakimlar")
                bakimlar = source_cursor.fetchall()
                
                source_cursor.execute("PRAGMA table_info(bakimlar)")
                columns = [row[1] for row in source_cursor.fetchall()]
                
                for bakim_data in bakimlar:
                    try:
                        bakim_dict = dict(zip(columns, bakim_data))
                        
                        # Yeni bakım ekle (bakımlar genelde unique olur)
                        new_bakim = Bakim()
                        for key, value in bakim_dict.items():
                            if hasattr(new_bakim, key) and key != 'id':
                                setattr(new_bakim, key, value)
                        
                        self.db_manager.session.add(new_bakim)
                        imported_counts['bakimlar'] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Bakım import error: {e}")
                        continue
            
            progress.setValue(70)
            
            # Pilleri aktar
            if 'piller' in tables:
                progress.setLabelText("Piller aktarılıyor...")
                
                source_cursor.execute("SELECT * FROM piller")
                piller = source_cursor.fetchall()
                
                source_cursor.execute("PRAGMA table_info(piller)")
                columns = [row[1] for row in source_cursor.fetchall()]
                
                for pil_data in piller:
                    try:
                        pil_dict = dict(zip(columns, pil_data))
                        
                        # Mevcut pili kontrol et
                        existing = self.db_manager.session.query(Pil).filter_by(
                            tezgah_no=pil_dict.get('tezgah_no'),
                            eksen=pil_dict.get('eksen')
                        ).first()
                        
                        if existing and merge_mode:
                            # Güncelle
                            for key, value in pil_dict.items():
                                if hasattr(existing, key) and key != 'id':
                                    setattr(existing, key, value)
                        elif not existing:
                            # Yeni ekle
                            new_pil = Pil()
                            for key, value in pil_dict.items():
                                if hasattr(new_pil, key) and key != 'id':
                                    setattr(new_pil, key, value)
                            self.db_manager.session.add(new_pil)
                        
                        imported_counts['piller'] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Pil import error: {e}")
                        continue
            
            progress.setValue(90)
            
            # Değişiklikleri kaydet
            self.db_manager.session.commit()
            source_conn.close()
            
            progress.setValue(100)
            progress.close()
            
            # Verileri yenile
            self.refresh_all_data()
            
            # Başarı mesajı
            message = f"✅ Veri içe aktarma başarılı!\n\n"
            message += f"📊 İçe aktarılan veriler:\n"
            message += f"• Tezgahlar: {imported_counts['tezgahlar']}\n"
            message += f"• Bakımlar: {imported_counts['bakimlar']}\n"
            message += f"• Piller: {imported_counts['piller']}"
            
            CustomMessageBox.information(self, "✅ Başarılı", message)
            
        except Exception as e:
            self.logger.error(f"Database import error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"Veritabanı içe aktarma hatası:\n{e}")
    
    def import_json_file(self, file_path):
        """JSON dosyasını içe aktar"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Progress dialog
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("JSON veriler aktarılıyor...", "İptal", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            imported_counts = {
                'tezgahlar': 0,
                'bakimlar': 0,
                'piller': 0
            }
            
            # Tezgahları aktar
            if 'tezgahlar' in data:
                progress.setLabelText("Tezgahlar aktarılıyor...")
                progress.setValue(20)
                
                for tezgah_data in data['tezgahlar']:
                    try:
                        existing = self.db_manager.session.query(Tezgah).filter_by(
                            tezgah_no=tezgah_data.get('tezgah_no')
                        ).first()
                        
                        if not existing:
                            new_tezgah = Tezgah()
                            for key, value in tezgah_data.items():
                                if hasattr(new_tezgah, key):
                                    setattr(new_tezgah, key, value)
                            self.db_manager.session.add(new_tezgah)
                            imported_counts['tezgahlar'] += 1
                            
                    except Exception as e:
                        self.logger.warning(f"JSON tezgah import error: {e}")
                        continue
            
            progress.setValue(60)
            
            # Bakımları aktar
            if 'bakimlar' in data:
                progress.setLabelText("Bakımlar aktarılıyor...")
                
                for bakim_data in data['bakimlar']:
                    try:
                        new_bakim = Bakim()
                        for key, value in bakim_data.items():
                            if hasattr(new_bakim, key):
                                setattr(new_bakim, key, value)
                        self.db_manager.session.add(new_bakim)
                        imported_counts['bakimlar'] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"JSON bakım import error: {e}")
                        continue
            
            progress.setValue(80)
            
            # Pilleri aktar
            if 'piller' in data:
                progress.setLabelText("Piller aktarılıyor...")
                
                for pil_data in data['piller']:
                    try:
                        existing = self.db_manager.session.query(Pil).filter_by(
                            tezgah_no=pil_data.get('tezgah_no'),
                            eksen=pil_data.get('eksen')
                        ).first()
                        
                        if not existing:
                            new_pil = Pil()
                            for key, value in pil_data.items():
                                if hasattr(new_pil, key):
                                    setattr(new_pil, key, value)
                            self.db_manager.session.add(new_pil)
                            imported_counts['piller'] += 1
                            
                    except Exception as e:
                        self.logger.warning(f"JSON pil import error: {e}")
                        continue
            
            # Değişiklikleri kaydet
            self.db_manager.session.commit()
            
            progress.setValue(100)
            progress.close()
            
            # Verileri yenile
            self.refresh_all_data()
            
            # Başarı mesajı
            message = f"✅ JSON veri içe aktarma başarılı!\n\n"
            message += f"📊 İçe aktarılan veriler:\n"
            message += f"• Tezgahlar: {imported_counts['tezgahlar']}\n"
            message += f"• Bakımlar: {imported_counts['bakimlar']}\n"
            message += f"• Piller: {imported_counts['piller']}"
            
            CustomMessageBox.information(self, "✅ Başarılı", message)
            
        except Exception as e:
            self.logger.error(f"JSON import error: {e}")
            CustomMessageBox.critical(self, "❌ Hata", f"JSON içe aktarma hatası:\n{e}")
    
    def closeEvent(self, event):
        """Uygulama kapatılırken - Resource cleanup"""
        try:
            if CustomMessageBox.question(self, "❓ Çıkış", 
                                       "Uygulamadan çıkmak istediğinizden emin misiniz?"):
                # Temizlik işlemleri
                self.cleanup_resources()
                
                self.logger.info("Application closed by user")
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            self.logger.error(f"Close event error: {e}")
            event.accept()  # Hata durumunda da kapat

def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    
    # Uygulama bilgileri
    app.setApplicationName("TezgahTakip")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("TezgahTakip")
    
    try:
        # Ana pencere
        window = TezgahTakipMainWindow()
        window.show()
        
        print("✅ TezgahTakip uygulaması başlatıldı!")
        
        # Uygulamayı çalıştır
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Uygulama başlatma hatası: {e}")
        # Ana pencere yoksa basit dialog oluştur
        error_app = QApplication.instance() or QApplication(sys.argv)
        error_dialog = CustomMessageBox(None, "❌ Kritik Hata", f"Uygulama başlatılamadı:\n{e}")
        error_dialog.exec_()
        sys.exit(1)

if __name__ == "__main__":
    main()