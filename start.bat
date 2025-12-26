@echo off
title TezgahTakip v2.0 - Başlatıcı
color 0A

echo.
echo ========================================
echo   TezgahTakip v2.0 Başlatılıyor...
echo   AI Güçlü Fabrika Bakım Yönetim Sistemi
echo ========================================
echo.

REM Python'un yüklü olup olmadığını kontrol et
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadı!
    echo Lütfen Python 3.7+ yükleyin: https://python.org
    pause
    exit /b 1
)

REM Gerekli dosyaların varlığını kontrol et
if not exist "tezgah_takip_app.py" (
    echo HATA: Ana uygulama dosyası bulunamadı!
    echo Lütfen tüm dosyaların aynı klasörde olduğundan emin olun.
    pause
    exit /b 1
)

REM Uygulamayı başlat
echo Python ile uygulama başlatılıyor...
echo.
python tezgah_takip_app.py

REM Hata durumunda bekle
if errorlevel 1 (
    echo.
    echo HATA: Uygulama başlatılamadı!
    echo.
    echo Olası çözümler:
    echo 1. Gerekli paketleri yükleyin: pip install -r requirements.txt
    echo 2. Python versiyonunu kontrol edin: python --version
    echo 3. Tüm dosyaların aynı klasörde olduğundan emin olun
    echo.
    pause
)