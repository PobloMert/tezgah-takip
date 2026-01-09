# 🎉 TezgahTakip v2.1.2 - Gelişmiş Yedekleme Sistemi

## 📋 Özet
TezgahTakip v2.1.2, güvenilirlik ve veri korunması odaklı önemli bir güncelleme. Gelişmiş otomatik yedekleme sistemi, zamanlanmış backup işlemleri ve kapsamlı güvenlik iyileştirmeleri içerir.

## 🆕 Yeni Özellikler

### 💾 Level 1 Scheduled Backup System
- **⏰ Otomatik Günlük Yedekleme**: Her gece 23:00'da otomatik backup
- **📅 7 Günlük Saklama**: Otomatik eski yedek temizleme
- **📦 Sıkıştırılmış Yedekler**: ZIP formatında metadata ile
- **⚙️ Yedekleme Ayarları**: Tam kontrol ve yapılandırma
- **🧪 Test Yedekleme**: Anında backup testi

### 🔒 Gelişmiş Güvenlik Sistemi
- **🛡️ Input Validation**: Kapsamlı veri doğrulama
- **🔐 Security Manager**: Gelişmiş güvenlik kontrolleri
- **📊 Bulk Operations**: Toplu işlem güvenliği
- **🚨 Exception Handling**: Gelişmiş hata yönetimi

### 🤖 AI Sistemi İyileştirmeleri
- **🆕 Gemini 2.0 Flash**: En yeni AI model desteği
- **⚡ Rate Limiting**: Akıllı istek yönetimi (5/dakika)
- **🔑 API Key Management**: Gelişmiş anahtar yönetimi
- **💬 Türkçe Destek**: Tam Türkçe AI yanıtları

## 🔧 İyileştirmeler

### 🐛 Çözülen Sorunlar
- ✅ PDF Türkçe karakter desteği (ç, ğ, ı, ö, ş, ü)
- ✅ Excel export güvenlik hataları
- ✅ Context menu işlemleri (düzenle, sil, detay)
- ✅ Pil değişimi validasyon hataları
- ✅ CustomMessageBox attribute hataları

### 🚀 Performans İyileştirmeleri
- Backup işlemleri arka planda çalışır
- Otomatik cleanup ile disk alanı optimizasyonu
- Thread-safe backup operasyonları
- Gelişmiş memory management

## 📦 Yedekleme Sistemi Detayları

### 🕐 Zamanlanmış Yedekleme
- **Varsayılan Saat**: 23:00 (yapılandırılabilir)
- **Kontrol Sıklığı**: Her dakika
- **Otomatik Başlatma**: Uygulama açılışında aktif
- **Status Bildirimleri**: Gerçek zamanlı durum güncellemeleri

### 📁 Yedek Dosya Formatı
```
backups/
├── tezgah_takip_backup_20260109_230000.zip
├── backup_metadata.json (içinde)
└── tezgah_takip_v2.db (içinde)
```

### 🔧 Yedekleme Ayarları
- **Aktif/Pasif**: Zamanlanmış yedeklemeyi aç/kapat
- **Yedekleme Saati**: Özel saat ayarlama (HH:MM)
- **Maksimum Yedek**: Saklanacak yedek sayısı (1-30)
- **Test Yedekleme**: Anında backup testi

## 📊 Sistem Gereksinimleri

### Minimum
- **İşletim Sistemi**: Windows 10 (64-bit)
- **RAM**: 4 GB
- **Disk Alanı**: 1 GB (yedekler için ek alan)
- **.NET Framework**: 4.7.2 veya üzeri

### Önerilen
- **İşletim Sistemi**: Windows 11 (64-bit)
- **RAM**: 8 GB
- **Disk Alanı**: 2 GB (yedekler ve loglar için)
- **İnternet**: AI özellikler ve güncellemeler için

## 🔄 v2.1.1'den Güncelleme

### ✅ Otomatik Güncelleme
- Mevcut verileriniz korunur
- Yedekleme sistemi otomatik aktif olur
- Ayarlar ve konfigürasyonlar taşınır

### 🆕 Yeni Özellikler
- Ayarlar > Yedekleme Ayarları menüsü
- Otomatik backup bildirimleri
- Gelişmiş hata raporlama

## 📦 İndirme Seçenekleri

### 💻 Kurulum Paketi (Önerilen)
**Dosya**: `TezgahTakip-v2.1.2-Release.zip`
1. ZIP dosyasını indirin ve çıkarın
2. `installer.bat` dosyasını yönetici olarak çalıştırın
3. Otomatik kurulum ve yedekleme sistemi kurulumu

### 📱 Portable Sürüm
**Klasör**: `TezgahTakip_v2.1.2_Portable/`
1. Klasörü istediğiniz yere kopyalayın
2. `Baslat.bat` çalıştırın
3. Yedekleme sistemi otomatik aktif

### 🔗 Direkt Executable
**Dosya**: `TezgahTakip_v2.1.2.exe`
1. Tek dosya çalıştırma
2. Yedekleme klasörü otomatik oluşturulur

## 🛡️ Güvenlik Özellikleri

### 🔐 Veri Korunması
- Otomatik günlük yedekleme
- Sıkıştırılmış ve metadata'lı backup
- 7 günlük veri geçmişi
- Güvenli dosya operasyonları

### 🚨 Hata Yönetimi
- Kapsamlı exception handling
- Detaylı hata logları
- Otomatik recovery mekanizmaları
- Kullanıcı dostu hata mesajları

## 🎯 Kullanım Kılavuzu

### 💾 Yedekleme Sistemi Kullanımı
1. **Otomatik**: Sistem her gece 23:00'da otomatik yedek alır
2. **Manuel**: Ayarlar > Yedekleme Ayarları > Test Yedekleme
3. **Yapılandırma**: Yedekleme saati ve ayarları değiştirin
4. **Kontrol**: Status bar'da yedekleme durumunu izleyin

### 🔧 Ayarlar Menüsü
1. **Yedekleme Ayarları**: Backup konfigürasyonu
2. **API Ayarları**: Gemini AI anahtarı
3. **Veri Yönetimi**: İçe/dışa aktarma
4. **Sistem Sağlığı**: Performans izleme

## 📊 Dosya Boyutları

| Dosya | Boyut | Açıklama |
|-------|-------|----------|
| `TezgahTakip_v2.1.2.exe` | ~50 MB | Ana uygulama |
| `TezgahTakip-v2.1.2-Release.zip` | ~65 MB | Tam paket |
| `Backup Files` | ~200 KB/gün | Günlük yedek boyutu |

## 🆘 Destek ve Sorun Giderme

### 📞 İletişim
- **GitHub Issues**: https://github.com/PobloMert/tezgah-takip/issues
- **Repository**: https://github.com/PobloMert/tezgah-takip
- **Dokümantasyon**: README.md ve wiki sayfaları

### 🔧 Yaygın Sorunlar
1. **Yedekleme Çalışmıyor**: Disk alanını kontrol edin
2. **AI Bağlantı Hatası**: API anahtarını yenileyin
3. **PDF Export Sorunu**: Sistem fontlarını kontrol edin
4. **Performans Sorunu**: Eski yedekleri temizleyin

### 📋 Log Dosyaları
- **Ana Log**: `logs/tezgah_takip.log`
- **Backup Log**: `logs/backup.log`
- **Error Log**: `logs/error.log`

## 🔄 Yedekleme Sistemi Teknical Detaylar

### 🏗️ Mimari
- **AdvancedBackupManager**: Ana yedekleme sınıfı
- **ScheduledBackupManager**: Zamanlanmış işlemler
- **QTimer Integration**: PyQt5 timer sistemi
- **Thread Safety**: Arka plan işlemleri

### 📝 Backup Metadata
```json
{
  "backup_info": {
    "created_at": "2026-01-09T23:00:00Z",
    "version": "2.1.2",
    "backup_type": "compressed"
  },
  "database_info": {
    "size_mb": 0.25,
    "tables": {"tezgah": 196, "bakimlar": 150},
    "total_records": 346
  }
}
```

## 📝 Lisans
Bu yazılım MIT lisansı altında dağıtılmaktadır. Ticari ve kişisel kullanım için ücretsizdir.

## 🙏 Teşekkürler
Sürekli geri bildirimleriniz ve önerileriniz için teşekkür ederiz. v2.1.2 ile veri güvenliği ve sistem güvenilirliği en üst seviyeye çıkarılmıştır.

---

**📅 Yayın Tarihi**: 9 Ocak 2026  
**🏷️ Versiyon**: 2.1.2  
**👨‍💻 Geliştirici**: TezgahTakip Ekibi  
**🔗 Repository**: https://github.com/PobloMert/tezgah-takip

**🎊 TezgahTakip v2.1.2 ile verileriniz artık daha güvende!**