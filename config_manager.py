#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Konfigürasyon Yöneticisi
Hardcoded path'leri ve ayarları merkezi olarak yönetir
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
from datetime import datetime

class ConfigManager:
    """Merkezi konfigürasyon yöneticisi"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "database": {
            "path": "tezgah_takip_v2.db",
            "backup_path": "backups",
            "connection_timeout": 30,
            "max_connections": 20
        },
        "logging": {
            "level": "INFO",
            "file_path": "logs/tezgah_takip.log",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "ui": {
            "theme": "dark",
            "font_size": "normal",
            "window_width": 1400,
            "window_height": 900,
            "refresh_interval_seconds": 30,
            "records_per_page": 100
        },
        "export": {
            "output_directory": "exports",
            "max_records_limit": 10000,
            "default_format": "xlsx",
            "include_charts": True,
            "chart_dpi": 300
        },
        "backup": {
            "auto_backup_enabled": True,
            "backup_interval_hours": 24,
            "max_backups": 30,
            "compress_backups": True,
            "include_logs": True
        },
        "security": {
            "api_key_file": "api_key.enc",
            "encryption_key_file": "encryption.key",
            "session_timeout_minutes": 60,
            "max_login_attempts": 5
        },
        "notifications": {
            "maintenance_alerts": True,
            "battery_alerts": True,
            "battery_warning_days": 355,
            "maintenance_warning_days": 7
        },
        "accessibility": {
            "high_contrast": False,
            "font_size": "normal",
            "screen_reader_support": False,
            "keyboard_navigation": True
        },
        "ai": {
            "provider": "gemini",
            "model": "gemini-pro",
            "max_tokens": 1000,
            "temperature": 0.7,
            "rate_limit_requests_per_minute": 60
        },
        "performance": {
            "cache_enabled": True,
            "cache_size_mb": 100,
            "lazy_loading": True,
            "pagination_enabled": True
        }
    }
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self._config = {}
        
        # Konfigürasyonu yükle
        self.load_config()
    
    def load_config(self) -> bool:
        """Konfigürasyonu dosyadan yükle"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Default config ile merge et
                self._config = self._merge_configs(self.DEFAULT_CONFIG, file_config)
                self.logger.info(f"Configuration loaded from: {self.config_file}")
            else:
                # Default config kullan
                self._config = self.DEFAULT_CONFIG.copy()
                self.save_config()  # Default config'i kaydet
                self.logger.info("Default configuration created")
            
            # Path'leri normalize et
            self._normalize_paths()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Fallback to default
            self._config = self.DEFAULT_CONFIG.copy()
            return False
    
    def save_config(self) -> bool:
        """Konfigürasyonu dosyaya kaydet"""
        try:
            # Backup oluştur (güvenli şekilde)
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.backup')
                
                # Eğer backup dosyası varsa önce sil
                if backup_file.exists():
                    backup_file.unlink()
                
                # Şimdi backup oluştur
                import shutil
                shutil.copy2(self.config_file, backup_file)
            
            # Yeni config'i kaydet
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """İki config'i merge et (recursive)"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _normalize_paths(self):
        """Path'leri normalize et ve mutlak path'e çevir"""
        try:
            # Database paths
            db_path = self._config["database"]["path"]
            if not os.path.isabs(db_path):
                self._config["database"]["path"] = os.path.abspath(db_path)
            
            backup_path = self._config["database"]["backup_path"]
            if not os.path.isabs(backup_path):
                self._config["database"]["backup_path"] = os.path.abspath(backup_path)
            
            # Log path
            log_path = self._config["logging"]["file_path"]
            if not os.path.isabs(log_path):
                self._config["logging"]["file_path"] = os.path.abspath(log_path)
                
                # Log directory oluştur
                log_dir = os.path.dirname(self._config["logging"]["file_path"])
                os.makedirs(log_dir, exist_ok=True)
            
            # Export path
            export_path = self._config["export"]["output_directory"]
            if not os.path.isabs(export_path):
                self._config["export"]["output_directory"] = os.path.abspath(export_path)
                
                # Export directory oluştur
                os.makedirs(self._config["export"]["output_directory"], exist_ok=True)
            
            # Security paths
            api_key_file = self._config["security"]["api_key_file"]
            if not os.path.isabs(api_key_file):
                self._config["security"]["api_key_file"] = os.path.abspath(api_key_file)
            
            encryption_key_file = self._config["security"]["encryption_key_file"]
            if not os.path.isabs(encryption_key_file):
                self._config["security"]["encryption_key_file"] = os.path.abspath(encryption_key_file)
            
        except Exception as e:
            self.logger.error(f"Path normalization error: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Nested key ile değer al
        Örnek: get("database.path") -> config["database"]["path"]
        """
        try:
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Get config error for key '{key_path}': {e}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Nested key ile değer ayarla
        Örnek: set("database.path", "/new/path") -> config["database"]["path"] = "/new/path"
        """
        try:
            keys = key_path.split('.')
            config = self._config
            
            # Son key hariç tüm key'leri traverse et
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Son key'e değeri ata
            config[keys[-1]] = value
            
            self.logger.info(f"Configuration updated: {key_path} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Set config error for key '{key_path}': {e}")
            return False
    
    def get_database_config(self) -> Dict:
        """Veritabanı konfigürasyonu"""
        return self.get("database", {})
    
    def get_ui_config(self) -> Dict:
        """UI konfigürasyonu"""
        return self.get("ui", {})
    
    def get_logging_config(self) -> Dict:
        """Logging konfigürasyonu"""
        return self.get("logging", {})
    
    def get_export_config(self) -> Dict:
        """Export konfigürasyonu"""
        return self.get("export", {})
    
    def get_backup_config(self) -> Dict:
        """Backup konfigürasyonu"""
        return self.get("backup", {})
    
    def get_security_config(self) -> Dict:
        """Security konfigürasyonu"""
        return self.get("security", {})
    
    def get_ai_config(self) -> Dict:
        """AI konfigürasyonu"""
        return self.get("ai", {})
    
    def get_accessibility_config(self) -> Dict:
        """Accessibility konfigürasyonu"""
        return self.get("accessibility", {})
    
    def update_ui_settings(self, settings: Dict) -> bool:
        """UI ayarlarını toplu güncelle"""
        try:
            for key, value in settings.items():
                self.set(f"ui.{key}", value)
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Update UI settings error: {e}")
            return False
    
    def update_accessibility_settings(self, settings: Dict) -> bool:
        """Accessibility ayarlarını toplu güncelle"""
        try:
            for key, value in settings.items():
                self.set(f"accessibility.{key}", value)
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Update accessibility settings error: {e}")
            return False
    
    def reset_to_defaults(self, section: Optional[str] = None) -> bool:
        """Konfigürasyonu default'a sıfırla"""
        try:
            if section:
                # Sadece belirli section'ı sıfırla
                if section in self.DEFAULT_CONFIG:
                    self._config[section] = self.DEFAULT_CONFIG[section].copy()
                    self.logger.info(f"Configuration section '{section}' reset to defaults")
                else:
                    self.logger.error(f"Unknown configuration section: {section}")
                    return False
            else:
                # Tüm config'i sıfırla
                self._config = self.DEFAULT_CONFIG.copy()
                self.logger.info("Configuration reset to defaults")
            
            self._normalize_paths()
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Reset to defaults error: {e}")
            return False
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """Konfigürasyonu validate et"""
        errors = []
        
        try:
            # Database path kontrolü
            db_path = self.get("database.path")
            if not db_path:
                errors.append("Database path is not configured")
            
            # Log directory kontrolü
            log_path = self.get("logging.file_path")
            if log_path:
                log_dir = os.path.dirname(log_path)
                if not os.path.exists(log_dir):
                    try:
                        os.makedirs(log_dir, exist_ok=True)
                    except Exception as e:
                        errors.append(f"Cannot create log directory: {e}")
            
            # Export directory kontrolü
            export_dir = self.get("export.output_directory")
            if export_dir and not os.path.exists(export_dir):
                try:
                    os.makedirs(export_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create export directory: {e}")
            
            # Numeric value kontrolü
            numeric_configs = [
                ("ui.refresh_interval_seconds", 1, 3600),
                ("ui.records_per_page", 10, 10000),
                ("backup.backup_interval_hours", 1, 8760),
                ("backup.max_backups", 1, 1000),
                ("notifications.battery_warning_days", 1, 3650)
            ]
            
            for config_key, min_val, max_val in numeric_configs:
                value = self.get(config_key)
                if value is not None:
                    try:
                        num_value = int(value)
                        if not (min_val <= num_value <= max_val):
                            errors.append(f"{config_key} must be between {min_val} and {max_val}")
                    except (ValueError, TypeError):
                        errors.append(f"{config_key} must be a valid number")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    def export_config(self, export_path: str) -> bool:
        """Konfigürasyonu dışa aktar"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "version": "2.0.0",
                "config": self._config
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Export config error: {e}")
            return False
    
    def import_config(self, import_path: str, merge: bool = True) -> bool:
        """Konfigürasyonu içe aktar"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if "config" not in import_data:
                self.logger.error("Invalid config file format")
                return False
            
            imported_config = import_data["config"]
            
            if merge:
                # Mevcut config ile merge et
                self._config = self._merge_configs(self._config, imported_config)
            else:
                # Tamamen değiştir
                self._config = imported_config
            
            self._normalize_paths()
            
            # Validate et
            is_valid, errors = self.validate_config()
            if not is_valid:
                self.logger.warning(f"Imported config has validation errors: {errors}")
            
            success = self.save_config()
            if success:
                self.logger.info(f"Configuration imported from: {import_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Import config error: {e}")
            return False
    
    def get_config_summary(self) -> Dict:
        """Konfigürasyon özeti"""
        try:
            return {
                "database_path": self.get("database.path"),
                "backup_enabled": self.get("backup.auto_backup_enabled"),
                "theme": self.get("ui.theme"),
                "font_size": self.get("ui.font_size"),
                "high_contrast": self.get("accessibility.high_contrast"),
                "ai_provider": self.get("ai.provider"),
                "export_format": self.get("export.default_format"),
                "log_level": self.get("logging.level"),
                "config_file": str(self.config_file),
                "last_modified": datetime.fromtimestamp(self.config_file.stat().st_mtime).isoformat() if self.config_file.exists() else None
            }
            
        except Exception as e:
            self.logger.error(f"Get config summary error: {e}")
            return {"error": str(e)}

# Global config instance
_config_instance = None

def get_config() -> ConfigManager:
    """Global config instance'ını al"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def reload_config():
    """Config'i yeniden yükle"""
    global _config_instance
    if _config_instance:
        _config_instance.load_config()

# Test fonksiyonu
def test_config_manager():
    """Config manager'ı test et"""
    print("🧪 Config Manager Test Başlıyor...")
    
    try:
        # Test config dosyası
        test_config_file = "test_config.json"
        
        # Config manager oluştur
        config = ConfigManager(test_config_file)
        
        # Get test
        db_path = config.get("database.path")
        print(f"Database path: {db_path}")
        
        # Set test
        config.set("ui.theme", "light")
        theme = config.get("ui.theme")
        print(f"Theme after set: {theme}")
        
        # Config sections test
        ui_config = config.get_ui_config()
        print(f"UI config: {ui_config}")
        
        # Validation test
        is_valid, errors = config.validate_config()
        print(f"Config validation: {is_valid}, errors: {errors}")
        
        # Summary test
        summary = config.get_config_summary()
        print(f"Config summary: {summary}")
        
        # Export test
        export_path = "test_config_export.json"
        config.export_config(export_path)
        print(f"Config exported to: {export_path}")
        
        # Cleanup
        for file_path in [test_config_file, export_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        print("✅ Config Manager testi başarılı!")
        
    except Exception as e:
        print(f"❌ Config Manager testi başarısız: {e}")

if __name__ == "__main__":
    test_config_manager()