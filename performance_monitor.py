#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Performance Monitor
Uygulama performansını izleme ve optimizasyon sistemi
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass
from collections import deque
import json

# Psutil'i güvenli şekilde import et
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

@dataclass
class PerformanceMetric:
    """Performance metrik veri yapısı"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    details: Optional[Dict[str, Any]] = None

class PerformanceMonitor:
    """Performance monitoring sınıfı"""
    
    def __init__(self, max_metrics: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_metrics = max_metrics
        
        # Metric storage
        self.metrics = deque(maxlen=max_metrics)
        self.function_timings = {}  # Function execution times
        self.query_timings = deque(maxlen=500)  # Database query times
        self.memory_usage = deque(maxlen=100)   # Memory usage history
        self.cpu_usage = deque(maxlen=100)      # CPU usage history
        
        # Performance thresholds
        self.thresholds = {
            'slow_query_ms': 1000,      # 1 second
            'slow_function_ms': 500,    # 500ms
            'high_memory_mb': 500,      # 500MB
            'high_cpu_percent': 80      # 80%
        }
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def start_monitoring(self, interval: float = 5.0):
        """Performance monitoring'i başlat"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Performance monitoring'i durdur"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: float):
        """Monitoring loop - sistem metriklerini topla"""
        while self.monitoring_active:
            try:
                # System metrics
                self._collect_system_metrics()
                
                # Memory cleanup
                self._cleanup_old_metrics()
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Sistem metriklerini topla"""
        try:
            if not PSUTIL_AVAILABLE:
                return
                
            current_time = datetime.now()
            
            # Memory usage
            memory_info = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            with self.lock:
                self.memory_usage.append({
                    'timestamp': current_time,
                    'system_percent': memory_info.percent,
                    'process_mb': process_memory,
                    'available_mb': memory_info.available / 1024 / 1024
                })
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            process_cpu = process.cpu_percent()
            
            with self.lock:
                self.cpu_usage.append({
                    'timestamp': current_time,
                    'system_percent': cpu_percent,
                    'process_percent': process_cpu
                })
            
            # Performance alerts
            self._check_performance_alerts(process_memory, cpu_percent)
            
        except Exception as e:
            self.logger.error(f"System metrics collection error: {e}")
    
    def _check_performance_alerts(self, memory_mb: float, cpu_percent: float):
        """Performance alert'lerini kontrol et"""
        if memory_mb > self.thresholds['high_memory_mb']:
            self.logger.warning(f"High memory usage: {memory_mb:.1f}MB")
        
        if cpu_percent > self.thresholds['high_cpu_percent']:
            self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
    
    def _cleanup_old_metrics(self):
        """Eski metrikleri temizle"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        with self.lock:
            # Remove old metrics
            while self.metrics and self.metrics[0].timestamp < cutoff_time:
                self.metrics.popleft()
    
    def record_metric(self, name: str, value: float, unit: str, 
                     category: str = "general", details: Optional[Dict] = None):
        """Manuel metrik kaydı"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            category=category,
            details=details
        )
        
        with self.lock:
            self.metrics.append(metric)
    
    def record_query_time(self, query: str, execution_time: float, 
                         result_count: Optional[int] = None):
        """Database query zamanını kaydet"""
        query_info = {
            'query': query[:200],  # İlk 200 karakter
            'execution_time_ms': execution_time * 1000,
            'result_count': result_count,
            'timestamp': datetime.now()
        }
        
        with self.lock:
            self.query_timings.append(query_info)
        
        # Slow query alert
        if execution_time * 1000 > self.thresholds['slow_query_ms']:
            self.logger.warning(f"Slow query detected: {execution_time*1000:.1f}ms - {query[:100]}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Performance özeti döndür"""
        with self.lock:
            current_time = datetime.now()
            
            # Recent metrics (son 5 dakika)
            recent_cutoff = current_time - timedelta(minutes=5)
            recent_metrics = [m for m in self.metrics if m.timestamp > recent_cutoff]
            
            # Query statistics
            recent_queries = [q for q in self.query_timings if q['timestamp'] > recent_cutoff]
            avg_query_time = sum(q['execution_time_ms'] for q in recent_queries) / len(recent_queries) if recent_queries else 0
            slow_queries = [q for q in recent_queries if q['execution_time_ms'] > self.thresholds['slow_query_ms']]
            
            # Memory statistics
            recent_memory = [m for m in self.memory_usage if m['timestamp'] > recent_cutoff]
            avg_memory = sum(m['process_mb'] for m in recent_memory) / len(recent_memory) if recent_memory else 0
            
            # CPU statistics
            recent_cpu = [c for c in self.cpu_usage if c['timestamp'] > recent_cutoff]
            avg_cpu = sum(c['process_percent'] for c in recent_cpu) / len(recent_cpu) if recent_cpu else 0
            
            return {
                'timestamp': current_time.isoformat(),
                'metrics_count': len(recent_metrics),
                'database': {
                    'total_queries': len(recent_queries),
                    'avg_query_time_ms': round(avg_query_time, 2),
                    'slow_queries_count': len(slow_queries),
                    'slowest_query_ms': max((q['execution_time_ms'] for q in recent_queries), default=0)
                },
                'system': {
                    'avg_memory_mb': round(avg_memory, 2),
                    'avg_cpu_percent': round(avg_cpu, 2),
                    'memory_samples': len(recent_memory),
                    'cpu_samples': len(recent_cpu)
                },
                'function_timings': dict(list(self.function_timings.items())[-10:])  # Son 10 function
            }
    
    def get_slow_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """En yavaş işlemleri döndür"""
        with self.lock:
            # Slow queries
            slow_queries = sorted(
                self.query_timings,
                key=lambda x: x['execution_time_ms'],
                reverse=True
            )[:limit]
            
            # Slow functions
            slow_functions = sorted(
                self.function_timings.items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )[:limit]
            
            return {
                'slow_queries': slow_queries,
                'slow_functions': [
                    {
                        'function': func,
                        'avg_time_ms': data['avg_time'] * 1000,
                        'call_count': data['call_count'],
                        'total_time_ms': data['total_time'] * 1000
                    }
                    for func, data in slow_functions
                ]
            }
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """Metrikleri dosyaya export et"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self.lock:
                # Metrics
                export_metrics = [
                    {
                        'name': m.name,
                        'value': m.value,
                        'unit': m.unit,
                        'category': m.category,
                        'timestamp': m.timestamp.isoformat(),
                        'details': m.details
                    }
                    for m in self.metrics if m.timestamp > cutoff_time
                ]
                
                # Query timings
                export_queries = [
                    {
                        'query': q['query'],
                        'execution_time_ms': q['execution_time_ms'],
                        'result_count': q['result_count'],
                        'timestamp': q['timestamp'].isoformat()
                    }
                    for q in self.query_timings if q['timestamp'] > cutoff_time
                ]
                
                # System metrics
                export_memory = [
                    {
                        'timestamp': m['timestamp'].isoformat(),
                        'system_percent': m['system_percent'],
                        'process_mb': m['process_mb'],
                        'available_mb': m['available_mb']
                    }
                    for m in self.memory_usage if m['timestamp'] > cutoff_time
                ]
                
                export_cpu = [
                    {
                        'timestamp': c['timestamp'].isoformat(),
                        'system_percent': c['system_percent'],
                        'process_percent': c['process_percent']
                    }
                    for c in self.cpu_usage if c['timestamp'] > cutoff_time
                ]
            
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'hours': hours,
                    'version': '2.1.3'
                },
                'metrics': export_metrics,
                'queries': export_queries,
                'memory_usage': export_memory,
                'cpu_usage': export_cpu,
                'function_timings': self.function_timings
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Performance metrics exported to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Metrics export error: {e}")
            return False

# Decorator functions
def monitor_performance(category: str = "function"):
    """Function performance monitoring decorator"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record timing
                func_name = f"{func.__module__}.{func.__name__}"
                
                if func_name not in performance_monitor.function_timings:
                    performance_monitor.function_timings[func_name] = {
                        'total_time': 0,
                        'call_count': 0,
                        'avg_time': 0
                    }
                
                timing_data = performance_monitor.function_timings[func_name]
                timing_data['total_time'] += execution_time
                timing_data['call_count'] += 1
                timing_data['avg_time'] = timing_data['total_time'] / timing_data['call_count']
                
                # Record metric
                performance_monitor.record_metric(
                    name=f"function_execution_time",
                    value=execution_time,
                    unit="seconds",
                    category=category,
                    details={'function': func_name}
                )
                
                # Slow function alert
                if execution_time * 1000 > performance_monitor.thresholds['slow_function_ms']:
                    performance_monitor.logger.warning(
                        f"Slow function: {func_name} took {execution_time*1000:.1f}ms"
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.logger.error(
                    f"Function {func.__name__} failed after {execution_time*1000:.1f}ms: {e}"
                )
                raise
                
        return wrapper
    return decorator

def monitor_database_query(func: Callable):
    """Database query monitoring decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Query bilgisini çıkarmaya çalış
            query_info = "Unknown query"
            result_count = None
            
            if hasattr(result, '__len__'):
                try:
                    result_count = len(result)
                except:
                    pass
            
            # Record query timing
            performance_monitor.record_query_time(
                query=query_info,
                execution_time=execution_time,
                result_count=result_count
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            performance_monitor.logger.error(
                f"Database query failed after {execution_time*1000:.1f}ms: {e}"
            )
            raise
            
    return wrapper

# Global performance monitor instance
performance_monitor = PerformanceMonitor()