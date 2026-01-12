#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Anahtarı Yönetim Modülü
Güvenli API anahtarı saklama ve yönetimi için
"""

import json
import os
import base64
import secrets
from datetime import datetime
import hashlib
import logging

# Cryptography import'u - opsiyonel
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("⚠️ Cryptography paketi bulunamadı. Basit şifreleme kullanılacak.")

class APIKeyManager:
    """API anahtarlarını güvenli şekilde yöneten sınıf"""
    
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.encryption_key_file = ".api_encryption_key"
        self._encryption_key = None
        self.logger = logging.getLogger(__name__)
        
        # Salt dosyası - her kurulumda farklı
        self.salt_file = ".api_salt"
        self._salt = None
        
    def _get_or_create_salt(self):
        """Salt'ı al veya oluştur - her kurulumda farklı"""
        if self._salt:
            return self._salt
            
        try:
            # Mevcut salt'ı oku
            if os.path.exists(self.salt_file):
                with open(self.salt_file, 'rb') as f:
                    self._salt = f.read()
                    if len(self._salt) == 32:  # Geçerli salt
                        return self._salt
            
            # Yeni salt oluştur
            self._salt = secrets.token_bytes(32)
            
            # Salt'ı kaydet
            with open(self.salt_file, 'wb') as f:
                f.write(self._salt)
            
            # Dosyayı gizle (Windows)
            try:
                import stat
                os.chmod(self.salt_file, stat.S_IREAD | stat.S_IWRITE)
            except:
                pass
                
            self.logger.info("New salt generated and saved")
            return self._salt
            
        except Exception as e:
            self.logger.error(f"Salt generation error: {e}")
            # Fallback: Deterministik salt (güvenlik riski ama çalışır)
            machine_id = self._get_machine_id()
            return hashlib.sha256(f"TezgahTakip2025{machine_id}".encode()).digest()[:32]
        
    def _get_machine_id(self):
        """Makine kimliğini al (şifreleme için)"""
        try:
            import platform
            import uuid
            
            # Makine bilgilerini topla
            machine_info = f"{platform.node()}-{platform.system()}-{uuid.getnode()}"
            
            # Hash'le
            return hashlib.sha256(machine_info.encode()).hexdigest()[:32]
        except Exception as e:
            self.logger.warning(f"Machine ID generation error: {e}")
            # Fallback: Sabit bir değer (güvenlik riski ama çalışır)
            return "TezgahTakip2025DefaultKey123456"
    
    def _get_encryption_key(self):
        """Şifreleme anahtarını al veya oluştur"""
        if self._encryption_key:
            return self._encryption_key
            
        # Makine kimliğini kullanarak anahtar türet
        machine_id = self._get_machine_id()
        
        if CRYPTOGRAPHY_AVAILABLE:
            # PBKDF2 ile güvenli anahtar türet
            salt = self._get_or_create_salt()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self._encryption_key = key
            return key
        else:
            # Fallback: Basit anahtar türetme
            salt = self._get_or_create_salt()
            key_material = machine_id.encode() + salt
            key = hashlib.sha256(key_material).hexdigest()[:32]
            self._encryption_key = key.encode()
            return self._encryption_key
    
    def _encrypt_api_key(self, api_key):
        """API anahtarını şifrele"""
        try:
            if CRYPTOGRAPHY_AVAILABLE:
                key = self._get_encryption_key()
                fernet = Fernet(key)
                encrypted = fernet.encrypt(api_key.encode())
                return base64.urlsafe_b64encode(encrypted).decode()
            else:
                # Fallback: XOR şifreleme (basit ama çalışır)
                key = self._get_encryption_key()
                encrypted = bytearray()
                for i, char in enumerate(api_key.encode()):
                    encrypted.append(char ^ key[i % len(key)])
                return base64.b64encode(bytes(encrypted)).decode()
        except Exception as e:
            self.logger.error(f"Şifreleme hatası: {e}")
            # Son fallback: Base64 encoding
            return base64.b64encode(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_api_key):
        """Şifrelenmiş API anahtarını çöz"""
        try:
            if CRYPTOGRAPHY_AVAILABLE:
                key = self._get_encryption_key()
                fernet = Fernet(key)
                
                # Base64 decode
                encrypted_data = base64.urlsafe_b64decode(encrypted_api_key.encode())
                
                # Decrypt
                decrypted = fernet.decrypt(encrypted_data)
                return decrypted.decode()
            else:
                # Fallback: XOR çözme
                key = self._get_encryption_key()
                encrypted_data = base64.b64decode(encrypted_api_key.encode())
                decrypted = bytearray()
                for i, byte in enumerate(encrypted_data):
                    decrypted.append(byte ^ key[i % len(key)])
                return bytes(decrypted).decode()
        except Exception as e:
            self.logger.error(f"Şifre çözme hatası: {e}")
            try:
                # Fallback: Base64 decoding
                return base64.b64decode(encrypted_api_key.encode()).decode()
            except Exception as e2:
                self.logger.error(f"Base64 decode hatası: {e2}")
                return ""
    
    def load_settings(self):
        """Ayarları yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_settings()
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Ayarlar yüklenirken hata: {e}")
            return self._get_default_settings()
        except Exception as e:
            self.logger.error(f"Beklenmeyen ayar yükleme hatası: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self):
        """Varsayılan ayarları döndür"""
        return {
            "general": {
                "start_tab": "dashboard",
                "auto_save": True,
                "theme": "dark"
            },
            "database": {
                "path": "tezgah_takip.db"
            },
            "appearance": {
                "font_family": "Segoe UI",
                "font_size": 9
            },
            "backup": {
                "auto_backup_enabled": True,
                "backup_interval_days": 7
            },
            "update": {
                "check_on_startup": False,
                "auto_download": False
            },
            "ai": {
                "gemini_api_key": "",
                "api_key_encrypted": False,
                "last_updated": ""
            }
        }
    
    def save_settings(self, settings):
        """Ayarları kaydet"""
        try:
            # Backup oluştur
            if os.path.exists(self.settings_file):
                backup_file = f"{self.settings_file}.backup"
                import shutil
                shutil.copy2(self.settings_file, backup_file)
            
            # Yeni ayarları kaydet
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.logger.info("Settings saved successfully")
            return True
        except (IOError, OSError) as e:
            self.logger.error(f"Ayarlar kaydedilirken IO hatası: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ayarlar kaydedilirken hata: {e}")
            return False
    
    def set_api_key(self, api_key):
        """API anahtarını güvenli şekilde kaydet"""
        try:
            # Input sanitization
            if not isinstance(api_key, str):
                raise ValueError("API anahtarı string olmalı")
            
            api_key = api_key.strip()
            
            # Validasyon
            is_valid, message = self.validate_api_key(api_key)
            if not is_valid:
                self.logger.warning(f"Invalid API key format: {message}")
                return False
            
            settings = self.load_settings()
            
            if not settings.get("ai"):
                settings["ai"] = {}
            
            # API anahtarını şifrele
            encrypted_key = self._encrypt_api_key(api_key)
            
            # Ayarlara kaydet
            settings["ai"]["gemini_api_key"] = encrypted_key
            settings["ai"]["api_key_encrypted"] = True
            settings["ai"]["last_updated"] = datetime.now().isoformat()
            
            # Kaydet
            success = self.save_settings(settings)
            
            if success:
                self.logger.info("✅ API anahtarı güvenli şekilde kaydedildi")
                return True
            else:
                self.logger.error("❌ API anahtarı kaydedilemedi")
                return False
                
        except Exception as e:
            self.logger.error(f"API anahtarı kaydedilirken hata: {e}")
            return False
    
    def get_api_key(self):
        """Kaydedilmiş API anahtarını al"""
        try:
            settings = self.load_settings()
            
            ai_settings = settings.get("ai", {})
            encrypted_key = ai_settings.get("gemini_api_key", "")
            is_encrypted = ai_settings.get("api_key_encrypted", False)
            
            if not encrypted_key:
                return ""
            
            if is_encrypted:
                # Şifrelenmiş anahtarı çöz
                decrypted_key = self._decrypt_api_key(encrypted_key)
                
                # Çözülen anahtarı validate et
                if decrypted_key:
                    is_valid, _ = self.validate_api_key(decrypted_key)
                    if is_valid:
                        return decrypted_key
                    else:
                        self.logger.warning("Decrypted API key is invalid")
                        return ""
                return ""
            else:
                # Şifrelenmemiş (eski format)
                return encrypted_key
                
        except Exception as e:
            self.logger.error(f"API anahtarı alınırken hata: {e}")
            return ""
    
    def has_api_key(self):
        """API anahtarının kaydedilip kaydedilmediğini kontrol et"""
        api_key = self.get_api_key()
        return bool(api_key and len(api_key.strip()) > 10)
    
    def validate_api_key(self, api_key):
        """API anahtarının formatını doğrula - Gelişmiş validasyon"""
        if not api_key:
            return False, "API anahtarı boş olamaz"
        
        if not isinstance(api_key, str):
            return False, "API anahtarı string olmalı"
        
        api_key = api_key.strip()
        
        # Uzunluk kontrolü
        if len(api_key) < 35:
            return False, "API anahtarı çok kısa (en az 35 karakter olmalı)"
        
        if len(api_key) > 50:
            return False, "API anahtarı çok uzun (en fazla 50 karakter olmalı)"
        
        # Gemini API anahtarı formatı kontrolü
        if not api_key.startswith("AIza"):
            return False, "Geçersiz Gemini API anahtarı formatı (AIza ile başlamalı)"
        
        # Karakter kontrolü - sadece alfanumerik ve bazı özel karakterler
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
            return False, "API anahtarı geçersiz karakter içeriyor"
        
        # Güvenlik kontrolü - yaygın test anahtarları
        test_keys = [
            "AIzaSyDummy",
            "AIzaSyTest",
            "AIzaSyExample",
            "AIzaSy1234567890"
        ]
        
        for test_key in test_keys:
            if api_key.startswith(test_key):
                return False, "Test API anahtarı kullanılamaz"
        
        return True, "API anahtarı formatı geçerli"
    
    def clear_api_key(self):
        """API anahtarını temizle"""
        try:
            settings = self.load_settings()
            
            if "ai" in settings:
                settings["ai"]["gemini_api_key"] = ""
                settings["ai"]["api_key_encrypted"] = False
                settings["ai"]["last_updated"] = ""
            
            success = self.save_settings(settings)
            
            if success:
                self.logger.info("✅ API anahtarı temizlendi")
                return True
            else:
                self.logger.error("❌ API anahtarı temizlenemedi")
                return False
                
        except Exception as e:
            self.logger.error(f"API anahtarı temizlenirken hata: {e}")
            return False

# Test fonksiyonu
def test_api_key_manager():
    """API Key Manager'ı test et"""
    print("🧪 API Key Manager Test Başlıyor...")
    
    manager = APIKeyManager()
    
    # Test API anahtarı
    test_key = "AIzaSyCjECBwJ3BmCwMYQdxiE7rXSYOqLa7Pj8A"
    
    # Doğrulama testi
    is_valid, message = manager.validate_api_key(test_key)
    print(f"Doğrulama: {is_valid} - {message}")
    
    # Kaydetme testi
    success = manager.set_api_key(test_key)
    print(f"Kaydetme: {success}")
    
    # Okuma testi
    retrieved_key = manager.get_api_key()
    print(f"Okuma: {retrieved_key == test_key}")
    
    # Varlık kontrolü
    has_key = manager.has_api_key()
    print(f"Varlık kontrolü: {has_key}")
    
    # Temizleme testi
    clear_success = manager.clear_api_key()
    print(f"Temizleme: {clear_success}")
    
    print("✅ Test tamamlandı!")

if __name__ == "__main__":
    test_api_key_manager()