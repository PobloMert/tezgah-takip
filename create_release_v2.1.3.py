#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip v2.1.3 - Release Creation Script
Gelişmiş Veritabanı Erişim Sistemi ile birlikte release oluşturma
"""

import os
import sys
import shutil
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path

VERSION = "2.1.3"
APP_NAME = "TezgahTakip"
RELEASE_DATE = datetime.now().strftime("%d.%m.%Y")

def print_header():
    """Release başlığını yazdır"""
    print("🎉" + "="*60 + "🎉")
    print(f"🏭 {APP_NAME} v{VERSION} - Release Creation")
    print("💾 Gelişmiş Veritabanı Erişim Sistemi")
    print(f"📅 {RELEASE_DATE}")
    print("🎉" + "="*60 + "🎉")
    print()

def check_requirements():
    """Gerekli dosyaların varlığını kontrol et"""
    print("🔍 Gerekli dosyalar kontrol ediliyor...")
    
    required_files = [
        "tezgah_takip_app.py",
        "main_window.py", 
        "enhanced_database_manager.py",
        "database_models.py",
        "gemini_ai.py",
        "config.json",
        "requirements.txt",
        "tezgah_icon.ico"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Eksik dosyalar: {', '.join(missing_files)}")
        return False
    
    print("✅ Tüm gerekli dosyalar mevcut")
    return True

def clean_build_dirs():
    """Build klasörlerini temizle"""
    print("🧹 Build klasörleri temizleniyor...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  🗑️ {dir_name} temizlendi")
    
    print("✅ Build klasörleri temizlendi")

def create_executable():
    """PyInstaller ile executable oluştur"""
    print("🔨 Executable oluşturuluyor...")
    
    # PyInstaller komutu
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", f"{APP_NAME}_v{VERSION}",
        "--icon", "tezgah_icon.ico",
        "--add-data", "tezgah_logo.png;.",
        "--add-data", "mtb_logo.png;.",
        "--add-data", "config.json;.",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui", 
        "--hidden-import", "PyQt5.QtWidgets",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "requests",
        "--collect-all", "PyQt5",
        "tezgah_takip_app.py"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Executable başarıyla oluşturuldu")
        
        # Dosya boyutunu kontrol et
        exe_path = f"dist/{APP_NAME}_v{VERSION}.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 {APP_NAME}_v{VERSION}.exe: {size_mb:.1f} MB")
            return True
        else:
            print("❌ Executable dosyası bulunamadı")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller hatası: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def create_portable_version():
    """Portable versiyon oluştur"""
    print("📦 Portable versiyon oluşturuluyor...")
    
    portable_dir = f"{APP_NAME}_v{VERSION}_Portable"
    
    # Portable klasörü oluştur
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)
    
    # Gerekli dosyaları kopyala
    files_to_copy = [
        f"dist/{APP_NAME}_v{VERSION}.exe",
        "config.json",
        "requirements.txt",
        "README.md",
        "tezgah_icon.ico"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, portable_dir)
            print(f"  📄 {file} kopyalandı")
    
    # Başlatma script'i oluştur
    start_script = f'''@echo off
chcp 65001 >nul
title {APP_NAME} v{VERSION} - Portable

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    {APP_NAME} v{VERSION}                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                💾 Gelişmiş Veritabanı Erişim Sistemi        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Portable sürüm başlatılıyor...
echo 💾 Gelişmiş veritabanı erişim sistemi aktif
echo.

"{APP_NAME}_v{VERSION}.exe"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Uygulama hata ile kapandı!
    echo 📋 Hata kodu: %errorlevel%
    echo.
    pause
)
'''
    
    with open(f"{portable_dir}/Baslat.bat", "w", encoding="utf-8") as f:
        f.write(start_script)
    
    print(f"✅ Portable versiyon oluşturuldu: {portable_dir}/")
    return portable_dir

def create_release_package():
    """Release paketi oluştur"""
    print("📦 Release paketi oluşturuluyor...")
    
    release_dir = f"{APP_NAME}-v{VERSION}-Release"
    
    # Release klasörü oluştur
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # Ana dosyaları kopyala
    main_files = [
        f"dist/{APP_NAME}_v{VERSION}.exe",
        "README.md",
        "requirements.txt",
        "config.json"
    ]
    
    for file in main_files:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
    
    # Portable versiyonu da ekle
    portable_dir = create_portable_version()
    if os.path.exists(portable_dir):
        shutil.move(portable_dir, f"{release_dir}/{portable_dir}")
    
    # Kurulum script'i oluştur
    installer_script = f'''@echo off
chcp 65001 >nul
title {APP_NAME} v{VERSION} - Kurulum

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    {APP_NAME} v{VERSION} KURULUM                 ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                💾 Gelişmiş Veritabanı Erişim Sistemi        ║
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
set "INSTALL_DIR=%ProgramFiles%\\{APP_NAME}"
echo 📁 Kurulum dizini: %INSTALL_DIR%

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo ✅ Kurulum klasörü oluşturuldu
)

echo 📄 Dosyalar kopyalanıyor...
copy "{APP_NAME}_v{VERSION}.exe" "%INSTALL_DIR%\\" >nul
copy "config.json" "%INSTALL_DIR%\\" >nul
copy "README.md" "%INSTALL_DIR%\\" >nul

REM Masaüstü kısayolu oluştur
echo 🔗 Masaüstü kısayolu oluşturuluyor...
set "DESKTOP=%USERPROFILE%\\Desktop"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\\shortcut.vbs"
echo sLinkFile = "%DESKTOP%\\{APP_NAME} v{VERSION}.lnk" >> "%TEMP%\\shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\\shortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\\{APP_NAME}_v{VERSION}.exe" >> "%TEMP%\\shortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\\shortcut.vbs"
echo oLink.Description = "{APP_NAME} v{VERSION} - AI Güçlü Fabrika Bakım Sistemi" >> "%TEMP%\\shortcut.vbs"
echo oLink.Save >> "%TEMP%\\shortcut.vbs"
cscript "%TEMP%\\shortcut.vbs" >nul
del "%TEMP%\\shortcut.vbs"

REM Başlat menüsü kısayolu
echo 📋 Başlat menüsü kısayolu oluşturuluyor...
set "STARTMENU=%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\\startmenu.vbs"
echo sLinkFile = "%STARTMENU%\\{APP_NAME} v{VERSION}.lnk" >> "%TEMP%\\startmenu.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\\startmenu.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\\{APP_NAME}_v{VERSION}.exe" >> "%TEMP%\\startmenu.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\\startmenu.vbs"
echo oLink.Description = "{APP_NAME} v{VERSION} - AI Güçlü Fabrika Bakım Sistemi" >> "%TEMP%\\startmenu.vbs"
echo oLink.Save >> "%TEMP%\\startmenu.vbs"
cscript "%TEMP%\\startmenu.vbs" >nul
del "%TEMP%\\startmenu.vbs"

echo.
echo ✅ Kurulum tamamlandı!
echo 📁 Kurulum dizini: %INSTALL_DIR%
echo 🔗 Masaüstü kısayolu oluşturuldu
echo 📋 Başlat menüsü kısayolu oluşturuldu
echo.
echo 🎉 {APP_NAME} v{VERSION} kullanıma hazır!
echo 💾 Gelişmiş veritabanı erişim sistemi aktif olacak
echo.
pause
'''
    
    with open(f"{release_dir}/installer.bat", "w", encoding="utf-8") as f:
        f.write(installer_script)
    
    print(f"✅ Release paketi oluşturuldu: {release_dir}/")
    return release_dir

def create_zip_packages():
    """ZIP paketleri oluştur"""
    print("🗜️ ZIP paketleri oluşturuluyor...")
    
    # Release paketi ZIP'i
    release_dir = f"{APP_NAME}-v{VERSION}-Release"
    if os.path.exists(release_dir):
        zip_name = f"{release_dir}.zip"
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(release_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, release_dir)
                    zipf.write(file_path, arc_name)
        
        # ZIP boyutunu kontrol et
        zip_size = os.path.getsize(zip_name) / (1024 * 1024)
        print(f"📦 {zip_name}: {zip_size:.1f} MB")
    
    # Tek executable ZIP'i
    exe_zip_name = f"{APP_NAME}-v{VERSION}-Windows.zip"
    with zipfile.ZipFile(exe_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        exe_path = f"dist/{APP_NAME}_v{VERSION}.exe"
        if os.path.exists(exe_path):
            zipf.write(exe_path, f"{APP_NAME}_v{VERSION}.exe")
        
        # Temel dosyaları ekle
        basic_files = ["README.md", "config.json"]
        for file in basic_files:
            if os.path.exists(file):
                zipf.write(file)
    
    exe_zip_size = os.path.getsize(exe_zip_name) / (1024 * 1024)
    print(f"📦 {exe_zip_name}: {exe_zip_size:.1f} MB")
    
    print("✅ ZIP paketleri oluşturuldu")

def show_summary():
    """Özet bilgileri göster"""
    print("\n" + "🎊"*60)
    print(f"🎉 {APP_NAME} v{VERSION} Release Tamamlandı!")
    print("🎊"*60)
    
    print(f"\n📦 Oluşturulan Dosyalar:")
    
    # Dosya listesi
    files_to_check = [
        f"dist/{APP_NAME}_v{VERSION}.exe",
        f"{APP_NAME}-v{VERSION}-Release.zip",
        f"{APP_NAME}-v{VERSION}-Windows.zip",
        f"{APP_NAME}-v{VERSION}-Release/",
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            if os.path.isfile(file):
                size = os.path.getsize(file) / (1024 * 1024)
                print(f"  ✅ {file} ({size:.1f} MB)")
            else:
                print(f"  ✅ {file} (klasör)")
        else:
            print(f"  ❌ {file} (bulunamadı)")
    
    print(f"\n🚀 Yeni Özellikler:")
    print("  💾 Enhanced Database Manager")
    print("  🔄 Otomatik fallback sistemi")
    print("  🔒 Gelişmiş güvenlik sistemi")
    print("  🤖 Gemini 2.0 Flash AI desteği")
    print("  ⚡ Performans optimizasyonları")
    
    print(f"\n📋 Sonraki Adımlar:")
    print("  1. GitHub'a commit ve push yapın")
    print("  2. GitHub Release oluşturun")
    print("  3. ZIP dosyalarını yükleyin")
    print("  4. Release notes'u ekleyin")
    
    print(f"\n🔗 GitHub Release Komutu:")
    print(f"  git tag v{VERSION}")
    print(f"  git push origin v{VERSION}")
    
    print("\n🎊 Release hazır! GitHub'ta paylaşabilirsiniz! 🎊")

def main():
    """Ana fonksiyon"""
    print_header()
    
    try:
        # Adım 1: Gereksinimler
        if not check_requirements():
            return 1
        
        # Adım 2: Temizlik
        clean_build_dirs()
        
        # Adım 3: Executable oluştur
        if not create_executable():
            return 1
        
        # Adım 4: Release paketi oluştur
        create_release_package()
        
        # Adım 5: ZIP paketleri oluştur
        create_zip_packages()
        
        # Adım 6: Özet
        show_summary()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Release oluşturma hatası: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)