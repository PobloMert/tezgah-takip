#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip Test Script
Uygulamanın temel fonksiyonlarını test eder
"""

import sys
import os
from datetime import datetime

# Test için gerekli modülleri import et
try:
    from database_models import DatabaseManager, Tezgah, Bakim, Pil
    from config_manager import ConfigManager
    from gemini_ai import GeminiAI
    print("✅ Tüm modüller başarıyla import edildi")
except ImportError as e:
    print(f"❌ Modül import hatası: {e}")
    sys.exit(1)

def test_database():
    """Veritabanı bağlantısını test et"""
    try:
        config_manager = ConfigManager()
        db_manager = DatabaseManager(config_manager.get("database.path"))
        
        # Tezgah sayısını kontrol et
        with db_manager.get_session() as session:
            tezgah_count = session.query(Tezgah).count()
            bakim_count = session.query(Bakim).count()
            pil_count = session.query(Pil).count()
            
        print(f"✅ Veritabanı bağlantısı başarılı")
        print(f"   📊 Tezgah sayısı: {tezgah_count}")
        print(f"   🔧 Bakım kayıt sayısı: {bakim_count}")
        print(f"   🔋 Pil kayıt sayısı: {pil_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Veritabanı test hatası: {e}")
        return False

def test_config():
    """Konfigürasyon yöneticisini test et"""
    try:
        config_manager = ConfigManager()
        
        # Temel ayarları kontrol et
        db_path = config_manager.get("database.path")
        ui_config = config_manager.get_ui_config()
        
        print(f"✅ Konfigürasyon yüklendi")
        print(f"   📁 Veritabanı yolu: {db_path}")
        print(f"   🖥️ UI ayarları: {len(ui_config)} öğe")
        
        return True
        
    except Exception as e:
        print(f"❌ Konfigürasyon test hatası: {e}")
        return False

def test_ai():
    """AI modülünü test et"""
    try:
        config_manager = ConfigManager()
        db_manager = DatabaseManager(config_manager.get("database.path"))
        gemini_ai = GeminiAI(db_manager)
        
        has_key = gemini_ai.has_api_key()
        print(f"✅ AI modülü yüklendi")
        print(f"   🔑 API anahtarı: {'Mevcut' if has_key else 'Yok'}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI modülü test hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🧪 TezgahTakip Test Başlatılıyor...")
    print("=" * 50)
    
    tests = [
        ("Konfigürasyon", test_config),
        ("Veritabanı", test_database),
        ("AI Modülü", test_ai)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name} testi...")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"📊 Test Sonuçları: {passed}/{total} başarılı")
    
    if passed == total:
        print("🎉 Tüm testler başarılı! Uygulama çalışmaya hazır.")
        return 0
    else:
        print("⚠️ Bazı testler başarısız. Lütfen hataları kontrol edin.")
        return 1

if __name__ == "__main__":
    sys.exit(main())