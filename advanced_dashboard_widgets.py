#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Dashboard Widget'ları
Gerçek zamanlı grafikler, performans metrikleri ve uyarı sistemi
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QGridLayout, QProgressBar,
                            QGraphicsDropShadowEffect, QSizePolicy, QTextEdit,
                            QScrollArea, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QLinearGradient, QBrush, QPixmap

# Matplotlib stil ayarları
plt.style.use('dark_background')
matplotlib_logger = logging.getLogger('matplotlib')
matplotlib_logger.setLevel(logging.WARNING)

class RealTimeChart(QWidget):
    """Gerçek zamanlı grafik widget'ı"""
    
    def __init__(self, title: str, db_manager, chart_type: str = "line", parent=None):
        super().__init__(parent)
        self.title = title
        self.db_manager = db_manager
        self.chart_type = chart_type
        self.logger = logging.getLogger(__name__)
        
        # Veri depolama
        self.time_data = []
        self.value_data = []
        self.max_points = 50  # Son 50 veri noktası
        
        self.setup_ui()
        self.setup_chart()
        self.setup_timer()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(500, 300)  # Boyutu küçülttük
        
        # Ana layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #ffffff; 
            background-color: #2c3e50;
            padding: 8px;
            border-radius: 5px;
            margin-bottom: 5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Grafik alanı
        self.figure = Figure(figsize=(8, 5), dpi=80, facecolor='#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555555; border-radius: 5px;")
        layout.addWidget(self.canvas)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        self.pause_btn = QPushButton("⏸️ Duraklat")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_btn)
        
        self.clear_btn = QPushButton("🗑️ Temizle")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def setup_chart(self):
        """Grafik kurulumu"""
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        
        # Başlangıç çizgisi
        self.line, = self.ax.plot([], [], 'g-', linewidth=2, marker='o', markersize=4)
        
        # Grid
        self.ax.grid(True, alpha=0.3, color='white')
        
        # Etiketler
        self.ax.set_xlabel('Zaman', color='white', fontweight='bold')
        self.ax.set_ylabel('Değer', color='white', fontweight='bold')
        
        self.figure.tight_layout()
    
    def setup_timer(self):
        """Timer kurulumu"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(5000)  # 5 saniyede bir güncelle
        self.is_paused = False
    
    def update_chart(self):
        """Grafiği güncelle"""
        if self.is_paused:
            return
        
        try:
            # Yeni veri al
            new_value = self.get_latest_data()
            current_time = datetime.now()
            
            # Veri ekle
            self.time_data.append(current_time)
            self.value_data.append(new_value)
            
            # Maksimum nokta sayısını aş
            if len(self.time_data) > self.max_points:
                self.time_data.pop(0)
                self.value_data.pop(0)
            
            # Grafiği güncelle
            if len(self.time_data) > 1:
                self.line.set_data(range(len(self.time_data)), self.value_data)
                
                # Eksen sınırlarını ayarla
                self.ax.set_xlim(0, len(self.time_data) - 1)
                if self.value_data:
                    min_val = min(self.value_data)
                    max_val = max(self.value_data)
                    margin = (max_val - min_val) * 0.1 if max_val != min_val else 1
                    self.ax.set_ylim(min_val - margin, max_val + margin)
                
                # X ekseni etiketlerini güncelle
                if len(self.time_data) >= 5:
                    step = max(1, len(self.time_data) // 5)
                    tick_positions = range(0, len(self.time_data), step)
                    tick_labels = [self.time_data[i].strftime('%H:%M') for i in tick_positions]
                    self.ax.set_xticks(tick_positions)
                    self.ax.set_xticklabels(tick_labels, rotation=45)
                
                self.canvas.draw()
                
        except Exception as e:
            self.logger.error(f"Chart update error: {e}")
    
    def get_latest_data(self) -> float:
        """En son veriyi al - alt sınıflar tarafından override edilecek"""
        # Örnek veri - gerçek implementasyonda veritabanından alınacak
        return np.random.randint(0, 100)
    
    def toggle_pause(self):
        """Duraklatma/devam ettirme"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setText("▶️ Devam")
            self.timer.stop()
        else:
            self.pause_btn.setText("⏸️ Duraklat")
            self.timer.start(5000)
    
    def clear_data(self):
        """Veriyi temizle"""
        self.time_data.clear()
        self.value_data.clear()
        self.ax.clear()
        self.setup_chart()
        self.canvas.draw()

class MaintenanceTrendChart(RealTimeChart):
    """Bakım trend grafiği"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__("📈 Gerçek Zamanlı Arıza Trendi", db_manager, "line", parent)
    
    def get_latest_data(self) -> float:
        """Son 24 saatteki arıza sayısını al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Bakim
                
                # Son 24 saatteki arızalar
                last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
                count = session.query(Bakim).filter(
                    Bakim.tarih >= last_24h
                ).count()
                
                return float(count)
                
        except Exception as e:
            self.logger.error(f"Maintenance trend data error: {e}")
            return 0.0

class PerformanceMetricsWidget(QFrame):
    """Performans metrikleri widget'ı"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(400, 280)  # Boyutu küçülttük
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #2c3e50;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Başlık
        title_label = QLabel("⚡ Performans Metrikleri")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #000000; 
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Metrik kartları için grid
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(10)
        
        # MTBF (Mean Time Between Failures)
        self.mtbf_card = self.create_metric_card("🔧 MTBF", "0 gün", "#3498db")
        metrics_layout.addWidget(self.mtbf_card, 0, 0)
        
        # MTTR (Mean Time To Repair)
        self.mttr_card = self.create_metric_card("⏱️ MTTR", "0 saat", "#e74c3c")
        metrics_layout.addWidget(self.mttr_card, 0, 1)
        
        # Tezgah Verimliliği
        self.efficiency_card = self.create_metric_card("📊 Verimlilik", "0%", "#2ecc71")
        metrics_layout.addWidget(self.efficiency_card, 1, 0)
        
        # Toplam Çalışma Süresi
        self.uptime_card = self.create_metric_card("⏰ Çalışma", "0%", "#f39c12")
        metrics_layout.addWidget(self.uptime_card, 1, 1)
        
        layout.addLayout(metrics_layout)
        
        # Detaylı bilgi alanı
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                color: #000000;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.details_text.setPlainText("Performans metrikleri hesaplanıyor...")
        layout.addWidget(self.details_text)
        
        self.setLayout(layout)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
    
    def create_metric_card(self, title: str, value: str, color: str) -> QFrame:
        """Metrik kartı oluştur"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 10px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 12px; 
            font-weight: bold; 
            color: white;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Değer
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: white;
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        
        # Kartı döndürmek için referans sakla
        card.value_label = value_label
        
        return card
    
    def setup_timer(self):
        """Timer kurulumu"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(10000)  # 10 saniyede bir güncelle
        
        # İlk güncelleme
        self.update_metrics()
    
    def update_metrics(self):
        """Metrikleri güncelle"""
        try:
            metrics = self.calculate_performance_metrics()
            
            # Kartları güncelle
            self.mtbf_card.value_label.setText(f"{metrics['mtbf']:.1f} gün")
            self.mttr_card.value_label.setText(f"{metrics['mttr']:.1f} saat")
            self.efficiency_card.value_label.setText(f"{metrics['efficiency']:.1f}%")
            self.uptime_card.value_label.setText(f"{metrics['uptime']:.1f}%")
            
            # Detaylı bilgi güncelle
            details = f"""
📊 PERFORMANS ANALİZİ:

🔧 MTBF (Arızalar Arası Ortalama Süre): {metrics['mtbf']:.1f} gün
   • Toplam çalışma süresi: {metrics['total_runtime']:.1f} saat
   • Toplam arıza sayısı: {metrics['total_failures']} adet

⏱️ MTTR (Ortalama Tamir Süresi): {metrics['mttr']:.1f} saat
   • En hızlı tamir: {metrics['min_repair_time']:.1f} saat
   • En yavaş tamir: {metrics['max_repair_time']:.1f} saat

📈 Verimlilik Trendi: {metrics['efficiency_trend']}
⚠️ Kritik Tezgahlar: {metrics['critical_machines']}
            """
            self.details_text.setPlainText(details.strip())
            
        except Exception as e:
            self.logger.error(f"Metrics update error: {e}")
            self.details_text.setPlainText(f"❌ Metrik hesaplama hatası: {e}")
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Performans metriklerini hesapla"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim
                from sqlalchemy import func
                
                # Temel veriler
                total_machines = session.query(Tezgah).filter(Tezgah.durum == 'Aktif').count()
                total_failures = session.query(Bakim).count()
                
                # Son 30 günlük veriler
                last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
                recent_failures = session.query(Bakim).filter(
                    Bakim.tarih >= last_30_days
                ).count()
                
                # MTBF hesaplama (Mean Time Between Failures)
                if total_failures > 0:
                    # Toplam çalışma süresi (30 gün * 24 saat * aktif tezgah sayısı)
                    total_runtime = 30 * 24 * total_machines
                    mtbf = total_runtime / max(recent_failures, 1) / 24  # Günlük
                else:
                    mtbf = 30.0  # Arıza yoksa 30 gün
                    total_runtime = 30 * 24 * total_machines
                
                # MTTR hesaplama (Mean Time To Repair)
                # Basit hesaplama - gerçek uygulamada tamir süresi kaydedilmeli
                mttr = 2.5  # Ortalama 2.5 saat (örnek değer)
                
                # Verimlilik hesaplama
                if total_machines > 0:
                    # Arıza oranına göre verimlilik
                    failure_rate = recent_failures / max(total_machines, 1)
                    efficiency = max(0, 100 - (failure_rate * 10))  # Basit formül
                else:
                    efficiency = 0
                
                # Çalışma süresi (uptime)
                uptime = max(0, 100 - (recent_failures / max(total_machines * 30, 1) * 100))
                
                # En çok arıza olan tezgahlar
                critical_query = session.query(
                    Tezgah.numarasi,
                    func.count(Bakim.id).label('failure_count')
                ).join(Bakim).filter(
                    Bakim.tarih >= last_30_days
                ).group_by(Tezgah.id).order_by(
                    func.count(Bakim.id).desc()
                ).limit(3).all()
                
                critical_machines = ", ".join([f"{t.numarasi}({t.failure_count})" for t in critical_query])
                if not critical_machines:
                    critical_machines = "Yok"
                
                # Trend analizi
                if recent_failures > total_failures / 2:
                    efficiency_trend = "📈 Artan"
                elif recent_failures < total_failures / 4:
                    efficiency_trend = "📉 Azalan"
                else:
                    efficiency_trend = "📊 Stabil"
                
                return {
                    'mtbf': mtbf,
                    'mttr': mttr,
                    'efficiency': efficiency,
                    'uptime': uptime,
                    'total_runtime': total_runtime,
                    'total_failures': total_failures,
                    'min_repair_time': 0.5,  # Örnek değer
                    'max_repair_time': 8.0,  # Örnek değer
                    'efficiency_trend': efficiency_trend,
                    'critical_machines': critical_machines
                }
                
        except Exception as e:
            self.logger.error(f"Performance metrics calculation error: {e}")
            return {
                'mtbf': 0.0, 'mttr': 0.0, 'efficiency': 0.0, 'uptime': 0.0,
                'total_runtime': 0.0, 'total_failures': 0,
                'min_repair_time': 0.0, 'max_repair_time': 0.0,
                'efficiency_trend': 'Bilinmiyor', 'critical_machines': 'Veri yok'
            }

class AlertNotificationWidget(QFrame):
    """Uyarı bildirimi widget'ı"""
    
    alert_triggered = pyqtSignal(str, str, str)  # title, message, level
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.alerts = []
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(350, 250)  # Boyutu küçülttük
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Başlık
        title_label = QLabel("🚨 Kritik Uyarılar")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #000000; 
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Uyarı listesi
        self.alert_scroll = QScrollArea()
        self.alert_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
        """)
        
        self.alert_widget = QWidget()
        self.alert_layout = QVBoxLayout()
        self.alert_layout.setSpacing(5)
        self.alert_widget.setLayout(self.alert_layout)
        
        self.alert_scroll.setWidget(self.alert_widget)
        self.alert_scroll.setWidgetResizable(True)
        layout.addWidget(self.alert_scroll)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Temizle")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_alerts)
        button_layout.addWidget(self.clear_btn)
        
        self.refresh_btn = QPushButton("🔄 Yenile")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.refresh_btn.clicked.connect(self.check_alerts)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
    
    def setup_timer(self):
        """Timer kurulumu"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alerts)
        self.timer.start(30000)  # 30 saniyede bir kontrol et
        
        # İlk kontrol
        self.check_alerts()
    
    def check_alerts(self):
        """Uyarıları kontrol et"""
        try:
            new_alerts = self.get_critical_alerts()
            
            for alert in new_alerts:
                if alert not in self.alerts:
                    self.add_alert(alert)
                    # Signal gönder
                    self.alert_triggered.emit(
                        alert['title'], 
                        alert['message'], 
                        alert['level']
                    )
            
            self.alerts = new_alerts
            
        except Exception as e:
            self.logger.error(f"Alert check error: {e}")
    
    def get_critical_alerts(self) -> List[Dict[str, Any]]:
        """Kritik uyarıları al"""
        alerts = []
        
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim, Pil
                from sqlalchemy import func
                
                # 1. Geciken bakımlar
                overdue_machines = session.query(Tezgah).filter(
                    Tezgah.sonraki_bakim_tarihi < datetime.now(timezone.utc),
                    Tezgah.durum == 'Aktif'
                ).all()
                
                for machine in overdue_machines:
                    days_overdue = (datetime.now(timezone.utc) - machine.sonraki_bakim_tarihi).days
                    alerts.append({
                        'title': f'⚠️ Geciken Bakım',
                        'message': f'Tezgah {machine.numarasi}: {days_overdue} gün gecikme',
                        'level': 'warning' if days_overdue < 7 else 'critical',
                        'timestamp': datetime.now(),
                        'type': 'overdue_maintenance'
                    })
                
                # 2. Eski piller
                old_batteries = session.query(Pil).filter(
                    Pil.durum == 'Aktif',
                    Pil.degisim_tarihi <= datetime.now(timezone.utc) - timedelta(days=365)
                ).all()
                
                for battery in old_batteries:
                    days_old = (datetime.now(timezone.utc) - battery.degisim_tarihi).days
                    alerts.append({
                        'title': f'🔋 Eski Pil',
                        'message': f'Tezgah {battery.tezgah.numarasi} - Eksen {battery.eksen}: {days_old} gün eski',
                        'level': 'warning' if days_old < 400 else 'critical',
                        'timestamp': datetime.now(),
                        'type': 'old_battery'
                    })
                
                # 3. Sık arızalanan tezgahlar
                frequent_failures = session.query(
                    Tezgah.numarasi,
                    func.count(Bakim.id).label('failure_count')
                ).join(Bakim).filter(
                    Bakim.tarih >= datetime.now(timezone.utc) - timedelta(days=30)
                ).group_by(Tezgah.id).having(
                    func.count(Bakim.id) >= 5
                ).all()
                
                for machine in frequent_failures:
                    alerts.append({
                        'title': f'🔧 Sık Arıza',
                        'message': f'Tezgah {machine.numarasi}: Son 30 günde {machine.failure_count} arıza',
                        'level': 'critical',
                        'timestamp': datetime.now(),
                        'type': 'frequent_failure'
                    })
                
        except Exception as e:
            self.logger.error(f"Get critical alerts error: {e}")
        
        return alerts
    
    def add_alert(self, alert: Dict[str, Any]):
        """Uyarı ekle"""
        alert_frame = QFrame()
        
        # Seviyeye göre renk
        if alert['level'] == 'critical':
            bg_color = "#ffebee"
            border_color = "#f44336"
        elif alert['level'] == 'warning':
            bg_color = "#fff3e0"
            border_color = "#ff9800"
        else:
            bg_color = "#e3f2fd"
            border_color = "#2196f3"
        
        alert_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 5px;
                padding: 8px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Başlık ve zaman
        header_layout = QHBoxLayout()
        
        title_label = QLabel(alert['title'])
        title_label.setStyleSheet("font-weight: bold; color: #000000; font-size: 12px;")
        header_layout.addWidget(title_label)
        
        time_label = QLabel(alert['timestamp'].strftime('%H:%M'))
        time_label.setStyleSheet("color: #666666; font-size: 10px;")
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Mesaj
        message_label = QLabel(alert['message'])
        message_label.setStyleSheet("color: #000000; font-size: 11px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        alert_frame.setLayout(layout)
        self.alert_layout.addWidget(alert_frame)
    
    def clear_alerts(self):
        """Uyarıları temizle"""
        # Layout'taki tüm widget'ları kaldır
        for i in reversed(range(self.alert_layout.count())):
            child = self.alert_layout.itemAt(i)
            if child and child.widget():
                child.widget().setParent(None)
        
        self.alerts.clear()

class MaintenanceAnalysisWidget(QFrame):
    """Bakım geçmişi analizi widget'ı"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(500, 320)  # Boyutu küçülttük
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #2c3e50;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Başlık
        title_label = QLabel("🔍 Bakım Geçmişi Analizi")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #000000; 
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Analiz tablosu
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(4)
        self.analysis_table.setHorizontalHeaderLabels([
            "Tezgah", "Arıza Sayısı", "Son Arıza", "Risk Seviyesi"
        ])
        
        # Tablo stili
        self.analysis_table.setStyleSheet("""
            QTableWidget {
                background-color: #f8f9fa;
                alternate-background-color: #e9ecef;
                color: #000000;
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QHeaderView::section {
                background-color: #6c757d;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.analysis_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.analysis_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.analysis_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.analysis_table)
        
        # Özet bilgiler
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(100)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                color: #000000;
                font-size: 11px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.summary_text)
        
        self.setLayout(layout)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
    
    def setup_timer(self):
        """Timer kurulumu"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_analysis)
        self.timer.start(60000)  # 1 dakikada bir güncelle
        
        # İlk güncelleme
        self.update_analysis()
    
    def update_analysis(self):
        """Analizi güncelle"""
        try:
            analysis_data = self.get_maintenance_analysis()
            
            # Tabloyu güncelle
            self.analysis_table.setRowCount(len(analysis_data['machines']))
            
            for row, machine_data in enumerate(analysis_data['machines']):
                # Tezgah
                self.analysis_table.setItem(row, 0, QTableWidgetItem(machine_data['tezgah']))
                
                # Arıza sayısı
                failure_item = QTableWidgetItem(str(machine_data['failure_count']))
                if machine_data['failure_count'] >= 5:
                    failure_item.setBackground(QColor("#ffebee"))
                self.analysis_table.setItem(row, 1, failure_item)
                
                # Son arıza
                last_failure = machine_data['last_failure']
                if last_failure:
                    last_failure_text = last_failure.strftime('%d.%m.%Y')
                else:
                    last_failure_text = "Yok"
                self.analysis_table.setItem(row, 2, QTableWidgetItem(last_failure_text))
                
                # Risk seviyesi
                risk_item = QTableWidgetItem(machine_data['risk_level'])
                if machine_data['risk_level'] == 'Yüksek':
                    risk_item.setBackground(QColor("#ffebee"))
                elif machine_data['risk_level'] == 'Orta':
                    risk_item.setBackground(QColor("#fff3e0"))
                else:
                    risk_item.setBackground(QColor("#e8f5e8"))
                self.analysis_table.setItem(row, 3, risk_item)
            
            # Özet güncelle
            summary = f"""
📊 ANALİZ ÖZETİ:
• Toplam Tezgah: {analysis_data['total_machines']}
• Yüksek Riskli: {analysis_data['high_risk_count']} tezgah
• Orta Riskli: {analysis_data['medium_risk_count']} tezgah
• Düşük Riskli: {analysis_data['low_risk_count']} tezgah

🔧 En Problemli: {analysis_data['most_problematic']}
📈 Trend: {analysis_data['trend_analysis']}
            """
            self.summary_text.setPlainText(summary.strip())
            
        except Exception as e:
            self.logger.error(f"Analysis update error: {e}")
            self.summary_text.setPlainText(f"❌ Analiz hatası: {e}")
    
    def get_maintenance_analysis(self) -> Dict[str, Any]:
        """Bakım analizi verilerini al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim
                from sqlalchemy import func
                
                # Son 90 günlük analiz
                analysis_period = datetime.now(timezone.utc) - timedelta(days=90)
                
                # Tezgah bazında arıza sayıları
                machine_failures = session.query(
                    Tezgah.numarasi,
                    func.count(Bakim.id).label('failure_count'),
                    func.max(Bakim.tarih).label('last_failure')
                ).outerjoin(Bakim).filter(
                    Bakim.tarih >= analysis_period
                ).group_by(Tezgah.id, Tezgah.numarasi).all()
                
                machines_data = []
                high_risk = medium_risk = low_risk = 0
                most_problematic = "Yok"
                max_failures = 0
                
                for machine in machine_failures:
                    failure_count = machine.failure_count or 0
                    
                    # Risk seviyesi belirleme
                    if failure_count >= 5:
                        risk_level = "Yüksek"
                        high_risk += 1
                    elif failure_count >= 2:
                        risk_level = "Orta"
                        medium_risk += 1
                    else:
                        risk_level = "Düşük"
                        low_risk += 1
                    
                    # En problemli tezgah
                    if failure_count > max_failures:
                        max_failures = failure_count
                        most_problematic = f"{machine.numarasi} ({failure_count} arıza)"
                    
                    machines_data.append({
                        'tezgah': machine.numarasi,
                        'failure_count': failure_count,
                        'last_failure': machine.last_failure,
                        'risk_level': risk_level
                    })
                
                # Risk seviyesine göre sırala
                machines_data.sort(key=lambda x: x['failure_count'], reverse=True)
                
                # Trend analizi
                recent_failures = session.query(Bakim).filter(
                    Bakim.tarih >= datetime.now(timezone.utc) - timedelta(days=30)
                ).count()
                
                older_failures = session.query(Bakim).filter(
                    Bakim.tarih >= datetime.now(timezone.utc) - timedelta(days=60),
                    Bakim.tarih < datetime.now(timezone.utc) - timedelta(days=30)
                ).count()
                
                if recent_failures > older_failures:
                    trend = "📈 Artan arıza trendi"
                elif recent_failures < older_failures:
                    trend = "📉 Azalan arıza trendi"
                else:
                    trend = "📊 Stabil trend"
                
                return {
                    'machines': machines_data,
                    'total_machines': len(machines_data),
                    'high_risk_count': high_risk,
                    'medium_risk_count': medium_risk,
                    'low_risk_count': low_risk,
                    'most_problematic': most_problematic,
                    'trend_analysis': trend
                }
                
        except Exception as e:
            self.logger.error(f"Maintenance analysis error: {e}")
            return {
                'machines': [],
                'total_machines': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'most_problematic': 'Veri yok',
                'trend_analysis': 'Analiz edilemiyor'
            }

class CriticalAlertDialog(QDialog):
    """Kritik uyarı dialog'u"""
    
    def __init__(self, title: str, message: str, level: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚨 Kritik Uyarı")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        # Seviyeye göre stil
        if level == 'critical':
            border_color = "#f44336"
            bg_color = "#ffebee"
        elif level == 'warning':
            border_color = "#ff9800"
            bg_color = "#fff3e0"
        else:
            border_color = "#2196f3"
            bg_color = "#e3f2fd"
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 3px solid {border_color};
                border-radius: 10px;
            }}
            QLabel {{
                color: #000000;
                font-size: 12px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {border_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Mesaj
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        # Butonlar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)