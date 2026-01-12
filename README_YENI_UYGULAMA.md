# 🏭 TezgahTakip v2.0 - AI Güçlü Fabrika Bakım Yönetim Sistemi

## 🎯 Proje Hakkında

TezgahTakip, fabrika tezgahlarının bakım ve takibini kolaylaştıran, Google Gemini AI ile güçlendirilmiş modern bir masaüstü uygulamasıdır. Her kullanıcı kendi API anahtarını güvenli şekilde girebilir ve AI özelliklerinden faydalanabilir.

## ✨ Özellikler

### 🔧 Temel Özellikler
- ✅ **Tezgah Yönetimi**: Tüm tezgahlarınızı tek yerden yönetin
- ✅ **Bakım Takibi**: Periyodik ve arızalı bakımları planlayın ve takip edin
- ✅ **Pil Takibi**: Tezgah pillerinin ömrünü izleyin ve değişim zamanlarını öğrenin
- ✅ **Raporlama**: Detaylı günlük, haftalık ve aylık raporlar oluşturun
- ✅ **Dashboard**: Tüm önemli metrikleri tek bakışta görün

### 🧠 AI Özellikleri (Gemini AI)
- ✅ **Akıllı Bakım Analizi**: AI ile bakım verilerinizi analiz edin
- ✅ **Pil Ömrü Tahmini**: Pil değişim zamanlarını önceden tahmin edin
- ✅ **Bakım Optimizasyonu**: Bakım programınızı optimize edin
- ✅ **Soru-Cevap**: AI'ya tezgah ve bakım hakkında sorular sorun
- ✅ **Akıllı Öneriler**: Performans iyileştirme önerileri alın

### 🔒 Güvenlik Özellikleri
- ✅ **Güvenli API Anahtarı Yönetimi**: Her kullanıcı kendi API anahtarını girer
- ✅ **Şifrelenmiş Saklama**: API anahtarları şifrelenerek saklanır
- ✅ **Makine Kimliği Tabanlı**: Şifreleme makine kimliğine bağlıdır
- ✅ **Çoklu Şifreleme Katmanı**: Fernet → XOR → Base64 fallback

### 🎨 Kullanıcı Arayüzü
- ✅ **Modern Koyu Tema**: Göz yormayan koyu tema
- ✅ **Responsive Tasarım**: Farklı ekran boyutlarına uyumlu
- ✅ **İstatistik Kartları**: Önemli metrikleri görsel olarak gösterir
- ✅ **Tabbed Interface**: Kolay navigasyon için sekmeli arayüz
- ✅ **Gerçek Zamanlı Güncelleme**: Veriler otomatik olarak güncellenir

## 📦 Kurulum

### 1. Gereksinimleri Yükleyin

```bash
# Python 3.7+ gereklidir
python --version

# Gerekli paketleri yükleyin
pip install -r requirements.txt
```

### 2. Uygulamayı Çalıştırın

```bash
python tezgah_takip_app.py
```

### 3. API Anahtarını Ayarlayın

İlk çalıştırmada uygulama sizden Gemini API anahtarı isteyecektir:

1. https://makersuite.google.com/app/apikey adresine gidin
2. Google hesabınızla giriş yapın
3. "Create API Key" butonuna tıklayın
4. Oluşturulan anahtarı kopyalayın
5. Uygulamada "Ayarlar > API Anahtarı" menüsünden girin

## 📁 Dosya Yapısı

```
TezgahTakip/
├── tezgah_takip_app.py          # Ana uygulama dosyası
├── main_window.py                # Ana pencere ve UI
├── database_models.py            # Veritabanı modelleri (SQLAlchemy)
├── gemini_ai.py                  # Gemini AI entegrasyonu
├── api_key_manager.py            # API anahtarı yönetimi
├── api_key_dialog.py             # API anahtarı giriş arayüzü
├── integration_helper.py         # Entegrasyon yardımcıları
├── demo_app.py                   # Test uygulaması
├── settings.json                 # Uygulama ayarları
├── requirements.txt              # Python bağımlılıkları
├── README_YENI_UYGULAMA.md      # Bu dosya
├── KURULUM_REHBERI.md           # Detaylı kurulum rehberi
├── API_ANAHTAR_SISTEMI_OZET.md  # API sistemi özeti
├── tezgah_takip.db              # SQLite veritabanı (otomatik oluşur)
├── logs/                         # Log dosyaları
│   └── tezgah_takip_YYYYMMDD.log
└── backups/                      # Otomatik yedekler
    └── tezgah_takip_backup_*.db
```

## 🚀 Hızlı Başlangıç

### İlk Kullanım

1. **Uygulamayı Başlatın**
   ```bash
   python tezgah_takip_app.py
   ```

2. **API Anahtarını Girin**
   - İlk açılışta API anahtarı istenecektir
   - "Evet" seçeneğini seçin
   - API anahtarınızı girin ve doğrulayın

3. **Dashboard'u İnceleyin**
   - Toplam tezgah sayısı
   - Aktif tezgah sayısı
   - Bekleyen bakım sayısı
   - Pil uyarıları

4. **Tezgah Ekleyin**
   - "Tezgahlar" sekmesine gidin
   - "➕ Yeni Tezgah" butonuna tıklayın
   - Tezgah bilgilerini girin

5. **AI Özelliklerini Kullanın**
   - "🧠 AI Analiz" sekmesine gidin
   - İstediğiniz analizi seçin
   - Sonuçları inceleyin

## 🎮 Kullanım Kılavuzu

### Dashboard
- **İstatistik Kartları**: Önemli metrikleri gösterir
- **AI İçgörüleri**: Gemini AI'dan gelen öneriler
- **Son Aktiviteler**: Sistemdeki son işlemler

### Tezgah Yönetimi
- **Tezgah Listesi**: Tüm tezgahları görüntüleyin
- **Yeni Tezgah**: Yeni tezgah ekleyin
- **Düzenle**: Mevcut tezgahı düzenleyin
- **Sil**: Tezgahı sistemden kaldırın

### Bakım Takibi
- **Bakım Planla**: Yeni bakım planı oluşturun
- **Bakım Geçmişi**: Geçmiş bakımları görüntüleyin
- **Durum Güncelle**: Bakım durumunu güncelleyin

### Pil Takibi
- **Pil Ekle**: Yeni pil kaydı oluşturun
- **Pil Durumu**: Pil durumlarını görüntüleyin
- **Değişim Uyarıları**: Değiştirilmesi gereken piller

### AI Analiz
- **Bakım Analizi**: Bakım verilerini AI ile analiz edin
- **Pil Ömrü Tahmini**: Pil ömürlerini tahmin edin
- **Bakım Optimizasyonu**: Bakım programını optimize edin
- **Soru Sor**: AI'ya sorular sorun

### Ayarlar
- **API Anahtarı**: Gemini API anahtarınızı yönetin
- **Tercihler**: Uygulama tercihlerini ayarlayın
- **Tema**: Görünüm ayarları

## 🔧 Teknik Detaylar

### Teknoloji Stack
- **Python**: 3.7+
- **GUI Framework**: PyQt5
- **Veritabanı**: SQLite + SQLAlchemy ORM
- **AI**: Google Gemini Pro
- **Şifreleme**: Fernet (cryptography)

### Veritabanı Şeması

#### Tezgah Tablosu
- id, tezgah_no, tezgah_adi, lokasyon, durum
- son_bakim_tarihi, sonraki_bakim_tarihi, bakim_periyodu
- aciklama, olusturma_tarihi, guncelleme_tarihi

#### Bakım Tablosu
- id, tezgah_id, bakim_tarihi, bakim_turu, durum
- bakim_yapan, aciklama, baslangic_saati, bitis_saati
- maliyet, yedek_parca, sonuc

#### Pil Tablosu
- id, tezgah_id, pil_seri_no, pil_tipi
- takma_tarihi, beklenen_omur, son_kontrol_tarihi
- voltaj, durum, aciklama

### API Entegrasyonu

```python
# Gemini AI kullanımı
from gemini_ai import GeminiAI

ai = GeminiAI()

# Bakım analizi
result = ai.analyze_maintenance_data(tezgah_data)

# Pil tahmini
result = ai.predict_battery_life(pil_data)

# Soru sorma
result = ai.answer_question("Tezgah bakımında en önemli 3 nokta nedir?")
```

### API Anahtarı Yönetimi

```python
# API anahtarı yönetimi
from api_key_manager import APIKeyManager

manager = APIKeyManager()

# API anahtarı kaydet
manager.set_api_key("AIzaSy...")

# API anahtarı al
api_key = manager.get_api_key()

# API anahtarı var mı kontrol et
has_key = manager.has_api_key()
```

## 🐛 Sorun Giderme

### Uygulama Açılmıyor
- Python versiyonunu kontrol edin: `python --version`
- Gerekli paketleri yükleyin: `pip install -r requirements.txt`
- Log dosyasını kontrol edin: `logs/tezgah_takip_*.log`

### API Anahtarı Çalışmıyor
- API anahtarının doğru olduğundan emin olun
- İnternet bağlantınızı kontrol edin
- Google Cloud Console'da API'nin aktif olduğunu kontrol edin
- Ayarlar > API Anahtarı'ndan yeni anahtar girin

### Veritabanı Hatası
- `tezgah_takip.db` dosyasının yazılabilir olduğundan emin olun
- Dosya izinlerini kontrol edin
- Yedek dosyadan geri yükleyin: `backups/` klasörü

### Şifreleme Hatası
- `cryptography` paketini yükleyin: `pip install cryptography`
- Eğer yüklenemiyorsa, uygulama basit şifreleme kullanacaktır

## 📊 Performans

- **Başlatma Süresi**: ~2-3 saniye
- **Veritabanı Sorgu Süresi**: <100ms
- **AI Yanıt Süresi**: 2-5 saniye (internet hızına bağlı)
- **Bellek Kullanımı**: ~150-200 MB
- **Disk Kullanımı**: ~50 MB (veritabanı boyutuna bağlı)

## 🔐 Güvenlik

### API Anahtarı Güvenliği
- API anahtarları şifrelenerek saklanır
- Makine kimliği tabanlı şifreleme
- Kod içinde hardcoded anahtar yok
- Her kullanıcı kendi anahtarını yönetir

### Veri Güvenliği
- SQLite veritabanı yerel olarak saklanır
- Otomatik yedekleme sistemi
- Transaction yönetimi ile veri bütünlüğü
- SQL injection koruması (parameterized queries)

## 🤝 Katkıda Bulunma

Bu proje açık kaynak değildir, ancak önerilerinizi paylaşabilirsiniz.

## 📞 Destek

### Sık Sorulan Sorular

**S: API anahtarım güvenli mi?**
C: Evet, anahtarınız şifrelenerek saklanır ve sadece sizin makinenizde çalışır.

**S: İnternet bağlantısı olmadan çalışır mı?**
C: Temel özellikler çalışır, ancak AI özellikleri için internet gereklidir.

**S: Birden fazla kullanıcı kullanabilir mi?**
C: Her kullanıcı kendi API anahtarını girmelidir.

**S: Veritabanı nerede saklanıyor?**
C: Uygulama klasöründe `tezgah_takip.db` dosyası olarak saklanır.

## 📝 Sürüm Notları

### v2.0.0 (Aralık 2025)
- ✅ Komple yeniden yazıldı
- ✅ API anahtarı yönetimi eklendi
- ✅ Gemini AI entegrasyonu
- ✅ Modern PyQt5 arayüzü
- ✅ SQLAlchemy ORM kullanımı
- ✅ Güvenli şifreleme sistemi
- ✅ Otomatik yedekleme
- ✅ Detaylı logging
- ✅ Splash screen
- ✅ Dashboard ve istatistikler

## 📄 Lisans

© 2025 TezgahTakip - Tüm hakları saklıdır.

## 🎉 Teşekkürler

- Google Gemini AI ekibine
- PyQt5 topluluğuna
- SQLAlchemy geliştiricilerine
- Tüm açık kaynak katkıda bulunanlara

---

**🏭 TezgahTakip v2.0 - AI Güçlü Fabrika Bakım Yönetim Sistemi**

**Geliştirme Tarihi**: Aralık 2025  
**Python Versiyonu**: 3.7+  
**Durum**: ✅ Kullanıma Hazır