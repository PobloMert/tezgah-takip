# TezgahTakip - EXE ve Setup Dosyası Oluşturma Kılavuzu

## 🎯 Amaç

Bu kılavuz, TezgahTakip Python uygulamasını Windows kullanıcıları için kullanıcı dostu EXE kurulum dosyasına dönüştürmeyi açıklar.

## 📋 Ön Gereksinimler

### 1. Windows İşletim Sistemi
- Windows 7 veya üstü
- Administrator hakları

### 2. Python 3.7 veya Üstü
```bash
python --version
```

### 3. Gerekli Kütüphaneler
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Inno Setup 6 (Opsiyonel ama Önerilen)
- **İndir**: https://jrsoftware.org/isdl.php
- **Kurulum**: Kurulum sihirbazını takip edin
- **Doğrulama**: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" olmalı

## 🚀 Hızlı Başlangıç (3 Adım)

### Adım 1: Build Script'ini Çalıştır
```bash
python build_system.py
```

### Adım 2: İşlemin Tamamlanmasını Bekle
- EXE oluşturma: 2-5 dakika
- Setup.exe oluşturma: 1-2 dakika
- **Toplam**: 5-10 dakika

### Adım 3: Çıktı Dosyalarını Kontrol Et
```
releases/
├── TezgahTakip_Setup_v2.3.1.exe  ← Kurulum dosyası (önerilen)
├── BUILD_RAPORU.txt              ← Detaylı rapor
└── KURULUM_KILAVUZU.txt          ← Kullanıcı kılavuzu

dist/
└── TezgahTakip/
    └── TezgahTakip.exe           ← Portable EXE (kurulum gerektirmez)
```

## 📦 Çıktı Dosyaları Açıklaması

### Setup.exe (TezgahTakip_Setup_v2.3.1.exe)
✅ **Önerilen Dağıtım Yöntemi**

- Profesyonel Windows kurulum sihirbazı
- Kullanıcılar "Program Ekle/Kaldır" bölümünden kaldırabilir
- Başlat Menüsü ve Masaüstü kısayolları oluşturur
- Dosya boyutu: ~150-200 MB
- **Kullanıcılar için**: Sadece indirip çalıştırın, tek tık ✨

### Portable EXE (dist/TezgahTakip/TezgahTakip.exe)
✅ **Alternatif Seçenek**

- Kurulum gerektirmez
- USB'ye kopyalanabilir
- Dosya boyutu: ~200-300 MB
- **Kullanıcılar için**: İndirip çalıştırın, klasör içinde kalmalı

## 🔍 Sorun Giderme

### ❌ "PyInstaller bulunamadı"
```bash
pip install pyinstaller
python build_system.py
```

### ❌ "Inno Setup bulunamadı (Windows'ta)"
```
1. https://jrsoftware.org/isdl.php adresine gidin
2. Inno Setup 6'yı indirin ve kurun
3. build_system.py'yi yeniden çalıştırın
4. Setup.exe otomatik oluşturulacak
```

### ❌ "EXE başlamıyor"
**Çözüm 1**: Visual C++ Runtime'ı yükle
```
https://support.microsoft.com/en-us/help/2977003
```

**Çözüm 2**: Python 3.9+ kullan
```bash
python --version  # 3.9+ olmalı
python build_system.py
```

### ❌ "Antivirus uyarısı alıyorum"
- Bu normal, PyInstaller'ın bilinen sorunu
- GitHub deposundaki kaynak kodları inceleyebilir misiniz
- Virüs taraması: https://www.virustotal.com/

## 🎨 EXE İyileştirmeleri

### İkon Ekleme
1. 256x256 PNG resmi oluştur ve `assets/icon.ico` olarak kaydet
2. `build_system.py` içinde şu satırı değiştir:
```python
icon=None,  # İcon dosyası: 'assets/icon.ico'
```
şuna:
```python
icon='assets/icon.ico',
```
3. `python build_system.py` çalıştır

### Versiyon Bilgisi Ekleme
`build_system.py` içinde `self.version` değerini güncelle:
```python
self.version = "2.4.0"  # Yeni sürüm
```

## 📊 Build Süresi Tahmini

| İşlem | Bilgisayar | Süre |
|-------|-----------|------|
| EXE Oluşturma | Orta (SSD) | 2-3 dakika |
| Setup.exe Oluşturma | - | 1-2 dakika |
| Toplam | - | **5-10 dakika** |

## 🔐 Güvenlik Notları

1. **Kaynak Kodlar Kilitli Değildir**
   - Kodlar görülebilir: `pyinstaller --onefile` ile biraz güvenlik artırabilirsiniz
   - Gizli kütüphaneleri obfüskate etmek için [PyArmor](https://pyarmor.readthedocs.io/) kullanın

2. **API Anahtarları**
   - Kodda sabit API anahtarları saklamayın
   - Ortam değişkenleri veya config dosyaları kullanın

3. **Sürüm Denetimi**
   - Build öncesi `requirements.txt`'i güncelleyin
   - Her yeni sürüm için `self.version` güncelleyin

## 🚀 GitHub Releases'e Yükleme

1. GitHub deposunun Releases bölümüne gidin
2. "New Release" tıklayın
3. `releases/TezgahTakip_Setup_vX.X.X.exe` dosyasını yükleyin
4. Açıklamaya `BUILD_RAPORU.txt` içeriğini yapıştırın

**Örnek Açıklama:**
```
## 🎉 TezgahTakip v2.3.1 - AI Güçlü Fabrika Bakım Yönetim Sistemi

### 📥 Kurulum
1. **TezgahTakip_Setup_v2.3.1.exe** dosyasını indirin
2. Çift tıklayın ve kurulum sihirbazını takip edin
3. Tamamlandıktan sonra otomatik olarak başlayacaktır

### ✨ Yenilikler
- ...
- ...

### 🐛 Düzeltmeler
- ...
```

## 📞 Destek

- **GitHub Issues**: https://github.com/PobloMert/tezgah-takip/issues
- **Raporlanan Hatalar**: Lütfen ekran görüntüsü ve hata mesajı ekleyin

## 📚 Kaynaklar

- [PyInstaller Belgeleri](https://pyinstaller.readthedocs.io/)
- [Inno Setup Belgeleri](https://jrsoftware.org/isinfo.php)
- [Python Paketleme Kılavuzu](https://packaging.python.org/)

---

**Not**: Build işlemi ilk kez çalıştırıldığında daha uzun sürebilir. Sonraki seferler daha hızlı olacaktır.

🎊 Başarılar!
