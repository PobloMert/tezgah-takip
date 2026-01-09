#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yeni Gemini API endpoint'ini test et
"""

import requests
import json
from api_key_manager import APIKeyManager

def test_new_gemini_api():
    """Yeni Gemini API'yi test et"""
    print("🧪 Yeni Gemini API Test Başlıyor...")
    
    try:
        # API anahtarını al
        api_manager = APIKeyManager()
        api_key = api_manager.get_api_key()
        
        if not api_key:
            print("❌ API anahtarı bulunamadı")
            return
        
        print(f"🔑 API anahtarı: {api_key[:4]}...{api_key[-4:]}")
        
        # Test endpoint'leri
        test_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash", 
            "gemini-1.0-pro"
        ]
        
        for model in test_models:
            print(f"\n🔍 Model test ediliyor: {model}")
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TezgahTakip/2.1"
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": "Merhaba! Bu bir test mesajıdır. Sadece 'Test başarılı' yanıtını ver."
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 20,
                    "temperature": 0.1
                }
            }
            
            try:
                response = requests.post(
                    f"{url}?key={api_key}",
                    headers=headers,
                    json=data,
                    timeout=15
                )
                
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        print(f"   ✅ Başarılı: {content.strip()}")
                        return model  # İlk çalışan modeli döndür
                    else:
                        print("   ❌ Boş yanıt")
                elif response.status_code == 404:
                    print("   ❌ Model bulunamadı (404)")
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Bilinmeyen hata')
                    print(f"   ❌ API hatası: {error_msg}")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ İstek hatası: {e}")
        
        print("\n❌ Hiçbir model çalışmadı")
        return None
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return None

if __name__ == "__main__":
    working_model = test_new_gemini_api()
    if working_model:
        print(f"\n🎉 Çalışan model bulundu: {working_model}")
    else:
        print("\n💡 Öneriler:")
        print("1. API anahtarınızın geçerli olduğundan emin olun")
        print("2. https://makersuite.google.com/app/apikey adresinden yeni anahtar alın")
        print("3. İnternet bağlantınızı kontrol edin")