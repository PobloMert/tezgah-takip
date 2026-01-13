@echo off
chcp 65001 >nul
title TezgahTakip v2.1.3 - Portable

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    TezgahTakip v2.1.3                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                💾 Gelişmiş Veritabanı Erişim Sistemi        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Portable sürüm başlatılıyor...
echo 💾 Gelişmiş veritabanı erişim sistemi aktif
echo.

"TezgahTakip_v2.1.3.exe"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Uygulama hata ile kapandı!
    echo 📋 Hata kodu: %errorlevel%
    echo.
    pause
)
