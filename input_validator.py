#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Input Validation Modülü
XSS, SQL Injection ve diğer güvenlik tehditlerine karşı koruma
"""

import re
import html
import logging
from typing import Optional, List, Dict, Any, Tuple

class InputValidator:
    """Gelişmiş input validation sınıfı"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Tehlikeli karakterler ve pattern'lar
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'vbscript:',                 # VBScript URLs
            r'onload\s*=',                # Event handlers
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'eval\s*\(',                 # Eval functions
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
            r'passthru\s*\(',
            r'DROP\s+TABLE',              # SQL injection
            r'DELETE\s+FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*SET',
            r'UNION\s+SELECT',
            r'--\s*',                     # SQL comments
            r'/\*.*?\*/',
            r';\s*DROP',
            r';\s*DELETE',
            r';\s*INSERT',
            r';\s*UPDATE'
        ]
        
        # Güvenli karakterler (whitelist)
        self.safe_chars = {
            'alphanumeric': r'^[a-zA-Z0-9\s\-_\.]+$',
            'text': r'^[a-zA-Z0-9\s\-_\.\,\!\?\(\)\[\]\{\}]+$',
            'turkish_text': r'^[a-zA-ZçğıöşüÇĞIİÖŞÜ0-9\s\-_\.\,\!\?\(\)\[\]\{\}]+$',
            'number': r'^[0-9]+$',
            'decimal': r'^[0-9]+\.?[0-9]*$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[0-9\s\-\(\)]{10,15}$',
            'tezgah_no': r'^[A-Z0-9\-_]{2,20}$',
            'date': r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        }
    
    def sanitize_input(self, input_text: str, max_length: int = 255) -> str:
        """Input'u temizle ve güvenli hale getir"""
        if not input_text:
            return ""
        
        # String'e çevir
        text = str(input_text).strip()
        
        # Uzunluk kontrolü
        if len(text) > max_length:
            text = text[:max_length]
            self.logger.warning(f"Input truncated to {max_length} characters")
        
        # HTML encode
        text = html.escape(text)
        
        # Tehlikeli pattern'ları temizle
        for pattern in self.dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Null byte temizle
        text = text.replace('\x00', '')
        
        # Çoklu boşlukları tek boşluğa çevir
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def validate_tezgah_no(self, tezgah_no: str) -> Tuple[bool, str]:
        """Tezgah numarası validasyonu"""
        if not tezgah_no:
            return False, "Tezgah numarası boş olamaz"
        
        # Sanitize
        clean_no = self.sanitize_input(tezgah_no, 20).upper()
        
        # Pattern kontrolü
        if not re.match(self.safe_chars['tezgah_no'], clean_no):
            return False, "Tezgah numarası sadece harf, rakam, tire ve alt çizgi içerebilir"
        
        # Uzunluk kontrolü
        if len(clean_no) < 2:
            return False, "Tezgah numarası en az 2 karakter olmalı"
        
        if len(clean_no) > 20:
            return False, "Tezgah numarası en fazla 20 karakter olabilir"
        
        return True, clean_no
    
    def validate_text_field(self, text: str, field_name: str, 
                           min_length: int = 0, max_length: int = 255,
                           allow_turkish: bool = True) -> Tuple[bool, str]:
        """Genel metin alanı validasyonu"""
        if not text and min_length > 0:
            return False, f"{field_name} boş olamaz"
        
        if not text:
            return True, ""
        
        # Sanitize
        clean_text = self.sanitize_input(text, max_length)
        
        # Uzunluk kontrolü
        if len(clean_text) < min_length:
            return False, f"{field_name} en az {min_length} karakter olmalı"
        
        # Pattern kontrolü
        pattern = self.safe_chars['turkish_text'] if allow_turkish else self.safe_chars['text']
        if not re.match(pattern, clean_text):
            return False, f"{field_name} geçersiz karakter içeriyor"
        
        return True, clean_text
    
    def validate_number(self, number_str: str, field_name: str,
                       min_value: Optional[float] = None,
                       max_value: Optional[float] = None,
                       allow_decimal: bool = True) -> Tuple[bool, Optional[float]]:
        """Sayı validasyonu"""
        if not number_str:
            return True, None
        
        # Sanitize
        clean_number = self.sanitize_input(number_str, 20)
        
        # Pattern kontrolü
        pattern = self.safe_chars['decimal'] if allow_decimal else self.safe_chars['number']
        if not re.match(pattern, clean_number):
            return False, None
        
        try:
            value = float(clean_number) if allow_decimal else int(clean_number)
            
            # Aralık kontrolü
            if min_value is not None and value < min_value:
                return False, None
            
            if max_value is not None and value > max_value:
                return False, None
            
            return True, value
            
        except (ValueError, OverflowError):
            return False, None
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """Email validasyonu"""
        if not email:
            return True, ""
        
        # Sanitize
        clean_email = self.sanitize_input(email, 100).lower()
        
        # Pattern kontrolü
        if not re.match(self.safe_chars['email'], clean_email):
            return False, "Geçersiz email formatı"
        
        return True, clean_email
    
    def validate_phone(self, phone: str) -> Tuple[bool, str]:
        """Telefon numarası validasyonu"""
        if not phone:
            return True, ""
        
        # Sanitize
        clean_phone = self.sanitize_input(phone, 20)
        
        # Pattern kontrolü
        if not re.match(self.safe_chars['phone'], clean_phone):
            return False, "Geçersiz telefon formatı"
        
        return True, clean_phone
    
    def check_sql_injection(self, input_text: str) -> bool:
        """SQL injection kontrolü"""
        if not input_text:
            return False
        
        # SQL injection pattern'larını kontrol et
        sql_patterns = [
            r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
            r'(--|\#|/\*|\*/)',
            r'(\bOR\b|\bAND\b).*?=.*?=',
            r';\s*(DROP|DELETE|INSERT|UPDATE)',
            r'\b(exec|execute|sp_|xp_)\b'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                self.logger.warning(f"SQL injection attempt detected: {pattern}")
                return True
        
        return False
    
    def check_xss(self, input_text: str) -> bool:
        """XSS kontrolü"""
        if not input_text:
            return False
        
        # XSS pattern'larını kontrol et
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                self.logger.warning(f"XSS attempt detected: {pattern}")
                return True
        
        return False
    
    def validate_and_sanitize(self, data: Dict[str, Any], 
                             validation_rules: Dict[str, Dict]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Toplu validation ve sanitization"""
        errors = []
        clean_data = {}
        
        for field_name, value in data.items():
            if field_name not in validation_rules:
                # Kural yoksa basit sanitization
                clean_data[field_name] = self.sanitize_input(str(value)) if value else None
                continue
            
            rules = validation_rules[field_name]
            field_type = rules.get('type', 'text')
            required = rules.get('required', False)
            
            # Required kontrolü
            if required and not value:
                errors.append(f"{field_name} zorunlu alan")
                continue
            
            # Type'a göre validation
            if field_type == 'tezgah_no':
                is_valid, result = self.validate_tezgah_no(value)
                if not is_valid:
                    errors.append(f"{field_name}: {result}")
                else:
                    clean_data[field_name] = result
                    
            elif field_type == 'text':
                min_len = rules.get('min_length', 0)
                max_len = rules.get('max_length', 255)
                allow_turkish = rules.get('allow_turkish', True)
                
                is_valid, result = self.validate_text_field(
                    value, field_name, min_len, max_len, allow_turkish
                )
                if not is_valid:
                    errors.append(f"{field_name}: {result}")
                else:
                    clean_data[field_name] = result
                    
            elif field_type == 'number':
                min_val = rules.get('min_value')
                max_val = rules.get('max_value')
                allow_decimal = rules.get('allow_decimal', True)
                
                is_valid, result = self.validate_number(
                    str(value), field_name, min_val, max_val, allow_decimal
                )
                if not is_valid:
                    errors.append(f"{field_name}: Geçersiz sayı")
                else:
                    clean_data[field_name] = result
                    
            elif field_type == 'email':
                is_valid, result = self.validate_email(value)
                if not is_valid:
                    errors.append(f"{field_name}: {result}")
                else:
                    clean_data[field_name] = result
                    
            else:
                # Varsayılan sanitization
                clean_data[field_name] = self.sanitize_input(str(value)) if value else None
        
        return len(errors) == 0, clean_data, errors

# Global validator instance
input_validator = InputValidator()

# Convenience functions
def sanitize(text: str, max_length: int = 255) -> str:
    """Hızlı sanitization"""
    return input_validator.sanitize_input(text, max_length)

def validate_tezgah_no(tezgah_no: str) -> Tuple[bool, str]:
    """Hızlı tezgah no validation"""
    return input_validator.validate_tezgah_no(tezgah_no)

def is_safe_input(text: str) -> bool:
    """Input'un güvenli olup olmadığını kontrol et"""
    if not text:
        return True
    
    return not (input_validator.check_sql_injection(text) or 
                input_validator.check_xss(text))