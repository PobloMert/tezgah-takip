@echo off
chcp 65001 >nul
title TezgahTakip v2.1.2 - GitHub Push

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    TezgahTakip v2.1.2                        ║
echo ║                  GitHub Release Push                         ║
echo ║                💾 Gelişmiş Yedekleme Sistemi                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🚀 GitHub'a v2.1.2 push işlemi başlatılıyor...
echo.

REM Git durumunu kontrol et
echo 📋 Git durumu kontrol ediliyor...
git status
echo.

REM Değişiklikleri ekle
echo 📄 Değişiklikler ekleniyor...
git add .
echo ✅ Tüm değişiklikler eklendi
echo.

REM Commit yap
echo 💾 Commit yapılıyor...
git commit -m "🎉 Release v2.1.2 - Gelişmiş Yedekleme Sistemi

🆕 Yeni Özellikler:
- 💾 Level 1 Scheduled Backup System
- ⏰ Otomatik günlük yedekleme (23:00)
- 📅 7 günlük yedek saklama politikası
- 🔒 Gelişmiş güvenlik sistemi
- 🤖 Gemini 2.0 Flash AI desteği

🔧 İyileştirmeler:
- ✅ PDF Türkçe karakter desteği
- ✅ Excel export güvenlik düzeltmeleri
- ✅ Context menu işlemleri
- ✅ Pil değişimi validasyon düzeltmeleri

📦 Teknik:
- advanced_backup_manager.py eklendi
- Thread-safe backup operasyonları
- Otomatik cleanup sistemi
- Kapsamlı hata yönetimi"

if %errorlevel% neq 0 (
    echo ❌ Commit başarısız!
    pause
    exit /b 1
)

echo ✅ Commit başarılı
echo.

REM Ana branch'e push
echo 🌐 Ana branch'e push yapılıyor...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ Push başarısız!
    pause
    exit /b 1
)
echo ✅ Ana branch push başarılı
echo.

REM Tag oluştur
echo 🏷️ v2.1.2 tag'i oluşturuluyor...
git tag -a v2.1.2 -m "TezgahTakip v2.1.2 - Gelişmiş Yedekleme Sistemi

🎉 Yeni Özellikler:
💾 Level 1 Scheduled Backup System
⏰ Otomatik günlük yedekleme (23:00)
📅 7 günlük yedek saklama
🔒 Gelişmiş güvenlik sistemi
🤖 Gemini 2.0 Flash AI

🔧 İyileştirmeler:
✅ PDF Türkçe karakter desteği
✅ Excel export güvenlik düzeltmeleri
✅ Context menu işlemleri
✅ Validasyon düzeltmeleri

📦 Dosyalar:
- TezgahTakip-v2.1.2-Release.zip
- TezgahTakip-v2.1.2-Windows.zip
- RELEASE_NOTES_v2.1.2.md
- CHANGELOG_v2.1.2.md"

if %errorlevel% neq 0 (
    echo ❌ Tag oluşturma başarısız!
    pause
    exit /b 1
)
echo ✅ Tag oluşturuldu
echo.

REM Tag'i push et
echo 🚀 Tag push ediliyor...
git push origin v2.1.2
if %errorlevel% neq 0 (
    echo ❌ Tag push başarısız!
    pause
    exit /b 1
)
echo ✅ Tag push başarılı
echo.

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🎊 PUSH TAMAMLANDI! 🎊                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 TezgahTakip v2.1.2 başarıyla GitHub'a push edildi!
echo.
echo 📋 Sonraki adımlar:
echo   1. GitHub'ta Releases sayfasına gidin
echo   2. v2.1.2 tag'ini bulun
echo   3. "Create release from tag" tıklayın
echo   4. Release notes'u ekleyin
echo   5. ZIP dosyalarını yükleyin
echo.
echo 🔗 GitHub Releases: https://github.com/PobloMert/tezgah-takip/releases
echo.
echo 💾 Release dosyaları:
echo   - TezgahTakip-v2.1.2-Release.zip
echo   - TezgahTakip-v2.1.2-Windows.zip
echo   - RELEASE_NOTES_v2.1.2.md
echo   - CHANGELOG_v2.1.2.md
echo.
pause