#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eski API anahtarını temizle
"""

from api_key_manager import APIKeyManager

def clear_old_api_key():
    """Eski API anahtarını temizle"""
    print("🧹 Eski API anahtarı temizleniyor...")
    
    try:
        api_manager = APIKeyManager()
        
        # Mevcut durumu göster
        if api_manager.has_api_key():
            existing_key = api_manager.get_api_key()
            masked_key = existing_key[:4] + "..." + existing_key[-4:] if len(existing_key) > 8 else "***"
            print(f"📋 Mevcut anahtar: {masked_key}")
        else:
            print("📋 Mevcut anahtar: Yok")
        
        # Temizle
        success = api_manager.clear_api_key()
        
        if success:
            print("✅ Eski API anahtarı başarıyla temizlendi!")
            print("💡 Şimdi uygulamayı açıp yeni API anahtarınızı girebilirsiniz.")
        else:
            print("❌ API anahtarı temizlenemedi")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    clear_old_api_key()