#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Build Configuration
EXE ve Setup dosyası oluşturma konfigürasyonu
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List

class BuildConfig:
    """Build konfigürasyonu"""
    
    # Temel Bilgiler
    APP_NAME = "TezgahTakip"
    APP_VERSION = "2.3.1"
    APP_COMPANY = "TezgahTakip"
    APP_DESCRIPTION = "🏭 AI Güçlü Fabrika Bakım Yönetim Sistemi"
    APP_AUTHOR = "PobloMert"
    APP_WEBSITE = "https://github.com/PobloMert/tezgah-takip"
    
    # Kurulum Ayarları
    INSTALL_DIR = "TezgahTakip"
    INSTALL_SIZE = "500"  # MB (Yaklaşık boyut)
    
    # Ana Giriş Noktaları
    MAIN_ENTRY = "tezgah_takip_app.py"
    LAUNCHER_ENTRY = "launcher.py"
    
    # Dahil edilecek Dosyalar
    INCLUDE_FILES = [
        "tezgah_takip_app.py",
        "main_window.py",
        "launcher.py",
        "api_key_manager.py",
        "gemini_ai.py",
        "database_models.py",
        "database_manager.py",
        "auto_updater.py",
        "update_compatibility_system.py",
        "report_generator.py",
        "notification_manager.py",
        "advanced_dashboard_widgets.py",
        "run_tezgah_takip.py",
        # Veri dosyaları
        "assets",
        "resources",
        "data",
        "config",
        "logs",
    ]
    
    # Gizli İmportlar (PyInstaller tarafından otomatik bulunmayan modüller)
    HIDDEN_IMPORTS = [
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtPrintSupport",
        "SQLAlchemy",
        "pandas",
        "openpyxl",
        "xlsxwriter",
        "reportlab",
        "matplotlib",
        "seaborn",
        "requests",
        "cryptography",
        "colorlog",
        "psutil",
        "py7zr",
        "babel",
        "pyyaml",
    ]
    
    # Hariç Tutulacak Modüller (Boyutu azaltmak için)
    EXCLUDE_MODULES = [
        "pytest",
        "black",
        "flake8",
        "mypy",
        "sphinx",
        "bandit",
        "memory_profiler",
        "line_profiler",
    ]
    
    # PyInstaller Ayarları
    PYINSTALLER_OPTIONS = {
        "one_file": True,  # Tek dosya olarak paketlensin
        "windowed": True,  # Console penceresini gizle
        "add_data": [],  # Ek veri dosyaları
        "collect_all": [
            "PyQt5",
            "babel",
        ],
    }
    
    # İkon Ayarları
    ICON_PATH = "assets/app_icon.ico"  # Varsa
    ICON_URL = "https://github.com/PobloMert/tezgah-takip/raw/main/assets/app_icon.ico"
    
    # Yapı Dosyaları
    BUILD_DIR = "build"
    DIST_DIR = "dist"
    BUILD_TEMP_DIR = "build_temp"
    SPEC_FILE = "tezgah_takip.spec"
    
    @staticmethod
    def get_pyinstaller_command() -> str:
        """PyInstaller komutunu oluştur"""
        cmd = ["pyinstaller"]
        
        # Ana dosya
        cmd.append(BuildConfig.MAIN_ENTRY)
        
        # Temel ayarlar
        cmd.append("--noconfirm")
        cmd.append("--clean")
        cmd.append("-y")
        
        # Tek dosya olarak
        cmd.append("-F")
        
        # GUI uygulaması
        cmd.append("-w")
        
        # Çıktı dizini
        cmd.extend(["-d", BuildConfig.BUILD_DIR])
        cmd.extend(["-p", BuildConfig DIST_DIR])
        
        # Ad
        cmd.extend(["-n", BuildConfig.APP_NAME])
        
        # İkon (varsa)
        if os.path.exists(BuildConfig.ICON_PATH):
            cmd.extend(["-i", BuildConfig.ICON_PATH])
        
        # Gizli importlar
        for module in BuildConfig.HIDDEN_IMPORTS:
            cmd.extend(["--hidden-import", module])
        
        # Hariç modüller
        for module in BuildConfig.EXCLUDE_MODULES:
            cmd.extend(["--exclude-module", module])
        
        # Sürüm bilgisi (Windows için)
        cmd.extend(["--version-file", "version_info.txt"])
        
        return " ".join(cmd)
    
    @staticmethod
    def get_inno_setup_config() -> str:
        """Inno Setup yapılandırması oluştur"""
        
        return f"""
[Setup]
AppName={BuildConfig.APP_NAME}
AppVersion={BuildConfig.APP_VERSION}
AppPublisher={BuildConfig.APP_COMPANY}
AppPublisherURL={BuildConfig.APP_WEBSITE}
AppSupportURL={BuildConfig.APP_WEBSITE}
DefaultDirName={{autopf}}\\{BuildConfig.INSTALL_DIR}
DefaultGroupName={BuildConfig.APP_NAME}
AllowNoIcons=yes
LicenseFile=LICENSE
UninstallDisplayIcon={{app}}\\{BuildConfig.APP_NAME}.exe
OutputDir=.\\dist
OutputBaseFilename={BuildConfig.APP_NAME}_Setup_v{BuildConfig.APP_VERSION}
SetupIconFile={BuildConfig.ICON_PATH}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
ShowLanguageDialog=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunch"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
Source: "dist\\{BuildConfig.APP_NAME}.exe"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{BuildConfig.APP_NAME}"; Filename: "{{app}}\\{BuildConfig.APP_NAME}.exe"
Name: "{{group}}\\{{cm:UninstallProgram,{BuildConfig.APP_NAME}}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{BuildConfig.APP_NAME}"; Filename: "{{app}}\\{BuildConfig.APP_NAME}.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{BuildConfig.APP_NAME}"; Filename: "{{app}}\\{BuildConfig.APP_NAME}.exe"; Tasks: quicklaunch

[Run]
Filename: "{{app}}\\{BuildConfig.APP_NAME}.exe"; Description: "{{cm:LaunchProgram,{BuildConfig.APP_NAME}}}"; Flags: nowait postinstall skipifsilent
"""

    @staticmethod
    def to_dict() -> Dict:
        """Konfigürasyonu dict'e dönüştür"""
        return {
            "app_name": BuildConfig.APP_NAME,
            "app_version": BuildConfig.APP_VERSION,
            "app_description": BuildConfig.APP_DESCRIPTION,
            "main_entry": BuildConfig.MAIN_ENTRY,
            "include_files": BuildConfig.INCLUDE_FILES,
            "hidden_imports": BuildConfig.HIDDEN_IMPORTS,
            "pyinstaller_command": BuildConfig.get_pyinstaller_command(),
        }

if __name__ == "__main__":
    print("🔧 TezgahTakip Build Configuration")
    print("=" * 60)
    print(f"App: {BuildConfig.APP_NAME} v{BuildConfig.APP_VERSION}")
    print(f"Description: {BuildConfig.APP_DESCRIPTION}")
    print(f"Install Directory: {BuildConfig.INSTALL_DIR}")
    print("\n📦 Included Files:")
    for file in BuildConfig.INCLUDE_FILES[:5]:
        print(f"  - {file}")
    print(f"  ... and {len(BuildConfig.INCLUDE_FILES) - 5} more files")
    print("\n🔗 Hidden Imports:")
    for imp in BuildConfig.HIDDEN_IMPORTS[:5]:
        print(f"  - {imp}")
    print(f"  ... and {len(BuildConfig.HIDDEN_IMPORTS) - 5} more imports")
    
    # Konfigürasyonu JSON olarak kaydet
    config_dict = BuildConfig.to_dict()
    with open("build_config.json", "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Konfigürasyon build_config.json dosyasına kaydedildi.")
