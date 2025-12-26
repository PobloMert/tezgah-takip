#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Logging Sistemi
Structured logging, log rotation, filtering ve monitoring
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    """Log seviyeleri"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log kategorileri"""
    SYSTEM = "SYSTEM"
    DATABASE = "DATABASE"
    UI = "UI"
    API = "API"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    USER_ACTION = "USER_ACTION"
    ERROR = "ERROR"

@dataclass
class StructuredLogEntry:
    """Yapılandırılmış log entry"""
    timestamp: str
    level: str
    category: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class StructuredFormatter(logging.Formatter):
    """JSON formatında structured logging formatter"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry = StructuredLogEntry(
            timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            level=record.levelname,
            category=getattr(record, 'category', LogCategory.SYSTEM.value),
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=str(threading.get_ident()),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            request_id=getattr(record, 'request_id', None)
        )
        
        # Extra data ekle
        if self.include_extra:
            extra_data = {}
            
            # Record'daki extra attribute'ları topla
            skip_attrs = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'category', 'user_id', 'session_id', 'request_id'
            }
            
            for key, value in record.__dict__.items():
                if key not in skip_attrs and not key.startswith('_'):
                    try:
                        # JSON serializable olup olmadığını kontrol et
                        json.dumps(value)
                        extra_data[key] = value
                    except (TypeError, ValueError):
                        extra_data[key] = str(value)
            
            if extra_data:
                log_entry.extra_data = extra_data
        
        # Exception bilgisi ekle
        if record.exc_info:
            if not log_entry.extra_data:
                log_entry.extra_data = {}
            log_entry.extra_data['exception'] = self.formatException(record.exc_info)
        
        # JSON'a çevir
        try:
            return json.dumps(asdict(log_entry), ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            # Fallback to simple format
            return f"{log_entry.timestamp} [{log_entry.level}] {log_entry.message}"

class ColoredConsoleFormatter(logging.Formatter):
    """Renkli console formatter"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Color code
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format message
        formatted = super().format(record)
        
        # Add color
        return f"{color}{formatted}{reset}"

class AdvancedLogger:
    """Gelişmiş logging sistemi"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.loggers = {}
        self.handlers = {}
        
        # Log directory oluştur
        self.log_dir = Path(self.config.get('log_directory', 'logs'))
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default logging konfigürasyonu"""
        return {
            'log_directory': 'logs',
            'log_level': 'INFO',
            'max_file_size_mb': 10,
            'backup_count': 5,
            'console_logging': True,
            'file_logging': True,
            'structured_logging': True,
            'colored_console': True,
            'log_categories': {
                'system': {'level': 'INFO', 'file': 'system.log'},
                'database': {'level': 'INFO', 'file': 'database.log'},
                'ui': {'level': 'WARNING', 'file': 'ui.log'},
                'api': {'level': 'INFO', 'file': 'api.log'},
                'security': {'level': 'WARNING', 'file': 'security.log'},
                'performance': {'level': 'INFO', 'file': 'performance.log'},
                'user_action': {'level': 'INFO', 'file': 'user_actions.log'},
                'error': {'level': 'ERROR', 'file': 'errors.log'}
            }
        }
    
    def _setup_logging(self):
        """Logging sistemini kur"""
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['log_level']))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.config.get('console_logging', True):
            console_handler = logging.StreamHandler(sys.stdout)
            
            if self.config.get('colored_console', True):
                console_formatter = ColoredConsoleFormatter(
                    '%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
                )
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
            self.handlers['console'] = console_handler
        
        # File handlers
        if self.config.get('file_logging', True):
            self._setup_file_handlers()
        
        # Category-specific loggers
        self._setup_category_loggers()
    
    def _setup_file_handlers(self):
        """Dosya handler'larını kur"""
        max_bytes = self.config.get('max_file_size_mb', 10) * 1024 * 1024
        backup_count = self.config.get('backup_count', 5)
        
        # Main log file
        main_log_file = self.log_dir / 'tezgah_takip.log'
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if self.config.get('structured_logging', True):
            main_formatter = StructuredFormatter()
        else:
            main_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)8s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
            )
        
        main_handler.setFormatter(main_formatter)
        
        # Root logger'a ekle
        root_logger = logging.getLogger()
        root_logger.addHandler(main_handler)
        self.handlers['main_file'] = main_handler
    
    def _setup_category_loggers(self):
        """Kategori-specific logger'ları kur"""
        categories = self.config.get('log_categories', {})
        
        for category, cat_config in categories.items():
            logger_name = f"tezgah_takip.{category}"
            logger = logging.getLogger(logger_name)
            
            # Level ayarla
            level = cat_config.get('level', 'INFO')
            logger.setLevel(getattr(logging, level))
            
            # File handler
            if 'file' in cat_config:
                log_file = self.log_dir / cat_config['file']
                
                max_bytes = self.config.get('max_file_size_mb', 10) * 1024 * 1024
                backup_count = self.config.get('backup_count', 5)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                
                if self.config.get('structured_logging', True):
                    formatter = StructuredFormatter()
                else:
                    formatter = logging.Formatter(
                        '%(asctime)s [%(levelname)8s] %(funcName)s:%(lineno)d - %(message)s'
                    )
                
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
                self.handlers[f"{category}_file"] = file_handler
            
            self.loggers[category] = logger
    
    def get_logger(self, category: str = "system") -> logging.Logger:
        """Kategori logger'ını al"""
        if category in self.loggers:
            return self.loggers[category]
        
        # Fallback to root logger
        return logging.getLogger(f"tezgah_takip.{category}")
    
    def log_user_action(self, action: str, user_id: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None):
        """Kullanıcı aksiyonunu logla"""
        logger = self.get_logger("user_action")
        
        extra = {
            'category': LogCategory.USER_ACTION.value,
            'user_id': user_id,
            'action': action
        }
        
        if details:
            extra.update(details)
        
        logger.info(f"User action: {action}", extra=extra)
    
    def log_security_event(self, event_type: str, severity: str = "WARNING",
                          details: Optional[Dict[str, Any]] = None):
        """Güvenlik olayını logla"""
        logger = self.get_logger("security")
        
        extra = {
            'category': LogCategory.SECURITY.value,
            'event_type': event_type,
            'severity': severity
        }
        
        if details:
            extra.update(details)
        
        message = f"Security event: {event_type}"
        
        if severity == "CRITICAL":
            logger.critical(message, extra=extra)
        elif severity == "ERROR":
            logger.error(message, extra=extra)
        else:
            logger.warning(message, extra=extra)
    
    def log_performance_metric(self, metric_name: str, value: float,
                             unit: str, details: Optional[Dict[str, Any]] = None):
        """Performance metriğini logla"""
        logger = self.get_logger("performance")
        
        extra = {
            'category': LogCategory.PERFORMANCE.value,
            'metric_name': metric_name,
            'metric_value': value,
            'metric_unit': unit
        }
        
        if details:
            extra.update(details)
        
        logger.info(f"Performance metric: {metric_name} = {value} {unit}", extra=extra)
    
    def log_database_operation(self, operation: str, table: str,
                             execution_time: Optional[float] = None,
                             record_count: Optional[int] = None):
        """Database operasyonunu logla"""
        logger = self.get_logger("database")
        
        extra = {
            'category': LogCategory.DATABASE.value,
            'operation': operation,
            'table': table
        }
        
        if execution_time is not None:
            extra['execution_time_ms'] = execution_time * 1000
        
        if record_count is not None:
            extra['record_count'] = record_count
        
        message = f"Database {operation} on {table}"
        if record_count is not None:
            message += f" ({record_count} records)"
        if execution_time is not None:
            message += f" in {execution_time*1000:.1f}ms"
        
        logger.info(message, extra=extra)
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Log istatistiklerini döndür"""
        # Bu implementasyon log dosyalarını parse ederek istatistik çıkarabilir
        # Şimdilik basit bir implementasyon
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'period_hours': hours,
            'log_files': [],
            'total_entries': 0,
            'level_counts': {},
            'category_counts': {}
        }
        
        # Log dosyalarını tara
        for log_file in self.log_dir.glob('*.log'):
            try:
                file_stats = {
                    'filename': log_file.name,
                    'size_bytes': log_file.stat().st_size,
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
                stats['log_files'].append(file_stats)
            except Exception:
                pass
        
        return stats
    
    def cleanup_old_logs(self, days: int = 30):
        """Eski log dosyalarını temizle"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        cleaned_files = []
        
        for log_file in self.log_dir.glob('*.log.*'):  # Rotated log files
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
            except Exception as e:
                self.get_logger("system").warning(f"Failed to cleanup log file {log_file}: {e}")
        
        if cleaned_files:
            self.get_logger("system").info(f"Cleaned up {len(cleaned_files)} old log files")
        
        return cleaned_files

# Global advanced logger instance
advanced_logger = AdvancedLogger()

# Convenience functions
def get_logger(category: str = "system") -> logging.Logger:
    """Logger al"""
    return advanced_logger.get_logger(category)

def log_user_action(action: str, user_id: Optional[str] = None, **kwargs):
    """Kullanıcı aksiyonu logla"""
    advanced_logger.log_user_action(action, user_id, kwargs)

def log_security_event(event_type: str, severity: str = "WARNING", **kwargs):
    """Güvenlik olayı logla"""
    advanced_logger.log_security_event(event_type, severity, kwargs)

def log_performance_metric(metric_name: str, value: float, unit: str, **kwargs):
    """Performance metrik logla"""
    advanced_logger.log_performance_metric(metric_name, value, unit, kwargs)

def log_database_operation(operation: str, table: str, execution_time: Optional[float] = None, 
                          record_count: Optional[int] = None):
    """Database operasyon logla"""
    advanced_logger.log_database_operation(operation, table, execution_time, record_count)