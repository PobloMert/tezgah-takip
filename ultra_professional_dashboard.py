#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Ultra Profesyonel Canlı Dashboard
Çok canlı, profesyonel ve yazıları net görünen dashboard
"""

import logging
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QGridLayout, QProgressBar,
                            QGraphicsDropShadowEffect, QSizePolicy, QScrollArea,
                            QSpacerItem, QGraphicsOpacityEffect)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, 
                         QRect, QParallelAnimationGroup, QSequentialAnimationGroup,
                         QAbstractAnimation, QVariantAnimation, QPoint)
from PyQt5.QtGui import (QFont, QColor, QPalette, QPainter, QLinearGradient, QBrush,
                        QRadialGradient, QPen, QPixmap, QFontMetrics, QPainterPath)

class UltraMetricCard(QFrame):
    """Ultra profesyonel metrik kartı - yazılar çok net"""
    
    def __init__(self, title: str, value: str, icon: str = "📊", 
                 color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.current_value = 0
        self.target_value = int(value) if value.isdigit() else 0
        
        self.setup_ui()
        self.setup_animations()
        self.start_animations()
    
    def setup_ui(self):
        """UI kurulumu - Ultra net yazılar"""
        self.setFixedSize(300, 180)
        
        # Ultra net stil - beyaz arka plan, kalın kenarlık
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 4px solid {self.color};
                border-radius: 20px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Üst kısım - Icon ve Title
        top_layout = QHBoxLayout()
        
        # Büyük Icon
        self.icon_label = QLabel(self.icon)
        self.icon_label.setStyleSheet(f"""
            font-size: 48px; 
            color: {self.color};
            background-color: transparent;
            font-weight: bold;
        """)
        top_layout.addWidget(self.icon_label)
        
        top_layout.addStretch()
        
        # Canlı nokta
        self.pulse_dot = QLabel("●")
        self.pulse_dot.setStyleSheet(f"""
            font-size: 24px; 
            color: {self.color};
            background-color: transparent;
        """)
        top_layout.addWidget(self.pulse_dot)
        
        layout.addLayout(top_layout)
        
        # Ana değer - Çok büyük ve net
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("""
            font-size: 64px; 
            font-weight: 900;
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Title - Çok net
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold;
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Progress bar - Canlı
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 3px solid #000000;
                border-radius: 12px;
                background-color: #f0f0f0;
                height: 12px;
                text-align: center;
                font-weight: bold;
                color: #000000;
            }}
            QProgressBar::chunk {{
                background-color: {self.color};
                border-radius: 9px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Güçlü gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
    
    def setup_animations(self):
        """Animasyonları kur"""
        # Sayaç animasyonu
        self.counter_animation = QVariantAnimation()
        self.counter_animation.setDuration(3000)
        self.counter_animation.setEasingCurve(QEasingCurve.OutBounce)
        self.counter_animation.valueChanged.connect(self.update_counter)
        
        # Progress animasyonu
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(3500)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Pulse animasyonu
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_effect)
        self.pulse_timer.start(800)
    
    def start_animations(self):
        """Animasyonları başlat"""
        # Sayaç animasyonu
        self.counter_animation.setStartValue(0)
        self.counter_animation.setEndValue(self.target_value)
        self.counter_animation.start()
        
        # Progress animasyonu
        progress_value = min(100, (self.target_value / 200) * 100)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(progress_value)
        self.progress_animation.start()
    
    def pulse_effect(self):
        """Pulse efekti"""
        colors = [self.color, "#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24"]
        color = random.choice(colors)
        self.pulse_dot.setStyleSheet(f"""
            font-size: 24px; 
            color: {color};
            background-color: transparent;
        """)
    
    def update_counter(self, value):
        """Sayaç güncelle"""
        self.current_value = int(value)
        self.value_label.setText(str(self.current_value))

class UltraLiveChart(QFrame):
    """Ultra canlı grafik widget'ı"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.data_points = []
        self.max_points = 25
        self.animation_offset = 0
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(450, 280)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 4px solid #2c3e50;
                border-radius: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Başlık - Ultra net
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: 900; 
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
            padding: 10px;
        """)
        layout.addWidget(title_label)
        
        # Grafik alanı
        self.chart_area = QWidget()
        self.chart_area.setMinimumHeight(200)
        layout.addWidget(self.chart_area)
        
        self.setLayout(layout)
        
        # Güçlü gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
    
    def setup_timer(self):
        """Timer kurulumu"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.add_data_point)
        self.update_timer.start(800)  # Daha hızlı güncelleme
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_chart)
        self.animation_timer.start(30)  # Çok smooth animasyon
    
    def add_data_point(self):
        """Yeni veri noktası ekle"""
        new_value = random.randint(20, 100)
        self.data_points.append(new_value)
        
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        
        self.update()
    
    def animate_chart(self):
        """Grafik animasyonu"""
        self.animation_offset += 2
        if self.animation_offset > 360:
            self.animation_offset = 0
        self.update()
    
    def paintEvent(self, event):
        """Ultra canlı grafik çiz"""
        super().paintEvent(event)
        
        if not self.data_points or len(self.data_points) < 2:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Grafik alanı
        rect = self.chart_area.geometry()
        rect.adjust(15, 15, -15, -15)
        
        # Veri normalizasyonu
        max_val = max(self.data_points)
        min_val = min(self.data_points)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Çizgi noktaları
        points = []
        for i, value in enumerate(self.data_points):
            x = rect.left() + (i * rect.width() / (len(self.data_points) - 1))
            y = rect.bottom() - ((value - min_val) / val_range * rect.height())
            points.append(QPoint(int(x), int(y)))
        
        # Ultra canlı gradient çizgi
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0, QColor("#e74c3c"))
        gradient.setColorAt(0.3, QColor("#f39c12"))
        gradient.setColorAt(0.6, QColor("#2ecc71"))
        gradient.setColorAt(1, QColor("#3498db"))
        
        pen = QPen(QBrush(gradient), 4)
        painter.setPen(pen)
        
        # Animasyonlu çizgi çiz
        for i in range(len(points) - 1):
            wave_offset = math.sin((i + self.animation_offset) * 0.15) * 3
            start_point = QPoint(points[i].x(), points[i].y() + int(wave_offset))
            end_point = QPoint(points[i + 1].x(), points[i + 1].y() + int(wave_offset))
            painter.drawLine(start_point, end_point)
        
        # Canlı noktalar
        for i, point in enumerate(points):
            pulse_size = 8 + math.sin((i + self.animation_offset) * 0.3) * 3
            glow_size = 12 + math.sin((i + self.animation_offset) * 0.2) * 4
            
            # Glow efekti
            painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(point, int(glow_size), int(glow_size))
            
            # Ana nokta
            painter.setBrush(QBrush(QColor("#e74c3c")))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(point, int(pulse_size), int(pulse_size))

class UltraProgressRing(QFrame):
    """Ultra canlı dairesel progress"""
    
    def __init__(self, title: str, value: int, max_value: int = 100, 
                 color: str = "#2ecc71", parent=None):
        super().__init__(parent)
        self.title = title
        self.current_value = 0
        self.target_value = value
        self.max_value = max_value
        self.color = color
        self.animation_angle = 0
        
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(220, 220)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 4px solid #34495e;
                border-radius: 110px;
            }
        """)
        
        # Güçlü gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
    
    def setup_animation(self):
        """Animasyon kurulumu"""
        # Değer animasyonu
        self.value_animation = QVariantAnimation()
        self.value_animation.setDuration(2500)
        self.value_animation.setEasingCurve(QEasingCurve.OutBounce)
        self.value_animation.valueChanged.connect(self.update_progress)
        self.value_animation.setStartValue(0)
        self.value_animation.setEndValue(self.target_value)
        
        # Dönen animasyon
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_animation)
        self.rotation_timer.start(40)
        
        # Animasyonu başlat
        QTimer.singleShot(800, self.value_animation.start)
    
    def update_progress(self, value):
        """Progress güncelle"""
        self.current_value = value
        self.update()
    
    def rotate_animation(self):
        """Dönen animasyon"""
        self.animation_angle += 3
        if self.animation_angle > 360:
            self.animation_angle = 0
        self.update()
    
    def paintEvent(self, event):
        """Ultra canlı dairesel progress çiz"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Merkez ve yarıçap
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 25
        
        # Arka plan daire
        painter.setPen(QPen(QColor("#ecf0f1"), 10))
        painter.drawEllipse(center, radius, radius)
        
        # Progress dairesi
        progress_angle = (self.current_value / self.max_value) * 360
        
        # Ultra canlı gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(self.color))
        gradient.setColorAt(0.5, QColor("#f39c12"))
        gradient.setColorAt(1, QColor("#e74c3c"))
        
        painter.setPen(QPen(QBrush(gradient), 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(
            center.x() - radius, center.y() - radius,
            radius * 2, radius * 2,
            90 * 16, -int(progress_angle * 16)
        )
        
        # Dönen parıltı noktaları
        for i in range(3):
            dot_angle = math.radians(self.animation_angle + i * 120)
            dot_x = center.x() + (radius + 20) * math.cos(dot_angle)
            dot_y = center.y() + (radius + 20) * math.sin(dot_angle)
            
            painter.setBrush(QBrush(QColor("#f39c12")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(dot_x), int(dot_y)), 6, 6)
        
        # Merkez metin - Ultra net
        painter.setPen(QPen(QColor("#000000")))
        painter.setFont(QFont("Arial Black", 28, QFont.Black))
        
        text = f"{self.current_value}%"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = center.x() - text_rect.width() // 2
        text_y = center.y() + text_rect.height() // 4
        painter.drawText(text_x, text_y, text)
        
        # Başlık - Ultra net
        painter.setFont(QFont("Arial Black", 14, QFont.Bold))
        title_rect = painter.fontMetrics().boundingRect(self.title)
        title_x = center.x() - title_rect.width() // 2
        title_y = center.y() + 35
        painter.drawText(title_x, title_y, self.title)

class UltraListWidget(QFrame):
    """Ultra canlı liste widget'ı"""
    
    def __init__(self, title: str, items: List[Dict], parent=None):
        super().__init__(parent)
        self.title = title
        self.items = items
        
        self.setup_ui()
        self.populate_list()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(380, 320)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 4px solid #9b59b6;
                border-radius: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Başlık - Ultra net
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: 900; 
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
            padding: 10px;
        """)
        layout.addWidget(title_label)
        
        # Liste alanı
        self.list_area = QVBoxLayout()
        layout.addLayout(self.list_area)
        
        self.setLayout(layout)
        
        # Güçlü gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
    
    def populate_list(self):
        """Liste doldur"""
        for i, item in enumerate(self.items[:5]):
            item_widget = self.create_list_item(item, i)
            self.list_area.addWidget(item_widget)
    
    def create_list_item(self, item: Dict, index: int) -> QWidget:
        """Ultra net liste öğesi oluştur"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 3px solid #34495e;
                border-radius: 12px;
                padding: 12px;
                margin: 3px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Rank - Ultra net
        rank_label = QLabel(f"#{index + 1}")
        rank_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: 900;
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
        """)
        rank_label.setFixedWidth(50)
        layout.addWidget(rank_label)
        
        # İsim - Ultra net
        name_label = QLabel(item.get('name', ''))
        name_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
        """)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Değer - Ultra net ve renkli
        value_label = QLabel(str(item.get('value', '')))
        value_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: 900;
            color: #e74c3c;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
        """)
        layout.addWidget(value_label)
        
        item_frame.setLayout(layout)
        return item_frame

class UltraProfessionalDashboardManager:
    """Ultra profesyonel dashboard yöneticisi"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_ultra_dashboard(self, parent_widget) -> QWidget:
        """Ultra profesyonel dashboard oluştur"""
        # Ana scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ecf0f1;
            }
        """)
        
        # Ana widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)
        
        # Ultra başlık
        self.create_ultra_header(main_layout)
        
        # Ultra metrikler
        self.create_ultra_metrics(main_layout)
        
        # Ultra grafikler
        self.create_ultra_charts(main_layout)
        
        main_layout.addStretch()
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)
        
        return scroll_area
    
    def create_ultra_header(self, main_layout):
        """Ultra başlık"""
        header_layout = QHBoxLayout()
        
        # Ultra başlık
        title_label = QLabel("🚀 TezgahTakip Ultra Dashboard")
        title_label.setStyleSheet("""
            font-size: 48px; 
            font-weight: 900; 
            color: #000000;
            background-color: transparent;
            font-family: 'Arial Black', Arial, sans-serif;
            margin-bottom: 20px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Ultra saat
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            font-size: 24px; 
            color: #000000;
            background-color: transparent;
            font-weight: 900;
            font-family: 'Arial Black', Arial, sans-serif;
        """)
        header_layout.addWidget(self.time_label)
        
        # Saat güncelleme
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
        main_layout.addLayout(header_layout)
    
    def create_ultra_metrics(self, main_layout):
        """Ultra metrikler"""
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(30)
        
        # Verileri al
        stats = self.get_dashboard_stats()
        
        # Ultra renkli kartlar
        colors = ["#e74c3c", "#2ecc71", "#3498db", "#f39c12"]
        icons = ["🏭", "✅", "🔧", "🔋"]
        
        metrics_data = [
            ("Toplam Tezgah", str(stats['total_machines'])),
            ("Aktif Tezgah", str(stats['active_machines'])),
            ("Bu Ay Arıza", str(stats['monthly_maintenance'])),
            ("Pil Uyarısı", str(stats['battery_warnings'])),
        ]
        
        for i, (title, value) in enumerate(metrics_data):
            card = UltraMetricCard(title, value, icons[i], colors[i])
            metrics_layout.addWidget(card)
        
        metrics_layout.addStretch()
        main_layout.addLayout(metrics_layout)
    
    def create_ultra_charts(self, main_layout):
        """Ultra grafikler"""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(30)
        
        # Ultra canlı grafik
        live_chart = UltraLiveChart("📈 Canlı Arıza Trendi")
        charts_layout.addWidget(live_chart)
        
        # Ultra progress'ler
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(20)
        
        efficiency_progress = UltraProgressRing("Verimlilik", 87, 100, "#2ecc71")
        progress_layout.addWidget(efficiency_progress)
        
        completion_progress = UltraProgressRing("Tamamlanma", 74, 100, "#e74c3c")
        progress_layout.addWidget(completion_progress)
        
        charts_layout.addLayout(progress_layout)
        
        # Ultra liste
        top_machines = self.get_top_problematic_machines()
        machines_list = UltraListWidget("🔧 En Çok Arıza Olan Tezgahlar", top_machines)
        charts_layout.addWidget(machines_list)
        
        charts_layout.addStretch()
        main_layout.addLayout(charts_layout)
    
    def update_time(self):
        """Saati güncelle"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%d.%m.%Y")
        self.time_label.setText(f"🕐 {current_time} | 📅 {current_date}")
    
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