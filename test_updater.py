#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Güncelleme Sistemi Test Scripti
"""

import sys
import os
from auto_updater import AutoUpdater

def test_updater():
    """Güncelleme sistemini test et"""
    print("🧪 TezgahTakip Güncelleme Sistemi Test Scripti")
    print("=" * 50)
    
    try:
        # AutoUpdater'ı başlat
        updater = AutoUpdater(current_version="2.1.3")
        print(f"✅ AutoUpdater başlatıldı - Mevcut versiyon: {updater.current_version}")
        
        # Güncellemeleri kontrol et
        print("\n🔍 Güncellemeler kontrol ediliyor...")
        update_info = updater.check_for_updates()
        
        if update_info.get('available'):
            print(f"🎉 Yeni versiyon mevcut: {update_info['version']}")
            print(f"📝 Yenilikler: {update_info.get('release_notes', 'Bilgi yok')[:100]}...")
            
            # Test modunda sadece bilgi göster
            print("\n⚠️ TEST MODU - Gerçek güncelleme yapılmayacak")
            print("Gerçek güncelleme için launcher.py kullanın")
            
        elif update_info.get('available') == False:
            if 'error' in update_info:
                print(f"❌ Hata: {update_info['error']}")
            else:
                print("✅ Uygulama güncel!")
        
        # Sistem bilgilerini göster
        print(f"\n📊 Sistem Bilgileri:")
        print(f"   Python: {sys.version}")
        print(f"   Platform: {sys.platform}")
        print(f"   Çalışma Dizini: {os.getcwd()}")
        print(f"   Script Dizini: {os.path.dirname(os.path.abspath(__file__))}")
        
        # Dosya varlık kontrolü
        print(f"\n📁 Dosya Kontrolü:")
        critical_files = [
            "launcher.py",
            "auto_updater.py", 
            "main_window.py",
            "run_tezgah_takip.py",
            "tezgah_takip_app.py"
        ]
        
        for file in critical_files:
            exists = "✅" if os.path.exists(file) else "❌"
            print(f"   {exists} {file}")
        
        print(f"\n✅ Test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updater()