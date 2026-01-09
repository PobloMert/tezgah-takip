#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate limit'i aşmadan API test et
"""

import requests
import json
import time
from api_key_manager import APIKeyManager

def test_api_with_delay():
    """Rate limit'e takılmadan API test et"""
    print("🧪 Rate Limit Güvenli API Test...")
    
    try:
        # API anahtarını al
        api_manager = APIKeyManager()
        
        # Yeni API anahtarı var mı kontrol et
        if not api_manager.has_api_key():
            print("❌ API anahtarı bulunamadı")
            print("💡 Lütfen önce uygulamada API anahtarınızı girin")
            return False
        
        api_key = api_manager.get_api_key()
        print(f"🔑 API anahtarı: {api_key[:4]}...{api_key[-4:]}")
        
        # Rate limit'i aşmamak için bekle
        print("⏳ Rate limit'i aşmamak için 5 saniye bekleniyor...")
        time.sleep(5)
        
        # Test isteği
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TezgahTakip/2.1"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": "Merhaba! Sadece 'API çalışıyor' yanıtını ver."
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 10,
                "temperature": 0.1
            }
        }
        
        print("🔍 API test ediliyor...")
        
        response = requests.post(
            f"{url}?key={api_key}",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Başarılı! Yanıt: {content.strip()}")
                return True
            else:
                print("❌ Boş yanıt alındı")
                return False
        elif response.status_code == 429:
            print("❌ Hala rate limit hatası")
            print("💡 Daha uzun bekleyin (5-10 dakika)")
            return False
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Bilinmeyen hata')
            print(f"❌ API hatası: {error_msg}")
            return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False

if __name__ == "__main__":
    success = test_api_with_delay()
    if success:
        print("\n🎉 API anahtarı çalışıyor! AI özellikleri kullanılabilir.")
    else:
        print("\n💡 Öneriler:")
        print("1. 5-10 dakika bekleyin (rate limit)")
        print("2. API anahtarınızın doğru girildiğinden emin olun")
        print("3. İnternet bağlantınızı kontrol edin")