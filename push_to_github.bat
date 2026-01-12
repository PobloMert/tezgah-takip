@echo off
echo ========================================
echo    GitHub'a Push Islemi
echo ========================================
echo.

echo Kod GitHub'a yukleniyor...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Push basarili!
    echo ========================================
    echo.
    echo Ilk release olusturmak icin:
    echo   git tag v2.0.0
    echo   git push origin v2.0.0
    echo.
    echo Repository URL:
    echo   https://github.com/PobloMert/tezgah-takip
    echo.
) else (
    echo.
    echo ========================================
    echo   Push basarisiz!
    echo ========================================
    echo.
    echo Lutfen once GitHub'da repository olusturun:
    echo   1. https://github.com/PobloMert adresine gidin
    echo   2. "New repository" butonuna tiklayin
    echo   3. Repository adi: tezgah-takip
    echo   4. Public olarak ayarlayin
    echo   5. "Create repository" butonuna tiklayin
    echo.
)

pause