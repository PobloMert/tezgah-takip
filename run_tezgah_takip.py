#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip Başlatıcı
Basit başlatma script'i
"""

import sys
import os

def main():
    """Ana fonksiyon"""
    print("🏭 TezgahTakip Başlatılıyor...")
    
    try:
        # Ana uygulamayı import et ve çalıştır
        from tezgah_takip_app import main as app_main
        return app_main()
        
    except ImportError as e:
        print(f"❌ Modül import hatası: {e}")
        print("\nLütfen şunları kontrol edin:")
        print("1. Tüm dosyaların aynı klasörde olduğunu")
        print("2. Gerekli paketlerin yüklü olduğunu: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())