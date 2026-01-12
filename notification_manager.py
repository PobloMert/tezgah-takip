#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Real-time Notification Manager
Gerçek zamanlı bildirim sistemi
"""

import logging
import threading
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon

class NotificationType(Enum):
    """Bildirim tipleri"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    MAINTENANCE = "maintenance"
    BATTERY = "battery"
    SYSTEM = "system"

class NotificationPriority(Enum):
    """Bildirim öncelikleri"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Notification:
    """Bildirim veri yapısı"""
    id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    timestamp: datetime
    source: str
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    dismissed: bool = False
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class NotificationManager(QObject):
    """Real-time notification manager"""
    
    # Signals
    notification_received = pyqtSignal(object)  # Notification object
    notification_read = pyqtSignal(str)         # notification_id
    notification_dismissed = pyqtSignal(str)    # notification_id
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Notification storage
        self.notifications = {}  # id -> Notification
        self.subscribers = {}    # type -> List[callback]
        self.rules = []          # Notification rules
        
        # System tray
        self.tray_icon = None
        self.setup_system_tray()
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Timers
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_expired_notifications)
        self.cleanup_timer.start(60000)  # Her dakika temizlik
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def setup_system_tray(self):
        """System tray icon kurulumu"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon()
                
                # Icon ayarla (varsayılan)
                self.tray_icon.setIcon(QApplication.style().standardIcon(
                    QApplication.style().SP_ComputerIcon
                ))
                
                # Context menu
                tray_menu = QMenu()
                
                show_action = QAction("Bildirimleri Göster", None)
                show_action.triggered.connect(self.show_notifications)
                tray_menu.addAction(show_action)
                
                clear_action = QAction("Tüm Bildirimleri Temizle", None)
                clear_action.triggered.connect(self.clear_all_notifications)
                tray_menu.addAction(clear_action)
                
                tray_menu.addSeparator()
                
                quit_action = QAction("Çıkış", None)
                quit_action.triggered.connect(QApplication.quit)
                tray_menu.addAction(quit_action)
                
                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.show()
                
                # Click handler
                self.tray_icon.activated.connect(self.tray_icon_activated)
                
                self.logger.info("System tray icon initialized")
            else:
                self.logger.warning("System tray not available")
                
        except Exception as e:
            self.logger.error(f"System tray setup failed: {e}")
    
    def tray_icon_activated(self, reason):
        """System tray icon click handler"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_notifications()
    
    def start_monitoring(self):
        """Background monitoring başlat"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("Notification monitoring started")
    
    def stop_monitoring(self):
        """Background monitoring durdur"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        self.logger.info("Notification monitoring stopped")
    
    def _monitoring_loop(self):
        """Monitoring loop - periyodik kontroller"""
        while self.monitoring_active:
            try:
                # Maintenance alerts
                self.check_maintenance_alerts()
                
                # Battery alerts
                self.check_battery_alerts()
                
                # System health
                self.check_system_health()
                
                # 5 dakika bekle
                time.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle
    
    def create_notification(self, title: str, message: str,
                          notification_type: NotificationType = NotificationType.INFO,
                          priority: NotificationPriority = NotificationPriority.NORMAL,
                          source: str = "system",
                          data: Optional[Dict] = None,
                          expires_in_minutes: Optional[int] = None,
                          action_text: Optional[str] = None,
                          action_url: Optional[str] = None) -> str:
        """Yeni bildirim oluştur"""
        
        # Unique ID oluştur
        notification_id = f"{int(time.time() * 1000)}_{hash(title + message) % 10000}"
        
        # Expiration time
        expires_at = None
        if expires_in_minutes:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        
        # Notification object
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            timestamp=datetime.now(timezone.utc),
            source=source,
            data=data,
            expires_at=expires_at,
            action_text=action_text,
            action_url=action_url
        )
        
        with self.lock:
            self.notifications[notification_id] = notification
        
        # Signal emit et
        self.notification_received.emit(notification)
        
        # System tray notification
        self.show_system_tray_notification(notification)
        
        # Subscribers'a bildir
        self.notify_subscribers(notification)
        
        self.logger.info(f"Notification created: {title}")
        return notification_id
    
    def show_system_tray_notification(self, notification: Notification):
        """System tray bildirimi göster"""
        if not self.tray_icon or not self.tray_icon.isVisible():
            return
        
        try:
            # Icon type
            icon_type = QSystemTrayIcon.Information
            
            if notification.type == NotificationType.WARNING:
                icon_type = QSystemTrayIcon.Warning
            elif notification.type == NotificationType.ERROR:
                icon_type = QSystemTrayIcon.Critical
            
            # Show notification
            self.tray_icon.showMessage(
                notification.title,
                notification.message,
                icon_type,
                5000  # 5 saniye
            )
            
        except Exception as e:
            self.logger.error(f"System tray notification failed: {e}")
    
    def subscribe(self, notification_type: NotificationType, callback: Callable):
        """Bildirim tipine abone ol"""
        if notification_type not in self.subscribers:
            self.subscribers[notification_type] = []
        
        self.subscribers[notification_type].append(callback)
        self.logger.info(f"Subscribed to {notification_type.value} notifications")
    
    def unsubscribe(self, notification_type: NotificationType, callback: Callable):
        """Abonelikten çık"""
        if notification_type in self.subscribers:
            try:
                self.subscribers[notification_type].remove(callback)
            except ValueError:
                pass
    
    def notify_subscribers(self, notification: Notification):
        """Subscribers'a bildirim gönder"""
        if notification.type in self.subscribers:
            for callback in self.subscribers[notification.type]:
                try:
                    callback(notification)
                except Exception as e:
                    self.logger.error(f"Subscriber callback failed: {e}")
    
    def mark_as_read(self, notification_id: str):
        """Bildirimi okundu olarak işaretle"""
        with self.lock:
            if notification_id in self.notifications:
                self.notifications[notification_id].read = True
                self.notification_read.emit(notification_id)
    
    def dismiss_notification(self, notification_id: str):
        """Bildirimi kapat"""
        with self.lock:
            if notification_id in self.notifications:
                self.notifications[notification_id].dismissed = True
                self.notification_dismissed.emit(notification_id)
    
    def get_notifications(self, include_read: bool = True, 
                         include_dismissed: bool = False,
                         notification_type: Optional[NotificationType] = None,
                         limit: Optional[int] = None) -> List[Notification]:
        """Bildirimleri getir"""
        with self.lock:
            notifications = list(self.notifications.values())
        
        # Filter
        filtered = []
        for notif in notifications:
            if not include_read and notif.read:
                continue
            if not include_dismissed and notif.dismissed:
                continue
            if notification_type and notif.type != notification_type:
                continue
            
            filtered.append(notif)
        
        # Sort by priority and timestamp
        filtered.sort(key=lambda x: (x.priority.value, x.timestamp), reverse=True)
        
        # Limit
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_unread_count(self) -> int:
        """Okunmamış bildirim sayısı"""
        with self.lock:
            return sum(1 for notif in self.notifications.values() 
                      if not notif.read and not notif.dismissed)
    
    def clear_all_notifications(self):
        """Tüm bildirimleri temizle"""
        with self.lock:
            self.notifications.clear()
        self.logger.info("All notifications cleared")
    
    def cleanup_expired_notifications(self):
        """Süresi dolmuş bildirimleri temizle"""
        current_time = datetime.now(timezone.utc)
        expired_ids = []
        
        with self.lock:
            for notif_id, notif in self.notifications.items():
                if notif.expires_at and notif.expires_at <= current_time:
                    expired_ids.append(notif_id)
            
            for notif_id in expired_ids:
                del self.notifications[notif_id]
        
        if expired_ids:
            self.logger.info(f"Cleaned up {len(expired_ids)} expired notifications")
    
    def check_maintenance_alerts(self):
        """Bakım uyarılarını kontrol et"""
        try:
            from database_models import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Yaklaşan bakımları kontrol et
            warning_date = datetime.now(timezone.utc) + timedelta(days=7)
            
            with db_manager.get_session() as session:
                from database_models import Tezgah
                
                overdue_maintenance = session.query(Tezgah)\
                    .filter(
                        Tezgah.sonraki_bakim_tarihi <= warning_date,
                        Tezgah.durum == 'Aktif'
                    ).all()
                
                for tezgah in overdue_maintenance:
                    # Duplicate notification kontrolü
                    existing_key = f"maintenance_alert_{tezgah.id}"
                    
                    if not any(notif.data and notif.data.get('key') == existing_key 
                             for notif in self.notifications.values()):
                        
                        days_until = (tezgah.sonraki_bakim_tarihi - datetime.now(timezone.utc)).days
                        
                        if days_until <= 0:
                            title = "🔴 Bakım Gecikti!"
                            message = f"{tezgah.numarasi} - {tezgah.aciklama} bakımı {abs(days_until)} gün gecikti"
                            priority = NotificationPriority.CRITICAL
                        else:
                            title = "⚠️ Yaklaşan Bakım"
                            message = f"{tezgah.numarasi} - {tezgah.aciklama} bakımı {days_until} gün sonra"
                            priority = NotificationPriority.HIGH
                        
                        self.create_notification(
                            title=title,
                            message=message,
                            notification_type=NotificationType.MAINTENANCE,
                            priority=priority,
                            source="maintenance_monitor",
                            data={
                                'key': existing_key,
                                'tezgah_id': tezgah.id,
                                'due_date': tezgah.sonraki_bakim_tarihi.isoformat()
                            },
                            expires_in_minutes=1440,  # 24 saat
                            action_text="Bakım Planla",
                            action_url=f"maintenance/plan/{tezgah.id}"
                        )
        
        except Exception as e:
            self.logger.error(f"Maintenance alert check failed: {e}")
    
    def check_battery_alerts(self):
        """Pil uyarılarını kontrol et"""
        try:
            from database_models import DatabaseManager, Pil, Tezgah
            
            db_manager = DatabaseManager()
            
            # 1 yıl önceki piller
            warning_date = datetime.now(timezone.utc) - timedelta(days=365)
            
            with db_manager.get_session() as session:
                old_batteries = session.query(Pil, Tezgah)\
                    .join(Tezgah)\
                    .filter(
                        Pil.degisim_tarihi <= warning_date,
                        Pil.durum == 'Aktif'
                    ).all()
                
                for pil, tezgah in old_batteries:
                    existing_key = f"battery_alert_{pil.id}"
                    
                    if not any(notif.data and notif.data.get('key') == existing_key 
                             for notif in self.notifications.values()):
                        
                        age_days = (datetime.now(timezone.utc) - pil.degisim_tarihi).days
                        
                        self.create_notification(
                            title="🔋 Pil Değişim Uyarısı",
                            message=f"{tezgah.numarasi} {pil.eksen} ekseni pili {age_days} günlük - değişim zamanı",
                            notification_type=NotificationType.BATTERY,
                            priority=NotificationPriority.HIGH,
                            source="battery_monitor",
                            data={
                                'key': existing_key,
                                'pil_id': pil.id,
                                'tezgah_id': tezgah.id,
                                'age_days': age_days
                            },
                            expires_in_minutes=2880,  # 48 saat
                            action_text="Pil Değiştir",
                            action_url=f"battery/change/{pil.id}"
                        )
        
        except Exception as e:
            self.logger.error(f"Battery alert check failed: {e}")
    
    def check_system_health(self):
        """Sistem sağlığını kontrol et"""
        try:
            try:
                import psutil
            except ImportError:
                self.logger.warning("psutil not available, skipping system health check")
                return
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.create_notification(
                    title="⚠️ Yüksek Bellek Kullanımı",
                    message=f"Sistem bellek kullanımı %{memory.percent:.1f} - performans etkilenebilir",
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.HIGH,
                    source="system_monitor",
                    expires_in_minutes=60
                )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.create_notification(
                    title="💾 Disk Alanı Yetersiz",
                    message=f"Disk kullanımı %{disk.percent:.1f} - alan temizliği gerekli",
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.CRITICAL,
                    source="system_monitor",
                    expires_in_minutes=120
                )
        
        except Exception as e:
            self.logger.error(f"System health check failed: {e}")
    
    def show_notifications(self):
        """Bildirim penceresini göster"""
        # Bu method UI tarafından implement edilecek
        self.logger.info("Show notifications requested")
    
    def export_notifications(self, filepath: str, days: int = 7) -> bool:
        """Bildirimleri export et"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with self.lock:
                export_data = []
                
                for notif in self.notifications.values():
                    if notif.timestamp >= cutoff_date:
                        export_data.append({
                            'id': notif.id,
                            'title': notif.title,
                            'message': notif.message,
                            'type': notif.type.value,
                            'priority': notif.priority.value,
                            'timestamp': notif.timestamp.isoformat(),
                            'source': notif.source,
                            'read': notif.read,
                            'dismissed': notif.dismissed,
                            'data': notif.data
                        })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_info': {
                        'timestamp': datetime.now().isoformat(),
                        'days': days,
                        'count': len(export_data)
                    },
                    'notifications': export_data
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Notifications exported to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Notification export failed: {e}")
            return False

# Global notification manager instance
notification_manager = NotificationManager()

# Convenience functions
def notify(title: str, message: str, 
          notification_type: NotificationType = NotificationType.INFO,
          priority: NotificationPriority = NotificationPriority.NORMAL,
          **kwargs) -> str:
    """Quick notification function"""
    return notification_manager.create_notification(
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        **kwargs
    )

def notify_maintenance_due(tezgah_name: str, days_overdue: int = 0):
    """Bakım uyarısı"""
    if days_overdue > 0:
        title = "🔴 Bakım Gecikti!"
        message = f"{tezgah_name} bakımı {days_overdue} gün gecikti"
        priority = NotificationPriority.CRITICAL
    else:
        title = "⚠️ Bakım Zamanı"
        message = f"{tezgah_name} bakım zamanı geldi"
        priority = NotificationPriority.HIGH
    
    return notify(title, message, NotificationType.MAINTENANCE, priority)

def notify_battery_old(tezgah_name: str, axis: str, age_days: int):
    """Pil uyarısı"""
    return notify(
        title="🔋 Pil Değişim Uyarısı",
        message=f"{tezgah_name} {axis} ekseni pili {age_days} günlük",
        notification_type=NotificationType.BATTERY,
        priority=NotificationPriority.HIGH
    )

def notify_error(title: str, message: str):
    """Hata bildirimi"""
    return notify(title, message, NotificationType.ERROR, NotificationPriority.HIGH)