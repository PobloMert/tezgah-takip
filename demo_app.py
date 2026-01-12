#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Uygulama - API Anahtarı Yönetimi
TezgahTakip uygulamasına nasıl entegre edileceğini gösteren demo
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                            QWidget, QPushButton, QLabel, QTextEdit, QMenuBar,
                            QMenu, QAction, QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# API anahtarı modüllerini import et
try:
    from api_key_manager import APIKeyManager
    from api_key_dialog import show_api_key_dialog
    from integration_helper import TezgahTakipIntegration
    API_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"API modülleri yüklenemedi: {e}")
    API_MODULES_AVAILABLE = False

class DemoMainWindow(QMainWindow):
    """Demo ana pencere"""
    
    def __init__(self):
        super().__init__()
        self.api_integration = None
        
        if API_MODULES_AVAILABLE:
            self.api_integration = TezgahTakipIntegration()
        
        self.setWindowTitle("🏭 TezgahTakip Demo - API Anahtarı Yönetimi")
        self.setGeometry(100, 100, 800, 600)
        
        # Stil
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
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
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-size: 11px;
                padding: 10px;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
        """)
        
        self.setup_ui()
        self.setup_menu()
        
        # API anahtarı kontrolü
        if self.api_integration:
            self.check_api_key_status()
    
    def setup_ui(self):
        """Arayüzü oluştur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("🏭 TezgahTakip - API Anahtarı Yönetimi Demo")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Açıklama
        info_label = QLabel(
            "Bu demo, TezgahTakip uygulamasına API anahtarı yönetiminin nasıl entegre edileceğini gösterir.\n"
            "Aşağıdaki butonları kullanarak API anahtarı işlemlerini test edebilirsiniz."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #cccccc; margin: 20px; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.api_settings_btn = QPushButton("🔑 API Anahtarı Ayarları")
        self.api_settings_btn.clicked.connect(self.show_api_settings)
        button_layout.addWidget(self.api_settings_btn)
        
        self.check_api_btn = QPushButton("🔍 API Anahtarı Kontrol Et")
        self.check_api_btn.clicked.connect(self.check_api_key_status)
        button_layout.addWidget(self.check_api_btn)
        
        self.test_gemini_btn = QPushButton("🧠 Gemini AI Test Et")
        self.test_gemini_btn.clicked.connect(self.test_gemini_ai)
        button_layout.addWidget(self.test_gemini_btn)
        
        layout.addLayout(button_layout)
        
        # Durum alanı
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(300)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Alt butonlar
        bottom_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Temizle")
        self.clear_btn.clicked.connect(self.clear_status)
        self.clear_btn.setStyleSheet("background-color: #666666;")
        bottom_layout.addWidget(self.clear_btn)
        
        bottom_layout.addStretch()
        
        self.exit_btn = QPushButton("❌ Çıkış")
        self.exit_btn.clicked.connect(self.close)
        self.exit_btn.setStyleSheet("background-color: #f44336;")
        bottom_layout.addWidget(self.exit_btn)
        
        layout.addLayout(bottom_layout)
        
        central_widget.setLayout(layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Demo uygulama hazır")
    
    def setup_menu(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Ayarlar menüsü
        settings_menu = menubar.addMenu("⚙️ Ayarlar")
        
        # API anahtarı action
        api_action = QAction("🔑 API Anahtarı", self)
        api_action.setStatusTip("Gemini API anahtarını ayarla")
        api_action.triggered.connect(self.show_api_settings)
        settings_menu.addAction(api_action)
        
        settings_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("❌ Çıkış", self)
        exit_action.setStatusTip("Uygulamadan çık")
        exit_action.triggered.connect(self.close)
        settings_menu.addAction(exit_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction("ℹ️ Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_api_settings(self):
        """API anahtarı ayarlarını göster"""
        if not API_MODULES_AVAILABLE:
            QMessageBox.warning(self, "Hata", "API modülleri yüklenemedi!")
            return
        
        try:
            self.log_message("🔑 API anahtarı ayarları açılıyor...")
            success = show_api_key_dialog(self)
            
            if success:
                self.log_message("✅ API anahtarı başarıyla kaydedildi!")
                self.check_api_key_status()
            else:
                self.log_message("❌ API anahtarı ayarları iptal edildi.")
                
        except Exception as e:
            self.log_message(f"❌ API ayarları hatası: {e}")
    
    def check_api_key_status(self):
        """API anahtarı durumunu kontrol et"""
        if not API_MODULES_AVAILABLE:
            self.log_message("❌ API modülleri yüklenemedi!")
            return
        
        try:
            self.log_message("🔍 API anahtarı durumu kontrol ediliyor...")
            
            has_key = self.api_integration.api_manager.has_api_key()
            
            if has_key:
                api_key = self.api_integration.get_api_key_for_gemini()
                if api_key:
                    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
                    self.log_message(f"✅ API anahtarı mevcut: {masked_key}")
                    self.status_bar.showMessage("API anahtarı: Mevcut ✅")
                else:
                    self.log_message("❌ API anahtarı okunamadı!")
                    self.status_bar.showMessage("API anahtarı: Hata ❌")
            else:
                self.log_message("⚠️ API anahtarı bulunamadı!")
                self.status_bar.showMessage("API anahtarı: Yok ⚠️")
                
        except Exception as e:
            self.log_message(f"❌ API kontrol hatası: {e}")
    
    def test_gemini_ai(self):
        """Gemini AI'yi test et"""
        if not API_MODULES_AVAILABLE:
            QMessageBox.warning(self, "Hata", "API modülleri yüklenemedi!")
            return
        
        try:
            self.log_message("🧠 Gemini AI test ediliyor...")
            
            api_key = self.api_integration.get_api_key_for_gemini()
            
            if not api_key:
                self.log_message("❌ API anahtarı bulunamadı! Önce API anahtarını ayarlayın.")
                QMessageBox.warning(self, "API Anahtarı Gerekli", 
                                  "Gemini AI'yi test etmek için önce API anahtarını ayarlamanız gerekiyor.")
                return
            
            # Basit test
            import requests
            
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": "Merhaba! Bu bir test mesajıdır. Kısaca yanıtla."
                    }]
                }]
            }
            
            self.log_message("📡 Gemini API'ye bağlanılıyor...")
            
            response = requests.post(
                f"{url}?key={api_key}",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    self.log_message(f"✅ Gemini AI yanıtı: {ai_response}")
                    QMessageBox.information(self, "Test Başarılı", 
                                          f"Gemini AI çalışıyor!\n\nYanıt: {ai_response[:100]}...")
                else:
                    self.log_message("❌ Gemini AI'den geçersiz yanıt!")
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
                
                self.log_message(f"❌ Gemini AI hatası: {error_msg}")
                QMessageBox.warning(self, "Test Başarısız", f"Gemini AI hatası:\n{error_msg}")
                
        except requests.exceptions.Timeout:
            self.log_message("❌ Bağlantı zaman aşımı!")
            QMessageBox.warning(self, "Bağlantı Hatası", "İnternet bağlantınızı kontrol edin.")
        except Exception as e:
            self.log_message(f"❌ Test hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Test sırasında hata oluştu:\n{e}")
    
    def clear_status(self):
        """Durum alanını temizle"""
        self.status_text.clear()
        self.log_message("🧹 Durum alanı temizlendi.")
    
    def log_message(self, message):
        """Durum alanına mesaj ekle"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.End)
        self.status_text.setTextCursor(cursor)
    
    def show_about(self):
        """Hakkında dialog'u"""
        QMessageBox.about(self, "Hakkında", 
                         "🏭 TezgahTakip API Anahtarı Yönetimi Demo\n\n"
                         "Bu demo uygulama, TezgahTakip uygulamasına API anahtarı "
                         "yönetiminin nasıl entegre edileceğini gösterir.\n\n"
                         "Özellikler:\n"
                         "• Güvenli API anahtarı saklama\n"
                         "• Kullanıcı dostu arayüz\n"
                         "• Gemini AI entegrasyonu\n"
                         "• Otomatik doğrulama\n\n"
                         "© 2025 TezgahTakip")
    
    def closeEvent(self, event):
        """Uygulama kapatılırken"""
        reply = QMessageBox.question(self, "Çıkış", 
                                   "Uygulamadan çıkmak istediğinizden emin misiniz?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    
    # Uygulama bilgileri
    app.setApplicationName("TezgahTakip API Demo")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TezgahTakip")
    
    # Ana pencere
    window = DemoMainWindow()
    window.show()
    
    # Başlangıç mesajı
    window.log_message("🚀 Demo uygulama başlatıldı!")
    window.log_message("💡 API anahtarı ayarları için menüden 'Ayarlar > API Anahtarı' seçin.")
    
    if API_MODULES_AVAILABLE:
        window.log_message("✅ API modülleri başarıyla yüklendi.")
    else:
        window.log_message("❌ API modülleri yüklenemedi!")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()