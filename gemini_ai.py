#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gemini AI Entegrasyonu
Google Gemini AI ile akıllı analiz ve öneriler
"""

import json
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from api_key_manager import APIKeyManager
import logging

class RateLimiter:
    """Rate limiting için basit sınıf"""
    
    def __init__(self, max_requests=5, time_window=60):  # Daha konservatif limit
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()
    
    def can_make_request(self):
        """İstek yapılabilir mi kontrol et"""
        with self.lock:
            now = time.time()
            # Eski istekleri temizle
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def wait_time(self):
        """Ne kadar beklemek gerekiyor"""
        with self.lock:
            if not self.requests:
                return 0
            oldest_request = min(self.requests)
            return max(0, self.time_window - (time.time() - oldest_request))

class GeminiAI:
    """Gemini AI entegrasyon sınıfı"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.api_manager = APIKeyManager()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.0-flash"  # Güncel ve stabil model
        self.timeout = 30
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests=5, time_window=60)  # Daha konservatif
        
        # Thread safety
        self.request_lock = threading.Lock()
        
    def get_api_key(self):
        """API anahtarını al"""
        return self.api_manager.get_api_key()
    
    def has_api_key(self):
        """API anahtarı var mı kontrol et"""
        return self.api_manager.has_api_key()
    
    def _make_request(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Gemini API'ye istek gönder - Rate limiting ve thread safety ile"""
        
        # Input sanitization
        if not isinstance(prompt, str) or not prompt.strip():
            return "❌ Geçersiz prompt"
        
        prompt = prompt.strip()
        if len(prompt) > 10000:  # Prompt uzunluk sınırı
            prompt = prompt[:10000] + "..."
        
        # Rate limiting kontrolü
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            self.logger.warning(f"Rate limit reached, need to wait {wait_time:.1f} seconds")
            return f"❌ Rate limit aşıldı. {wait_time:.1f} saniye bekleyin."
        
        with self.request_lock:
            try:
                api_key = self.get_api_key()
                if not api_key:
                    return "❌ API anahtarı bulunamadı. Lütfen ayarlardan API anahtarınızı girin."
                
                url = f"{self.base_url}/models/{self.model}:generateContent"
                
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "TezgahTakip/2.0"
                }
                
                data = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": min(max_tokens, 2048),  # Maksimum sınır
                        "temperature": 0.7,
                        "topP": 0.8,
                        "topK": 40
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH", 
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        }
                    ]
                }
                
                self.logger.info(f"Making API request to Gemini (prompt length: {len(prompt)})")
                
                response = requests.post(
                    f"{url}?key={api_key}",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            content = candidate['content']['parts'][0]['text']
                            self.logger.info("API request successful")
                            return content.strip()
                        else:
                            return "❌ Gemini AI'den geçersiz yanıt formatı alındı."
                    else:
                        return "❌ Gemini AI'den boş yanıt alındı."
                elif response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Bilinmeyen hata')
                    if "API_KEY_INVALID" in str(error_data):
                        return "❌ API anahtarı geçersiz veya süresi dolmuş. Lütfen yeni bir API anahtarı girin."
                    else:
                        return f"❌ API hatası: {error_message}"
                elif response.status_code == 403:
                    return "❌ API anahtarı için yetki yok veya kota aşıldı."
                elif response.status_code == 429:
                    return "❌ Çok fazla istek gönderildi. Lütfen bekleyin."
                else:
                    return f"❌ HTTP {response.status_code}: API bağlantı hatası"
                    
            except requests.exceptions.Timeout:
                self.logger.error("API request timeout")
                return "❌ Bağlantı zaman aşımı. İnternet bağlantınızı kontrol edin."
            except requests.exceptions.ConnectionError:
                self.logger.error("API connection error")
                return "❌ İnternet bağlantısı yok. Bağlantınızı kontrol edin."
            except Exception as e:
                self.logger.error(f"API request error: {e}")
                return f"❌ AI isteği hatası: {str(e)}"
    
    def analyze_maintenance_data(self, tezgah_data: List[Dict]) -> str:
        """Bakım verilerini analiz et - Input validation ile"""
        try:
            if not tezgah_data or not isinstance(tezgah_data, list):
                return "📊 Analiz edilecek tezgah verisi bulunamadı."
            
            # Veri sanitization
            sanitized_data = []
            for item in tezgah_data[:10]:  # Maksimum 10 kayıt
                if isinstance(item, dict):
                    sanitized_item = {}
                    for key, value in item.items():
                        if isinstance(value, str):
                            # Tehlikeli karakterleri temizle
                            sanitized_value = str(value).replace('<', '').replace('>', '').replace('"', '')[:100]
                            sanitized_item[key] = sanitized_value
                        else:
                            sanitized_item[key] = str(value)[:50]
                    sanitized_data.append(sanitized_item)
            
            if not sanitized_data:
                return "📊 Geçerli tezgah verisi bulunamadı."
            
            # Veri özetini hazırla
            total_tezgah = len(sanitized_data)
            active_count = sum(1 for t in sanitized_data if t.get('durum') == 'Aktif')
            maintenance_count = sum(1 for t in sanitized_data if t.get('durum') == 'Bakımda')
            
            prompt = f"""
Tezgah Takip Sistemi - Bakım Analizi

Sistem Özeti:
- Toplam Tezgah: {total_tezgah}
- Aktif Tezgah: {active_count}
- Bakımda Tezgah: {maintenance_count}

Tezgah Detayları:
{json.dumps(sanitized_data, ensure_ascii=False, indent=2)}

Lütfen bu verileri analiz ederek şunları sağla:
1. Genel durum değerlendirmesi
2. Kritik bakım önerileri
3. Performans iyileştirme önerileri
4. Risk analizi
5. Öncelikli aksiyonlar

Yanıtını Türkçe olarak, madde madde ve anlaşılır şekilde ver.
"""
            
            return self._make_request(prompt, max_tokens=1500)
            
        except Exception as e:
            self.logger.error(f"Maintenance analysis error: {e}")
            return f"❌ Bakım analizi hatası: {str(e)}"
    
    def predict_battery_life(self, pil_data: List[Dict]) -> str:
        """Pil ömrü tahmini yap"""
        try:
            if not pil_data:
                return "🔋 Analiz edilecek pil verisi bulunamadı."
            
            prompt = f"""
Tezgah Takip Sistemi - Pil Ömrü Analizi

Pil Verileri:
{json.dumps(pil_data[:10], ensure_ascii=False, indent=2)}

Bu pil verilerini analiz ederek şunları sağla:
1. Pil durumu genel değerlendirmesi
2. Değiştirilmesi gereken piller
3. Pil ömrü tahminleri
4. Pil bakım önerileri
5. Maliyet analizi

Yanıtını Türkçe olarak, madde madde ve anlaşılır şekilde ver.
"""
            
            return self._make_request(prompt, max_tokens=1200)
            
        except Exception as e:
            return f"❌ Pil analizi hatası: {str(e)}"
    
    def generate_maintenance_recommendations(self, tezgah_id: int, maintenance_history: List[Dict]) -> str:
        """Bakım önerileri oluştur"""
        try:
            prompt = f"""
Tezgah Takip Sistemi - Bakım Önerileri

Tezgah ID: {tezgah_id}
Bakım Geçmişi:
{json.dumps(maintenance_history, ensure_ascii=False, indent=2)}

Bu tezgah için şunları analiz et ve öner:
1. Bakım sıklığı optimizasyonu
2. Önleyici bakım önerileri
3. Kritik kontrol noktaları
4. Yedek parça önerileri
5. Maliyet optimizasyonu

Yanıtını Türkçe olarak, uygulanabilir öneriler şeklinde ver.
"""
            
            return self._make_request(prompt, max_tokens=1200)
            
        except Exception as e:
            return f"❌ Bakım önerisi hatası: {str(e)}"
    
    def analyze_performance_trends(self, performance_data: Dict) -> str:
        """Performans trendlerini analiz et"""
        try:
            prompt = f"""
Tezgah Takip Sistemi - Performans Trend Analizi

Performans Verileri:
{json.dumps(performance_data, ensure_ascii=False, indent=2)}

Bu performans verilerini analiz ederek şunları sağla:
1. Performans trend analizi
2. Verimlilik değerlendirmesi
3. Sorunlu alanların tespiti
4. İyileştirme önerileri
5. Gelecek projeksiyonları

Yanıtını Türkçe olarak, grafiksel verilerle desteklenebilir şekilde ver.
"""
            
            return self._make_request(prompt, max_tokens=1500)
            
        except Exception as e:
            return f"❌ Performans analizi hatası: {str(e)}"
    
    def generate_smart_alerts(self, alert_data: Dict) -> str:
        """Akıllı uyarılar oluştur"""
        try:
            prompt = f"""
Tezgah Takip Sistemi - Akıllı Uyarı Sistemi

Uyarı Verileri:
{json.dumps(alert_data, ensure_ascii=False, indent=2)}

Bu verilere göre şunları oluştur:
1. Öncelikli uyarılar
2. Risk seviyesi değerlendirmesi
3. Acil müdahale gereken durumlar
4. Önleyici aksiyonlar
5. Takip edilmesi gereken metrikler

Yanıtını Türkçe olarak, öncelik sırasına göre düzenle.
"""
            
            return self._make_request(prompt, max_tokens=1000)
            
        except Exception as e:
            return f"❌ Akıllı uyarı hatası: {str(e)}"
    
    def answer_question(self, question: str, context_data: Optional[Dict] = None) -> str:
        """Kullanıcı sorusunu yanıtla - Input sanitization ile"""
        try:
            if not question or not isinstance(question, str):
                return "❌ Geçersiz soru"
            
            # Input sanitization
            question = question.strip()
            if len(question) < 3:
                return "❌ Soru çok kısa"
            
            if len(question) > 500:
                question = question[:500] + "..."
            
            # Tehlikeli içerik kontrolü
            dangerous_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
            for pattern in dangerous_patterns:
                if pattern.lower() in question.lower():
                    return "❌ Güvenlik nedeniyle bu soru işlenemiyor"
            
            context = ""
            if context_data and isinstance(context_data, dict):
                # Context data sanitization
                sanitized_context = {}
                for key, value in list(context_data.items())[:5]:  # Maksimum 5 item
                    if isinstance(value, str):
                        sanitized_context[key] = str(value)[:200]
                    else:
                        sanitized_context[key] = str(value)[:100]
                
                context = f"\nSistem Verileri:\n{json.dumps(sanitized_context, ensure_ascii=False, indent=2)}"
            
            prompt = f"""
Tezgah Takip Sistemi - Soru & Cevap

Kullanıcı Sorusu: {question}
{context}

Bu soruyu tezgah takip ve bakım yönetimi uzmanı olarak yanıtla. 
Yanıtın pratik, uygulanabilir ve Türkçe olsun.
Eğer sistem verileri varsa bunları da dikkate al.
"""
            
            return self._make_request(prompt, max_tokens=1000)
            
        except Exception as e:
            self.logger.error(f"Question answering error: {e}")
            return f"❌ Soru yanıtlama hatası: {str(e)}"
    
    def generate_report_insights(self, report_data: Dict) -> str:
        """Rapor içgörüleri oluştur"""
        try:
            prompt = f"""
Tezgah Takip Sistemi - Rapor İçgörüleri

Rapor Verileri:
{json.dumps(report_data, ensure_ascii=False, indent=2)}

Bu rapor verilerinden şunları çıkar:
1. Önemli bulgular
2. Trend analizleri
3. Dikkat edilmesi gereken noktalar
4. Öneriler ve aksiyonlar
5. Gelecek planlaması

Yanıtını Türkçe olarak, yönetici seviyesinde özetleyerek ver.
"""
            
            return self._make_request(prompt, max_tokens=1500)
            
        except Exception as e:
            return f"❌ Rapor analizi hatası: {str(e)}"
    
    def optimize_maintenance_schedule(self, schedule_data: List[Dict]) -> str:
        """Bakım programını optimize et"""
        try:
            prompt = f"""
Tezgah Takip Sistemi - Bakım Programı Optimizasyonu

Mevcut Bakım Programı:
{json.dumps(schedule_data, ensure_ascii=False, indent=2)}

Bu bakım programını optimize ederek şunları sağla:
1. Optimum bakım sıklığı önerileri
2. Kaynak kullanımı optimizasyonu
3. Maliyet-fayda analizi
4. Risk minimizasyonu
5. Yeni bakım takvimi önerisi

Yanıtını Türkçe olarak, uygulanabilir bir plan şeklinde ver.
"""
            
            return self._make_request(prompt, max_tokens=1500)
            
        except Exception as e:
            return f"❌ Bakım optimizasyonu hatası: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        """API bağlantısını test et"""
        try:
            if not self.has_api_key():
                return False, "API anahtarı bulunamadı"
            
            test_prompt = "Merhaba! Bu bir bağlantı testidir. Sadece 'Test başarılı' yanıtını ver."
            response = self._make_request(test_prompt, max_tokens=50)
            
            if response and not response.startswith("❌"):
                self.logger.info("API connection test successful")
                return True, "Bağlantı başarılı"
            else:
                self.logger.warning(f"API connection test failed: {response}")
                return False, response or "Bilinmeyen hata"
                
        except Exception as e:
            self.logger.error(f"API connection test error: {e}")
            return False, f"Test hatası: {str(e)}"

# Test fonksiyonu
def test_gemini_ai():
    """Gemini AI'yi test et"""
    print("🧪 Gemini AI Test Başlıyor...")
    
    try:
        ai = GeminiAI()
        
        # API anahtarı kontrolü
        has_key = ai.has_api_key()
        print(f"API anahtarı var: {has_key}")
        
        if has_key:
            # Bağlantı testi
            success, message = ai.test_connection()
            print(f"Bağlantı testi: {success} - {message}")
            
            if success:
                # Basit soru testi
                response = ai.answer_question("Tezgah bakımında en önemli 3 nokta nedir?")
                print(f"Soru yanıtı: {response[:100]}...")
        
        print("✅ Gemini AI testi tamamlandı!")
        
    except Exception as e:
        print(f"❌ Gemini AI testi başarısız: {e}")

if __name__ == "__main__":
    test_gemini_ai()