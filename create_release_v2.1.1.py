#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip v2.1.1 - Release Package Creator
"""

import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

VERSION = "2.1.1"
APP_NAME = "TezgahTakip"

def create_release_package():
    """v2.1.1 Release paketi oluştur"""
    print(f"📦 {APP_NAME} v{VERSION} Release Paketi Oluşturuluyor...")
    print("=" * 60)
    
    # Release klasörü oluştur
    release_dir = Path(f"{APP_NAME}-v{VERSION}-Release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    print("📁 Release klasörü oluşturuldu")
    
    # Ana dosyaları kopyala
    files_to_copy = [
        ("dist/TezgahTakip_v2.1.1.exe", "TezgahTakip_v2.1.1.exe"),
        ("dist/Baslat.bat", "Baslat.bat"),
        ("dist/README.txt", "README.txt"),
        ("config.json", "config.json"),
        ("settings.json", "settings.json"),
        ("README.md", "README.md"),
        ("KURULUM_REHBERI.md", "KURULUM_REHBERI.md"),
        ("CHANGELOG_v2.1.1.md", "CHANGELOG_v2.1.1.md"),
        ("RELEASE_NOTES_v2.1.1.md", "RELEASE_NOTES_v2.1.1.md"),
    ]
    
    copied_files = []
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, release_dir / dst)
            copied_files.append(dst)
            print(f"   ✅ {dst}")
        else:
            print(f"   ⚠️ {dst} (dosya bulunamadı)")
    
    # Kurulum script'i oluştur
    installer_content = f'''@echo off
chcp 65001 >nul
title {APP_NAME} v{VERSION} Kurulum

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    {APP_NAME} v{VERSION}                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                      Kurulum Programı                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set INSTALL_DIR=%USERPROFILE%\\Desktop\\{APP_NAME}_v{VERSION}

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
copy "{APP_NAME}_v{VERSION}.exe" "%INSTALL_DIR%\\" >nul 2>&1
copy "Baslat.bat" "%INSTALL_DIR%\\" >nul 2>&1
copy "README.txt" "%INSTALL_DIR%\\" >nul 2>&1
if exist "config.json" copy "config.json" "%INSTALL_DIR%\\" >nul 2>&1
if exist "settings.json" copy "settings.json" "%INSTALL_DIR%\\" >nul 2>&1

REM Masaüstü kısayolu oluştur
echo    🖥️  Masaüstü kısayolu oluşturuluyor...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\{APP_NAME} v{VERSION}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{APP_NAME}_v{VERSION}.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ✅ KURULUM TAMAMLANDI                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 {APP_NAME} v{VERSION} başarıyla kuruldu!
echo.
echo 📍 Kurulum Konumu: %INSTALL_DIR%
echo 🖥️  Masaüstü kısayolu oluşturuldu
echo.
echo 🚀 Başlatma Seçenekleri:
echo    • Masaüstündeki kısayola çift tıklayın
echo    • %INSTALL_DIR%\\Baslat.bat dosyasını çalıştırın
echo    • %INSTALL_DIR%\\{APP_NAME}_v{VERSION}.exe dosyasını çalıştırın
echo.

set /p START="Uygulamayı şimdi başlatmak istiyor musunuz? (E/H): "
if /i "%START%"=="E" (
    start "" "%INSTALL_DIR%\\{APP_NAME}_v{VERSION}.exe"
)

echo.
echo Kurulum tamamlandı. Bu pencereyi kapatabilirsiniz.
pause >nul
'''
    
    with open(release_dir / "KURULUM.bat", 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    copied_files.append("KURULUM.bat")
    print("   ✅ KURULUM.bat")
    
    # Release notları oluştur
    release_notes = f'''# {APP_NAME} v{VERSION} - Release Notes

## 🎉 Yeni Özellikler

### ✅ Düzeltilen Hatalar
- DateTime import hataları düzeltildi
- Geçersiz karakter hataları giderildi
- Database session yönetimi iyileştirildi
- JSON import/export stabilize edildi

### 🚀 Performans İyileştirmeleri
- Uygulama başlatma hızı artırıldı
- Bellek kullanımı optimize edildi
- UI responsiveness iyileştirildi

### 🔧 Teknik Güncellemeler
- PyQt5 uyumluluğu artırıldı
- SQLAlchemy 2.0 desteği
- Modern Python 3.11+ uyumluluğu

## 📋 Sistem Gereksinimleri
- Windows 10/11 (64-bit)
- En az 4 GB RAM
- En az 500 MB boş disk alanı
- .NET Framework 4.7.2 veya üzeri

## 🚀 Kurulum
1. KURULUM.bat dosyasını çalıştırın
2. Kurulum talimatlarını takip edin
3. Masaüstündeki kısayolu kullanın

## 📁 Dosya Boyutu
- Ana executable: ~110 MB
- Toplam kurulum: ~120 MB

## 🔗 Destek
- GitHub: https://github.com/PobloMert/tezgah-takip
- Versiyon: {VERSION}
- Build Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}

## 📝 Lisans
MIT License - Açık kaynak yazılım

---
© 2024-2025 TezgahTakip - AI Güçlü Fabrika Bakım Yönetim Sistemi
'''
    
    with open(release_dir / "RELEASE_NOTES.txt", 'w', encoding='utf-8') as f:
        f.write(release_notes)
    
    copied_files.append("RELEASE_NOTES.txt")
    print("   ✅ RELEASE_NOTES.txt")
    
    # ZIP paketi oluştur
    zip_name = f"{APP_NAME}-v{VERSION}-Windows.zip"
    print(f"\n📦 ZIP paketi oluşturuluyor: {zip_name}")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for file_name in copied_files:
            file_path = release_dir / file_name
            if file_path.exists():
                zipf.write(file_path, file_name)
                size_kb = file_path.stat().st_size / 1024
                print(f"   📄 {file_name} ({size_kb:.1f} KB)")
    
    # ZIP boyutunu kontrol et
    if os.path.exists(zip_name):
        zip_size_mb = os.path.getsize(zip_name) / (1024 * 1024)
        print(f"\n✅ ZIP paketi oluşturuldu: {zip_name} ({zip_size_mb:.1f} MB)")
    
    # Özet
    print("\n" + "="*60)
    print(f"🎉 {APP_NAME} v{VERSION} RELEASE HAZIR!")
    print("="*60)
    
    print(f"\n📁 Release Klasörü: {release_dir}")
    print(f"📦 ZIP Paketi: {zip_name}")
    
    print(f"\n📋 İçerik ({len(copied_files)} dosya):")
    for file_name in copied_files:
        print(f"   • {file_name}")
    
    print(f"\n🚀 Dağıtım:")
    print(f"   • Son kullanıcılar için: {zip_name}")
    print(f"   • GitHub Release için: {zip_name}")
    print(f"   • Direkt kurulum için: {release_dir}/KURULUM.bat")
    
    print(f"\n✨ Release v{VERSION} başarıyla oluşturuldu!")
    
    return True

if __name__ == "__main__":
    create_release_package()