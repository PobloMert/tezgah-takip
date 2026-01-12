@echo off
chcp 65001 >nul
title TezgahTakip v2.1.2 - Kurulum

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    TezgahTakip v2.1.2 KURULUM                 ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                  💾 Gelişmiş Yedekleme Sistemi               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🔧 Kurulum başlatılıyor...
echo.

REM Yönetici kontrolü
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Bu kurulum yönetici yetkileri gerektirir!
    echo 🔄 Lütfen "Yönetici olarak çalıştır" seçeneğini kullanın.
    echo.
    pause
    exit /b 1
)

echo ✅ Yönetici yetkileri doğrulandı
echo.

REM Program Files klasörüne kopyala
set "INSTALL_DIR=%ProgramFiles%\TezgahTakip"
echo 📁 Kurulum dizini: %INSTALL_DIR%

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo ✅ Kurulum klasörü oluşturuldu
)

echo 📄 Dosyalar kopyalanıyor...
copy "TezgahTakip_v2.1.2.exe" "%INSTALL_DIR%\" >nul
copy "config.json" "%INSTALL_DIR%\" >nul
copy "README.md" "%INSTALL_DIR%\" >nul

REM Masaüstü kısayolu oluştur
echo 🔗 Masaüstü kısayolu oluşturuluyor...
set "DESKTOP=%USERPROFILE%\Desktop"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\shortcut.vbs"
echo sLinkFile = "%DESKTOP%\TezgahTakip v2.1.2.lnk" >> "%TEMP%\shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\shortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\TezgahTakip_v2.1.2.exe" >> "%TEMP%\shortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\shortcut.vbs"
echo oLink.Description = "TezgahTakip v2.1.2 - AI Güçlü Fabrika Bakım Sistemi" >> "%TEMP%\shortcut.vbs"
echo oLink.Save >> "%TEMP%\shortcut.vbs"
cscript "%TEMP%\shortcut.vbs" >nul
del "%TEMP%\shortcut.vbs"

REM Başlat menüsü kısayolu
echo 📋 Başlat menüsü kısayolu oluşturuluyor...
set "STARTMENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\startmenu.vbs"
echo sLinkFile = "%STARTMENU%\TezgahTakip v2.1.2.lnk" >> "%TEMP%\startmenu.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\startmenu.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\TezgahTakip_v2.1.2.exe" >> "%TEMP%\startmenu.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\startmenu.vbs"
echo oLink.Description = "TezgahTakip v2.1.2 - AI Güçlü Fabrika Bakım Sistemi" >> "%TEMP%\startmenu.vbs"
echo oLink.Save >> "%TEMP%\startmenu.vbs"
cscript "%TEMP%\startmenu.vbs" >nul
del "%TEMP%\startmenu.vbs"

echo.
echo ✅ Kurulum tamamlandı!
echo 📁 Kurulum dizini: %INSTALL_DIR%
echo 🔗 Masaüstü kısayolu oluşturuldu
echo 📋 Başlat menüsü kısayolu oluşturuldu
echo.
echo 🎉 TezgahTakip v2.1.2 kullanıma hazır!
echo 💾 Otomatik yedekleme sistemi aktif olacak
echo.
pause
