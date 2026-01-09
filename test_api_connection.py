#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API bağlantısını test etmek için basit script
"""

from api_key_manager import APIKeyManager
from gemini_ai import GeminiAI
import logging

def test_current_api_status():
    """Mevcut API durumunu test et"""
    print("🔍 API Durumu Kontrol Ediliyor...")
    
    try:
        # API Manager
        api_manager = APIKeyManager()
        
        # API anahtarı var mı?
        has_key = api_manager.has_api_key()
        print(f"📋 API anahtarı kayıtlı: {has_key}")
        
        if has_key:
            # API anahtarını al (güvenlik için maskelenmiş)
            api_key = api_manager.get_api_key()
            if api_key:
                masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
                print(f"🔑 Kayıtlı anahtar: {masked_key}")
                
                # Format kontrolü
                is_valid, message = api_manager.validate_api_key(api_key)
                print(f"📝 Format kontrolü: {is_valid} - {message}")
                
                # Gemini AI bağlantı testi
                print("\n🤖 Gemini AI Bağlantı Testi...")
                gemini = GeminiAI()
                
                success, test_message = gemini.test_connection()
                print(f"🌐 Bağlantı testi: {success}")
                print(f"📄 Mesaj: {test_message}")
                
                if not success:
                    print("\n❌ API anahtarı çalışmıyor. Yeni anahtar gerekli.")
                    print("💡 Çözüm önerileri:")
                    print("   1. Yeni API anahtarı alın: https://makersuite.google.com/app/apikey")
                    print("   2. Eski anahtarı temizleyin ve yenisini girin")
                    print("   3. İnternet bağlantınızı kontrol edin")
                else:
                    print("\n✅ API anahtarı çalışıyor!")
            else:
                print("❌ API anahtarı okunamadı")
        else:
            print("\n💡 API anahtarı bulunamadı.")
            print("🔗 Yeni API anahtarı almak için: https://makersuite.google.com/app/apikey")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_current_api_status()