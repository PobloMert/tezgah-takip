#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entegrasyon Yardımcı Modülü
Mevcut TezgahTakip uygulamasına API anahtarı yönetimini entegre etmek için
"""

import os
import sys
import json
from PyQt5.QtWidgets import QApplication
from api_key_manager import APIKeyManager
from api_key_dialog import show_api_key_dialog, CustomMessageBox

class TezgahTakipIntegration:
    """TezgahTakip uygulaması için entegrasyon sınıfı"""
    
    def __init__(self):
        self.api_manager = APIKeyManager()
    
    def check_api_key_on_startup(self, parent_widget=None):
        """Uygulama başlangıcında API anahtarını kontrol et"""
        try:
            if not self.api_manager.has_api_key():
                # API anahtarı yok, kullanıcıya sor
                if CustomMessageBox.question(
                    parent_widget,
                    "API Anahtarı Gerekli",
                    "Gemini AI özelliklerini kullanmak için API anahtarı gereklidir.\n\n"
                    "Şimdi API anahtarınızı girmek ister misiniz?\n\n"
                    "Not: API anahtarı olmadan AI özellikleri çalışmayacaktır."
                ):
                    return self.show_api_key_settings(parent_widget)
                else:
                    CustomMessageBox.information(
                        parent_widget,
                        "Bilgi",
                        "API anahtarını daha sonra Ayarlar > API Anahtarı menüsünden girebilirsiniz."
                    )
                    return False
            else:
                # API anahtarı var, geçerliliğini kontrol et
                api_key = self.api_manager.get_api_key()
                if len(api_key.strip()) < 10:
                    # Geçersiz anahtar
                    CustomMessageBox.warning(
                        parent_widget,
                        "Geçersiz API Anahtarı",
                        "Kayıtlı API anahtarı geçersiz görünüyor.\n\n"
                        "Lütfen yeni bir API anahtarı girin."
                    )
                    return self.show_api_key_settings(parent_widget)
                
                return True
                
        except Exception as e:
            print(f"API anahtarı kontrolü sırasında hata: {e}")
            return False
    
    def show_api_key_settings(self, parent_widget=None):
        """API anahtarı ayarları dialog'unu göster"""
        try:
            return show_api_key_dialog(parent_widget)
        except Exception as e:
            CustomMessageBox.critical(
                parent_widget,
                "Hata",
                f"API anahtarı ayarları açılırken hata oluştu:\n{e}"
            )
            return False
    
    def get_api_key_for_gemini(self):
        """Gemini AI için API anahtarını al"""
        try:
            api_key = self.api_manager.get_api_key()
            if api_key and len(api_key.strip()) > 10:
                return api_key.strip()
            else:
                return None
        except Exception as e:
            print(f"API anahtarı alınırken hata: {e}")
            return None
    
    def update_gemini_ai_config(self, gemini_ai_instance):
        """Mevcut GeminiAI instance'ını güncelle"""
        try:
            api_key = self.get_api_key_for_gemini()
            if api_key and hasattr(gemini_ai_instance, 'api_key'):
                gemini_ai_instance.api_key = api_key
                print("✅ Gemini AI API anahtarı güncellendi")
                return True
            else:
                print("❌ API anahtarı bulunamadı veya GeminiAI instance geçersiz")
                return False
        except Exception as e:
            print(f"Gemini AI güncellenirken hata: {e}")
            return False
    
    def create_settings_menu_action(self, parent_widget, menu_bar=None):
        """Ayarlar menüsüne API anahtarı seçeneği ekle"""
        try:
            from PyQt5.QtWidgets import QAction
            from PyQt5.QtGui import QIcon
            
            # API anahtarı action'ı oluştur
            api_key_action = QAction("🔑 API Anahtarı", parent_widget)
            api_key_action.setStatusTip("Gemini API anahtarını ayarla")
            api_key_action.triggered.connect(lambda: self.show_api_key_settings(parent_widget))
            
            return api_key_action
            
        except Exception as e:
            print(f"Menu action oluşturulurken hata: {e}")
            return None
    
    def patch_main_application(self, main_window):
        """Ana uygulamayı patch'le (mevcut koda müdahale etmeden)"""
        try:
            # Ana pencereye integration referansı ekle
            main_window.api_integration = self
            
            # Startup kontrolü
            self.check_api_key_on_startup(main_window)
            
            # Eğer ayarlar menüsü varsa API anahtarı seçeneği ekle
            if hasattr(main_window, 'menuBar'):
                menu_bar = main_window.menuBar()
                
                # Ayarlar menüsünü bul veya oluştur
                settings_menu = None
                for action in menu_bar.actions():
                    if action.menu() and ('ayar' in action.text().lower() or 'setting' in action.text().lower()):
                        settings_menu = action.menu()
                        break
                
                if settings_menu:
                    # Separator ekle
                    settings_menu.addSeparator()
                    
                    # API anahtarı action'ı ekle
                    api_action = self.create_settings_menu_action(main_window)
                    if api_action:
                        settings_menu.addAction(api_action)
                        print("✅ API anahtarı menü seçeneği eklendi")
            
            return True
            
        except Exception as e:
            print(f"Ana uygulama patch'lenirken hata: {e}")
            return False

def create_startup_script():
    """Uygulama başlangıcı için script oluştur"""
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip API Anahtarı Başlangıç Script'i
Bu script'i ana uygulamanın başlangıcında çağırın
"""

import sys
import os

# Mevcut dizini Python path'ine ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from integration_helper import TezgahTakipIntegration
    
    def initialize_api_key_system(main_window=None):
        """API anahtarı sistemini başlat"""
        try:
            integration = TezgahTakipIntegration()
            
            if main_window:
                # Ana pencere ile entegrasyon
                integration.patch_main_application(main_window)
            else:
                # Sadece kontrol
                integration.check_api_key_on_startup()
            
            return integration
            
        except Exception as e:
            print(f"API anahtarı sistemi başlatılırken hata: {e}")
            return None
    
    def get_gemini_api_key():
        """Gemini API anahtarını al (mevcut kodda kullanmak için)"""
        try:
            integration = TezgahTakipIntegration()
            return integration.get_api_key_for_gemini()
        except Exception as e:
            print(f"API anahtarı alınırken hata: {e}")
            return None

except ImportError as e:
    print(f"API anahtarı modülleri yüklenemedi: {e}")
    
    def initialize_api_key_system(main_window=None):
        return None
    
    def get_gemini_api_key():
        return None
'''
    
    with open("startup_integration.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ Başlangıç script'i oluşturuldu: startup_integration.py")

def create_requirements_file():
    """Gerekli paketler için requirements.txt oluştur"""
    requirements = """# API Anahtarı Yönetimi için gerekli paketler
cryptography>=41.0.0
PyQt5>=5.15.0
requests>=2.25.0
"""
    
    with open("api_requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    
    print("✅ Gereksinimler dosyası oluşturuldu: api_requirements.txt")

def create_installation_guide():
    """Kurulum rehberi oluştur"""
    guide = """# 🔑 API Anahtarı Yönetimi - Kurulum Rehberi

## 📦 Kurulum

### 1. Gerekli Paketleri Yükleyin
```bash
pip install -r api_requirements.txt
```

### 2. Dosyaları Kopyalayın
Aşağıdaki dosyaları ana uygulamanızın bulunduğu klasöre kopyalayın:
- `api_key_manager.py`
- `api_key_dialog.py`
- `integration_helper.py`
- `startup_integration.py`

### 3. Ana Uygulamaya Entegrasyon

#### Yöntem 1: Otomatik Entegrasyon (Önerilen)
Ana uygulamanızın başlangıcında şu kodu ekleyin:

```python
# Ana uygulama dosyasının başına ekleyin
try:
    from startup_integration import initialize_api_key_system, get_gemini_api_key
    
    # Ana pencere oluşturulduktan sonra
    api_integration = initialize_api_key_system(main_window)
    
    # Gemini AI için API anahtarı
    api_key = get_gemini_api_key()
    if api_key:
        # Mevcut Gemini AI instance'ınızı güncelleyin
        gemini_ai.api_key = api_key
    
except ImportError:
    print("API anahtarı sistemi yüklenemedi")
```

#### Yöntem 2: Manuel Entegrasyon
```python
from integration_helper import TezgahTakipIntegration

# Ana uygulamada
integration = TezgahTakipIntegration()

# Başlangıçta kontrol
integration.check_api_key_on_startup(main_window)

# API anahtarını al
api_key = integration.get_api_key_for_gemini()
```

## 🎯 Kullanım

### Kullanıcı Deneyimi
1. Uygulama ilk açıldığında API anahtarı kontrolü yapılır
2. API anahtarı yoksa kullanıcıya sorulur
3. Ayarlar menüsünden API anahtarı değiştirilebilir
4. API anahtarı güvenli şekilde şifrelenerek saklanır

### Geliştirici API'si
```python
# API anahtarı var mı kontrol et
has_key = integration.api_manager.has_api_key()

# API anahtarını al
api_key = integration.get_api_key_for_gemini()

# API anahtarı ayarları göster
integration.show_api_key_settings(parent_widget)
```

## 🔒 Güvenlik

- API anahtarları Fernet (symmetric encryption) ile şifrelenir
- Makine kimliği kullanılarak anahtar türetilir
- Şifrelenmiş veriler settings.json'da saklanır
- Eski format (şifrelenmemiş) otomatik olarak desteklenir

## 🐛 Sorun Giderme

### API Anahtarı Doğrulama Hatası
- İnternet bağlantınızı kontrol edin
- API anahtarının doğru olduğundan emin olun
- Google Cloud Console'da API'nin aktif olduğunu kontrol edin

### Şifreleme Hatası
- `cryptography` paketinin yüklü olduğundan emin olun
- Dosya izinlerini kontrol edin

### Import Hatası
- Tüm dosyaların aynı klasörde olduğundan emin olun
- Python path'ini kontrol edin

## 📞 Destek

Sorunlarınız için GitHub Issues bölümünü kullanın.
"""
    
    with open("API_INTEGRATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ Kurulum rehberi oluşturuldu: API_INTEGRATION_GUIDE.md")

# Test fonksiyonu
def test_integration():
    """Entegrasyon sistemini test et"""
    print("🧪 Entegrasyon Testi Başlıyor...")
    
    try:
        # Integration oluştur
        integration = TezgahTakipIntegration()
        
        # API anahtarı kontrolü
        has_key = integration.api_manager.has_api_key()
        print(f"API anahtarı var: {has_key}")
        
        # API anahtarı al
        api_key = integration.get_api_key_for_gemini()
        print(f"API anahtarı alındı: {bool(api_key)}")
        
        print("✅ Entegrasyon testi başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Entegrasyon testi başarısız: {e}")
        return False

if __name__ == "__main__":
    # Yardımcı dosyaları oluştur
    create_startup_script()
    create_requirements_file()
    create_installation_guide()
    
    # Test
    test_integration()
    
    print("\n🎉 API Anahtarı Yönetim Sistemi hazır!")
    print("📖 Kurulum için API_INTEGRATION_GUIDE.md dosyasını okuyun.")