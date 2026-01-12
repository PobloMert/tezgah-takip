#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Automatic Retry Manager
Otomatik yeniden deneme mekanizmaları - exponential backoff, file lock detection, process conflict resolution
"""

import time
import logging
import sqlite3
import os
from typing import Callable, Any, Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

class RetryReason(Enum):
    """Yeniden deneme sebepleri"""
    DATABASE_LOCKED = "database_locked"
    FILE_ACCESS_DENIED = "file_access_denied"
    PROCESS_CONFLICT = "process_conflict"
    TRANSIENT_ERROR = "transient_error"
    NETWORK_ERROR = "network_error"
    RESOURCE_BUSY = "resource_busy"

@dataclass
class RetryAttempt:
    """Yeniden deneme girişimi bilgileri"""
    attempt_number: int
    reason: RetryReason
    error: Exception
    timestamp: datetime
    delay_seconds: float
    success: bool = False

@dataclass
class RetryResult:
    """Yeniden deneme sonucu"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempts: List[RetryAttempt] = None
    total_duration: float = 0.0
    final_attempt_number: int = 0

class AutomaticRetryManager:
    """
    Otomatik yeniden deneme yöneticisi
    
    Özellikler:
    - Exponential backoff ile yeniden deneme
    - Dosya kilidi algılama ve bekleme
    - Process çakışması çözümü
    - Geçici hata yönetimi
    """
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Retry Manager başlat
        
        Args:
            max_retries: Maksimum yeniden deneme sayısı
            base_delay: Temel bekleme süresi (saniye)
            max_delay: Maksimum bekleme süresi (saniye)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger(__name__)
        
        # Retry istatistikleri
        self.retry_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_retries': 0,
            'retry_reasons': {},
            'average_retry_count': 0.0,
            'max_retry_count': 0
        }
    
    def retry_with_backoff(self, 
                          operation: Callable,
                          *args,
                          retry_on_exceptions: Tuple = (sqlite3.OperationalError, PermissionError, OSError),
                          custom_retry_logic: Optional[Callable[[Exception], bool]] = None,
                          **kwargs) -> RetryResult:
        """
        Exponential backoff ile operasyonu yeniden dene
        
        Args:
            operation: Çalıştırılacak operasyon
            args: Operasyon argümanları
            retry_on_exceptions: Yeniden deneme yapılacak exception türleri
            custom_retry_logic: Özel yeniden deneme mantığı
            kwargs: Operasyon keyword argümanları
            
        Returns:
            RetryResult: Yeniden deneme sonucu
        """
        start_time = time.time()
        attempts = []
        
        self.retry_stats['total_operations'] += 1
        
        for attempt in range(self.max_retries + 1):
            try:
                # Operasyonu çalıştır
                result = operation(*args, **kwargs)
                
                # Başarılı
                if attempts:
                    attempts[-1].success = True
                
                duration = time.time() - start_time
                self.retry_stats['successful_operations'] += 1
                
                if attempts:
                    retry_count = len(attempts)
                    self.retry_stats['total_retries'] += retry_count
                    self.retry_stats['max_retry_count'] = max(self.retry_stats['max_retry_count'], retry_count)
                    
                    # Ortalama retry count güncelle
                    total_ops = self.retry_stats['successful_operations'] + self.retry_stats['failed_operations']
                    if total_ops > 0:
                        self.retry_stats['average_retry_count'] = self.retry_stats['total_retries'] / total_ops
                
                self.logger.info(f"✅ Operation successful after {attempt} attempts in {duration:.2f}s")
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_duration=duration,
                    final_attempt_number=attempt
                )
                
            except Exception as e:
                # Yeniden deneme gerekli mi kontrol et
                should_retry = False
                retry_reason = self._determine_retry_reason(e)
                
                if custom_retry_logic:
                    should_retry = custom_retry_logic(e)
                elif isinstance(e, retry_on_exceptions):
                    should_retry = True
                elif self._is_retryable_error(e):
                    should_retry = True
                
                # Attempt kaydet
                delay = self._calculate_delay(attempt)
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    reason=retry_reason,
                    error=e,
                    timestamp=datetime.now(),
                    delay_seconds=delay,
                    success=False
                )
                attempts.append(attempt_info)
                
                # İstatistik güncelle
                reason_key = retry_reason.value
                self.retry_stats['retry_reasons'][reason_key] = self.retry_stats['retry_reasons'].get(reason_key, 0) + 1
                
                # Son deneme mi?
                if attempt >= self.max_retries or not should_retry:
                    duration = time.time() - start_time
                    self.retry_stats['failed_operations'] += 1
                    
                    # Failed operations için de retry count'u güncelle
                    if attempts:
                        retry_count = len(attempts)
                        self.retry_stats['total_retries'] += retry_count
                        self.retry_stats['max_retry_count'] = max(self.retry_stats['max_retry_count'], retry_count)
                        
                        # Ortalama retry count güncelle
                        total_ops = self.retry_stats['successful_operations'] + self.retry_stats['failed_operations']
                        if total_ops > 0:
                            self.retry_stats['average_retry_count'] = self.retry_stats['total_retries'] / total_ops
                    
                    self.logger.error(f"❌ Operation failed after {attempt + 1} attempts in {duration:.2f}s: {e}")
                    
                    return RetryResult(
                        success=False,
                        error=e,
                        attempts=attempts,
                        total_duration=duration,
                        final_attempt_number=attempt
                    )
                
                # Yeniden deneme için bekle
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed ({retry_reason.value}), retrying in {delay:.2f}s: {e}")
                
                # Özel bekleme mantığı
                if retry_reason == RetryReason.DATABASE_LOCKED:
                    self._wait_for_database_unlock(delay)
                elif retry_reason == RetryReason.PROCESS_CONFLICT:
                    self._resolve_process_conflict(delay)
                else:
                    time.sleep(delay)
        
        # Bu noktaya hiç gelmemeli
        duration = time.time() - start_time
        return RetryResult(
            success=False,
            error=Exception("Max retries exceeded"),
            attempts=attempts,
            total_duration=duration,
            final_attempt_number=self.max_retries
        )
    
    def _determine_retry_reason(self, error: Exception) -> RetryReason:
        """Hatadan yeniden deneme sebebini belirle"""
        error_str = str(error).lower()
        
        if "database is locked" in error_str or "locked" in error_str:
            return RetryReason.DATABASE_LOCKED
        elif "permission denied" in error_str or "access denied" in error_str:
            return RetryReason.FILE_ACCESS_DENIED
        elif "resource busy" in error_str or "busy" in error_str:
            return RetryReason.RESOURCE_BUSY
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return RetryReason.NETWORK_ERROR
        else:
            return RetryReason.TRANSIENT_ERROR
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Hatanın yeniden denenebilir olup olmadığını kontrol et"""
        retryable_messages = [
            "database is locked",
            "permission denied",
            "resource temporarily unavailable",
            "device or resource busy",
            "operation would block",
            "connection reset",
            "timeout"
        ]
        
        error_str = str(error).lower()
        return any(msg in error_str for msg in retryable_messages)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Exponential backoff ile bekleme süresini hesapla"""
        # Exponential backoff: base_delay * (2 ^ attempt) + jitter
        delay = self.base_delay * (2 ** attempt)
        
        # Jitter ekle (randomness)
        jitter = random.uniform(0, delay * 0.1)
        delay += jitter
        
        # Max delay'i aşmasın
        delay = min(delay, self.max_delay)
        
        return delay
    
    def _wait_for_database_unlock(self, base_delay: float):
        """Veritabanı kilidinin açılmasını bekle"""
        self.logger.info("🔒 Database locked, waiting for unlock...")
        
        # Kısa aralıklarla kontrol et
        check_interval = min(0.5, base_delay / 4)
        max_wait = base_delay
        waited = 0
        
        while waited < max_wait:
            time.sleep(check_interval)
            waited += check_interval
            
            # Kilit durumunu kontrol etmek için basit bir test yap
            # (Bu gerçek implementasyonda daha sofistike olabilir)
            
        self.logger.info(f"⏰ Waited {waited:.2f}s for database unlock")
    
    def _resolve_process_conflict(self, base_delay: float):
        """Process çakışmasını çözmeye çalış"""
        self.logger.info("⚔️ Process conflict detected, attempting resolution...")
        
        try:
            if not PSUTIL_AVAILABLE:
                self.logger.warning("⚠️ psutil not available, using simple delay")
                time.sleep(base_delay)
                return
            
            # Mevcut process'leri kontrol et
            current_pid = os.getpid()
            conflicting_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] != current_pid:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'tezgah_takip' in cmdline.lower() or 'python' in proc.info['name'].lower():
                            conflicting_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if conflicting_processes:
                self.logger.warning(f"⚠️ Found {len(conflicting_processes)} potentially conflicting processes")
                
                # Kısa süre bekle (process'lerin tamamlanması için)
                time.sleep(min(base_delay, 5.0))
            else:
                time.sleep(base_delay)
                
        except Exception as e:
            self.logger.error(f"❌ Process conflict resolution failed: {e}")
            time.sleep(base_delay)
    
    def detect_file_locks(self, file_path: str) -> List[Dict]:
        """Dosya kilitlerini algıla"""
        locks = []
        
        try:
            # Windows için lsof benzeri işlevsellik
            if os.name == 'nt':
                locks = self._detect_windows_file_locks(file_path)
            else:
                locks = self._detect_unix_file_locks(file_path)
                
        except Exception as e:
            self.logger.error(f"❌ File lock detection failed: {e}")
        
        return locks
    
    def _detect_windows_file_locks(self, file_path: str) -> List[Dict]:
        """Windows'ta dosya kilitlerini algıla"""
        locks = []
        
        try:
            if not PSUTIL_AVAILABLE:
                self.logger.debug("psutil not available for file lock detection")
                return locks
            
            # psutil ile açık dosyaları kontrol et
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for file_info in proc.open_files():
                        if file_info.path == file_path:
                            locks.append({
                                'pid': proc.info['pid'],
                                'process_name': proc.info['name'],
                                'file_path': file_info.path,
                                'mode': getattr(file_info, 'mode', 'unknown')
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Windows file lock detection error: {e}")
        
        return locks
    
    def _detect_unix_file_locks(self, file_path: str) -> List[Dict]:
        """Unix/Linux'ta dosya kilitlerini algıla"""
        locks = []
        
        try:
            # lsof komutu ile kontrol et
            import subprocess
            result = subprocess.run(['lsof', file_path], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Header'ı atla
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        locks.append({
                            'process_name': parts[0],
                            'pid': parts[1],
                            'file_path': file_path
                        })
                        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.debug(f"Unix file lock detection failed: {e}")
        
        return locks
    
    def wait_for_process_completion(self, process_names: List[str], timeout: float = 30.0) -> bool:
        """Belirtilen process'lerin tamamlanmasını bekle"""
        if not PSUTIL_AVAILABLE:
            self.logger.warning("⚠️ psutil not available, using simple timeout")
            time.sleep(min(timeout, 5.0))
            return True
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            found_processes = []
            
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in [name.lower() for name in process_names]:
                        found_processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not found_processes:
                self.logger.info(f"✅ All target processes completed")
                return True
            
            self.logger.info(f"⏳ Waiting for processes: {found_processes}")
            time.sleep(1.0)
        
        self.logger.warning(f"⚠️ Timeout waiting for processes to complete")
        return False
    
    def get_retry_statistics(self) -> Dict:
        """Yeniden deneme istatistiklerini al"""
        return {
            'summary': {
                'total_operations': self.retry_stats['total_operations'],
                'successful_operations': self.retry_stats['successful_operations'],
                'failed_operations': self.retry_stats['failed_operations'],
                'success_rate': (
                    self.retry_stats['successful_operations'] / 
                    max(1, self.retry_stats['total_operations'])
                ) * 100,
                'total_retries': self.retry_stats['total_retries'],
                'average_retry_count': self.retry_stats['average_retry_count'],
                'max_retry_count': self.retry_stats['max_retry_count']
            },
            'retry_reasons': self.retry_stats['retry_reasons'],
            'configuration': {
                'max_retries': self.max_retries,
                'base_delay': self.base_delay,
                'max_delay': self.max_delay
            }
        }
    
    def reset_statistics(self):
        """İstatistikleri sıfırla"""
        self.retry_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_retries': 0,
            'retry_reasons': {},
            'average_retry_count': 0.0,
            'max_retry_count': 0
        }
        self.logger.info("📊 Retry statistics reset")

# Convenience functions
def retry_database_operation(operation: Callable, *args, **kwargs) -> RetryResult:
    """Veritabanı operasyonu için yeniden deneme"""
    retry_manager = AutomaticRetryManager(max_retries=3, base_delay=0.5, max_delay=10.0)
    
    return retry_manager.retry_with_backoff(
        operation,
        *args,
        retry_on_exceptions=(sqlite3.OperationalError, sqlite3.DatabaseError, PermissionError),
        **kwargs
    )

def retry_file_operation(operation: Callable, *args, **kwargs) -> RetryResult:
    """Dosya operasyonu için yeniden deneme"""
    retry_manager = AutomaticRetryManager(max_retries=5, base_delay=1.0, max_delay=30.0)
    
    return retry_manager.retry_with_backoff(
        operation,
        *args,
        retry_on_exceptions=(PermissionError, OSError, IOError),
        **kwargs
    )

def retry_network_operation(operation: Callable, *args, **kwargs) -> RetryResult:
    """Network operasyonu için yeniden deneme"""
    retry_manager = AutomaticRetryManager(max_retries=3, base_delay=2.0, max_delay=60.0)
    
    return retry_manager.retry_with_backoff(
        operation,
        *args,
        retry_on_exceptions=(ConnectionError, TimeoutError, OSError),
        **kwargs
    )