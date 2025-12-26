#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Executable Builder
PyInstaller ile tek dosya executable oluşturur
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_spec_file():
    """PyInstaller spec dosyası oluştur"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Ana uygulama için analiz
main_a = Analysis(
    ['run_tezgah_takip.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('mtb_logo.png', '.'),
        ('mtb_logo.svg', '.'),
        ('config.json', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'sqlalchemy.dialects.sqlite',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
        ('mtb_logo.png', '.'),
        ('auto_updater.py', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'requests',
        'packaging.version',
    ],
    hookspath=[],
    hooksconfig={},
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
    name='TezgahTakip',
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
    icon='mtb_logo.png' if os.path.exists('mtb_logo.png') else None,
)

# Launcher EXE
launcher_exe = EXE(
    launcher_pyz,
    launcher_a.scripts,
    launcher_a.binaries,
    launcher_a.zipfiles,
    launcher_a.datas,
    [],
    name='TezgahTakip_Launcher',
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
    icon='mtb_logo.png' if os.path.exists('mtb_logo.png') else None,
)
'''
    
    with open('tezgah_takip.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Spec dosyası oluşturuldu: tezgah_takip.spec")

def install_requirements():
    """Gerekli paketleri yükle"""
    print("📦 Gerekli paketler yükleniyor...")
    
    requirements = [
        'PyQt5>=5.15.0',
        'SQLAlchemy>=2.0.0',
        'requests>=2.25.0',
        'packaging>=21.0',
        'pyinstaller>=5.0.0',
    ]
    
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
            print(f"✅ {req} yüklendi")
        except subprocess.CalledProcessError as e:
            print(f"❌ {req} yüklenemedi: {e}")
            return False
    
    return True

def build_executable():
    """Executable dosyaları oluştur"""
    print("🔨 Executable dosyalar oluşturuluyor...")
    
    try:
        # PyInstaller ile build
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'tezgah_takip.spec'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build başarılı!")
            print("📁 Dosyalar dist/ klasöründe oluşturuldu")
            return True
        else:
            print(f"❌ Build hatası:\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build hatası: {e}")
        return False

def create_installer():
    """Basit installer oluştur"""
    installer_content = '''@echo off
echo ========================================
echo    TezgahTakip Kurulum Programi
echo ========================================
echo.

REM Kurulum dizini
set INSTALL_DIR=%PROGRAMFILES%\\TezgahTakip

echo Kurulum dizini: %INSTALL_DIR%
echo.

REM Dizin oluştur
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Dosyaları kopyala
echo Dosyalar kopyalaniyor...
copy "TezgahTakip_Launcher.exe" "%INSTALL_DIR%\\" >nul
copy "TezgahTakip.exe" "%INSTALL_DIR%\\" >nul

REM Masaüstü kısayolu oluştur
echo Masaustu kisayolu olusturuluyor...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\TezgahTakip.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\TezgahTakip_Launcher.exe'; $Shortcut.Save()"

REM Başlat menüsü kısayolu
echo Baslat menusu kisayolu olusturuluyor...
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\TezgahTakip" mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\TezgahTakip"
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\TezgahTakip\\TezgahTakip.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\TezgahTakip_Launcher.exe'; $Shortcut.Save()"

echo.
echo ========================================
echo   Kurulum tamamlandi!
echo ========================================
echo.
echo Masaustundeki TezgahTakip kisayoluna
echo tiklayarak uygulamayi baslatabilirsiniz.
echo.
pause
'''
    
    with open('dist/installer.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print("✅ Installer oluşturuldu: dist/installer.bat")

def create_portable_package():
    """Portable paket oluştur"""
    print("📦 Portable paket oluşturuluyor...")
    
    try:
        # Portable dizini oluştur
        portable_dir = Path("dist/TezgahTakip_Portable")
        portable_dir.mkdir(exist_ok=True)
        
        # Dosyaları kopyala
        files_to_copy = [
            "dist/TezgahTakip_Launcher.exe",
            "dist/TezgahTakip.exe",
            "config.json",
            "README.md"
        ]
        
        for file_path in files_to_copy:
            if os.path.exists(file_path):
                shutil.copy2(file_path, portable_dir)
        
        # Başlatma script'i oluştur
        start_script = '''@echo off
echo TezgahTakip baslatiliyor...
start TezgahTakip_Launcher.exe
'''
        
        with open(portable_dir / "Baslat.bat", 'w', encoding='utf-8') as f:
            f.write(start_script)
        
        print("✅ Portable paket oluşturuldu: dist/TezgahTakip_Portable/")
        return True
        
    except Exception as e:
        print(f"❌ Portable paket hatası: {e}")
        return False

def main():
    """Ana build fonksiyonu"""
    print("🏭 TezgahTakip Executable Builder")
    print("=" * 50)
    
    # Gerekli paketleri kontrol et ve yükle
    if not install_requirements():
        print("❌ Gerekli paketler yüklenemedi!")
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
    
    print("\n🎉 Build işlemi tamamlandı!")
    print("\n📁 Oluşturulan dosyalar:")
    print("   • dist/TezgahTakip_Launcher.exe (Ana launcher)")
    print("   • dist/TezgahTakip.exe (Ana uygulama)")
    print("   • dist/installer.bat (Kurulum programı)")
    print("   • dist/TezgahTakip_Portable/ (Portable versiyon)")
    
    print("\n🚀 Kullanım:")
    print("   1. Kurulum için: installer.bat çalıştırın")
    print("   2. Portable için: TezgahTakip_Portable klasörünü kopyalayın")
    print("   3. Direkt çalıştırma: TezgahTakip_Launcher.exe")
    
    return True

if __name__ == "__main__":
    main()