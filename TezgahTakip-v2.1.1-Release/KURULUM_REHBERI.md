# 🔑 TezgahTakip - API Anahtarı Yönetimi Kurulum Rehberi

## 📋 Genel Bakış

Bu sistem, TezgahTakip uygulamasına güvenli API anahtarı yönetimi ekler. Kullanıcılar kendi Gemini API anahtarlarını güvenli şekilde girebilir ve yönetebilir.

## 🎯 Özellikler

- ✅ **Güvenli Saklama**: API anahtarları şifrelenerek saklanır
- ✅ **Kullanıcı Dostu**: Kolay API anahtarı giriş arayüzü
- ✅ **Otomatik Doğrulama**: API anahtarı geçerliliği test edilir
- ✅ **Ayarlar Entegrasyonu**: Mevcut ayarlar menüsüne entegre olur
- ✅ **Geriye Uyumluluk**: Mevcut kodla uyumlu çalışır

## 📦 Kurulum

### 1. Dosyaları Kopyalayın

Aşağıdaki dosyaları TezgahTakip.exe'nin bulunduğu klasöre kopyalayın:

```
📁 TezgahTakip Klasörü/
├── 📄 TezgahTakip.exe (mevcut)
├── 📄 settings.json (güncellenmiş)
├── 📄 api_key_manager.py (YENİ)
├── 📄 api_key_dialog.py (YENİ)
├── 📄 integration_helper.py (YENİ)
├── 📄 startup_integration.py (YENİ)
└── 📄 demo_app.py (TEST İÇİN)
```

### 2. Gerekli Paketleri Kontrol Edin

```bash
# Gerekli paketler (çoğu zaten yüklü olmalı)
pip install PyQt5 requests

# Opsiyonel (daha güvenli şifreleme için)
pip install cryptography
```

### 3. Demo Uygulamasını Test Edin

```bash
python demo_app.py
```

Bu demo ile API anahtarı sistemini test edebilirsiniz.

## 🔧 Ana Uygulamaya Entegrasyon

### Seçenek 1: Otomatik Entegrasyon (Kolay)

Ana uygulamanızın başlangıç koduna şunu ekleyin:

```python
# Ana uygulama dosyasının başına
try:
    from startup_integration import initialize_api_key_system, get_gemini_api_key
    
    # Ana pencere oluşturulduktan sonra
    api_integration = initialize_api_key_system(main_window)
    
    # Gemini AI için API anahtarı al
    api_key = get_gemini_api_key()
    if api_key:
        # Mevcut Gemini AI instance'ınızı güncelleyin
        if hasattr(self, 'gemini_ai'):
            self.gemini_ai.api_key = api_key
            print("✅ API anahtarı güncellendi")
    else:
        print("⚠️ API anahtarı bulunamadı")
        
except ImportError:
    print("⚠️ API anahtarı sistemi yüklenemedi")
```

### Seçenek 2: Manuel Entegrasyon (Gelişmiş)

```python
from integration_helper import TezgahTakipIntegration

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # API entegrasyonu
        self.api_integration = TezgahTakipIntegration()
        
        # UI kurulumu
        self.setup_ui()
        
        # API anahtarı kontrolü
        self.api_integration.check_api_key_on_startup(self)
        
        # Ayarlar menüsüne API anahtarı ekle
        self.add_api_key_to_settings_menu()
    
    def add_api_key_to_settings_menu(self):
        """Ayarlar menüsüne API anahtarı seçeneği ekle"""
        if hasattr(self, 'settings_menu'):
            api_action = self.api_integration.create_settings_menu_action(self)
            if api_action:
                self.settings_menu.addSeparator()
                self.settings_menu.addAction(api_action)
    
    def get_gemini_api_key(self):
        """Gemini AI için API anahtarını al"""
        return self.api_integration.get_api_key_for_gemini()
```

## 🎮 Kullanım

### Kullanıcı Deneyimi

1. **İlk Açılış**: Uygulama API anahtarı ister
2. **API Anahtarı Girişi**: Kullanıcı kendi anahtarını girer
3. **Doğrulama**: Sistem anahtarı test eder
4. **Kaydetme**: Anahtar güvenli şekilde saklanır
5. **Kullanım**: AI özellikleri çalışmaya başlar

### Ayarlar Menüsü

Kullanıcılar şu seçeneklere sahip olur:
- 🔑 **API Anahtarı**: Yeni anahtar gir/güncelle
- 🔍 **Doğrula**: Mevcut anahtarı test et
- 🗑️ **Temizle**: Anahtarı sil

## 🔒 Güvenlik

### Şifreleme Yöntemleri

1. **Birincil**: Fernet (cryptography paketi)
   - Endüstri standardı AES şifreleme
   - Makine kimliği ile anahtar türetme
   - PBKDF2 ile güvenli anahtar genişletme

2. **Yedek**: XOR Şifreleme
   - Cryptography paketi yoksa
   - Basit ama etkili koruma
   - Makine kimliği tabanlı

3. **Son Çare**: Base64 Encoding
   - Minimum koruma
   - Sadece görsel gizleme

### Veri Saklama

```json
{
    "ai": {
        "gemini_api_key": "şifrelenmiş_anahtar",
        "api_key_encrypted": true,
        "last_updated": "2025-12-20T19:30:00"
    }
}
```

## 🧪 Test Senaryoları

### 1. Yeni Kullanıcı
- Uygulama açılır
- API anahtarı istenir
- Kullanıcı anahtarını girer
- Doğrulama yapılır
- Anahtar kaydedilir

### 2. Mevcut Kullanıcı
- Uygulama açılır
- Kayıtlı anahtar bulunur
- AI özellikleri çalışır

### 3. Geçersiz Anahtar
- Eski/geçersiz anahtar tespit edilir
- Kullanıcıdan yeni anahtar istenir
- Güncelleme yapılır

### 4. İnternet Yok
- Doğrulama atlanır
- Kayıtlı anahtar kullanılır
- Uyarı gösterilir

## 🐛 Sorun Giderme

### API Anahtarı Çalışmıyor

**Belirtiler:**
- "API key expired" hatası
- AI özellikleri çalışmıyor

**Çözüm:**
1. Ayarlar > API Anahtarı'na git
2. Yeni API anahtarı gir
3. Doğrula butonuna tıkla
4. Kaydet

### Şifreleme Hatası

**Belirtiler:**
- API anahtarı kaydedilemiyor
- "Şifreleme hatası" mesajı

**Çözüm:**
1. `pip install cryptography` çalıştır
2. Uygulamayı yeniden başlat
3. Dosya izinlerini kontrol et

### Import Hatası

**Belirtiler:**
- "ModuleNotFoundError" hatası
- API sistemi yüklenmiyor

**Çözüm:**
1. Tüm dosyaların aynı klasörde olduğunu kontrol et
2. Python path'ini kontrol et
3. Gerekli paketleri yükle

## 📞 Destek

### Hızlı Yardım

```python
# API anahtarı durumunu kontrol et
from api_key_manager import APIKeyManager
manager = APIKeyManager()
print(f"API anahtarı var: {manager.has_api_key()}")

# API anahtarını test et
from api_key_dialog import show_api_key_dialog
show_api_key_dialog()

# Demo uygulamayı çalıştır
python demo_app.py
```

### Sık Sorulan Sorular

**S: API anahtarım güvenli mi?**
C: Evet, anahtarınız şifrelenerek saklanır ve sadece sizin makinenizde çalışır.

**S: API anahtarını nasıl alırım?**
C: https://makersuite.google.com/app/apikey adresinden ücretsiz alabilirsiniz.

**S: Eski API anahtarım çalışmıyor?**
C: Google'da API anahtarlarının süresi dolabilir. Yeni bir anahtar oluşturun.

**S: Birden fazla kullanıcı kullanabilir mi?**
C: Her kullanıcı kendi API anahtarını girmelidir. Sistem kullanıcı bazında çalışır.

## 🎉 Sonuç

Bu sistem ile:
- ✅ Kullanıcılar kendi API anahtarlarını yönetir
- ✅ Güvenlik endişeleri ortadan kalkar
- ✅ Kolay kurulum ve kullanım
- ✅ Mevcut uygulamayla uyumlu çalışır

**Kurulum tamamlandıktan sonra demo uygulamayı test etmeyi unutmayın!**

---
**© 2025 TezgahTakip - API Anahtarı Yönetim Sistemi**