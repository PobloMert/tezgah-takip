# 🚀 TezgahTakip Dağıtım ve Güncelleme Rehberi

## 📋 İçindekiler
1. [Tek Tıkla Çalışan Uygulama Oluşturma](#tek-tıkla-çalışan-uygulama-oluşturma)
2. [Otomatik Güncelleme Sistemi](#otomatik-güncelleme-sistemi)
3. [GitHub Releases ile Dağıtım](#github-releases-ile-dağıtım)
4. [Kullanıcı Verilerini Koruma](#kullanıcı-verilerini-koruma)
5. [Yeni Versiyon Yayınlama](#yeni-versiyon-yayınlama)

## 🎯 Tek Tıkla Çalışan Uygulama Oluşturma

### 1. Geliştirme Ortamını Hazırlama
```bash
# Gerekli paketleri yükle
pip install PyQt5>=5.15.0 SQLAlchemy>=2.0.0 requests>=2.25.0 packaging>=21.0 pyinstaller>=5.0.0

# Build script'ini çalıştır
python build_executable.py
```

### 2. Oluşturulan Dosyalar
- `dist/TezgahTakip_Launcher.exe` - Ana launcher (kullanıcıların çalıştıracağı)
- `dist/TezgahTakip.exe` - Ana uygulama
- `dist/installer.bat` - Otomatik kurulum programı
- `dist/TezgahTakip_Portable/` - Portable versiyon

### 3. Kullanıcı Deneyimi
```
Kullanıcı İşlemleri:
1. TezgahTakip_Launcher.exe'yi çift tıklar
2. Launcher otomatik güncelleme kontrolü yapar
3. Gerekirse güncellemeyi indirir ve uygular
4. Ana uygulamayı başlatır
5. Kullanıcı verilerini korur (veritabanı, ayarlar)
```

## 🔄 Otomatik Güncelleme Sistemi

### Nasıl Çalışır?
1. **Güncelleme Kontrolü**: GitHub Releases API'sini kontrol eder
2. **Versiyon Karşılaştırması**: Semantic versioning kullanır
3. **Güvenli İndirme**: HTTPS üzerinden güvenli indirme
4. **Yedekleme**: Güncelleme öncesi otomatik yedekleme
5. **Geri Alma**: Hata durumunda otomatik geri alma

### Kullanıcı Verileri Korunur
- `*.db` - Veritabanı dosyaları
- `config.json` - Kullanıcı ayarları
- `settings.json` - Uygulama ayarları
- `backups/` - Kullanıcı yedekleri

### Güncellenen Dosyalar
- `main_window.py` - Ana uygulama kodu
- `database_models.py` - Veritabanı modelleri
- `*.py` - Diğer Python dosyaları
- `requirements.txt` - Bağımlılıklar

## 📦 GitHub Releases ile Dağıtım

### 1. Repository Kurulumu
```bash
# GitHub repository oluştur
git init
git remote add origin https://github.com/USERNAME/tezgah-takip.git

# Dosyaları ekle
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 2. GitHub Actions Kurulumu
- `.github/workflows/release.yml` dosyası otomatik build yapar
- Tag push'unda otomatik release oluşturur
- Windows executable'ları build eder

### 3. Secrets Ayarları
GitHub repository → Settings → Secrets and variables → Actions:
- `GITHUB_TOKEN` otomatik olarak mevcut

## 🆕 Yeni Versiyon Yayınlama

### 1. Kod Değişikliklerini Yap
```bash
# Değişiklikleri yap
git add .
git commit -m "feat: yeni özellik eklendi"
git push
```

### 2. Versiyon Tag'i Oluştur
```bash
# Semantic versioning kullan
git tag v2.1.0
git push origin v2.1.0
```

### 3. Otomatik Build ve Release
- GitHub Actions otomatik çalışır
- Windows executable'ları build eder
- Release oluşturur ve dosyaları yükler
- Kullanıcılar otomatik güncelleme alır

### 4. Versiyon Numaraları
```
v2.0.0 - Major release (büyük değişiklikler)
v2.1.0 - Minor release (yeni özellikler)
v2.1.1 - Patch release (hata düzeltmeleri)
```

## 🔒 Kullanıcı Verilerini Koruma

### Güncelleme Sırasında Korunan Veriler
```
Korunan Dosyalar:
├── *.db (tüm veritabanı dosyaları)
├── config.json (kullanıcı ayarları)
├── settings.json (uygulama ayarları)
├── backups/ (kullanıcı yedekleri)
└── logs/ (log dosyaları)

Güncellenen Dosyalar:
├── *.py (Python kaynak kodları)
├── *.exe (executable dosyalar)
├── requirements.txt
└── README.md
```

### Yedekleme Stratejisi
1. **Güncelleme Öncesi**: Otomatik yedekleme
2. **Hata Durumunda**: Otomatik geri alma
3. **Kullanıcı Kontrolü**: Manuel yedekleme seçeneği

## 📋 Dağıtım Kontrol Listesi

### Yeni Versiyon Hazırlığı
- [ ] Kod değişiklikleri test edildi
- [ ] Versiyon numarası güncellendi
- [ ] CHANGELOG.md güncellendi
- [ ] Yeni özellikler dokümante edildi
- [ ] Geriye uyumluluk kontrol edildi

### Release Süreci
- [ ] Git tag oluşturuldu
- [ ] GitHub Actions başarıyla çalıştı
- [ ] Release notes yazıldı
- [ ] Test kullanıcıları bilgilendirildi
- [ ] Güncelleme testi yapıldı

### Kullanıcı Desteği
- [ ] Kurulum rehberi hazırlandı
- [ ] Sorun giderme kılavuzu oluşturuldu
- [ ] İletişim kanalları belirlendi
- [ ] Geri bildirim sistemi kuruldu

## 🛠️ Geliştirici Komutları

### Build Komutları
```bash
# Executable oluştur
python build_executable.py

# Sadece launcher build et
pyinstaller --onefile --windowed launcher.py

# Ana uygulama build et
pyinstaller --onefile --windowed run_tezgah_takip.py
```

### Test Komutları
```bash
# Güncelleme sistemini test et
python auto_updater.py

# Launcher'ı test et
python launcher.py

# Ana uygulamayı test et
python run_tezgah_takip.py
```

### Dağıtım Komutları
```bash
# Yeni versiyon tag'i
git tag v2.1.0
git push origin v2.1.0

# Manuel release (gerekirse)
gh release create v2.1.0 dist/*.exe --title "TezgahTakip v2.1.0"
```

## 🎯 Kullanıcı Deneyimi Akışı

### İlk Kurulum
1. Kullanıcı `installer.bat` çalıştırır
2. Program Files'a kurulum yapılır
3. Masaüstü ve başlat menüsü kısayolları oluşturulur
4. İlk çalıştırmada örnek veriler yüklenir

### Günlük Kullanım
1. Masaüstü kısayoluna tıklar
2. Launcher otomatik güncelleme kontrolü yapar
3. Gerekirse sessizce günceller
4. Ana uygulamayı başlatır
5. Kullanıcı verilerini korur

### Güncelleme Deneyimi
1. Launcher yeni versiyon tespit eder
2. Kullanıcıya bildirim gösterir
3. Onay alırsa güncellemeyi indirir
4. Yedekleme yapar
5. Güncellemeyi uygular
6. Başarısızlık durumunda geri alır

## 📞 Destek ve Sorun Giderme

### Yaygın Sorunlar
- **Windows Defender Uyarısı**: Güvenli olarak işaretleyin
- **Güncelleme Başarısız**: İnternet bağlantısını kontrol edin
- **Uygulama Açılmıyor**: Yönetici olarak çalıştırın

### Log Dosyaları
- `logs/tezgah_takip.log` - Ana uygulama logları
- `logs/updater.log` - Güncelleme logları
- `logs/launcher.log` - Launcher logları

### İletişim
- GitHub Issues: Hata raporları
- Email: Direkt destek
- Dokümantasyon: README.md

---

Bu rehber ile TezgahTakip uygulamanızı profesyonel bir şekilde dağıtabilir ve kullanıcılarınıza sorunsuz güncelleme deneyimi sunabilirsiniz! 🚀