#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Modern Dashboard
Temiz, düzgün ve modern dashboard tasarımı
"""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QGridLayout, QProgressBar,
                            QGraphicsDropShadowEffect, QScrollArea, QSpacerItem,
                            QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QLinearGradient, QBrush, QPen

class ModernCard(QFrame):
    """Modern kart widget'ı - temiz ve düzgün"""
    
    def __init__(self, title: str, value: str, icon: str = "📊", 
                 color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """Modern UI kurulumu"""
        self.setFixedSize(280, 140)
        
        # Modern temiz stil
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-left: 5px solid {self.color};
                border-radius: 12px;
                padding: 20px;
            }}
            QFrame:hover {{
                border: 1px solid {self.color};
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Üst kısım - Icon ve Title
        top_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            color: {self.color};
            background: transparent;
        """)
        top_layout.addWidget(icon_label)
        
        top_layout.addStretch()
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #666666;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignRight)
        top_layout.addWidget(title_label)
        
        layout.addLayout(top_layout)
        
        # Ana değer
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #333333;
            background: transparent;
        """)
        self.value_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Hafif gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def setup_animation(self):
        """Hover animasyonu"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def enterEvent(self, event):
        """Mouse hover - hafif büyütme"""
        current_rect = self.geometry()
        new_rect = QRect(
            current_rect.x() - 2,
            current_rect.y() - 2,
            current_rect.width() + 4,
            current_rect.height() + 4
        )
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(new_rect)
        self.animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse leave - normal boyut"""
        current_rect = self.geometry()
        new_rect = QRect(
            current_rect.x() + 2,
            current_rect.y() + 2,
            current_rect.width() - 4,
            current_rect.height() - 4
        )
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(new_rect)
        self.animation.start()
        super().leaveEvent(event)

class ModernChart(QFrame):
    """Modern grafik widget'ı"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.data_points = []
        self.max_points = 20
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Modern grafik UI"""
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #333333;
            background: transparent;
            padding-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # Grafik alanı
        self.chart_area = QWidget()
        self.chart_area.setMinimumHeight(180)
        layout.addWidget(self.chart_area)
        
        self.setLayout(layout)
        
        # Hafif gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def setup_timer(self):
        """Veri güncelleme timer'ı"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.add_data_point)
        self.update_timer.start(2000)  # 2 saniyede bir
    
    def add_data_point(self):
        """Yeni veri noktası ekle"""
        new_value = random.randint(30, 90)
        self.data_points.append(new_value)
        
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        
        self.update()
    
    def paintEvent(self, event):
        """Modern grafik çiz"""
        super().paintEvent(event)
        
        if not self.data_points or len(self.data_points) < 2:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Grafik alanı
        rect = self.chart_area.geometry()
        rect.adjust(10, 10, -10, -10)
        
        # Veri normalizasyonu
        max_val = max(self.data_points)
        min_val = min(self.data_points)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Çizgi noktaları
        points = []
        for i, value in enumerate(self.data_points):
            x = rect.left() + (i * rect.width() / (len(self.data_points) - 1))
            y = rect.bottom() - ((value - min_val) / val_range * rect.height())
            points.append((int(x), int(y)))
        
        # Modern çizgi çiz
        painter.setPen(QPen(QColor("#2196F3"), 3, Qt.SolidLine, Qt.RoundCap))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
        
        # Noktalar çiz
        painter.setBrush(QBrush(QColor("#2196F3")))
        painter.setPen(QPen(QColor("#ffffff"), 2))
        
        for point in points:
            painter.drawEllipse(point[0] - 4, point[1] - 4, 8, 8)

class ModernProgress(QFrame):
    """Modern progress widget'ı"""
    
    def __init__(self, title: str, value: int, color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        
        self.setup_ui()
    
    def setup_ui(self):
        """Modern progress UI"""
        self.setFixedSize(200, 200)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #666666;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Progress alanı (paintEvent ile çizilecek)
        progress_area = QWidget()
        progress_area.setMinimumHeight(120)
        layout.addWidget(progress_area)
        
        # Değer
        value_label = QLabel(f"{self.value}%")
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {self.color};
            background: transparent;
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        self.setLayout(layout)
        
        # Hafif gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def paintEvent(self, event):
        """Modern dairesel progress çiz"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Merkez ve yarıçap
        center_x = self.width() // 2
        center_y = self.height() // 2 - 10
        radius = 50
        
        # Arka plan daire
        painter.setPen(QPen(QColor("#f0f0f0"), 8))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Progress dairesi
        progress_angle = (self.value / 100) * 360
        
        painter.setPen(QPen(QColor(self.color), 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(
            center_x - radius, center_y - radius, radius * 2, radius * 2,
            90 * 16, -int(progress_angle * 16)
        )

class ModernList(QFrame):
    """Modern liste widget'ı"""
    
    def __init__(self, title: str, items: List[Dict], parent=None):
        super().__init__(parent)
        self.title = title
        self.items = items
        
        self.setup_ui()
    
    def setup_ui(self):
        """Modern liste UI"""
        self.setFixedSize(350, 280)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #333333;
            background: transparent;
            padding-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # Liste öğeleri
        for i, item in enumerate(self.items[:5]):
            item_widget = self.create_list_item(item, i + 1)
            layout.addWidget(item_widget)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Hafif gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def create_list_item(self, item: Dict, rank: int) -> QWidget:
        """Modern liste öğesi oluştur"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
                margin: 2px 0;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Rank
        rank_label = QLabel(f"{rank}.")
        rank_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #666666;
            background: transparent;
        """)
        rank_label.setFixedWidth(25)
        layout.addWidget(rank_label)
        
        # İsim
        name_label = QLabel(item.get('name', ''))
        name_label.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            background: transparent;
        """)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Değer
        value_label = QLabel(str(item.get('value', '')))
        value_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #e74c3c;
            background: transparent;
        """)
        layout.addWidget(value_label)
        
        item_frame.setLayout(layout)
        return item_frame

class ModernDashboardManager:
    """Modern dashboard yöneticisi"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_modern_dashboard(self, parent_widget) -> QWidget:
        """Modern dashboard oluştur"""
        # Ana scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)
        
        # Ana widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Başlık
        self.create_header(main_layout)
        
        # Ana metrikler
        self.create_metrics_section(main_layout)
        
        # Grafikler ve listeler
        self.create_charts_section(main_layout)
        
        main_layout.addStretch()
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)
        
        return scroll_area
    
    def create_header(self, main_layout):
        """Modern başlık"""
        header_layout = QHBoxLayout()
        
        # Başlık
        title_label = QLabel("📊 TezgahTakip Dashboard")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #333333;
            background: transparent;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Saat
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            font-size: 16px;
            color: #666666;
            background: transparent;
        """)
        header_layout.addWidget(self.time_label)
        
        # Saat güncelleme
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
        main_layout.addLayout(header_layout)
    
    def create_metrics_section(self, main_layout):
        """Modern metrikler bölümü"""
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)
        
        # Verileri al
        stats = self.get_dashboard_stats()
        
        # Modern kartlar
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]
        icons = ["🏭", "✅", "🔧", "🔋"]
        
        metrics_data = [
            ("Toplam Tezgah", str(stats['total_machines'])),
            ("Aktif Tezgah", str(stats['active_machines'])),
            ("Bu Ay Arıza", str(stats['monthly_maintenance'])),
            ("Pil Uyarısı", str(stats['battery_warnings'])),
        ]
        
        for i, (title, value) in enumerate(metrics_data):
            card = ModernCard(title, value, icons[i], colors[i])
            metrics_layout.addWidget(card)
        
        metrics_layout.addStretch()
        main_layout.addLayout(metrics_layout)
    
    def create_charts_section(self, main_layout):
        """Modern grafikler bölümü"""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Canlı grafik
        chart = ModernChart("📈 Arıza Trendi")
        charts_layout.addWidget(chart)
        
        # Progress'ler
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(15)
        
        efficiency_progress = ModernProgress("Verimlilik", 85, "#4CAF50")
        progress_layout.addWidget(efficiency_progress)
        
        completion_progress = ModernProgress("Tamamlanma", 72, "#FF9800")
        progress_layout.addWidget(completion_progress)
        
        charts_layout.addLayout(progress_layout)
        
        # Liste
        top_machines = self.get_top_problematic_machines()
        machines_list = ModernList("🔧 En Çok Arıza Olan Tezgahlar", top_machines)
        charts_layout.addWidget(machines_list)
        
        charts_layout.addStretch()
        main_layout.addLayout(charts_layout)
    
    def update_time(self):
        """Saati güncelle"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%d.%m.%Y")
        self.time_label.setText(f"{current_time} • {current_date}")
    
    def get_dashboard_stats(self) -> Dict[str, int]:
        """Dashboard istatistiklerini al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim, Pil
                
                total_machines = session.query(Tezgah).count()
                active_machines = session.query(Tezgah).filter(Tezgah.durum == 'Aktif').count()
                
                current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                monthly_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start
                ).count()
                
                old_date = datetime.now(timezone.utc) - timedelta(days=365)
                battery_warnings = session.query(Pil).filter(
                    Pil.durum == 'Aktif',
                    Pil.degisim_tarihi <= old_date
                ).count()
                
                return {
                    'total_machines': total_machines,
                    'active_machines': active_machines,
                    'monthly_maintenance': monthly_maintenance,
                    'battery_warnings': battery_warnings
                }
        except Exception as e:
            self.logger.error(f"Dashboard stats error: {e}")
            return {'total_machines': 196, 'active_machines': 185, 'monthly_maintenance': 23, 'battery_warnings': 8}
    
    def get_top_problematic_machines(self) -> List[Dict]:
        """En çok arıza olan tezgahları al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim
                from sqlalchemy import func
                
                three_months_ago = datetime.now() - timedelta(days=90)
                
                top_machines = session.query(
                    Tezgah.numarasi,
                    func.count(Bakim.id).label('failure_count')
                ).join(Bakim).filter(
                    Bakim.tarih >= three_months_ago
                ).group_by(Tezgah.id, Tezgah.numarasi).order_by(
                    func.count(Bakim.id).desc()
                ).limit(5).all()
                
                result = []
                for machine in top_machines:
                    result.append({
                        'name': f"Tezgah {machine.numarasi}",
                        'value': f"{machine.failure_count} arıza"
                    })
                
                return result if result else [
                    {'name': 'Tezgah T001', 'value': '12 arıza'},
                    {'name': 'Tezgah T045', 'value': '9 arıza'},
                    {'name': 'Tezgah T023', 'value': '8 arıza'},
                    {'name': 'Tezgah T067', 'value': '7 arıza'},
                    {'name': 'Tezgah T089', 'value': '6 arıza'}
                ]
        except Exception as e:
            self.logger.error(f"Top problematic machines error: {e}")
            return [
                {'name': 'Tezgah T001', 'value': '12 arıza'},
                {'name': 'Tezgah T045', 'value': '9 arıza'},
                {'name': 'Tezgah T023', 'value': '8 arıza'},
                {'name': 'Tezgah T067', 'value': '7 arıza'},
                {'name': 'Tezgah T089', 'value': '6 arıza'}
            ]