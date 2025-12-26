#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip Kurulum Script'i
Gerekli paketleri yükler ve uygulamayı hazırlar
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Python versiyonunu kontrol et"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ gerekli. Mevcut versiyon: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python versiyonu: {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Gerekli paketleri yükle"""
    print("📦 Gerekli paketler yükleniyor...")
    
    try:
        # requirements.txt dosyasını kontrol et
        if not Path("requirements.txt").exists():
            print("❌ requirements.txt dosyası bulunamadı!")
            return False
        
        # Paketleri yükle
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tüm paketler başarıyla yüklendi!")
            return True
        else:
            print(f"❌ Paket yükleme hatası: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Paket yükleme sırasında hata: {e}")
        return False

def create_directories():
    """Gerekli klasörleri oluştur"""
    print("📁 Gerekli klasörler oluşturuluyor...")
    
    directories = ["logs", "backups"]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ {directory} klasörü hazır")
        except Exception as e:
            print(f"❌ {directory} klasörü oluşturulamadı: {e}")
            return False
    
    return True

def test_installation():
    """Kurulumu test et"""
    print("🧪 Kurulum test ediliyor...")
    
    try:
        # Modülleri import etmeyi dene
        modules_to_test = [
            "PyQt5.QtWidgets",
            "sqlalchemy",
            "requests"
        ]
        
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module} modülü yüklendi")
            except ImportError:
                print(f"❌ {module} modülü yüklenemedi")
                return False
        
        # Veritabanını test et
        try:
            from database_models import DatabaseManager
            db = DatabaseManager("test_setup.db")
            count = db.get_tezgah_count()
            db.close()
            
            # Test dosyasını sil
            if os.path.exists("test_setup.db"):
                os.remove("test_setup.db")
            
            print(f"✅ Veritabanı testi başarılı (test tezgah sayısı: {count})")
            
        except Exception as e:
            print(f"❌ Veritabanı testi başarısız: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test sırasında hata: {e}")
        return False

def main():
    """Ana kurulum fonksiyonu"""
    print("🏭 TezgahTakip v2.0 Kurulum Script'i")
    print("=" * 50)
    
    # Adım 1: Python versiyonu
    if not check_python_version():
        return 1
    
    # Adım 2: Gerekli paketleri yükle
    if not install_requirements():
        print("\n❌ Paket yükleme başarısız!")
        print("Manuel yükleme için: pip install -r requirements.txt")
        return 1
    
    # Adım 3: Klasörleri oluştur
    if not create_directories():
        return 1
    
    # Adım 4: Kurulumu test et
    if not test_installation():
        print("\n❌ Kurulum testi başarısız!")
        return 1
    
    # Başarı mesajı
    print("\n🎉 Kurulum başarıyla tamamlandı!")
    print("\nUygulamayı başlatmak için:")
    print("  python tezgah_takip_app.py")
    print("veya")
    print("  python run_tezgah_takip.py")
    
    print("\n📋 Sonraki adımlar:")
    print("1. Uygulamayı başlatın")
    print("2. Google Gemini API anahtarınızı girin")
    print("3. Tezgahlarınızı ekleyin")
    print("4. AI özelliklerini keşfedin!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())