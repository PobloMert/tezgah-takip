#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Error Simulation Utilities
Test için çeşitli hata koşullarını simüle eden araçlar
"""

import os
import sys
import shutil
import sqlite3
import tempfile
import logging
import time
import threading
import subprocess
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager
import stat

class ErrorType(Enum):
    """Simüle edilebilir hata türleri"""
    PERMISSION_DENIED = "permission_denied"
    FILE_NOT_FOUND = "file_not_found"
    DISK_FULL = "disk_full"
    DATABASE_LOCKED = "database_locked"
    DATABASE_CORRUPTED = "database_corrupted"
    NETWORK_TIMEOUT = "network_timeout"
    PROCESS_CONFLICT = "process_conflict"
    ANTIVIRUS_INTERFERENCE = "antivirus_interference"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    SLOW_FILESYSTEM = "slow_filesystem"

@dataclass
class ErrorSimulationConfig:
    """Hata simülasyon konfigürasyonu"""
    error_type: ErrorType
    duration_seconds: float = 5.0
    intensity: str = "medium"  # low, medium, high
    target_path: Optional[str] = None
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}

class ErrorSimulationUtilities:
    """
    Hata simülasyon araçları
    
    Test senaryoları için çeşitli hata koşullarını simüle eder:
    - Dosya izin hataları
    - Disk dolu durumu
    - Veritabanı kilitleme
    - Bozuk veritabanı dosyaları
    - Process çakışmaları
    - Antivirüs müdahalesi
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Error Simulation Utilities başlat
        
        Args:
            temp_dir: Geçici dosyalar için dizin
        """
        self.logger = logging.getLogger(__name__)
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="error_sim_")
        self.active_simulations: List[Dict[str, Any]] = []
        self.cleanup_callbacks: List[Callable] = []
        
        # Temp dizini oluştur
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.logger.info(f"🎭 Error Simulation Utilities başlatıldı: {self.temp_dir}")
    
    def simulate_permission_error(self, target_path: str, config: ErrorSimulationConfig) -> Dict[str, Any]:
        """
        Dosya izin hatası simülasyonu
        
        Args:
            target_path: Hedef dosya/dizin yolu
            config: Simülasyon konfigürasyonu
            
        Returns:
            Dict: Simülasyon bilgileri
        """
        try:
            self.logger.info(f"🔒 Permission error simülasyonu başlatılıyor: {target_path}")
            
            # Orijinal izinleri kaydet
            original_permissions = None
            if os.path.exists(target_path):
                original_permissions = os.stat(target_path).st_mode
            
            # Yeni izinleri ayarla (intensity'ye göre)
            if config.intensity == "low":
                # Sadece yazma iznini kaldır
                new_permissions = stat.S_IREAD
            elif config.intensity == "medium":
                # Okuma ve yazma iznini kaldır
                new_permissions = 0o000
            else:  # high
                # Tüm izinleri kaldır ve dosyayı gizle
                new_permissions = 0o000
            
            # İzinleri değiştir
            if os.path.exists(target_path):
                os.chmod(target_path, new_permissions)
            
            # Cleanup callback kaydet
            def cleanup():
                try:
                    if original_permissions and os.path.exists(target_path):
                        os.chmod(target_path, original_permissions)
                        self.logger.info(f"✅ Permission restored: {target_path}")
                except Exception as e:
                    self.logger.error(f"❌ Permission restore error: {e}")
            
            self.cleanup_callbacks.append(cleanup)
            
            # Simülasyon bilgileri
            simulation_info = {
                'type': ErrorType.PERMISSION_DENIED,
                'target_path': target_path,
                'original_permissions': original_permissions,
                'new_permissions': new_permissions,
                'cleanup_callback': cleanup,
                'start_time': time.time()
            }
            
            self.active_simulations.append(simulation_info)
            
            # Otomatik cleanup timer (eğer duration belirtilmişse)
            if config.duration_seconds > 0:
                timer = threading.Timer(config.duration_seconds, cleanup)
                timer.start()
                simulation_info['timer'] = timer
            
            self.logger.info(f"✅ Permission error simülasyonu aktif: {config.intensity} intensity")
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"❌ Permission error simulation failed: {e}")
            return {'error': str(e)}
    
    def simulate_disk_full_error(self, config: ErrorSimulationConfig) -> Dict[str, Any]:
        """
        Disk dolu hatası simülasyonu
        
        Args:
            config: Simülasyon konfigürasyonu
            
        Returns:
            Dict: Simülasyon bilgileri
        """
        try:
            self.logger.info("💾 Disk full error simülasyonu başlatılıyor...")
            
            # Büyük geçici dosya oluştur
            temp_file_path = os.path.join(self.temp_dir, "disk_full_simulator.tmp")
            
            # Intensity'ye göre dosya boyutu
            if config.intensity == "low":
                file_size_mb = 100  # 100MB
            elif config.intensity == "medium":
                file_size_mb = 500  # 500MB
            else:  # high
                file_size_mb = 1000  # 1GB
            
            # Mevcut disk alanını kontrol et
            total, used, free = shutil.disk_usage(self.temp_dir)
            free_mb = free / (1024 * 1024)
            
            # Güvenli boyut hesapla (mevcut alanın %80'i max)
            safe_size_mb = min(file_size_mb, free_mb * 0.8)
            
            if safe_size_mb < 10:
                self.logger.warning("⚠️ Insufficient disk space for simulation")
                return {'error': 'Insufficient disk space for simulation'}
            
            # Büyük dosya oluştur
            def create_large_file():
                try:
                    with open(temp_file_path, 'wb') as f:
                        chunk_size = 1024 * 1024  # 1MB chunks
                        chunks_to_write = int(safe_size_mb)
                        
                        for i in range(chunks_to_write):
                            f.write(b'0' * chunk_size)
                            if i % 100 == 0:  # Her 100MB'da log
                                self.logger.debug(f"Written {i} MB...")
                    
                    self.logger.info(f"✅ Large file created: {safe_size_mb:.1f} MB")
                    
                except Exception as e:
                    self.logger.error(f"❌ Large file creation error: {e}")
            
            # Dosyayı arka planda oluştur
            creation_thread = threading.Thread(target=create_large_file)
            creation_thread.start()
            
            # Cleanup callback
            def cleanup():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        self.logger.info(f"✅ Disk full simulation cleaned up")
                except Exception as e:
                    self.logger.error(f"❌ Disk full cleanup error: {e}")
            
            self.cleanup_callbacks.append(cleanup)
            
            # Simülasyon bilgileri
            simulation_info = {
                'type': ErrorType.DISK_FULL,
                'temp_file_path': temp_file_path,
                'file_size_mb': safe_size_mb,
                'cleanup_callback': cleanup,
                'creation_thread': creation_thread,
                'start_time': time.time()
            }
            
            self.active_simulations.append(simulation_info)
            
            # Otomatik cleanup
            if config.duration_seconds > 0:
                timer = threading.Timer(config.duration_seconds, cleanup)
                timer.start()
                simulation_info['timer'] = timer
            
            self.logger.info(f"✅ Disk full simulation active: {safe_size_mb:.1f} MB file")
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"❌ Disk full simulation failed: {e}")
            return {'error': str(e)}
    
    def simulate_database_locked_error(self, db_path: str, config: ErrorSimulationConfig) -> Dict[str, Any]:
        """
        Veritabanı kilitleme hatası simülasyonu
        
        Args:
            db_path: Veritabanı dosya yolu
            config: Simülasyon konfigürasyonu
            
        Returns:
            Dict: Simülasyon bilgileri
        """
        try:
            self.logger.info(f"🔒 Database lock simülasyonu başlatılıyor: {db_path}")
            
            # Veritabanı bağlantısı aç ve kilitle
            lock_connections = []
            
            # Intensity'ye göre kilit sayısı
            if config.intensity == "low":
                lock_count = 1
            elif config.intensity == "medium":
                lock_count = 3
            else:  # high
                lock_count = 5
            
            for i in range(lock_count):
                try:
                    conn = sqlite3.connect(db_path, timeout=0.1)
                    # Exclusive lock
                    conn.execute("BEGIN EXCLUSIVE TRANSACTION")
                    lock_connections.append(conn)
                    self.logger.debug(f"Database lock {i+1}/{lock_count} acquired")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not acquire lock {i+1}: {e}")
            
            # Cleanup callback
            def cleanup():
                try:
                    for conn in lock_connections:
                        try:
                            conn.rollback()
                            conn.close()
                        except:
                            pass
                    self.logger.info(f"✅ Database locks released: {len(lock_connections)} connections")
                except Exception as e:
                    self.logger.error(f"❌ Database lock cleanup error: {e}")
            
            self.cleanup_callbacks.append(cleanup)
            
            # Simülasyon bilgileri
            simulation_info = {
                'type': ErrorType.DATABASE_LOCKED,
                'db_path': db_path,
                'lock_connections': lock_connections,
                'lock_count': len(lock_connections),
                'cleanup_callback': cleanup,
                'start_time': time.time()
            }
            
            self.active_simulations.append(simulation_info)
            
            # Otomatik cleanup
            if config.duration_seconds > 0:
                timer = threading.Timer(config.duration_seconds, cleanup)
                timer.start()
                simulation_info['timer'] = timer
            
            self.logger.info(f"✅ Database lock simulation active: {len(lock_connections)} locks")
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"❌ Database lock simulation failed: {e}")
            return {'error': str(e)}
    
    def create_corrupted_database(self, output_path: str, config: ErrorSimulationConfig) -> Dict[str, Any]:
        """
        Bozuk veritabanı dosyası oluştur
        
        Args:
            output_path: Çıktı dosya yolu
            config: Simülasyon konfigürasyonu
            
        Returns:
            Dict: Simülasyon bilgileri
        """
        try:
            self.logger.info(f"💥 Corrupted database oluşturuluyor: {output_path}")
            
            # Önce geçerli bir veritabanı oluştur
            conn = sqlite3.connect(output_path)
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS test_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        data BLOB
                    )
                ''')
                
                # Test verisi ekle
                for i in range(100):
                    cursor.execute("INSERT INTO test_table (name, data) VALUES (?, ?)",
                                 (f"Test {i}", b"test_data_" * 100))
                
                conn.commit()
                
            finally:
                conn.close()
            
            # Şimdi dosyayı boz
            corruption_methods = {
                "low": self._corrupt_database_header,
                "medium": self._corrupt_database_pages,
                "high": self._corrupt_database_completely
            }
            
            corruption_method = corruption_methods.get(config.intensity, self._corrupt_database_pages)
            corruption_info = corruption_method(output_path)
            
            # Simülasyon bilgileri
            simulation_info = {
                'type': ErrorType.DATABASE_CORRUPTED,
                'db_path': output_path,
                'corruption_method': config.intensity,
                'corruption_info': corruption_info,
                'start_time': time.time()
            }
            
            self.active_simulations.append(simulation_info)
            
            self.logger.info(f"✅ Corrupted database created: {config.intensity} corruption")
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"❌ Corrupted database creation failed: {e}")
            return {'error': str(e)}
    
    def _corrupt_database_header(self, db_path: str) -> Dict[str, Any]:
        """SQLite header'ını boz"""
        try:
            with open(db_path, 'r+b') as f:
                # SQLite header magic number'ı boz
                f.seek(0)
                f.write(b'CORRUPTED_SQLITE_HEADER')
            
            return {'method': 'header_corruption', 'location': 'header'}
            
        except Exception as e:
            return {'method': 'header_corruption', 'error': str(e)}
    
    def _corrupt_database_pages(self, db_path: str) -> Dict[str, Any]:
        """Veritabanı sayfalarını boz"""
        try:
            file_size = os.path.getsize(db_path)
            corruption_points = []
            
            with open(db_path, 'r+b') as f:
                # Dosyanın çeşitli yerlerinde bozulma yap
                for i in range(5):
                    position = (file_size // 10) * (i + 2)  # %20, %30, %40, %50, %60
                    f.seek(position)
                    f.write(b'CORRUPTED_PAGE_DATA_BLOCK')
                    corruption_points.append(position)
            
            return {'method': 'page_corruption', 'corruption_points': corruption_points}
            
        except Exception as e:
            return {'method': 'page_corruption', 'error': str(e)}
    
    def _corrupt_database_completely(self, db_path: str) -> Dict[str, Any]:
        """Veritabanını tamamen boz"""
        try:
            file_size = os.path.getsize(db_path)
            
            with open(db_path, 'r+b') as f:
                # Dosyanın %50'sini rastgele verilerle doldur
                f.seek(file_size // 4)
                corruption_data = b'COMPLETELY_CORRUPTED_DATABASE_FILE' * (file_size // 100)
                f.write(corruption_data[:file_size // 2])
            
            return {'method': 'complete_corruption', 'corruption_size': file_size // 2}
            
        except Exception as e:
            return {'method': 'complete_corruption', 'error': str(e)}
    
    def simulate_process_conflict(self, config: ErrorSimulationConfig) -> Dict[str, Any]:
        """
        Process çakışması simülasyonu
        
        Args:
            config: Simülasyon konfigürasyonu
            
        Returns:
            Dict: Simülasyon bilgileri
        """
        try:
            self.logger.info("⚔️ Process conflict simülasyonu başlatılıyor...")
            
            # Dummy process'ler başlat
            processes = []
            
            # Intensity'ye göre process sayısı
            if config.intensity == "low":
                process_count = 2
            elif config.intensity == "medium":
                process_count = 5
            else:  # high
                process_count = 10
            
            for i in range(process_count):
                try:
                    # Python subprocess ile dummy process
                    process = subprocess.Popen([
                        sys.executable, '-c',
                        f'import time; print("Dummy process {i}"); time.sleep({config.duration_seconds})'
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    processes.append(process)
                    self.logger.debug(f"Dummy process {i} started: PID {process.pid}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not start dummy process {i}: {e}")
            
            # Cleanup callback
            def cleanup():
                try:
                    for process in processes:
                        try:
                            process.terminate()
                            process.wait(timeout=5)
                        except:
                            try:
                                process.kill()
                            except:
                                pass
                    self.logger.info(f"✅ Process conflict simulation cleaned up: {len(processes)} processes")
                except Exception as e:
                    self.logger.error(f"❌ Process conflict cleanup error: {e}")
            
            self.cleanup_callbacks.append(cleanup)
            
            # Simülasyon bilgileri
            simulation_info = {
                'type': ErrorType.PROCESS_CONFLICT,
                'processes': processes,
                'process_count': len(processes),
                'cleanup_callback': cleanup,
                'start_time': time.time()
            }
            
            self.active_simulations.append(simulation_info)
            
            # Otomatik cleanup
            if config.duration_seconds > 0:
                timer = threading.Timer(config.duration_seconds, cleanup)
                timer.start()
                simulation_info['timer'] = timer
            
            self.logger.info(f"✅ Process conflict simulation active: {len(processes)} processes")
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"❌ Process conflict simulation failed: {e}")
            return {'error': str(e)}
    
    def simulate_slow_filesystem(self, config: ErrorSimulationConfig) -> Dict[str, Any]:
        """
        Yavaş dosya sistemi simülasyonu
        
        Args:
            config: Simülasyon konfigürasyonu
            
        Returns:
            Dict: Simülasyon bilgileri
        """
        try:
            self.logger.info("🐌 Slow filesystem simülasyonu başlatılıyor...")
            
            # Intensity'ye göre gecikme
            if config.intensity == "low":
                delay_seconds = 0.5
            elif config.intensity == "medium":
                delay_seconds = 2.0
            else:  # high
                delay_seconds = 5.0
            
            # Dosya I/O işlemlerini yavaşlat
            original_open = open
            
            def slow_open(*args, **kwargs):
                time.sleep(delay_seconds)
                return original_open(*args, **kwargs)
            
            # Monkey patch
            import builtins
            builtins.open = slow_open
            
            # Cleanup callback
            def cleanup():
                try:
                    builtins.open = original_open
                    self.logger.info("✅ Slow filesystem simulation cleaned up")
                except Exception as e:
                    self.logger.error(f"❌ Slow filesystem cleanup error: {e}")
            
            self.cleanup_callbacks.append(cleanup)
            
            # Simülasyon bilgileri
            simulation_info = {
                'type': ErrorType.SLOW_FILESYSTEM,
                'delay_seconds': delay_seconds,
                'cleanup_callback': cleanup,
                'start_time': time.time()
            }
            
            self.active_simulations.append(simulation_info)
            
            # Otomatik cleanup
            if config.duration_seconds > 0:
                timer = threading.Timer(config.duration_seconds, cleanup)
                timer.start()
                simulation_info['timer'] = timer
            
            self.logger.info(f"✅ Slow filesystem simulation active: {delay_seconds}s delay")
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"❌ Slow filesystem simulation failed: {e}")
            return {'error': str(e)}
    
    @contextmanager
    def temporary_error_simulation(self, error_type: ErrorType, **kwargs):
        """
        Context manager for temporary error simulation
        
        Args:
            error_type: Hata türü
            **kwargs: Simülasyon parametreleri
            
        Usage:
            with error_sim.temporary_error_simulation(ErrorType.PERMISSION_DENIED, target_path="test.db"):
                # Test code here
                pass
        """
        config = ErrorSimulationConfig(
            error_type=error_type,
            **kwargs
        )
        
        simulation_info = None
        
        try:
            # Simülasyonu başlat
            if error_type == ErrorType.PERMISSION_DENIED:
                simulation_info = self.simulate_permission_error(kwargs.get('target_path', ''), config)
            elif error_type == ErrorType.DISK_FULL:
                simulation_info = self.simulate_disk_full_error(config)
            elif error_type == ErrorType.DATABASE_LOCKED:
                simulation_info = self.simulate_database_locked_error(kwargs.get('db_path', ''), config)
            elif error_type == ErrorType.PROCESS_CONFLICT:
                simulation_info = self.simulate_process_conflict(config)
            elif error_type == ErrorType.SLOW_FILESYSTEM:
                simulation_info = self.simulate_slow_filesystem(config)
            else:
                raise ValueError(f"Unsupported error type: {error_type}")
            
            yield simulation_info
            
        finally:
            # Cleanup
            if simulation_info and 'cleanup_callback' in simulation_info:
                simulation_info['cleanup_callback']()
    
    def cleanup_all_simulations(self):
        """Tüm aktif simülasyonları temizle"""
        try:
            self.logger.info(f"🧹 Cleaning up {len(self.active_simulations)} active simulations...")
            
            # Cleanup callbacks'leri çalıştır
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"❌ Cleanup callback error: {e}")
            
            # Timer'ları durdur
            for simulation in self.active_simulations:
                if 'timer' in simulation:
                    try:
                        simulation['timer'].cancel()
                    except:
                        pass
            
            # Temp dizini temizle
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            # Listeleri temizle
            self.active_simulations.clear()
            self.cleanup_callbacks.clear()
            
            self.logger.info("✅ All simulations cleaned up")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup all simulations error: {e}")
    
    def get_active_simulations(self) -> List[Dict[str, Any]]:
        """Aktif simülasyonları al"""
        return [
            {
                'type': sim['type'].value,
                'start_time': sim['start_time'],
                'duration': time.time() - sim['start_time'],
                'details': {k: v for k, v in sim.items() 
                           if k not in ['cleanup_callback', 'timer', 'lock_connections', 'processes']}
            }
            for sim in self.active_simulations
        ]
    
    def __del__(self):
        """Destructor - cleanup"""
        try:
            self.cleanup_all_simulations()
        except:
            pass

# Test utilities
def create_test_database_files(output_dir: str) -> Dict[str, str]:
    """
    Test için çeşitli veritabanı dosyaları oluştur
    
    Args:
        output_dir: Çıktı dizini
        
    Returns:
        Dict: Oluşturulan dosya yolları
    """
    os.makedirs(output_dir, exist_ok=True)
    
    files = {}
    error_sim = ErrorSimulationUtilities()
    
    try:
        # Normal veritabanı
        normal_db = os.path.join(output_dir, "normal_test.db")
        conn = sqlite3.connect(normal_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES ('test_data')")
        conn.commit()
        conn.close()
        files['normal'] = normal_db
        
        # Bozuk veritabanları
        for intensity in ['low', 'medium', 'high']:
            corrupted_db = os.path.join(output_dir, f"corrupted_{intensity}_test.db")
            config = ErrorSimulationConfig(
                error_type=ErrorType.DATABASE_CORRUPTED,
                intensity=intensity
            )
            error_sim.create_corrupted_database(corrupted_db, config)
            files[f'corrupted_{intensity}'] = corrupted_db
        
        return files
        
    finally:
        error_sim.cleanup_all_simulations()

if __name__ == "__main__":
    # Test runner
    logging.basicConfig(level=logging.INFO)
    
    # Test error simulation
    error_sim = ErrorSimulationUtilities()
    
    try:
        print("🎭 Error Simulation Utilities Test")
        print("=" * 50)
        
        # Test corrupted database creation
        test_db = os.path.join(error_sim.temp_dir, "test_corrupted.db")
        config = ErrorSimulationConfig(
            error_type=ErrorType.DATABASE_CORRUPTED,
            intensity="medium"
        )
        
        result = error_sim.create_corrupted_database(test_db, config)
        print(f"Corrupted database test: {result}")
        
        # Test context manager
        with error_sim.temporary_error_simulation(
            ErrorType.SLOW_FILESYSTEM,
            intensity="low",
            duration_seconds=2.0
        ) as sim_info:
            print(f"Temporary simulation: {sim_info}")
            # Simulate some file operation
            time.sleep(1)
        
        print("✅ All tests completed")
        
    finally:
        error_sim.cleanup_all_simulations()