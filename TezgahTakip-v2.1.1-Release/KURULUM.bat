@echo off
chcp 65001 >nul
title TezgahTakip v2.1.1 Kurulum

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    TezgahTakip v2.1.1                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                      Kurulum Programı                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set INSTALL_DIR=%USERPROFILE%\Desktop\TezgahTakip_v2.1.1

echo 📁 Kurulum dizini: %INSTALL_DIR%
echo.

set /p CONFIRM="Masaüstüne kurmak istiyor musunuz? (E/H): "
if /i not "%CONFIRM%"=="E" (
    echo Kurulum iptal edildi.
    pause
    exit /b 0
)

echo.
echo 🔄 Kurulum başlatılıyor...

REM Kurulum dizini oluştur
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Dosyaları kopyala
echo    📋 Dosyalar kopyalanıyor...
copy "TezgahTakip_v2.1.1.exe" "%INSTALL_DIR%\" >nul 2>&1
copy "Baslat.bat" "%INSTALL_DIR%\" >nul 2>&1
copy "README.txt" "%INSTALL_DIR%\" >nul 2>&1
if exist "config.json" copy "config.json" "%INSTALL_DIR%\" >nul 2>&1
if exist "settings.json" copy "settings.json" "%INSTALL_DIR%\" >nul 2>&1

REM Masaüstü kısayolu oluştur
echo    🖥️  Masaüstü kısayolu oluşturuluyor...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\TezgahTakip v2.1.1.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\TezgahTakip_v2.1.1.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ✅ KURULUM TAMAMLANDI                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 TezgahTakip v2.1.1 başarıyla kuruldu!
echo.
echo 📍 Kurulum Konumu: %INSTALL_DIR%
echo 🖥️  Masaüstü kısayolu oluşturuldu
echo.
echo 🚀 Başlatma Seçenekleri:
echo    • Masaüstündeki kısayola çift tıklayın
echo    • %INSTALL_DIR%\Baslat.bat dosyasını çalıştırın
echo    • %INSTALL_DIR%\TezgahTakip_v2.1.1.exe dosyasını çalıştırın
echo.

set /p START="Uygulamayı şimdi başlatmak istiyor musunuz? (E/H): "
if /i "%START%"=="E" (
    start "" "%INSTALL_DIR%\TezgahTakip_v2.1.1.exe"
)

echo.
echo Kurulum tamamlandı. Bu pencereyi kapatabilirsiniz.
pause >nul
