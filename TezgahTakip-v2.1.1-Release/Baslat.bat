@echo off
chcp 65001 >nul
title TezgahTakip v2.1.1

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    TezgahTakip v2.1.1                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Uygulama başlatılıyor...

"TezgahTakip_v2.1.1.exe"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Uygulama başlatılamadı!
    echo Lütfen şunları kontrol edin:
    echo • Antivirüs programının uygulamayı engellemediğini
    echo • Gerekli .NET Framework'ün yüklü olduğunu
    echo • Yönetici yetkilerinizi
    echo.
    pause
)
