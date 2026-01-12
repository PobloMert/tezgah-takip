#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Güvenlik Yöneticisi
Path traversal, input validation ve güvenlik kontrolleri
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import hashlib
import secrets
import time
from datetime import datetime, timedelta

class SecurityManager:
    """Güvenlik kontrolleri ve validasyon sınıfı"""
    
    # Güvenli dosya uzantıları
    ALLOWED_FILE_EXTENSIONS = {
        'database': ['.db', '.sqlite', '.sqlite3'],
        'backup': ['.db', '.zip', '.gz', '.bak'],
        'export': ['.xlsx', '.pdf', '.csv', '.json'],
        'config': ['.json', '.ini', '.cfg'],
        'log': ['.log', '.txt']
    }
    
    # Tehlikeli karakterler
    DANGEROUS_CHARS = ['<', '>', '"', "'", '&', '\x00', '\r', '\n', '\t']
    
    # Path traversal pattern'leri
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',
        r'\.\.\.',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
        r'..%2f',
        r'..%5c'
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.failed_attempts = {}  # IP/User bazlı failed attempt tracking
        self.rate_limits = {}      # Rate limiting
        
    def validate_file_path(self, file_path: Union[str, Path], 
                          file_type: str = 'general',
                          base_dir: Optional[str] = None) -> tuple[bool, str]:
        """
        Dosya yolu güvenlik validasyonu
        
        Args:
            file_path: Kontrol edilecek dosya yolu
            file_type: Dosya tipi (database, backup, export, etc.)
            base_dir: İzin verilen base directory
            
        Returns:
            (is_valid, error_message)
        """
        try:
            if not file_path:
                return False, "Dosya yolu boş olamaz"
            
            file_path_str = str(file_path)
            
            # Path traversal kontrolü
            for pattern in self.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, file_path_str, re.IGNORECASE):
                    self.logger.warning(f"Path traversal attempt detected: {file_path_str}")
                    return False, "Geçersiz dosya yolu - güvenlik riski"
            
            # Absolute path kontrolü (sadece relative path'lere izin ver)
            if os.path.isabs(file_path_str):
                return False, "Absolute path'lere izin verilmiyor"
            
            # Null byte kontrolü
            if '\x00' in file_path_str:
                return False, "Null byte karakteri tespit edildi"
            
            # Dosya uzantısı kontrolü
            if file_type in self.ALLOWED_FILE_EXTENSIONS:
                allowed_extensions = self.ALLOWED_FILE_EXTENSIONS[file_type]
                file_extension = Path(file_path).suffix.lower()
                
                if file_extension not in allowed_extensions:
                    return False, f"İzin verilmeyen dosya uzantısı: {file_extension}"
            
            # Base directory kontrolü
            if base_dir:
                try:
                    # Resolve path'leri normalize et
                    resolved_path = Path(base_dir) / Path(file_path)
                    resolved_path = resolved_path.resolve()
                    base_path = Path(base_dir).resolve()
                    
                    # Path'in base directory içinde olduğunu kontrol et
                    if not str(resolved_path).startswith(str(base_path)):
                        return False, "Dosya izin verilen dizin dışında"
                        
                except Exception as e:
                    self.logger.error(f"Path resolution error: {e}")
                    return False, "Dosya yolu çözümlenemedi"
            
            # Dosya adı uzunluk kontrolü
            filename = Path(file_path).name
            if len(filename) > 255:
                return False, "Dosya adı çok uzun (max 255 karakter)"
            
            # Tehlikeli karakter kontrolü
            for char in self.DANGEROUS_CHARS:
                if char in filename:
                    return False, f"Dosya adında tehlikeli karakter: {char}"
            
            return True, "Geçerli dosya yolu"
            
        except Exception as e:
            self.logger.error(f"File path validation error: {e}")
            return False, f"Validasyon hatası: {e}"
    
    def sanitize_input(self, input_text: str, 
                      max_length: int = 1000,
                      allow_html: bool = False) -> str:
        """
        Kullanıcı input'unu güvenli hale getir
        
        Args:
            input_text: Temizlenecek metin
            max_length: Maksimum uzunluk
            allow_html: HTML'e izin ver mi
            
        Returns:
            Temizlenmiş metin
        """
        if not input_text:
            return ""
        
        # Uzunluk kontrolü
        if len(input_text) > max_length:
            input_text = input_text[:max_length]
        
        # HTML temizleme (eğer izin verilmiyorsa)
        if not allow_html:
            # Basit HTML escape
            input_text = input_text.replace('&', '&amp;')
            input_text = input_text.replace('<', '&lt;')
            input_text = input_text.replace('>', '&gt;')
            input_text = input_text.replace('"', '&quot;')
            input_text = input_text.replace("'", '&#x27;')
        
        # Null byte temizleme
        input_text = input_text.replace('\x00', '')
        
        # Control character'leri temizle
        input_text = ''.join(char for char in input_text if ord(char) >= 32 or char in '\t\n\r')
        
        return input_text.strip()
    
    def validate_sql_table_name(self, table_name: str, 
                               allowed_tables: List[str]) -> tuple[bool, str]:
        """
        SQL tablo adı validasyonu
        
        Args:
            table_name: Kontrol edilecek tablo adı
            allowed_tables: İzin verilen tablo listesi
            
        Returns:
            (is_valid, error_message)
        """
        if not table_name:
            return False, "Tablo adı boş olamaz"
        
        # Whitelist kontrolü
        if table_name not in allowed_tables:
            self.logger.warning(f"Unauthorized table access attempt: {table_name}")
            return False, f"İzin verilmeyen tablo: {table_name}"
        
        # SQL injection pattern kontrolü
        sql_patterns = [
            r';',           # Statement separator
            r'--',          # SQL comment
            r'/\*',         # SQL comment start
            r'\*/',         # SQL comment end
            r'\bUNION\b',   # UNION keyword
            r'\bSELECT\b',  # SELECT keyword
            r'\bINSERT\b',  # INSERT keyword
            r'\bUPDATE\b',  # UPDATE keyword
            r'\bDELETE\b',  # DELETE keyword
            r'\bDROP\b',    # DROP keyword
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, table_name, re.IGNORECASE):
                self.logger.warning(f"SQL injection attempt in table name: {table_name}")
                return False, "Tablo adında geçersiz karakter/kelime"
        
        return True, "Geçerli tablo adı"
    
    def check_rate_limit(self, identifier: str, 
                        max_requests: int = 10,
                        time_window: int = 60) -> tuple[bool, int]:
        """
        Rate limiting kontrolü
        
        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            max_requests: Maksimum istek sayısı
            time_window: Zaman penceresi (saniye)
            
        Returns:
            (is_allowed, remaining_time)
        """
        current_time = time.time()
        
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Eski istekleri temizle
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if current_time - req_time < time_window
        ]
        
        # Rate limit kontrolü
        if len(self.rate_limits[identifier]) >= max_requests:
            oldest_request = min(self.rate_limits[identifier])
            remaining_time = int(time_window - (current_time - oldest_request))
            return False, remaining_time
        
        # Yeni isteği kaydet
        self.rate_limits[identifier].append(current_time)
        return True, 0
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Güvenli token oluştur"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Şifre hash'leme (PBKDF2)
        
        Returns:
            (hashed_password, salt)
        """
        if not salt:
            salt = secrets.token_hex(32)
        
        # PBKDF2 ile hash
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100k iterations
        )
        
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Şifre doğrulama"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return computed_hash == hashed_password
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Güvenlik olaylarını logla"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self.logger.warning(f"SECURITY_EVENT: {log_entry}")
    
    def cleanup_old_data(self):
        """Eski rate limit ve failed attempt verilerini temizle"""
        current_time = time.time()
        
        # 1 saatlik rate limit verilerini temizle
        for identifier in list(self.rate_limits.keys()):
            self.rate_limits[identifier] = [
                req_time for req_time in self.rate_limits[identifier]
                if current_time - req_time < 3600
            ]
            
            if not self.rate_limits[identifier]:
                del self.rate_limits[identifier]
        
        # 24 saatlik failed attempt verilerini temizle
        for identifier in list(self.failed_attempts.keys()):
            if current_time - self.failed_attempts[identifier].get('last_attempt', 0) > 86400:
                del self.failed_attempts[identifier]

# Global security manager instance
security_manager = SecurityManager()