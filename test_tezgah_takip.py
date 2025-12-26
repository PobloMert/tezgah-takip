#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Unit Tests
Tüm modüller için kapsamlı test suite
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Test için gerekli modülleri import et
try:
    from database_models import DatabaseManager, Tezgah, Bakim, Pil, validate_tezgah_numarasi, validate_text_field
    from api_key_manager import APIKeyManager
    from backup_manager import BackupManager
    from config_manager import ConfigManager
    from accessibility_manager import AccessibilityManager
    from progress_manager import ProgressManager
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class TestDatabaseModels(unittest.TestCase):
    """Database models test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(self.test_db_path)
    
    def tearDown(self):
        """Test cleanup"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_creation(self):
        """Veritabanı oluşturma testi"""
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Tablo sayısını kontrol et
        tezgah_count = self.db_manager.get_tezgah_count()
        self.assertGreaterEqual(tezgah_count, 0)
    
    def test_tezgah_validation(self):
        """Tezgah validasyon testi"""
        # Geçerli tezgah numarası
        valid_no = validate_tezgah_numarasi("TZ001")
        self.assertEqual(valid_no, "TZ001")
        
        # Geçersiz tezgah numarası
        with self.assertRaises(ValueError):
            validate_tezgah_numarasi("")
        
        with self.assertRaises(ValueError):
            validate_tezgah_numarasi("T")  # Çok kısa
        
        with self.assertRaises(ValueError):
            validate_tezgah_numarasi("TZ001@")  # Geçersiz karakter
    
    def test_text_field_validation(self):
        """Metin alanı validasyon testi"""
        # Geçerli metin
        valid_text = validate_text_field("Test Açıklama", "Açıklama", min_len=5, max_len=50)
        self.assertEqual(valid_text, "Test Açıklama")
        
        # Çok kısa metin
        with self.assertRaises(ValueError):
            validate_text_field("Test", "Açıklama", min_len=5, max_len=50)
        
        # Çok uzun metin
        with self.assertRaises(ValueError):
            validate_text_field("A" * 100, "Açıklama", min_len=5, max_len=50)
        
        # Tehlikeli karakter
        with self.assertRaises(ValueError):
            validate_text_field("Test<script>", "Açıklama")
    
    def test_tezgah_crud_operations(self):
        """Tezgah CRUD işlemleri testi"""
        with self.db_manager.get_session() as session:
            # Create
            tezgah = Tezgah(
                numarasi="TEST001",
                aciklama="Test Tezgahı",
                lokasyon="Test Atölyesi",
                durum="Aktif",
                bakim_periyodu=30
            )
            session.add(tezgah)
            session.commit()
            
            # Read
            found_tezgah = session.query(Tezgah).filter_by(numarasi="TEST001").first()
            self.assertIsNotNone(found_tezgah)
            self.assertEqual(found_tezgah.aciklama, "Test Tezgahı")
            
            # Update
            found_tezgah.durum = "Bakımda"
            session.commit()
            
            updated_tezgah = session.query(Tezgah).filter_by(numarasi="TEST001").first()
            self.assertEqual(updated_tezgah.durum, "Bakımda")
            
            # Delete
            session.delete(found_tezgah)
            session.commit()
            
            deleted_tezgah = session.query(Tezgah).filter_by(numarasi="TEST001").first()
            self.assertIsNone(deleted_tezgah)

class TestAPIKeyManager(unittest.TestCase):
    """API Key Manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.test_key_file = tempfile.mktemp(suffix='.enc')
        self.test_encryption_file = tempfile.mktemp(suffix='.key')
        self.api_manager = APIKeyManager(self.test_key_file, self.test_encryption_file)
    
    def tearDown(self):
        """Test cleanup"""
        for file_path in [self.test_key_file, self.test_encryption_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def test_api_key_storage(self):
        """API anahtarı saklama testi"""
        test_key = "test_api_key_12345"
        
        # API anahtarını kaydet
        success = self.api_manager.save_api_key(test_key)
        self.assertTrue(success)
        
        # API anahtarını kontrol et
        self.assertTrue(self.api_manager.has_api_key())
        
        # API anahtarını al
        retrieved_key = self.api_manager.get_api_key()
        self.assertEqual(retrieved_key, test_key)
    
    def test_api_key_validation(self):
        """API anahtarı validasyon testi"""
        # Geçersiz API anahtarı
        invalid_keys = ["", "short", "a" * 300]  # Boş, çok kısa, çok uzun
        
        for invalid_key in invalid_keys:
            success = self.api_manager.save_api_key(invalid_key)
            self.assertFalse(success)
    
    def test_api_key_deletion(self):
        """API anahtarı silme testi"""
        test_key = "test_api_key_to_delete"
        
        # API anahtarını kaydet
        self.api_manager.save_api_key(test_key)
        self.assertTrue(self.api_manager.has_api_key())
        
        # API anahtarını sil
        success = self.api_manager.delete_api_key()
        self.assertTrue(success)
        self.assertFalse(self.api_manager.has_api_key())

class TestBackupManager(unittest.TestCase):
    """Backup Manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test.db")
        
        # Test veritabanı oluştur
        import sqlite3
        conn = sqlite3.connect(self.test_db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES ('Test Data')")
        conn.commit()
        conn.close()
        
        self.backup_manager = BackupManager(self.test_db_path)
    
    def tearDown(self):
        """Test cleanup"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_backup_creation(self):
        """Yedek oluşturma testi"""
        # Basit yedek
        success, result = self.backup_manager.create_backup(compressed=False)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(result))
        
        # Sıkıştırılmış yedek
        success, result = self.backup_manager.create_backup(compressed=True)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(result))
    
    def test_backup_listing(self):
        """Yedek listeleme testi"""
        # Yedek oluştur
        self.backup_manager.create_backup(compressed=True)
        
        # Yedekleri listele
        backups = self.backup_manager.list_backups()
        self.assertGreater(len(backups), 0)
        
        # İlk yedek bilgilerini kontrol et
        backup = backups[0]
        self.assertIn('filename', backup)
        self.assertIn('size_bytes', backup)
        self.assertIn('created_at', backup)
    
    def test_backup_statistics(self):
        """Yedek istatistikleri testi"""
        # Yedek oluştur
        self.backup_manager.create_backup(compressed=True)
        
        # İstatistikleri al
        stats = self.backup_manager.get_backup_statistics()
        
        self.assertIn('total_backups', stats)
        self.assertIn('total_size_mb', stats)
        self.assertGreater(stats['total_backups'], 0)

class TestConfigManager(unittest.TestCase):
    """Config Manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.test_config_file = tempfile.mktemp(suffix='.json')
        self.config_manager = ConfigManager(self.test_config_file)
    
    def tearDown(self):
        """Test cleanup"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
    
    def test_config_get_set(self):
        """Config get/set testi"""
        # Set value
        success = self.config_manager.set("test.value", "test_data")
        self.assertTrue(success)
        
        # Get value
        value = self.config_manager.get("test.value")
        self.assertEqual(value, "test_data")
        
        # Get non-existent value with default
        default_value = self.config_manager.get("non.existent", "default")
        self.assertEqual(default_value, "default")
    
    def test_config_sections(self):
        """Config section'ları testi"""
        # Database config
        db_config = self.config_manager.get_database_config()
        self.assertIsInstance(db_config, dict)
        self.assertIn("path", db_config)
        
        # UI config
        ui_config = self.config_manager.get_ui_config()
        self.assertIsInstance(ui_config, dict)
        self.assertIn("theme", ui_config)
    
    def test_config_validation(self):
        """Config validasyon testi"""
        is_valid, errors = self.config_manager.validate_config()
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(errors, list)
    
    def test_config_save_load(self):
        """Config kaydetme/yükleme testi"""
        # Değer ayarla
        self.config_manager.set("test.save_load", "test_value")
        
        # Kaydet
        success = self.config_manager.save_config()
        self.assertTrue(success)
        
        # Yeni instance oluştur ve yükle
        new_config = ConfigManager(self.test_config_file)
        loaded_value = new_config.get("test.save_load")
        self.assertEqual(loaded_value, "test_value")

class TestAccessibilityManager(unittest.TestCase):
    """Accessibility Manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.accessibility_manager = AccessibilityManager()
    
    def test_accessibility_settings(self):
        """Accessibility ayarları testi"""
        settings = self.accessibility_manager.get_accessibility_settings()
        
        self.assertIsInstance(settings, dict)
        self.assertIn("theme", settings)
        self.assertIn("font_size", settings)
        self.assertIn("high_contrast_enabled", settings)
    
    def test_font_sizes(self):
        """Font boyutları testi"""
        font_sizes = self.accessibility_manager.FONT_SIZES
        
        self.assertIn("small", font_sizes)
        self.assertIn("normal", font_sizes)
        self.assertIn("large", font_sizes)
        self.assertIn("extra_large", font_sizes)
        
        # Font boyutları artan sırada olmalı
        sizes = list(font_sizes.values())
        self.assertEqual(sizes, sorted(sizes))

class TestProgressManager(unittest.TestCase):
    """Progress Manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.progress_manager = ProgressManager()
    
    def test_progress_manager_creation(self):
        """Progress manager oluşturma testi"""
        self.assertIsNotNone(self.progress_manager)
        self.assertEqual(len(self.progress_manager.active_dialogs), 0)
        self.assertEqual(len(self.progress_manager.active_indicators), 0)
    
    def test_inline_indicator_creation(self):
        """Inline indicator oluşturma testi"""
        indicator = self.progress_manager.create_inline_indicator()
        self.assertIsNotNone(indicator)
        self.assertIn(indicator, self.progress_manager.active_indicators)

class TestIntegration(unittest.TestCase):
    """Entegrasyon testleri"""
    
    def setUp(self):
        """Test setup"""
        self.test_dir = tempfile.mkdtemp()
        
        # Test dosya yolları
        self.test_db_path = os.path.join(self.test_dir, "integration_test.db")
        self.test_config_path = os.path.join(self.test_dir, "config.json")
        
        # Managers
        self.config_manager = ConfigManager(self.test_config_path)
        self.db_manager = DatabaseManager(self.test_db_path)
        self.backup_manager = BackupManager(self.test_db_path)
    
    def tearDown(self):
        """Test cleanup"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_config_database_integration(self):
        """Config ve database entegrasyonu testi"""
        # Config'den database path'i al
        db_path = self.config_manager.get("database.path")
        self.assertIsNotNone(db_path)
        
        # Database manager ile tezgah sayısını al
        tezgah_count = self.db_manager.get_tezgah_count()
        self.assertGreaterEqual(tezgah_count, 0)
    
    def test_database_backup_integration(self):
        """Database ve backup entegrasyonu testi"""
        # Test verisi ekle
        with self.db_manager.get_session() as session:
            tezgah = Tezgah(
                numarasi="INT001",
                aciklama="Integration Test Tezgahı",
                durum="Aktif"
            )
            session.add(tezgah)
        
        # Yedek oluştur
        success, result = self.backup_manager.create_backup(compressed=True)
        self.assertTrue(success)
        
        # Yedek dosyasının var olduğunu kontrol et
        self.assertTrue(os.path.exists(result))
    
    def test_full_workflow(self):
        """Tam iş akışı testi"""
        # 1. Tezgah ekle
        with self.db_manager.get_session() as session:
            tezgah = Tezgah(
                numarasi="WF001",
                aciklama="Workflow Test Tezgahı",
                lokasyon="Test Atölyesi",
                durum="Aktif",
                bakim_periyodu=30
            )
            session.add(tezgah)
            session.commit()
            tezgah_id = tezgah.id
        
        # 2. Bakım kaydı ekle
        with self.db_manager.get_session() as session:
            bakim = Bakim(
                tezgah_id=tezgah_id,
                tarih=datetime.now(timezone.utc),
                bakim_yapan="Test Teknisyen",
                aciklama="Test bakım işlemi",
                durum="Tamamlandı"
            )
            session.add(bakim)
        
        # 3. Pil kaydı ekle
        with self.db_manager.get_session() as session:
            pil = Pil(
                tezgah_id=tezgah_id,
                eksen="X",
                pil_modeli="Test Pil Model",
                degisim_tarihi=datetime.now(timezone.utc),
                degistiren_kisi="Test Teknisyen"
            )
            session.add(pil)
        
        # 4. Verileri kontrol et
        tezgah_count = self.db_manager.get_tezgah_count()
        self.assertGreater(tezgah_count, 0)
        
        # 5. Yedek oluştur
        success, backup_path = self.backup_manager.create_backup(compressed=True)
        self.assertTrue(success)
        
        # 6. Yedek listesini kontrol et
        backups = self.backup_manager.list_backups()
        self.assertGreater(len(backups), 0)

def run_all_tests():
    """Tüm testleri çalıştır"""
    print("🧪 TezgahTakip Unit Tests Başlıyor...")
    print("=" * 60)
    
    # Test suite oluştur
    test_suite = unittest.TestSuite()
    
    # Test sınıflarını ekle
    test_classes = [
        TestDatabaseModels,
        TestAPIKeyManager,
        TestBackupManager,
        TestConfigManager,
        TestAccessibilityManager,
        TestProgressManager,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✅ Tüm testler başarılı!")
        return True
    else:
        print(f"❌ {len(result.failures)} test başarısız, {len(result.errors)} hata")
        
        if result.failures:
            print("\n🔴 Başarısız Testler:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
        
        if result.errors:
            print("\n💥 Hatalı Testler:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('\\n')[-2]}")
        
        return False

def run_specific_test(test_class_name: str):
    """Belirli bir test sınıfını çalıştır"""
    test_classes = {
        'database': TestDatabaseModels,
        'api': TestAPIKeyManager,
        'backup': TestBackupManager,
        'config': TestConfigManager,
        'accessibility': TestAccessibilityManager,
        'progress': TestProgressManager,
        'integration': TestIntegration
    }
    
    if test_class_name.lower() in test_classes:
        test_class = test_classes[test_class_name.lower()]
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    else:
        print(f"❌ Bilinmeyen test sınıfı: {test_class_name}")
        print(f"Mevcut test sınıfları: {', '.join(test_classes.keys())}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TezgahTakip Unit Tests")
    parser.add_argument("--test", "-t", help="Belirli bir test sınıfını çalıştır", default=None)
    parser.add_argument("--list", "-l", action="store_true", help="Mevcut test sınıflarını listele")
    
    args = parser.parse_args()
    
    if args.list:
        print("Mevcut test sınıfları:")
        print("- database: Database models testleri")
        print("- api: API key manager testleri")
        print("- backup: Backup manager testleri")
        print("- config: Config manager testleri")
        print("- accessibility: Accessibility manager testleri")
        print("- progress: Progress manager testleri")
        print("- integration: Entegrasyon testleri")
    elif args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
class TestSecurityManager(unittest.TestCase):
    """Security manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        from security_manager import SecurityManager
        self.security_manager = SecurityManager()
    
    def test_file_path_validation(self):
        """Dosya yolu validasyon testi"""
        # Geçerli path
        is_valid, message = self.security_manager.validate_file_path("test.db", "database")
        self.assertTrue(is_valid)
        
        # Path traversal saldırısı
        is_valid, message = self.security_manager.validate_file_path("../../../etc/passwd", "database")
        self.assertFalse(is_valid)
        self.assertIn("güvenlik riski", message.lower())
        
        # Absolute path
        is_valid, message = self.security_manager.validate_file_path("/etc/passwd", "database")
        self.assertFalse(is_valid)
        
        # Null byte
        is_valid, message = self.security_manager.validate_file_path("test\x00.db", "database")
        self.assertFalse(is_valid)
    
    def test_input_sanitization(self):
        """Input sanitization testi"""
        # Normal metin
        clean_text = self.security_manager.sanitize_input("Normal metin")
        self.assertEqual(clean_text, "Normal metin")
        
        # HTML injection
        dirty_html = "<script>alert('xss')</script>"
        clean_html = self.security_manager.sanitize_input(dirty_html)
        self.assertNotIn("<script>", clean_html)
        
        # Uzun metin
        long_text = "A" * 2000
        clean_long = self.security_manager.sanitize_input(long_text, max_length=100)
        self.assertEqual(len(clean_long), 100)
    
    def test_sql_table_validation(self):
        """SQL tablo adı validasyon testi"""
        allowed_tables = ['tezgah', 'bakimlar', 'pil_degisimler']
        
        # Geçerli tablo
        is_valid, message = self.security_manager.validate_sql_table_name('tezgah', allowed_tables)
        self.assertTrue(is_valid)
        
        # Geçersiz tablo
        is_valid, message = self.security_manager.validate_sql_table_name('users', allowed_tables)
        self.assertFalse(is_valid)
        
        # SQL injection denemesi
        is_valid, message = self.security_manager.validate_sql_table_name('tezgah; DROP TABLE users;', allowed_tables)
        self.assertFalse(is_valid)
    
    def test_rate_limiting(self):
        """Rate limiting testi"""
        # Normal istekler
        for i in range(5):
            is_allowed, remaining = self.security_manager.check_rate_limit("test_user", max_requests=10, time_window=60)
            self.assertTrue(is_allowed)
        
        # Rate limit aşımı
        for i in range(10):
            self.security_manager.check_rate_limit("test_user2", max_requests=5, time_window=60)
        
        is_allowed, remaining = self.security_manager.check_rate_limit("test_user2", max_requests=5, time_window=60)
        self.assertFalse(is_allowed)
        self.assertGreater(remaining, 0)

class TestPerformanceMonitor(unittest.TestCase):
    """Performance monitor test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        from performance_monitor import PerformanceMonitor
        self.perf_monitor = PerformanceMonitor()
    
    def test_metric_recording(self):
        """Metrik kaydetme testi"""
        # Metrik kaydet
        self.perf_monitor.record_metric("test_metric", 123.45, "ms", "test")
        
        # Özet al
        summary = self.perf_monitor.get_performance_summary()
        self.assertIn("metrics_count", summary)
        self.assertGreaterEqual(summary["metrics_count"], 1)
    
    def test_query_timing(self):
        """Query timing testi"""
        # Query timing kaydet
        self.perf_monitor.record_query_time("SELECT * FROM test", 0.5, 100)
        
        # Slow operations al
        slow_ops = self.perf_monitor.get_slow_operations(limit=5)
        self.assertIn("slow_queries", slow_ops)
    
    def test_monitoring_lifecycle(self):
        """Monitoring yaşam döngüsü testi"""
        # Monitoring başlat
        self.perf_monitor.start_monitoring(interval=0.1)
        self.assertTrue(self.perf_monitor.monitoring_active)
        
        # Kısa süre bekle
        import time
        time.sleep(0.2)
        
        # Monitoring durdur
        self.perf_monitor.stop_monitoring()
        self.assertFalse(self.perf_monitor.monitoring_active)

class TestAdvancedLogger(unittest.TestCase):
    """Advanced logger test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.test_log_dir = tempfile.mkdtemp()
        
        from advanced_logger import AdvancedLogger
        config = {
            'log_directory': self.test_log_dir,
            'log_level': 'DEBUG',
            'console_logging': False,
            'file_logging': True
        }
        self.logger_manager = AdvancedLogger(config)
    
    def tearDown(self):
        """Test cleanup"""
        shutil.rmtree(self.test_log_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Logger oluşturma testi"""
        logger = self.logger_manager.get_logger("test")
        self.assertIsNotNone(logger)
        
        # Log mesajı
        logger.info("Test log message")
        
        # Log dosyası oluştu mu kontrol et
        log_files = list(Path(self.test_log_dir).glob("*.log"))
        self.assertGreater(len(log_files), 0)
    
    def test_structured_logging(self):
        """Structured logging testi"""
        logger = self.logger_manager.get_logger("system")
        
        # Extra data ile log
        logger.info("Test message", extra={
            'user_id': 'test_user',
            'action': 'test_action',
            'custom_data': {'key': 'value'}
        })
        
        # Log dosyasını kontrol et
        log_files = list(Path(self.test_log_dir).glob("*.log"))
        if log_files:
            with open(log_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("test_user", content)
    
    def test_log_statistics(self):
        """Log istatistikleri testi"""
        # Birkaç log mesajı
        logger = self.logger_manager.get_logger("test")
        for i in range(5):
            logger.info(f"Test message {i}")
        
        # İstatistikleri al
        stats = self.logger_manager.get_log_statistics()
        self.assertIn("log_files", stats)
        self.assertIn("total_entries", stats)

class TestNotificationManager(unittest.TestCase):
    """Notification manager test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        from notification_manager import NotificationManager, NotificationType, NotificationPriority
        self.notification_manager = NotificationManager()
        self.NotificationType = NotificationType
        self.NotificationPriority = NotificationPriority
    
    def test_notification_creation(self):
        """Bildirim oluşturma testi"""
        notif_id = self.notification_manager.create_notification(
            title="Test Notification",
            message="Test message",
            notification_type=self.NotificationType.INFO,
            priority=self.NotificationPriority.NORMAL
        )
        
        self.assertIsNotNone(notif_id)
        
        # Bildirimi al
        notifications = self.notification_manager.get_notifications()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].title, "Test Notification")
    
    def test_notification_filtering(self):
        """Bildirim filtreleme testi"""
        # Farklı tipte bildirimler oluştur
        self.notification_manager.create_notification(
            "Info", "Info message", self.NotificationType.INFO
        )
        self.notification_manager.create_notification(
            "Warning", "Warning message", self.NotificationType.WARNING
        )
        self.notification_manager.create_notification(
            "Error", "Error message", self.NotificationType.ERROR
        )
        
        # Sadece warning bildirimleri
        warnings = self.notification_manager.get_notifications(
            notification_type=self.NotificationType.WARNING
        )
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].type, self.NotificationType.WARNING)
    
    def test_notification_read_status(self):
        """Bildirim okundu durumu testi"""
        notif_id = self.notification_manager.create_notification(
            "Test", "Test message", self.NotificationType.INFO
        )
        
        # Başlangıçta okunmamış
        unread_count = self.notification_manager.get_unread_count()
        self.assertEqual(unread_count, 1)
        
        # Okundu olarak işaretle
        self.notification_manager.mark_as_read(notif_id)
        
        # Okunmamış sayısı azaldı
        unread_count = self.notification_manager.get_unread_count()
        self.assertEqual(unread_count, 0)

class TestIntegration(unittest.TestCase):
    """Integration test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test.db")
        
        # Test veritabanı
        self.db_manager = DatabaseManager(self.test_db_path)
        
        # Test backup manager
        self.backup_manager = BackupManager(self.test_db_path)
    
    def tearDown(self):
        """Test cleanup"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Tam iş akışı testi"""
        # 1. Tezgah ekle
        with self.db_manager.get_session() as session:
            tezgah = Tezgah(
                numarasi="INT001",
                aciklama="Integration Test Tezgahı",
                lokasyon="Test Atölyesi",
                durum="Aktif"
            )
            session.add(tezgah)
            session.commit()
            tezgah_id = tezgah.id
        
        # 2. Bakım kaydı ekle
        with self.db_manager.get_session() as session:
            bakim = Bakim(
                tezgah_id=tezgah_id,
                tarih=datetime.now(timezone.utc),
                bakim_yapan="Test Teknisyen",
                aciklama="Integration test bakımı",
                durum="Tamamlandı"
            )
            session.add(bakim)
            session.commit()
        
        # 3. Pil kaydı ekle
        with self.db_manager.get_session() as session:
            pil = Pil(
                tezgah_id=tezgah_id,
                eksen="X",
                pil_modeli="Test Pil",
                degisim_tarihi=datetime.now(timezone.utc),
                degistiren_kisi="Test Teknisyen",
                durum="Aktif"
            )
            session.add(pil)
            session.commit()
        
        # 4. Verileri kontrol et
        tezgah_count = self.db_manager.get_tezgah_count()
        self.assertGreaterEqual(tezgah_count, 1)
        
        # 5. Yedek oluştur
        success, result = self.backup_manager.create_backup(compressed=True)
        self.assertTrue(success)
        
        # 6. Dashboard istatistikleri
        stats = self.db_manager.get_dashboard_stats()
        self.assertGreaterEqual(stats['total_tezgah'], 1)
    
    def test_performance_under_load(self):
        """Yük altında performans testi"""
        import time
        
        # Çok sayıda tezgah ekle
        start_time = time.time()
        
        tezgah_data = []
        for i in range(100):
            tezgah_data.append({
                'numarasi': f'PERF{i:03d}',
                'aciklama': f'Performance Test Tezgahı {i}',
                'lokasyon': f'Test Atölyesi {i % 10}',
                'durum': 'Aktif',
                'bakim_periyodu': 30
            })
        
        # Bulk insert
        with self.db_manager.get_session() as session:
            session.bulk_insert_mappings(Tezgah, tezgah_data)
        
        insert_time = time.time() - start_time
        
        # Query performance
        start_time = time.time()
        
        with self.db_manager.get_session() as session:
            tezgahlar = session.query(Tezgah).limit(50).all()
        
        query_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(insert_time, 5.0)  # 5 saniyeden az
        self.assertLess(query_time, 1.0)   # 1 saniyeden az
        self.assertEqual(len(tezgahlar), 50)

class TestErrorHandling(unittest.TestCase):
    """Error handling test sınıfı"""
    
    def test_database_connection_error(self):
        """Veritabanı bağlantı hatası testi"""
        # Geçersiz veritabanı yolu
        with self.assertRaises(Exception):
            DatabaseManager("/invalid/path/test.db")
    
    def test_validation_errors(self):
        """Validasyon hatası testi"""
        # Geçersiz tezgah numarası
        with self.assertRaises(ValueError):
            validate_tezgah_numarasi("INVALID@#$")
        
        # Geçersiz metin alanı
        with self.assertRaises(ValueError):
            validate_text_field("", "Test Field", min_len=5)
    
    def test_backup_error_handling(self):
        """Yedekleme hata yönetimi testi"""
        # Geçersiz veritabanı yolu ile backup manager
        backup_manager = BackupManager("/nonexistent/path/test.db")
        
        # Backup oluşturma başarısız olmalı
        success, message = backup_manager.create_backup()
        self.assertFalse(success)
        self.assertIn("bulunamadı", message.lower())

if __name__ == '__main__':
    # Test suite oluştur
    test_suite = unittest.TestSuite()
    
    # Test sınıflarını ekle
    test_classes = [
        TestDatabaseModels,
        TestSecurityManager,
        TestPerformanceMonitor,
        TestAdvancedLogger,
        TestNotificationManager,
        TestIntegration,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Test sonuçları
    print(f"\n{'='*50}")
    print(f"Test Sonuçları:")
    print(f"Toplam Test: {result.testsRun}")
    print(f"Başarılı: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Başarısız: {len(result.failures)}")
    print(f"Hata: {len(result.errors)}")
    print(f"{'='*50}")
    
    # Exit code
    sys.exit(0 if result.wasSuccessful() else 1)