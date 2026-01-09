#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip v2.1.1 - Quick Build Script
Hızlı executable oluşturma
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

VERSION = "2.1.1"
APP_NAME = "TezgahTakip"

def quick_build():
    """Hızlı build işlemi"""
    print(f"🚀 {APP_NAME} v{VERSION} - Quick Build")
    print("=" * 50)
    
    # Eski dist klasörünü temizle
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("🧹 Eski dist klasörü temizlendi")
    
    # Ana uygulama için basit build
    print("🔨 Ana uygulama build ediliyor...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", f"{APP_NAME}_v{VERSION}",
        "--icon", "tezgah_icon.ico",
        "--add-data", "tezgah_logo.png;.",
        "--add-data", "config.json;.",
        "--add-data", "settings.json;.",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui", 
        "--hidden-import", "PyQt5.QtWidgets",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--clean",
        "--noconfirm",
        "tezgah_takip_app.py"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Build başarılı!")
            
            # Dosya boyutunu kontrol et
            exe_path = f"dist/{APP_NAME}_v{VERSION}.exe"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📁 {APP_NAME}_v{VERSION}.exe: {size_mb:.1f} MB")
                
                # Basit başlatma script'i oluştur
                start_script = f'''@echo off
chcp 65001 >nul
title {APP_NAME} v{VERSION}

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    {APP_NAME} v{VERSION}                         ║
echo ║            AI Güçlü Fabrika Bakım Yönetim Sistemi           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Uygulama başlatılıyor...

"{APP_NAME}_v{VERSION}.exe"

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
'''
                
                with open("dist/Baslat.bat", 'w', encoding='utf-8') as f:
                    f.write(start_script)
                
                print("✅ Başlatma script'i oluşturuldu: Baslat.bat")
                
                # README oluştur
                readme_content = f'''# {APP_NAME} v{VERSION}

## Kullanım
1. "{APP_NAME}_v{VERSION}.exe" dosyasını çalıştırın
2. Veya "Baslat.bat" dosyasını kullanın

## Özellikler
- AI güçlü fabrika bakım yönetimi
- Modern PyQt5 arayüzü
- SQLite veritabanı
- Excel/JSON import/export
- Otomatik yedekleme
- Gelişmiş raporlama

## Sistem Gereksinimleri
- Windows 10/11 (64-bit)
- En az 4 GB RAM
- En az 500 MB boş disk alanı

## Versiyon: {VERSION}
## Build Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}

## Destek
GitHub: https://github.com/PobloMert/tezgah-takip
'''
                
                with open("dist/README.txt", 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                
                print("✅ README dosyası oluşturuldu")
                
                print("\n🎉 Quick Build Tamamlandı!")
                print(f"📁 Dosya: dist/{APP_NAME}_v{VERSION}.exe")
                print("🚀 Başlatmak için: dist/Baslat.bat")
                
                return True
            else:
                print("❌ Executable dosyası oluşturulamadı!")
                return False
        else:
            print("❌ Build hatası:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Build timeout! İşlem çok uzun sürdü.")
        return False
    except Exception as e:
        print(f"❌ Build hatası: {e}")
        return False

if __name__ == "__main__":
    success = quick_build()
    if success:
        print(f"\n✨ {APP_NAME} v{VERSION} hazır!")
    else:
        print("\n❌ Build başarısız!")
        sys.exit(1)