#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Anahtarı Giriş Dialog'u
Kullanıcıdan Gemini API anahtarı almak için PyQt5 arayüzü
"""

import sys
import logging
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QFrame,
                            QCheckBox, QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
import requests
import json
from api_key_manager import APIKeyManager

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
    def warning(parent, title, message):
        """Uyarı dialog'u"""
        dialog = CustomMessageBox(parent, title, message, "warning")
        dialog.exec_()
    
    @staticmethod
    def critical(parent, title, message):
        """Hata dialog'u"""
        dialog = CustomMessageBox(parent, title, message, "error")
        dialog.exec_()

class APIKeyValidator(QThread):
    """API anahtarını arka planda doğrulayan thread - Thread safe"""
    
    validation_complete = pyqtSignal(bool, str)
    
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """API anahtarını Google Gemini API'ye test ederek doğrula"""
        try:
            # Rate limiting - çok fazla test isteği önlemek için
            import time
            time.sleep(2)  # 2 saniye bekle
            
            # Thread içinde yeni API manager oluştur (thread safety)
            from api_key_manager import APIKeyManager
            temp_manager = APIKeyManager()
            
            # Geçici olarak API anahtarını ayarla (sadece test için)
            is_valid, message = temp_manager.validate_api_key(self.api_key)
            if not is_valid:
                self.validation_complete.emit(False, message)
                return
            
            # Gemini API test endpoint'i
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TezgahTakip/2.0"
            }
            
            # Basit test verisi
            data = {
                "contents": [{
                    "parts": [{
                        "text": "Test"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 10,
                    "temperature": 0.1
                }
            }
            
            self.logger.info("Testing API key validation")
            
            # API çağrısı - daha uzun timeout
            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30  # Daha uzun timeout
            )
            
            if response.status_code == 200:
                self.validation_complete.emit(True, "API anahtarı geçerli ve çalışıyor!")
            elif response.status_code == 400:
                error_data = response.json()
                if "API_KEY_INVALID" in str(error_data):
                    self.validation_complete.emit(False, "API anahtarı geçersiz veya süresi dolmuş")
                else:
                    error_msg = error_data.get('error', {}).get('message', 'Bilinmeyen hata')
                    self.validation_complete.emit(False, f"API hatası: {error_msg}")
            elif response.status_code == 403:
                self.validation_complete.emit(False, "API anahtarı için yetki yok veya kota aşıldı")
            elif response.status_code == 429:
                self.validation_complete.emit(False, "Çok fazla istek gönderildi. 1-2 dakika bekleyip tekrar deneyin.\n\nGemini API'nin ücretsiz versiyonunda dakika başına istek limiti vardır.")
            else:
                self.validation_complete.emit(False, f"HTTP {response.status_code}: API bağlantı hatası")
                
        except requests.exceptions.Timeout:
            self.validation_complete.emit(False, "Bağlantı zaman aşımı - İnternet bağlantınızı kontrol edin")
        except requests.exceptions.ConnectionError:
            self.validation_complete.emit(False, "İnternet bağlantısı yok - Bağlantınızı kontrol edin")
        except Exception as e:
            self.logger.error(f"API validation error: {e}")
            self.validation_complete.emit(False, f"Doğrulama hatası: {str(e)}")

class APIKeyDialog(QDialog):
    """API Anahtarı giriş dialog'u"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_manager = APIKeyManager()
        self.validator_thread = None
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("🔑 Gemini API Anahtarı Ayarları")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # Stil
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit:focus {
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
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-size: 10px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        self.setup_ui()
        self.load_existing_key()
    
    def setup_ui(self):
        """Arayüzü oluştur"""
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("🔑 Google Gemini API Anahtarı")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Açıklama
        info_text = """
API anahtarınız güvenli şekilde şifrelenerek saklanacaktır.
Gemini AI özelliklerini kullanmak için geçerli bir API anahtarı gereklidir.
        """
        info_label = QLabel(info_text.strip())
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #cccccc; margin: 10px;")
        layout.addWidget(info_label)
        
        # API Anahtarı Grubu
        api_group = QGroupBox("API Anahtarı")
        api_layout = QVBoxLayout()
        
        # API anahtarı girişi
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("AIzaSy... (Gemini API anahtarınızı buraya girin)")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        api_layout.addWidget(self.api_key_input)
        
        # Göster/Gizle checkbox
        self.show_key_checkbox = QCheckBox("API anahtarını göster")
        self.show_key_checkbox.stateChanged.connect(self.toggle_key_visibility)
        api_layout.addWidget(self.show_key_checkbox)
        
        # Doğrulama butonu
        self.validate_button = QPushButton("🔍 API Anahtarını Doğrula")
        self.validate_button.clicked.connect(self.validate_api_key)
        self.validate_button.setEnabled(False)
        api_layout.addWidget(self.validate_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        api_layout.addWidget(self.progress_bar)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Durum mesajı
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setPlainText("API anahtarınızı girin ve doğrula butonuna tıklayın.")
        layout.addWidget(self.status_text)
        
        # Nasıl alınır bilgisi
        help_group = QGroupBox("📋 API Anahtarı Nasıl Alınır?")
        help_layout = QVBoxLayout()
        
        help_text = """🔗 Adım adım API anahtarı alma:

1. https://makersuite.google.com/app/apikey adresine gidin
2. Google hesabınızla giriş yapın  
3. "Create API Key" butonuna tıklayın
4. Oluşturulan anahtarı kopyalayın (AIzaSy... ile başlar)
5. Yukarıdaki alana yapıştırın ve "Doğrula" butonuna tıklayın

⚠️ Önemli: API anahtarı ücretsizdir ancak kullanım limiti vardır.
💡 İpucu: Anahtarınızı kimseyle paylaşmayın ve güvenli saklayın."""
        
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #cccccc; font-size: 10px; line-height: 1.4;")
        help_layout.addWidget(help_label)
        
        # Link butonu
        link_button = QPushButton("🌐 API Anahtarı Sayfasını Aç")
        link_button.clicked.connect(self.open_api_key_page)
        link_button.setStyleSheet("background-color: #2196F3;")
        help_layout.addWidget(link_button)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("🗑️ Temizle")
        self.clear_button.clicked.connect(self.clear_api_key)
        self.clear_button.setStyleSheet("background-color: #f44336;")
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("❌ İptal")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("background-color: #666666;")
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("💾 Kaydet")
        self.save_button.clicked.connect(self.save_api_key)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_existing_key(self):
        """Mevcut API anahtarını yükle ve durumunu kontrol et"""
        try:
            if self.api_manager.has_api_key():
                # Güvenlik için sadece ilk ve son 4 karakteri göster
                existing_key = self.api_manager.get_api_key()
                if len(existing_key) > 8:
                    masked_key = existing_key[:4] + "..." + existing_key[-4:]
                    
                    # API anahtarının çalışıp çalışmadığını kontrol et
                    from gemini_ai import GeminiAI
                    gemini = GeminiAI()
                    is_working, test_message = gemini.test_connection()
                    
                    if is_working:
                        self.api_key_input.setPlaceholderText(f"Mevcut: {masked_key} (Çalışıyor)")
                        self.status_text.setPlainText("✅ Kayıtlı API anahtarı bulundu ve çalışıyor. Yeni anahtar girmek için üzerine yazın.")
                        self.save_button.setText("💾 Güncelle")
                    else:
                        self.api_key_input.setPlaceholderText(f"Mevcut: {masked_key} (Geçersiz)")
                        self.status_text.setPlainText(f"❌ Kayıtlı API anahtarı geçersiz: {test_message}\n\nLütfen yeni bir API anahtarı girin.")
                        self.save_button.setText("💾 Güncelle")
                        
                        # Geçersiz anahtarı otomatik temizle seçeneği sun
                        if "geçersiz" in test_message.lower() or "süresi dolmuş" in test_message.lower():
                            self.status_text.append("\n💡 Geçersiz anahtarı otomatik olarak temizlemek için 'Temizle' butonunu kullanın.")
            else:
                self.status_text.setPlainText("🔑 API anahtarı bulunamadı. Lütfen yeni bir API anahtarı girin.")
        except Exception as e:
            self.logger.error(f"Mevcut anahtar yüklenirken hata: {e}")
            self.status_text.setPlainText("⚠️ API anahtarı durumu kontrol edilemedi. Yeni anahtar girmeyi deneyin.")
    
    def on_api_key_changed(self):
        """API anahtarı değiştiğinde çağrılır"""
        api_key = self.api_key_input.text().strip()
        
        # Buton durumlarını güncelle
        has_text = len(api_key) > 0
        self.validate_button.setEnabled(has_text)
        
        # Format kontrolü
        if has_text:
            is_valid, message = self.api_manager.validate_api_key(api_key)
            if is_valid:
                self.status_text.setPlainText(f"✅ {message}")
                self.save_button.setEnabled(True)
            else:
                self.status_text.setPlainText(f"❌ {message}")
                self.save_button.setEnabled(False)
        else:
            self.status_text.setPlainText("API anahtarınızı girin.")
            self.save_button.setEnabled(False)
    
    def toggle_key_visibility(self):
        """API anahtarı görünürlüğünü değiştir"""
        if self.show_key_checkbox.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
    
    def validate_api_key(self):
        """API anahtarını doğrula - Thread safe"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            CustomMessageBox.warning(self, "Uyarı", "Lütfen API anahtarını girin.")
            return
        
        # Format kontrolü
        is_valid, message = self.api_manager.validate_api_key(api_key)
        if not is_valid:
            CustomMessageBox.warning(self, "Format Hatası", message)
            return
        
        # Önceki thread'i temizle
        if self.validator_thread and self.validator_thread.isRunning():
            self.validator_thread.quit()
            self.validator_thread.wait()
        
        # Doğrulama başlat
        self.validate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Sonsuz progress
        self.status_text.setPlainText("🔍 API anahtarı doğrulanıyor... Lütfen bekleyin.")
        
        # Validator thread başlat
        self.validator_thread = APIKeyValidator(api_key)
        self.validator_thread.validation_complete.connect(self.on_validation_complete)
        self.validator_thread.finished.connect(self.on_validation_finished)
        self.validator_thread.start()
        
        self.logger.info("API key validation started")
    
    def on_validation_finished(self):
        """Thread tamamlandığında cleanup"""
        try:
            if self.validator_thread:
                self.validator_thread.deleteLater()
                self.validator_thread = None
        except Exception as e:
            self.logger.error(f"Validation cleanup error: {e}")
    
    def closeEvent(self, event):
        """Dialog kapatılırken thread'i temizle"""
        try:
            if self.validator_thread and self.validator_thread.isRunning():
                self.validator_thread.quit()
                self.validator_thread.wait(3000)  # 3 saniye bekle
                if self.validator_thread.isRunning():
                    self.validator_thread.terminate()
            event.accept()
        except Exception as e:
            self.logger.error(f"Dialog close error: {e}")
            event.accept()
    
    def on_validation_complete(self, is_valid, message):
        """Doğrulama tamamlandığında çağrılır"""
        self.progress_bar.setVisible(False)
        self.validate_button.setEnabled(True)
        
        if is_valid:
            self.status_text.setPlainText(f"✅ {message}")
            self.save_button.setEnabled(True)
            CustomMessageBox.information(self, "Başarılı", "API anahtarı geçerli! Artık kaydedebilirsiniz.")
        else:
            self.status_text.setPlainText(f"❌ {message}")
            self.save_button.setEnabled(False)
            CustomMessageBox.warning(self, "Doğrulama Hatası", message)
    
    def save_api_key(self):
        """API anahtarını kaydet"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            CustomMessageBox.warning(self, "Uyarı", "Lütfen API anahtarını girin.")
            return
        
        # Kaydet
        success = self.api_manager.set_api_key(api_key)
        
        if success:
            CustomMessageBox.information(self, "Başarılı", 
                                  "API anahtarı güvenli şekilde kaydedildi!\n\n"
                                  "Artık Gemini AI özelliklerini kullanabilirsiniz.")
            self.accept()
        else:
            CustomMessageBox.critical(self, "Hata", "API anahtarı kaydedilemedi. Lütfen tekrar deneyin.")
    
    def clear_api_key(self):
        """API anahtarını temizle"""
        if CustomMessageBox.question(self, "Onay", 
                                   "Kayıtlı API anahtarını silmek istediğinizden emin misiniz?\n\n"
                                   "Bu işlem geri alınamaz ve AI özellikleri çalışmayacaktır."):
            success = self.api_manager.clear_api_key()
            if success:
                self.api_key_input.clear()
                self.api_key_input.setPlaceholderText("AIzaSy... (Gemini API anahtarınızı buraya girin)")
                self.status_text.setPlainText("🗑️ API anahtarı temizlendi.")
                CustomMessageBox.information(self, "Başarılı", "API anahtarı temizlendi.")
            else:
                CustomMessageBox.critical(self, "Hata", "API anahtarı temizlenemedi.")
    
    def open_api_key_page(self):
        """API anahtarı sayfasını aç"""
        import webbrowser
        try:
            webbrowser.open("https://makersuite.google.com/app/apikey")
        except Exception as e:
            CustomMessageBox.warning(self, "Hata", f"Web sayfası açılamadı: {e}")

def show_api_key_dialog(parent=None):
    """API anahtarı dialog'unu göster"""
    dialog = APIKeyDialog(parent)
    return dialog.exec_() == QDialog.Accepted

# Test için
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test dialog'u
    dialog = APIKeyDialog()
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        print("API anahtarı kaydedildi!")
    else:
        print("İptal edildi.")
    
    sys.exit()