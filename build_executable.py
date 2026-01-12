#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip v2.1.3 - Executable Builder
PyInstaller ile profesyonel executable paket oluşturur
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

VERSION = "2.1.3"
APP_NAME = "TezgahTakip"

def create_spec_file():
    """PyInstaller spec dosyası oluştur"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# TezgahTakip v{VERSION} - PyInstaller Spec File

block_cipher = None

# Ana uygulama için analiz
main_a = Analysis(
    ['tezgah_takip_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('tezgah_logo.png', '.'),
        ('tezgah_icon.ico', '.'),
        ('tezgah_logo.svg', '.'),
        ('config.json', '.'),
        ('settings.json', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
        ('KURULUM_REHBERI.md', '.'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
        'requests.adapters',
        'urllib3.util.retry',
        'cryptography.fernet',
        'json',
        'sqlite3',
        'datetime',
        'logging.handlers',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Launcher için analiz
launcher_a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('tezgah_logo.png', '.'),
        ('tezgah_icon.ico', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'requests',
        'packaging.version',
        'subprocess',
        'threading',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Ana uygulama PYZ
main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)

# Launcher PYZ  
launcher_pyz = PYZ(launcher_a.pure, launcher_a.zipped_data, cipher=block_cipher)

# Ana uygulama EXE
main_exe = EXE(
    main_pyz,
    main_a.scripts,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='tezgah_icon.ico' if os.path.exists('tezgah_icon.ico') else None,
    version_file=None,
)

# Launcher EXE
launcher_exe = EXE(
    launcher_pyz,
    launcher_a.scripts,
    launcher_a.binaries,
    launcher_a.zipfiles,
    launcher_a.datas,
    [],
    name='{APP_NAME}_Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='tezgah_icon.ico' if os.path.exists('tezgah_icon.ico') else None,
    version_file=None,
)
'''
    
    with open('tezgah_takip.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Spec dosyası oluşturuldu: tezgah_takip.spec")

def check_requirements():
    """Gerekli dosyaları kontrol et"""
    print("🔍 Gerekli dosyalar kontrol ediliyor...")
    
    required_files = [
        'tezgah_takip_app.py',
        'main_window.py',
        'database_models.py',
        'launcher.py',
        'tezgah_icon.ico',
        'tezgah_logo.png',
        'config.json',
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

def install_build_requirements():
    """Build için gerekli paketleri yükle"""
    print("📦 Build paketleri yükleniyor...")
    
    build_requirements = [
        'pyinstaller>=5.0.0',
        'PyQt5>=5.15.0',
        'SQLAlchemy>=2.0.0',
        'requests>=2.25.0',
        'packaging>=21.0',
        'cryptography>=41.0.0',
    ]
    
    for req in build_requirements:
        try:
            print(f"   Installing {req}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', req
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {req}")
            else:
                print(f"   ❌ {req}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ {req}: {e}")
            return False
    
    return True

def clean_build_dirs():
    """Build dizinlerini temizle"""
    print("🧹 Eski build dosyaları temizleniyor...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   🗑️ {dir_name} temizlendi")
    
    # .spec dosyasını da temizle
    if os.path.exists('tezgah_takip.spec'):
        os.remove('tezgah_takip.spec')
        print("   🗑️ Eski spec dosyası temizlendi")

def build_executable():
    """Executable dosyaları oluştur"""
    print("🔨 Executable dosyalar oluşturuluyor...")
    print("   Bu işlem birkaç dakika sürebilir...")
    
    try:
        # PyInstaller ile build
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            '--log-level=WARN',
            'tezgah_takip.spec'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build başarılı!")
            
            # Dosya boyutlarını kontrol et
            exe_files = ['dist/TezgahTakip.exe', 'dist/TezgahTakip_Launcher.exe']
            for exe_file in exe_files:
                if os.path.exists(exe_file):
                    size_mb = os.path.getsize(exe_file) / (1024 * 1024)
                    print(f"   📁 {os.path.basename(exe_file)}: {size_mb:.1f} MB")
            
            return True
        else:
            print(f"❌ Build hatası:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build hatası: {e}")
        return False

def create_installer():
    """Gelişmiş installer oluştur"""
    installer_content = f'''@echo off
chcp 65001 >nul
title TezgahTakip v{VERSION} Kurulum Programı

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    TezgahTakip v{VERSION}                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ║                      Kurulum Programı                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Yönetici kontrolü
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Bu kurulum yönetici yetkileri gerektirir.
    echo    Lütfen "Yönetici olarak çalıştır" seçeneğini kullanın.
    echo.
    pause
    exit /b 1
)

REM Kurulum dizini
set INSTALL_DIR=%PROGRAMFILES%\\{APP_NAME}
set DATA_DIR=%APPDATA%\\{APP_NAME}

echo 📁 Kurulum dizini: %INSTALL_DIR%
echo 📁 Veri dizini: %DATA_DIR%
echo.

REM Onay al
set /p CONFIRM="Kuruluma devam etmek istiyor musunuz? (E/H): "
if /i not "%CONFIRM%"=="E" (
    echo Kurulum iptal edildi.
    pause
    exit /b 0
)

echo.
echo 🔄 Kurulum başlatılıyor...

REM Dizinleri oluştur
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

REM Ana dosyaları kopyala
echo    📋 Ana dosyalar kopyalanıyor...
copy "{APP_NAME}_Launcher.exe" "%INSTALL_DIR%\\" >nul 2>&1
copy "{APP_NAME}.exe" "%INSTALL_DIR%\\" >nul 2>&1

REM Konfigürasyon dosyalarını kopyala
if exist "config.json" copy "config.json" "%DATA_DIR%\\" >nul 2>&1
if exist "settings.json" copy "settings.json" "%DATA_DIR%\\" >nul 2>&1

REM Masaüstü kısayolu oluştur
echo    🖥️  Masaüstü kısayolu oluşturuluyor...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\{APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{APP_NAME}_Launcher.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\{APP_NAME}_Launcher.exe'; $Shortcut.Save()" >nul 2>&1

REM Başlat menüsü kısayolu
echo    📋 Başlat menüsü kısayolu oluşturuluyor...
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}" mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}\\{APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{APP_NAME}_Launcher.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\{APP_NAME}_Launcher.exe'; $Shortcut.Save()" >nul 2>&1

REM Kaldırma programı oluştur
echo    🗑️  Kaldırma programı oluşturuluyor...
(
echo @echo off
echo chcp 65001 ^>nul
echo title {APP_NAME} Kaldırma Programı
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    {APP_NAME} v{VERSION}                         ║
echo ║                     Kaldırma Programı                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo set /p CONFIRM="Uygulamayı kaldırmak istediğinizden emin misiniz? (E/H): "
echo if /i not "%%CONFIRM%%"=="E" (
echo     echo Kaldırma iptal edildi.
echo     pause
echo     exit /b 0
echo ^)
echo.
echo echo 🗑️  Uygulama kaldırılıyor...
echo.
echo REM Kısayolları sil
echo del "%%USERPROFILE%%\\Desktop\\{APP_NAME}.lnk" ^>nul 2^>^&1
echo rmdir /s /q "%%APPDATA%%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}" ^>nul 2^>^&1
echo.
echo REM Veri dizinini sil
echo rmdir /s /q "%%APPDATA%%\\{APP_NAME}" ^>nul 2^>^&1
echo.
echo REM Program dizinini sil
echo cd /d "%%TEMP%%"
echo rmdir /s /q "%INSTALL_DIR%" ^>nul 2^>^&1
echo.
echo echo ✅ {APP_NAME} başarıyla kaldırıldı.
echo pause
) > "%INSTALL_DIR%\\Uninstall.bat"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ✅ KURULUM TAMAMLANDI                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 {APP_NAME} v{VERSION} başarıyla kuruldu!
echo.
echo 📍 Kurulum Konumu: %INSTALL_DIR%
echo 📍 Veri Konumu: %DATA_DIR%
echo.
echo 🚀 Başlatma Seçenekleri:
echo    • Masaüstündeki kısayola çift tıklayın
echo    • Başlat menüsünden {APP_NAME} seçin
echo    • %INSTALL_DIR%\\{APP_NAME}_Launcher.exe dosyasını çalıştırın
echo.
echo 🗑️  Kaldırmak için: %INSTALL_DIR%\\Uninstall.bat dosyasını çalıştırın
echo.

set /p START="Uygulamayı şimdi başlatmak istiyor musunuz? (E/H): "
if /i "%START%"=="E" (
    start "" "%INSTALL_DIR%\\{APP_NAME}_Launcher.exe"
)

echo.
echo Kurulum tamamlandı. Bu pencereyi kapatabilirsiniz.
pause >nul
'''
    
    with open('dist/installer.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print("✅ Gelişmiş installer oluşturuldu: dist/installer.bat")

def create_portable_package():
    """Portable paket oluştur"""
    print("📦 Portable paket oluşturuluyor...")
    
    try:
        # Portable dizini oluştur
        portable_dir = Path(f"dist/{APP_NAME}_v{VERSION}_Portable")
        if portable_dir.exists():
            shutil.rmtree(portable_dir)
        portable_dir.mkdir(parents=True)
        
        # Ana dosyaları kopyala
        files_to_copy = [
            ("dist/TezgahTakip_Launcher.exe", "TezgahTakip_Launcher.exe"),
            ("dist/TezgahTakip.exe", "TezgahTakip.exe"),
            ("config.json", "config.json"),
            ("settings.json", "settings.json"),
            ("README.md", "README.md"),
        ]
        
        for src, dst in files_to_copy:
            if os.path.exists(src):
                shutil.copy2(src, portable_dir / dst)
        
        # Başlatma script'i oluştur
        start_script = f'''@echo off
chcp 65001 >nul
title {APP_NAME} v{VERSION} - Portable

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    {APP_NAME} v{VERSION}                         ║
echo ║                    Portable Sürüm                           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 {APP_NAME} başlatılıyor...
echo.

REM Launcher'ı başlat
if exist "{APP_NAME}_Launcher.exe" (
    start "" "{APP_NAME}_Launcher.exe"
) else (
    echo ❌ {APP_NAME}_Launcher.exe bulunamadı!
    echo.
    echo Lütfen şunları kontrol edin:
    echo • Tüm dosyaların aynı klasörde olduğunu
    echo • Antivirüs programının dosyaları engellemediğini
    echo.
    pause
)
'''
        
        with open(portable_dir / "Baslat.bat", 'w', encoding='utf-8') as f:
            f.write(start_script)
        
        # Portable bilgi dosyası oluştur
        info_content = f'''# {APP_NAME} v{VERSION} - Portable Sürüm

## Kullanım
1. "Baslat.bat" dosyasına çift tıklayın
2. Veya "{APP_NAME}_Launcher.exe" dosyasını direkt çalıştırın

## Özellikler
- Kurulum gerektirmez
- Tüm veriler bu klasörde saklanır
- USB bellek veya harici disk üzerinde çalışır
- Sistem kayıt defterini değiştirmez

## Sistem Gereksinimleri
- Windows 10/11 (64-bit)
- .NET Framework 4.7.2 veya üzeri
- En az 4 GB RAM
- En az 500 MB boş disk alanı

## Destek
- GitHub: https://github.com/PobloMert/tezgah-takip
- Versiyon: {VERSION}
- Oluşturulma: {datetime.now().strftime("%d.%m.%Y %H:%M")}

## Lisans
Bu yazılım MIT lisansı altında dağıtılmaktadır.
'''
        
        with open(portable_dir / "PORTABLE_BILGI.md", 'w', encoding='utf-8') as f:
            f.write(info_content)
        
        print(f"✅ Portable paket oluşturuldu: {portable_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Portable paket hatası: {e}")
        return False

def create_release_package():
    """Release paketi oluştur"""
    print("📦 Release paketi oluşturuluyor...")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        release_name = f"{APP_NAME}-v{VERSION}-Release"
        
        # ZIP dosyası oluştur
        with zipfile.ZipFile(f"dist/{release_name}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Executable dosyalar
            zipf.write("dist/TezgahTakip_Launcher.exe", "TezgahTakip_Launcher.exe")
            zipf.write("dist/TezgahTakip.exe", "TezgahTakip.exe")
            zipf.write("dist/installer.bat", "installer.bat")
            
            # Dokümantasyon
            if os.path.exists("README.md"):
                zipf.write("README.md", "README.md")
            if os.path.exists("KURULUM_REHBERI.md"):
                zipf.write("KURULUM_REHBERI.md", "KURULUM_REHBERI.md")
            
            # Konfigürasyon
            if os.path.exists("config.json"):
                zipf.write("config.json", "config.json")
            if os.path.exists("settings.json"):
                zipf.write("settings.json", "settings.json")
        
        print(f"✅ Release paketi oluşturuldu: dist/{release_name}.zip")
        return True
        
    except Exception as e:
        print(f"❌ Release paketi hatası: {e}")
        return False

def print_build_summary():
    """Build özeti yazdır"""
    print("\n" + "="*70)
    print(f"🎉 {APP_NAME} v{VERSION} BUILD TAMAMLANDI!")
    print("="*70)
    
    print("\n📁 Oluşturulan Dosyalar:")
    
    # Executable dosyalar
    exe_files = [
        ("dist/TezgahTakip_Launcher.exe", "Ana Launcher"),
        ("dist/TezgahTakip.exe", "Ana Uygulama"),
        ("dist/installer.bat", "Kurulum Programı"),
    ]
    
    for file_path, description in exe_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"   ✅ {description}: {os.path.basename(file_path)} ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {description}: {os.path.basename(file_path)} (BULUNAMADI)")
    
    # Paketler
    packages = [
        f"dist/{APP_NAME}_v{VERSION}_Portable/",
        f"dist/{APP_NAME}-v{VERSION}-Release.zip"
    ]
    
    print("\n📦 Paketler:")
    for package in packages:
        if os.path.exists(package):
            if package.endswith('/'):
                print(f"   ✅ Portable Paket: {os.path.basename(package.rstrip('/'))}")
            else:
                size_mb = os.path.getsize(package) / (1024 * 1024)
                print(f"   ✅ Release Paketi: {os.path.basename(package)} ({size_mb:.1f} MB)")
    
    print("\n🚀 Kullanım Seçenekleri:")
    print("   1. 💻 Kurulum: installer.bat dosyasını çalıştırın")
    print("   2. 📱 Portable: Portable klasörünü istediğiniz yere kopyalayın")
    print("   3. 🔗 Direkt: TezgahTakip_Launcher.exe dosyasını çalıştırın")
    
    print("\n📋 Dağıtım:")
    print("   • GitHub Release için ZIP dosyasını kullanın")
    print("   • Son kullanıcılar için installer.bat önerilir")
    print("   • USB/Portable kullanım için Portable klasörünü kullanın")
    
    print("\n✨ Build başarıyla tamamlandı!")

def main():
    """Ana build fonksiyonu"""
    print("🏭 TezgahTakip v{VERSION} - Professional Build System")
    print("=" * 70)
    
    # Gerekli dosyaları kontrol et
    if not check_requirements():
        print("❌ Gerekli dosyalar eksik!")
        return False
    
    # Build dizinlerini temizle
    clean_build_dirs()
    
    # Build paketlerini yükle
    if not install_build_requirements():
        print("❌ Build paketleri yüklenemedi!")
        return False
    
    # Spec dosyası oluştur
    create_spec_file()
    
    # Build
    if not build_executable():
        print("❌ Build başarısız!")
        return False
    
    # Installer oluştur
    create_installer()
    
    # Portable paket oluştur
    create_portable_package()
    
    # Release paketi oluştur
    create_release_package()
    
    # Özet yazdır
    print_build_summary()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Build işlemi başarısız!")
        sys.exit(1)
    else:
        print(f"\n🎉 {APP_NAME} v{VERSION} hazır!")
        sys.exit(0)