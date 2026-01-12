# TezgahTakip v2.1.1 - Değişiklik Günlüğü

## 🆕 Yeni Özellikler

### 🎨 Gelişmiş Arayüz
- **Tab Sekmeli Arayüz**: Modern tab widget sistemi ile daha kolay navigasyon
- **Ayarlar Sekmesi**: Kapsamlı ayarlar paneli eklendi
  - API Ayarları
  - Veri Yönetimi (İçe/Dışa Aktarma, Yedekleme)
  - Uygulama Ayarları
  - Sistem Sağlığı
  - Hakkında Bilgileri

### 🔧 İyileştirmeler
- **Tab Görünürlüğü**: Tab sekmelerinin görünmediği sorun düzeltildi
- **Menü Erişimi**: Ayarlar sekmesi ile menü fonksiyonlarına kolay erişim
- **Responsive Tasarım**: Daha iyi ekran uyumluluğu
- **Kod Temizliği**: Kullanılmayan kodlar kaldırıldı

### 📦 Build Sistemi
- **Gelişmiş Build Script**: Profesyonel paketleme sistemi
- **Çoklu Paket Formatı**: 
  - Installer (installer.bat)
  - Portable Paket
  - Release ZIP
- **Otomatik Versiyon Yönetimi**: Tüm dosyalarda tutarlı versiyon numaraları

## 🐛 Düzeltilen Hatalar

### 🖥️ Arayüz Sorunları
- Tab sekmelerinin görünmeme sorunu çözüldü
- Menü çubuğu erişim sorunu ayarlar sekmesi ile çözüldü
- Yazı görünürlük sorunları düzeltildi

### 🔧 Teknik İyileştirmeler
- Kullanılmayan import'lar kaldırıldı
- Navigation bar sistemi kaldırıldı (tab widget lehine)
- QStackedWidget bağımlılığı kaldırıldı
- Kod optimizasyonu yapıldı

## 📋 Teknik Detaylar

### 🏗️ Mimari Değişiklikler
- Navigation bar sisteminden tab widget sistemine geçiş
- Ayarlar menüsü yerine ayarlar sekmesi
- Daha temiz ve modüler kod yapısı

### 📦 Paketleme
- PyInstaller ile optimize edilmiş build
- UPX sıkıştırma aktif
- Tek dosya executable
- Tüm bağımlılıklar dahil

### 🎯 Performans
- Daha hızlı başlangıç
- Düşük bellek kullanımı
- Optimize edilmiş dosya boyutu

## 🚀 Kullanım

### 💻 Kurulum Seçenekleri
1. **Installer**: `installer.bat` ile otomatik kurulum
2. **Portable**: Klasörü kopyala ve çalıştır
3. **Direkt**: `TezgahTakip_Launcher.exe` çalıştır

### 📱 Yeni Özellik Kullanımı
- **Ayarlar**: Sağ üstteki "⚙️ Ayarlar" sekmesine tıklayın
- **API Anahtarı**: Ayarlar > API Ayarları
- **Veri Yönetimi**: Ayarlar > Veri Yönetimi
- **Sistem Bilgisi**: Ayarlar > Sistem Sağlığı

## 📊 İstatistikler

### 📁 Dosya Boyutları
- **Launcher**: ~15 MB
- **Ana Uygulama**: ~48 MB
- **Release Paketi**: ~62 MB

### 🎯 Sistem Gereksinimleri
- Windows 10/11 (64-bit)
- .NET Framework 4.7.2+
- 4 GB RAM (minimum)
- 500 MB disk alanı

## 🔄 v2.1.0'dan v2.1.1'e Geçiş

### ✅ Otomatik Güncelleme
- Mevcut veriler korunur
- Ayarlar otomatik taşınır
- Yedekler korunur

### 🆕 Yeni Özellikler
- Ayarlar sekmesi otomatik görünür
- Tab navigasyonu aktif
- Tüm menü fonksiyonları erişilebilir

---

**Geliştirici Notu**: v2.1.1, kullanıcı geri bildirimlerine dayalı olarak geliştirilmiştir. Tab sekmelerinin görünmeme sorunu ve ayarlara erişim zorluğu tamamen çözülmüştür.

**Tarih**: 4 Ocak 2026  
**Geliştirici**: TezgahTakip Ekibi  
**Lisans**: MIT