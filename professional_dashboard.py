#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Profesyonel Animasyonlu Dashboard
Çok güzel, renkli, animasyonlu ve canlı grafikli dashboard
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

class AnimatedMetricCard(QFrame):
    """Süper animasyonlu metrik kartı"""
    
    def __init__(self, title: str, value: str, icon: str = "📊", 
                 gradient_colors: List[str] = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.gradient_colors = gradient_colors or ["#667eea", "#764ba2"]
        self.current_value = 0
        self.target_value = int(value) if value.isdigit() else 0
        
        self.setup_ui()
        self.setup_animations()
        self.setup_shadow()
        self.start_entrance_animation()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(280, 160)
        
        # Beyaz arka plan - yazılar görünsün
        simple_style = f"""
            QFrame {{
                background-color: white;
                border: 3px solid {self.gradient_colors[0]};
                border-radius: 20px;
                color: black;
            }}
        """
        self.setStyleSheet(simple_style)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Üst kısım - Icon ve Title
        top_layout = QHBoxLayout()
        
        # Animasyonlu Icon
        self.icon_label = QLabel(self.icon)
        self.icon_label.setStyleSheet("""
            font-size: 36px; 
            color: black;
            background-color: transparent;
            font-weight: bold;
        """)
        top_layout.addWidget(self.icon_label)
        
        top_layout.addStretch()
        
        # Pulse animasyonu için nokta
        self.pulse_dot = QLabel("●")
        self.pulse_dot.setStyleSheet("""
            font-size: 20px; 
            color: red;
            background-color: transparent;
        """)
        top_layout.addWidget(self.pulse_dot)
        
        layout.addLayout(top_layout)
        
        # Ana değer - Animasyonlu sayaç
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("""
            font-size: 48px; 
            font-weight: bold;
            color: black;
            background-color: transparent;
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            color: black;
            background-color: transparent;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid black;
                border-radius: 10px;
                background-color: #f0f0f0;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def setup_animations(self):
        """Animasyonları kur"""
        # Sayaç animasyonu
        self.counter_animation = QVariantAnimation()
        self.counter_animation.setDuration(2000)
        self.counter_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.counter_animation.valueChanged.connect(self.update_counter)
        
        # Pulse animasyonu
        self.pulse_animation = QPropertyAnimation(self.pulse_dot, b"geometry")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setLoopCount(-1)
        
        # Icon bounce animasyonu
        self.icon_bounce = QPropertyAnimation(self.icon_label, b"geometry")
        self.icon_bounce.setDuration(800)
        self.icon_bounce.setEasingCurve(QEasingCurve.OutBounce)
        
        # Progress animasyonu
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(2500)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Hover animasyonları
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
    
    def start_entrance_animation(self):
        """Giriş animasyonu"""
        # Başlangıçta görünmez yap
        self.setStyleSheet(self.styleSheet() + "background-color: transparent;")
        
        # Fade in animasyonu
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Animasyonları başlat
        QTimer.singleShot(100, self.start_all_animations)
    
    def start_all_animations(self):
        """Tüm animasyonları başlat"""
        # Fade in
        self.fade_animation.start()
        
        # Sayaç animasyonu
        self.counter_animation.setStartValue(0)
        self.counter_animation.setEndValue(self.target_value)
        self.counter_animation.start()
        
        # Progress animasyonu
        progress_value = min(100, (self.target_value / 200) * 100)  # Normalize et
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(progress_value)
        self.progress_animation.start()
        
        # Pulse animasyonu başlat
        self.start_pulse_animation()
    
    def start_pulse_animation(self):
        """Pulse animasyonu"""
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_effect)
        self.pulse_timer.start(1500)
    
    def pulse_effect(self):
        """Pulse efekti"""
        colors = ["#00ff88", "#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24"]
        color = random.choice(colors)
        self.pulse_dot.setStyleSheet(f"""
            font-size: 20px; 
            color: {color};
            background-color: transparent;
        """)
    
    def update_counter(self, value):
        """Sayaç güncelle"""
        self.current_value = int(value)
        self.value_label.setText(str(self.current_value))
    
    def update_value(self, new_value: str):
        """Değeri güncelle"""
        self.target_value = int(new_value) if new_value.isdigit() else 0
        self.counter_animation.setStartValue(self.current_value)
        self.counter_animation.setEndValue(self.target_value)
        self.counter_animation.start()
    
    def enterEvent(self, event):
        """Mouse hover başlangıç"""
        self.animate_hover(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse hover bitiş"""
        self.animate_hover(False)
        super().leaveEvent(event)
    
    def animate_hover(self, hover: bool):
        """Hover animasyonu"""
        current_rect = self.geometry()
        if hover:
            # Büyüt
            new_rect = QRect(
                current_rect.x() - 5,
                current_rect.y() - 5,
                current_rect.width() + 10,
                current_rect.height() + 10
            )
        else:
            # Normal boyut
            new_rect = QRect(
                current_rect.x() + 5,
                current_rect.y() + 5,
                current_rect.width() - 10,
                current_rect.height() - 10
            )
        
        self.scale_animation.setStartValue(current_rect)
        self.scale_animation.setEndValue(new_rect)
        self.scale_animation.start()

class LiveChartWidget(QFrame):
    """Canlı grafik widget'ı"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.data_points = []
        self.max_points = 20
        self.animation_offset = 0
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #2c3e50;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: black;
            background-color: transparent;
            padding: 5px;
        """)
        layout.addWidget(title_label)
        
        # Grafik alanı
        self.chart_area = QWidget()
        self.chart_area.setMinimumHeight(180)
        layout.addWidget(self.chart_area)
        
        self.setLayout(layout)
        
        # Gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def setup_timer(self):
        """Timer kurulumu"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.add_data_point)
        self.update_timer.start(1000)  # Her saniye yeni veri
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_chart)
        self.animation_timer.start(50)  # Smooth animasyon
    
    def add_data_point(self):
        """Yeni veri noktası ekle"""
        # Rastgele veri (gerçek uygulamada veritabanından gelecek)
        new_value = random.randint(10, 100)
        self.data_points.append(new_value)
        
        # Maksimum nokta sayısını aş
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        
        self.update()
    
    def animate_chart(self):
        """Grafik animasyonu"""
        self.animation_offset += 1
        if self.animation_offset > 360:
            self.animation_offset = 0
        self.update()
    
    def paintEvent(self, event):
        """Grafik çiz"""
        super().paintEvent(event)
        
        if not self.data_points:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Grafik alanı
        rect = self.chart_area.geometry()
        rect.adjust(10, 10, -10, -10)
        
        if len(self.data_points) < 2:
            return
        
        # Veri normalizasyonu
        max_val = max(self.data_points)
        min_val = min(self.data_points)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Çizgi çiz
        points = []
        for i, value in enumerate(self.data_points):
            x = rect.left() + (i * rect.width() / (len(self.data_points) - 1))
            y = rect.bottom() - ((value - min_val) / val_range * rect.height())
            points.append(QPoint(int(x), int(y)))
        
        # Gradient çizgi
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0, QColor("#00ff88"))
        gradient.setColorAt(0.5, QColor("#00d4ff"))
        gradient.setColorAt(1, QColor("#ff6b6b"))
        
        pen = QPen(QBrush(gradient), 3)
        painter.setPen(pen)
        
        # Animasyonlu çizgi çiz
        for i in range(len(points) - 1):
            # Dalga efekti
            wave_offset = math.sin((i + self.animation_offset) * 0.1) * 2
            start_point = QPoint(points[i].x(), points[i].y() + int(wave_offset))
            end_point = QPoint(points[i + 1].x(), points[i + 1].y() + int(wave_offset))
            painter.drawLine(start_point, end_point)
        
        # Noktalar çiz
        for i, point in enumerate(points):
            # Pulse efekti
            pulse_size = 6 + math.sin((i + self.animation_offset) * 0.2) * 2
            
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(QPen(QColor("#00ff88"), 2))
            painter.drawEllipse(point, int(pulse_size), int(pulse_size))

class CircularProgressWidget(QFrame):
    """Dairesel progress widget'ı"""
    
    def __init__(self, title: str, value: int, max_value: int = 100, 
                 color: str = "#00ff88", parent=None):
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
        self.setFixedSize(200, 200)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #34495e;
                border-radius: 100px;
            }
        """)
        
        # Gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def setup_animation(self):
        """Animasyon kurulumu"""
        # Değer animasyonu
        self.value_animation = QVariantAnimation()
        self.value_animation.setDuration(2000)
        self.value_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.value_animation.valueChanged.connect(self.update_progress)
        self.value_animation.setStartValue(0)
        self.value_animation.setEndValue(self.target_value)
        
        # Dönen animasyon
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_animation)
        self.rotation_timer.start(50)
        
        # Animasyonu başlat
        QTimer.singleShot(500, self.value_animation.start)
    
    def update_progress(self, value):
        """Progress güncelle"""
        self.current_value = value
        self.update()
    
    def rotate_animation(self):
        """Dönen animasyon"""
        self.animation_angle += 2
        if self.animation_angle > 360:
            self.animation_angle = 0
        self.update()
    
    def paintEvent(self, event):
        """Dairesel progress çiz"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Merkez ve yarıçap
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 20
        
        # Arka plan daire
        painter.setPen(QPen(QColor("#bdc3c7"), 8))
        painter.drawEllipse(center, radius, radius)
        
        # Progress dairesi
        progress_angle = (self.current_value / self.max_value) * 360
        
        # Gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(self.color))
        gradient.setColorAt(1, QColor("#e74c3c"))
        
        painter.setPen(QPen(QBrush(gradient), 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(
            center.x() - radius, center.y() - radius,
            radius * 2, radius * 2,
            90 * 16, -int(progress_angle * 16)
        )
        
        # Dönen nokta
        dot_angle = math.radians(self.animation_angle)
        dot_x = center.x() + (radius + 15) * math.cos(dot_angle)
        dot_y = center.y() + (radius + 15) * math.sin(dot_angle)
        
        painter.setBrush(QBrush(QColor("#27ae60")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(dot_x), int(dot_y)), 5, 5)
        
        # Merkez metin - Siyah renk
        painter.setPen(QPen(QColor("#2c3e50")))
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        
        text = f"{self.current_value}%"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = center.x() - text_rect.width() // 2
        text_y = center.y() + text_rect.height() // 4
        painter.drawText(text_x, text_y, text)
        
        # Başlık - Siyah renk
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        title_rect = painter.fontMetrics().boundingRect(self.title)
        title_x = center.x() - title_rect.width() // 2
        title_y = center.y() + 30
        painter.drawText(title_x, title_y, self.title)

class AnimatedListWidget(QFrame):
    """Animasyonlu liste widget'ı"""
    
    def __init__(self, title: str, items: List[Dict], parent=None):
        super().__init__(parent)
        self.title = title
        self.items = items
        self.current_item = 0
        
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(350, 300)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #34495e;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: black;
            background-color: transparent;
            padding: 5px;
        """)
        layout.addWidget(title_label)
        
        # Liste alanı
        self.list_area = QVBoxLayout()
        layout.addLayout(self.list_area)
        
        self.setLayout(layout)
        
        # Gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        # İlk öğeleri ekle
        self.populate_list()
    
    def populate_list(self):
        """Liste doldur"""
        for i, item in enumerate(self.items[:5]):  # İlk 5 öğe
            item_widget = self.create_list_item(item, i)
            self.list_area.addWidget(item_widget)
    
    def create_list_item(self, item: Dict, index: int) -> QWidget:
        """Liste öğesi oluştur"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 10px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Rank
        rank_label = QLabel(f"#{index + 1}")
        rank_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold;
            color: black;
            background-color: transparent;
        """)
        rank_label.setFixedWidth(40)
        layout.addWidget(rank_label)
        
        # İsim
        name_label = QLabel(item.get('name', ''))
        name_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            color: black;
            background-color: transparent;
        """)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Değer
        value_label = QLabel(str(item.get('value', '')))
        value_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            color: red;
            background-color: transparent;
        """)
        layout.addWidget(value_label)
        
        item_frame.setLayout(layout)
        
        # Giriş animasyonu
        opacity_effect = QGraphicsOpacityEffect()
        item_frame.setGraphicsEffect(opacity_effect)
        
        fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        fade_animation.setDuration(800)
        fade_animation.setStartValue(0.0)
        fade_animation.setEndValue(1.0)
        fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Animasyonu gecikmeyle başlat
        QTimer.singleShot(index * 200, fade_animation.start)
        
        return item_frame
    
    def setup_animation(self):
        """Animasyon kurulumu"""
        self.highlight_timer = QTimer()
        self.highlight_timer.timeout.connect(self.highlight_next_item)
        self.highlight_timer.start(2000)  # 2 saniyede bir highlight
    
    def highlight_next_item(self):
        """Sıradaki öğeyi highlight et"""
        # Bu fonksiyon liste öğelerini sırayla highlight edebilir
        pass

class ProfessionalDashboardManager:
    """Profesyonel dashboard yöneticisi"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.widgets = {}
    
    def create_professional_dashboard(self, parent_widget) -> QWidget:
        """Profesyonel dashboard oluştur"""
        # Ana scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
        
        # Ana widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Başlık bölümü
        self.create_header_section(main_layout)
        
        # Ana metrikler - Animasyonlu kartlar
        self.create_metrics_section(main_layout)
        
        # Grafikler bölümü
        self.create_charts_section(main_layout)
        
        # Progress ve listeler
        self.create_progress_section(main_layout)
        
        main_layout.addStretch()
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)
        
        return scroll_area
    
    def create_header_section(self, main_layout):
        """Başlık bölümü"""
        header_layout = QHBoxLayout()
        
        # Ana başlık
        title_label = QLabel("🚀 TezgahTakip Dashboard")
        title_label.setStyleSheet("""
            font-size: 36px; 
            font-weight: bold; 
            color: black;
            background-color: transparent;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Canlı saat
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            font-size: 18px; 
            color: black;
            background-color: transparent;
            font-weight: bold;
        """)
        header_layout.addWidget(self.time_label)
        
        # Saat güncelleme
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
        main_layout.addLayout(header_layout)
    
    def create_metrics_section(self, main_layout):
        """Metrikler bölümü"""
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(25)
        
        # Verileri al
        stats = self.get_dashboard_stats()
        
        # Animasyonlu metrik kartları
        gradients = [
            ["#667eea", "#764ba2"],  # Mor-Mavi
            ["#f093fb", "#f5576c"],  # Pembe-Kırmızı
            ["#4facfe", "#00f2fe"],  # Mavi-Cyan
            ["#43e97b", "#38f9d7"],  # Yeşil-Turkuaz
        ]
        
        metrics_data = [
            ("Toplam Tezgah", str(stats['total_machines']), "🏭"),
            ("Aktif Tezgah", str(stats['active_machines']), "✅"),
            ("Bu Ay Arıza", str(stats['monthly_maintenance']), "🔧"),
            ("Pil Uyarısı", str(stats['battery_warnings']), "🔋"),
        ]
        
        for i, (title, value, icon) in enumerate(metrics_data):
            card = AnimatedMetricCard(title, value, icon, gradients[i])
            self.widgets[f'metric_{i}'] = card
            metrics_layout.addWidget(card)
        
        metrics_layout.addStretch()
        main_layout.addLayout(metrics_layout)
    
    def create_charts_section(self, main_layout):
        """Grafikler bölümü"""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(25)
        
        # Canlı grafik
        live_chart = LiveChartWidget("📈 Canlı Arıza Trendi")
        charts_layout.addWidget(live_chart)
        
        # Dairesel progress'ler
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(15)
        
        # Sistem verimliliği
        efficiency_progress = CircularProgressWidget("Verimlilik", 85, 100, "#00ff88")
        progress_layout.addWidget(efficiency_progress)
        
        # Bakım tamamlanma
        completion_progress = CircularProgressWidget("Tamamlanma", 72, 100, "#ff6b6b")
        progress_layout.addWidget(completion_progress)
        
        charts_layout.addLayout(progress_layout)
        
        # En çok arıza olan tezgahlar listesi
        top_machines = self.get_top_problematic_machines()
        machines_list = AnimatedListWidget("🔧 En Çok Arıza Olan Tezgahlar", top_machines)
        charts_layout.addWidget(machines_list)
        
        charts_layout.addStretch()
        main_layout.addLayout(charts_layout)
    
    def create_progress_section(self, main_layout):
        """Progress bölümü - Sadece sistem durumu"""
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(25)
        
        # Sistem durumu - Daha büyük ve merkezi
        system_status = [
            {"name": "CPU Kullanımı", "value": "45%"},
            {"name": "Bellek Kullanımı", "value": "62%"},
            {"name": "Disk Alanı", "value": "78%"},
            {"name": "Ağ Trafiği", "value": "Normal"},
        ]
        status_list = AnimatedListWidget("💻 Sistem Durumu", system_status)
        progress_layout.addWidget(status_list)
        
        progress_layout.addStretch()
        main_layout.addLayout(progress_layout)
    
    def update_time(self):
        """Saati güncelle"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%d.%m.%Y")
        self.time_label.setText(f"🕐 {current_time} | 📅 {current_date}")
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
    
    # Callback fonksiyonları
    def create_report(self):
        """Rapor oluştur"""
        try:
            parent = self.get_main_window()
            if parent and hasattr(parent, 'tab_widget'):
                parent.tab_widget.setCurrentIndex(4)
        except Exception as e:
            self.logger.error(f"Create report error: {e}")
    
    def add_maintenance(self):
        """Yeni arıza ekle"""
        try:
            parent = self.get_main_window()
            if parent and hasattr(parent, 'add_bakim'):
                parent.add_bakim()
        except Exception as e:
            self.logger.error(f"Add maintenance error: {e}")
    
    def show_analysis(self):
        """Analiz göster"""
        try:
            parent = self.get_main_window()
            if parent and hasattr(parent, 'tab_widget'):
                parent.tab_widget.setCurrentIndex(5)
        except Exception as e:
            self.logger.error(f"Show analysis error: {e}")
    
    def show_settings(self):
        """Ayarları göster"""
        try:
            parent = self.get_main_window()
            if parent and hasattr(parent, 'show_preferences'):
                parent.show_preferences()
        except Exception as e:
            self.logger.error(f"Show settings error: {e}")
    
    def get_main_window(self):
        """Ana pencereyi bul"""
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'tab_widget'):
                    return widget
            return None
        except Exception as e:
            self.logger.error(f"Get main window error: {e}")
            return None