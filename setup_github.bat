@echo off
echo ========================================
echo    TezgahTakip GitHub Setup
echo ========================================
echo.

REM Git repository'sini başlat
echo Git repository baslatiliyor...
git init

REM .gitignore dosyası oluştur (eğer yoksa)
if not exist ".gitignore" (
    echo .gitignore olusturuluyor...
    echo # Python > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.py[cod] >> .gitignore
    echo *$py.class >> .gitignore
    echo *.so >> .gitignore
    echo .Python >> .gitignore
    echo build/ >> .gitignore
    echo develop-eggs/ >> .gitignore
    echo dist/ >> .gitignore
    echo downloads/ >> .gitignore
    echo eggs/ >> .gitignore
    echo .eggs/ >> .gitignore
    echo lib/ >> .gitignore
    echo lib64/ >> .gitignore
    echo parts/ >> .gitignore
    echo sdist/ >> .gitignore
    echo var/ >> .gitignore
    echo wheels/ >> .gitignore
    echo *.egg-info/ >> .gitignore
    echo .installed.cfg >> .gitignore
    echo *.egg >> .gitignore
    echo MANIFEST >> .gitignore
    echo. >> .gitignore
    echo # PyInstaller >> .gitignore
    echo *.manifest >> .gitignore
    echo *.spec >> .gitignore
    echo. >> .gitignore
    echo # Logs >> .gitignore
    echo logs/ >> .gitignore
    echo *.log >> .gitignore
    echo. >> .gitignore
    echo # Database >> .gitignore
    echo *.db >> .gitignore
    echo *.sqlite >> .gitignore
    echo *.sqlite3 >> .gitignore
    echo. >> .gitignore
    echo # Backups >> .gitignore
    echo backups/ >> .gitignore
    echo backup_before_update/ >> .gitignore
    echo temp_update/ >> .gitignore
    echo. >> .gitignore
    echo # Config files with sensitive data >> .gitignore
    echo .secrets.json >> .gitignore
    echo .encryption_key >> .gitignore
    echo. >> .gitignore
    echo # IDE >> .gitignore
    echo .vscode/ >> .gitignore
    echo .idea/ >> .gitignore
    echo *.swp >> .gitignore
    echo *.swo >> .gitignore
    echo. >> .gitignore
    echo # OS >> .gitignore
    echo .DS_Store >> .gitignore
    echo Thumbs.db >> .gitignore
    echo desktop.ini >> .gitignore
)

REM README.md oluştur
echo README.md olusturuluyor...
echo # 🏭 TezgahTakip - AI Güçlü Fabrika Bakım Yönetim Sistemi > README.md
echo. >> README.md
echo ## 🎯 Proje Hakkında >> README.md
echo. >> README.md
echo TezgahTakip, fabrika tezgahlarının bakım ve takibini kolaylaştıran, Google Gemini AI ile güçlendirilmiş modern bir masaüstü uygulamasıdır. >> README.md
echo. >> README.md
echo ### ✨ Özellikler >> README.md
echo. >> README.md
echo - 🏭 **Tezgah Yönetimi**: Kapsamlı tezgah takip sistemi >> README.md
echo - ⚠️ **Arıza Kayıt Sistemi**: Detaylı arıza takibi ve analizi >> README.md
echo - 🔋 **Pil Takibi**: Otomatik pil değişim uyarıları >> README.md
echo - 🧠 **AI Analizi**: Gemini AI ile akıllı bakım önerileri >> README.md
echo - 📊 **Modern Dashboard**: Gerçek zamanlı istatistikler >> README.md
echo - 🔄 **Otomatik Güncelleme**: Tek tıkla güncelleme sistemi >> README.md
echo - 💾 **Yedekleme**: Otomatik veri yedekleme >> README.md
echo - 🎨 **Modern Arayüz**: PyQt5 ile kullanıcı dostu tasarım >> README.md
echo. >> README.md
echo ### 🚀 Hızlı Başlangıç >> README.md
echo. >> README.md
echo #### İndirme >> README.md
echo. >> README.md
echo 1. [Releases](https://github.com/PobloMert/tezgah-takip/releases) sayfasından en son sürümü indirin >> README.md
echo 2. `installer.bat` dosyasını çalıştırın >> README.md
echo 3. Masaüstündeki kısayola tıklayarak uygulamayı başlatın >> README.md
echo. >> README.md
echo #### Geliştirici Kurulumu >> README.md
echo. >> README.md
echo ```bash >> README.md
echo git clone https://github.com/PobloMert/tezgah-takip.git >> README.md
echo cd tezgah-takip >> README.md
echo pip install -r requirements.txt >> README.md
echo python run_tezgah_takip.py >> README.md
echo ``` >> README.md
echo. >> README.md
echo ### 📦 Executable Oluşturma >> README.md
echo. >> README.md
echo ```bash >> README.md
echo python build_executable.py >> README.md
echo ``` >> README.md
echo. >> README.md
echo ### 🔄 Otomatik Güncelleme >> README.md
echo. >> README.md
echo Uygulama otomatik güncelleme sistemi ile donatılmıştır: >> README.md
echo. >> README.md
echo - Başlangıçta otomatik güncelleme kontrolü >> README.md
echo - Ayarlar menüsünden manuel kontrol >> README.md
echo - Güvenli indirme ve yedekleme >> README.md
echo - Kullanıcı verilerini koruma >> README.md
echo. >> README.md
echo ### 💻 Sistem Gereksinimleri >> README.md
echo. >> README.md
echo - Windows 10/11 (64-bit) >> README.md
echo - Python 3.7+ (geliştirici kurulumu için) >> README.md
echo - 4 GB RAM (önerilen) >> README.md
echo - 500 MB disk alanı >> README.md
echo. >> README.md
echo ### 🤝 Katkıda Bulunma >> README.md
echo. >> README.md
echo 1. Fork edin >> README.md
echo 2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`) >> README.md
echo 3. Commit edin (`git commit -m 'Add amazing feature'`) >> README.md
echo 4. Push edin (`git push origin feature/amazing-feature`) >> README.md
echo 5. Pull Request oluşturun >> README.md
echo. >> README.md
echo ### 📄 Lisans >> README.md
echo. >> README.md
echo Bu proje MIT lisansı altında lisanslanmıştır. >> README.md
echo. >> README.md
echo ### 📞 İletişim >> README.md
echo. >> README.md
echo - GitHub Issues: Hata raporları ve özellik istekleri >> README.md
echo - Email: Direkt destek için >> README.md

REM Dosyaları stage'e ekle
echo Dosyalar Git'e ekleniyor...
git add .

REM İlk commit
echo Ilk commit yapiliyor...
git commit -m "feat: TezgahTakip v2.0.0 - AI Güçlü Fabrika Bakım Yönetim Sistemi

✨ Özellikler:
- 🏭 Kapsamlı tezgah yönetimi
- ⚠️ Arıza kayıt ve takip sistemi  
- 🔋 Pil takibi ve uyarı sistemi
- 🧠 Gemini AI entegrasyonu
- 📊 Modern dashboard tasarımı
- 🔄 Otomatik güncelleme sistemi
- 💾 Yedekleme ve geri yükleme
- 🎨 PyQt5 ile modern arayüz

🚀 Dağıtım:
- Tek tıkla çalışan executable
- Otomatik kurulum programı
- Portable versiyon desteği
- GitHub Releases entegrasyonu"

REM Remote repository ekle
echo Remote repository ekleniyor...
git remote add origin https://github.com/PobloMert/tezgah-takip.git

echo.
echo ========================================
echo   Git repository hazir!
echo ========================================
echo.
echo Sonraki adimlar:
echo 1. GitHub'da 'tezgah-takip' repository'sini olusturun
echo 2. Asagidaki komutu calistirin:
echo    git push -u origin main
echo.
echo Ilk release icin:
echo    git tag v2.0.0
echo    git push origin v2.0.0
echo.
pause