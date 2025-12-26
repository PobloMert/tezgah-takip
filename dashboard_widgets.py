#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Dashboard Widget'ları
İnteraktif dashboard bileşenleri
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QGridLayout, QProgressBar,
                            QGraphicsDropShadowEffect, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QLinearGradient, QBrush

# Gelişmiş widget'ları import et
try:
    from advanced_dashboard_widgets import (
        RealTimeChart, MaintenanceTrendChart, PerformanceMetricsWidget,
        AlertNotificationWidget, MaintenanceAnalysisWidget, CriticalAlertDialog
    )
    ADVANCED_WIDGETS_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"Advanced widgets not available: {e}")
    ADVANCED_WIDGETS_AVAILABLE = False

class AnimatedCard(QFrame):
    """Animasyonlu kart widget'ı"""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str, value: str, icon: str = "📊", 
                 color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        
        self.setup_ui()
        self.setup_animations()
        self.setup_shadow()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(200, 120)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color}, stop:1 {self._darken_color(self.color)});
                border: none;
                border-radius: 10px;
                color: white;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Üst kısım - Icon ve Title
        top_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 24px; color: white;")
        top_layout.addWidget(icon_label)
        
        top_layout.addStretch()
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.9); font-weight: bold;")
        title_label.setAlignment(Qt.AlignRight)
        top_layout.addWidget(title_label)
        
        layout.addLayout(top_layout)
        
        layout.addStretch()
        
        # Alt kısım - Value
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet("font-size: 28px; color: white; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def setup_animations(self):
        """Animasyon kurulumu - Sadece gölge ve renk efektleri"""
        # Geometry animasyonu kaldırıldı, sadece görsel efektler kullanılacak
        pass
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def update_value(self, new_value: str):
        """Değeri güncelle"""
        self.value_label.setText(new_value)
    
    def mousePressEvent(self, event):
        """Mouse tıklama"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Mouse hover başlangıç"""
        self.animate_scale(1.05)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse hover bitiş"""
        self.animate_scale(1.0)
        super().leaveEvent(event)
    
    def animate_scale(self, scale_factor: float):
        """Ölçek animasyonu - Pozisyon sabit kalacak şekilde"""
        # Animasyon yerine sadece CSS transform kullan
        if scale_factor > 1.0:
            # Hover efekti - sadece gölge ve renk değişimi
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {self._lighten_color(self.color)}, 
                        stop:1 {self.color});
                    border: none;
                    border-radius: 10px;
                    color: white;
                }}
            """)
            # Gölge efektini güçlendir
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 120))
            shadow.setOffset(0, 8)
            self.setGraphicsEffect(shadow)
        else:
            # Normal durum
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {self.color}, stop:1 {self._darken_color(self.color)});
                    border: none;
                    border-radius: 10px;
                    color: white;
                }}
            """)
            # Normal gölge
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 80))
            shadow.setOffset(0, 5)
            self.setGraphicsEffect(shadow)
    
    def _darken_color(self, color: str) -> str:
        """Rengi koyulaştır"""
        color_map = {
            "#4CAF50": "#388E3C",
            "#2196F3": "#1976D2", 
            "#FF9800": "#F57C00",
            "#F44336": "#D32F2F",
            "#9C27B0": "#7B1FA2"
        }
        return color_map.get(color, "#333333")
    
    def _lighten_color(self, color: str) -> str:
        """Rengi açıklaştır"""
        color_map = {
            "#4CAF50": "#66BB6A",
            "#2196F3": "#42A5F5",
            "#FF9800": "#FFB74D", 
            "#F44336": "#EF5350",
            "#9C27B0": "#BA68C8"
        }
        return color_map.get(color, "#666666")

class TrendCard(QFrame):
    """Trend gösterici kart"""
    
    def __init__(self, title: str, current_value: float, previous_value: float,
                 unit: str = "", icon: str = "📈", parent=None):
        super().__init__(parent)
        self.title = title
        self.current_value = current_value
        self.previous_value = previous_value
        self.unit = unit
        self.icon = icon
        
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(250, 140)
        self.setFrameStyle(QFrame.Box)
        
        # Trend hesapla
        if self.previous_value > 0:
            change_percent = ((self.current_value - self.previous_value) / self.previous_value) * 100
        else:
            change_percent = 0
        
        is_positive = change_percent >= 0
        trend_color = "#4CAF50" if is_positive else "#F44336"
        trend_icon = "📈" if is_positive else "📉"
        trend_text = f"+{change_percent:.1f}%" if is_positive else f"{change_percent:.1f}%"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {trend_color};
                background-color: #fafafa;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Başlık satırı
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Ana değer
        value_label = QLabel(f"{self.current_value:,.0f}{self.unit}")
        value_label.setStyleSheet("font-size: 24px; color: #333; font-weight: bold; margin: 5px 0;")
        layout.addWidget(value_label)
        
        # Trend bilgisi
        trend_layout = QHBoxLayout()
        
        trend_icon_label = QLabel(trend_icon)
        trend_icon_label.setStyleSheet("font-size: 16px;")
        trend_layout.addWidget(trend_icon_label)
        
        trend_label = QLabel(trend_text)
        trend_label.setStyleSheet(f"font-size: 14px; color: {trend_color}; font-weight: bold;")
        trend_layout.addWidget(trend_label)
        
        trend_layout.addStretch()
        
        comparison_label = QLabel(f"vs önceki dönem ({self.previous_value:,.0f}{self.unit})")
        comparison_label.setStyleSheet("font-size: 10px; color: #999;")
        trend_layout.addWidget(comparison_label)
        
        layout.addLayout(trend_layout)
        
        self.setLayout(layout)
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class ProgressCard(QFrame):
    """Progress gösterici kart"""
    
    def __init__(self, title: str, current: int, target: int, 
                 unit: str = "", icon: str = "🎯", parent=None):
        super().__init__(parent)
        self.title = title
        self.current = current
        self.target = target
        self.unit = unit
        self.icon = icon
        
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(280, 120)
        self.setFrameStyle(QFrame.Box)
        
        # Progress hesapla
        progress_percent = min(100, (self.current / self.target * 100)) if self.target > 0 else 0
        
        # Renk belirleme
        if progress_percent >= 90:
            color = "#4CAF50"  # Yeşil
        elif progress_percent >= 70:
            color = "#FF9800"  # Turuncu
        else:
            color = "#F44336"  # Kırmızı
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: #fafafa;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Başlık satırı
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Progress yüzdesi
        percent_label = QLabel(f"{progress_percent:.0f}%")
        percent_label.setStyleSheet(f"font-size: 16px; color: {color}; font-weight: bold;")
        header_layout.addWidget(percent_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(progress_percent))
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(progress_bar)
        
        # Detay bilgisi
        detail_label = QLabel(f"{self.current:,}{self.unit} / {self.target:,}{self.unit}")
        detail_label.setStyleSheet("font-size: 11px; color: #999; margin-top: 5px;")
        detail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(detail_label)
        
        self.setLayout(layout)
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class AlertCard(QFrame):
    """Uyarı kartı"""
    
    def __init__(self, title: str, alert_count: int, alert_type: str = "warning", parent=None):
        super().__init__(parent)
        self.title = title
        self.alert_count = alert_count
        self.alert_type = alert_type
        
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(200, 100)
        self.setFrameStyle(QFrame.Box)
        
        # Alert tipine göre renk ve icon
        alert_config = {
            "warning": {"color": "#FF9800", "icon": "⚠️", "bg": "#FFF3E0"},
            "error": {"color": "#F44336", "icon": "❌", "bg": "#FFEBEE"},
            "info": {"color": "#2196F3", "icon": "ℹ️", "bg": "#E3F2FD"},
            "success": {"color": "#4CAF50", "icon": "✅", "bg": "#E8F5E8"}
        }
        
        config = alert_config.get(self.alert_type, alert_config["warning"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {config['bg']};
                border: 1px solid {config['color']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: white;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Üst kısım
        top_layout = QHBoxLayout()
        
        icon_label = QLabel(config['icon'])
        icon_label.setStyleSheet("font-size: 20px;")
        top_layout.addWidget(icon_label)
        
        count_label = QLabel(str(self.alert_count))
        count_label.setStyleSheet(f"font-size: 24px; color: {config['color']}; font-weight: bold;")
        count_label.setAlignment(Qt.AlignRight)
        top_layout.addWidget(count_label)
        
        layout.addLayout(top_layout)
        
        # Alt kısım - Başlık
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"font-size: 11px; color: {config['color']}; font-weight: bold;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        self.setLayout(layout)
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)

class MaintenanceHistoryCard(QFrame):
    """Geçmiş arızalar widget'ı - Modern tasarım"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(380, 220)
        self.setFrameStyle(QFrame.Box)
        
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: 15px;
            }
            QFrame:hover {
                border-color: #4CAF50;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #ffffff);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Başlık - Modern tasarım
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 20px;
                border: none;
            }
        """)
        
        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel("🔧")
        icon_label.setStyleSheet("font-size: 20px; color: white;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        icon_container.setLayout(icon_layout)
        
        header_layout.addWidget(icon_container)
        
        # Title ve subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title_label = QLabel("Geçmiş Arızalar")
        title_label.setStyleSheet("""
            font-size: 16px; 
            color: #2c3e50; 
            font-weight: bold;
            margin: 0px;
        """)
        
        subtitle_label = QLabel("Bakım ve arıza istatistikleri")
        subtitle_label.setStyleSheet("""
            font-size: 11px; 
            color: #6c757d; 
            margin: 0px;
        """)
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Ayırıcı çizgi
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("border: 1px solid #e9ecef; margin: 5px 0px;")
        layout.addWidget(separator)
        
        # İstatistikler alanı
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(8)
        layout.addLayout(self.stats_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_data(self, maintenance_stats):
        """Arıza verilerini güncelle - Yazı görünürlüğü düzeltildi"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.stats_layout.count())):
            child = self.stats_layout.itemAt(i)
            if child:
                widget = child.widget()
                if widget:
                    widget.setParent(None)
                else:
                    # Layout item ise
                    layout_item = child.layout()
                    if layout_item:
                        self._clear_layout(layout_item)
                    self.stats_layout.removeItem(child)
        
        # Toplam arıza sayısı - Büyük ve öne çıkan (KOYU YAZI)
        total_container = QFrame()
        total_container.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border-radius: 8px;
                padding: 8px;
                border: 2px solid #1976d2;
            }
        """)
        
        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(12, 8, 12, 8)
        
        total_icon = QLabel("📊")
        total_icon.setStyleSheet("font-size: 18px;")
        total_layout.addWidget(total_icon)
        
        total_text_layout = QVBoxLayout()
        total_text_layout.setSpacing(2)
        
        total_label = QLabel("Toplam Arıza")
        total_label.setStyleSheet("font-size: 12px; color: #000000; font-weight: bold;")  # SİYAH YAZI
        
        total_value = QLabel(str(maintenance_stats.get('total_maintenance', 0)))
        total_value.setStyleSheet("font-size: 24px; color: #000000; font-weight: bold;")  # SİYAH YAZI
        
        total_text_layout.addWidget(total_label)
        total_text_layout.addWidget(total_value)
        
        total_layout.addLayout(total_text_layout)
        total_layout.addStretch()
        
        total_container.setLayout(total_layout)
        self.stats_layout.addWidget(total_container)
        
        # Diğer istatistikler - Kompakt kartlar (KOYU YAZI)
        stats_row_layout = QHBoxLayout()
        stats_row_layout.setSpacing(8)
        
        # Bu ay arızalar
        month_card = self._create_stat_card(
            "📅", "Bu Ay", 
            str(maintenance_stats.get('monthly_maintenance', 0)), 
            "#fff8e1", "#000000"  # AÇIK SARI ARKA PLAN, SİYAH YAZI
        )
        stats_row_layout.addWidget(month_card)
        
        # Tamamlanan arızalar
        completed_card = self._create_stat_card(
            "✅", "Tamamlanan", 
            str(maintenance_stats.get('completed_maintenance', 0)), 
            "#f1f8e9", "#000000"  # AÇIK YEŞİL ARKA PLAN, SİYAH YAZI
        )
        stats_row_layout.addWidget(completed_card)
        
        self.stats_layout.addLayout(stats_row_layout)
        
        # En çok arıza olan tezgah - Özel kart (KOYU YAZI)
        if 'most_problematic_tezgah' in maintenance_stats and maintenance_stats['most_problematic_tezgah']:
            problem_info = maintenance_stats['most_problematic_tezgah']
            problem_card = QFrame()
            problem_card.setStyleSheet("""
                QFrame {
                    background-color: #fff3e0;
                    border-radius: 8px;
                    border: 2px solid #ff9800;
                    padding: 6px;
                }
            """)
            
            problem_layout = QHBoxLayout()
            problem_layout.setContentsMargins(10, 6, 10, 6)
            
            problem_icon = QLabel("⚠️")
            problem_icon.setStyleSheet("font-size: 16px;")
            problem_layout.addWidget(problem_icon)
            
            problem_text = QLabel(f"En Çok Arıza: {problem_info['tezgah']} ({problem_info['count']} arıza)")
            problem_text.setStyleSheet("font-size: 12px; color: #000000; font-weight: bold;")  # SİYAH YAZI
            problem_layout.addWidget(problem_text)
            problem_layout.addStretch()
            
            problem_card.setLayout(problem_layout)
            self.stats_layout.addWidget(problem_card)
    
    def _create_stat_card(self, icon, title, value, bg_color, text_color):
        """Küçük istatistik kartı oluştur - Yazı görünürlüğü düzeltildi"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 6px;
                border: 2px solid #333333;
                padding: 4px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        # Icon ve title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 11px; color: {text_color}; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 18px; color: {text_color}; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def _clear_layout(self, layout):
        """Layout'u temizle"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                self._clear_layout(child.layout())
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class MaintenanceTrendCard(QFrame):
    """Arıza trend kartı - Modern tasarım"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """UI kurulumu"""
        self.setFixedSize(320, 220)
        self.setFrameStyle(QFrame.Box)
        
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: 15px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #ffffff);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Başlık - Modern tasarım
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 20px;
                border: none;
            }
        """)
        
        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel("📈")
        icon_label.setStyleSheet("font-size: 20px; color: white;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        icon_container.setLayout(icon_layout)
        
        header_layout.addWidget(icon_container)
        
        # Title ve subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title_label = QLabel("Arıza Trendi")
        title_label.setStyleSheet("""
            font-size: 16px; 
            color: #2c3e50; 
            font-weight: bold;
            margin: 0px;
        """)
        
        subtitle_label = QLabel("Aylık karşılaştırma ve trend analizi")
        subtitle_label.setStyleSheet("""
            font-size: 11px; 
            color: #6c757d; 
            margin: 0px;
        """)
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Ayırıcı çizgi
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("border: 1px solid #e9ecef; margin: 5px 0px;")
        layout.addWidget(separator)
        
        # Trend bilgisi alanı
        self.trend_layout = QVBoxLayout()
        self.trend_layout.setSpacing(10)
        layout.addLayout(self.trend_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_trend(self, current_month, previous_month, trend_data):
        """Trend verilerini güncelle - Yazı görünürlüğü düzeltildi"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.trend_layout.count())):
            child = self.trend_layout.itemAt(i)
            if child:
                widget = child.widget()
                if widget:
                    widget.setParent(None)
                else:
                    # Layout item ise
                    layout_item = child.layout()
                    if layout_item:
                        self._clear_layout(layout_item)
                    self.trend_layout.removeItem(child)
        
        # Trend hesaplama
        if previous_month > 0:
            change_percent = ((current_month - previous_month) / previous_month) * 100
        else:
            change_percent = 0 if current_month == 0 else 100
        
        is_increasing = change_percent > 0
        trend_color = "#F44336" if is_increasing else "#4CAF50"  # Arıza artışı kötü
        trend_bg_color = "#ffebee" if is_increasing else "#e8f5e8"
        trend_icon = "📈" if is_increasing else "📉"
        
        # Ana trend göstergesi - Büyük kart (KOYU YAZI)
        main_trend_card = QFrame()
        main_trend_card.setStyleSheet(f"""
            QFrame {{
                background-color: {trend_bg_color};
                border-radius: 10px;
                border: 3px solid #333333;
                padding: 10px;
            }}
        """)
        
        main_trend_layout = QVBoxLayout()
        main_trend_layout.setContentsMargins(15, 12, 15, 12)
        main_trend_layout.setSpacing(8)
        
        # Trend icon ve yüzde
        trend_header = QHBoxLayout()
        
        trend_icon_label = QLabel(trend_icon)
        trend_icon_label.setStyleSheet("font-size: 28px;")
        trend_header.addWidget(trend_icon_label)
        
        trend_text_layout = QVBoxLayout()
        trend_text_layout.setSpacing(2)
        
        if change_percent > 0:
            trend_text = f"+{change_percent:.1f}% Artış"
            status_text = "Arıza sayısı arttı"
        elif change_percent < 0:
            trend_text = f"{change_percent:.1f}% Azalış"
            status_text = "Arıza sayısı azaldı"
        else:
            trend_text = "Değişim Yok"
            status_text = "Arıza sayısı stabil"
        
        trend_value_label = QLabel(trend_text)
        trend_value_label.setStyleSheet("font-size: 18px; color: #000000; font-weight: bold;")  # SİYAH YAZI
        
        trend_status_label = QLabel(status_text)
        trend_status_label.setStyleSheet("font-size: 12px; color: #000000; font-weight: normal;")  # SİYAH YAZI
        
        trend_text_layout.addWidget(trend_value_label)
        trend_text_layout.addWidget(trend_status_label)
        
        trend_header.addLayout(trend_text_layout)
        trend_header.addStretch()
        
        main_trend_layout.addLayout(trend_header)
        
        main_trend_card.setLayout(main_trend_layout)
        self.trend_layout.addWidget(main_trend_card)
        
        # Karşılaştırma kartları (KOYU YAZI)
        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(8)
        
        # Bu ay kartı
        current_card = self._create_comparison_card(
            "📅", "Bu Ay", str(current_month), "#f0f8ff", "#000000"  # AÇIK MAVİ ARKA PLAN, SİYAH YAZI
        )
        comparison_layout.addWidget(current_card)
        
        # Geçen ay kartı
        previous_card = self._create_comparison_card(
            "📊", "Geçen Ay", str(previous_month), "#f3e5f5", "#000000"  # AÇIK MOR ARKA PLAN, SİYAH YAZI
        )
        comparison_layout.addWidget(previous_card)
        
        self.trend_layout.addLayout(comparison_layout)
        
        # Haftalık trend (eğer veri varsa) (KOYU YAZI)
        if 'weekly_trend' in trend_data:
            weekly_card = QFrame()
            weekly_card.setStyleSheet("""
                QFrame {
                    background-color: #fff8e1;
                    border-radius: 6px;
                    border: 2px solid #333333;
                    padding: 6px;
                }
            """)
            
            weekly_layout = QHBoxLayout()
            weekly_layout.setContentsMargins(10, 6, 10, 6)
            
            weekly_icon = QLabel("📊")
            weekly_icon.setStyleSheet("font-size: 14px;")
            weekly_layout.addWidget(weekly_icon)
            
            weekly_label = QLabel(f"Bu Hafta: {trend_data['weekly_trend']} arıza")
            weekly_label.setStyleSheet("font-size: 12px; color: #000000; font-weight: bold;")  # SİYAH YAZI
            weekly_layout.addWidget(weekly_label)
            weekly_layout.addStretch()
            
            weekly_card.setLayout(weekly_layout)
            self.trend_layout.addWidget(weekly_card)
        
        # Trend yorumu (KOYU YAZI)
        comment_card = QFrame()
        if change_percent > 20:
            comment = "⚠️ Arıza sayısında önemli artış!"
            comment_bg = "#ffebee"
        elif change_percent < -20:
            comment = "✅ Arıza sayısında önemli azalış!"
            comment_bg = "#e8f5e8"
        elif abs(change_percent) <= 5:
            comment = "📊 Arıza sayısı stabil"
            comment_bg = "#f5f5f5"
        else:
            comment = "📈 Normal değişim aralığında"
            comment_bg = "#fff3e0"
        
        comment_card.setStyleSheet(f"""
            QFrame {{
                background-color: {comment_bg};
                border-radius: 6px;
                border: 2px solid #333333;
                padding: 6px;
            }}
        """)
        
        comment_layout = QHBoxLayout()
        comment_layout.setContentsMargins(8, 4, 8, 4)
        
        comment_label = QLabel(comment)
        comment_label.setStyleSheet("font-size: 11px; color: #000000; font-weight: bold;")  # SİYAH YAZI
        comment_label.setWordWrap(True)
        comment_layout.addWidget(comment_label)
        
        comment_card.setLayout(comment_layout)
        self.trend_layout.addWidget(comment_card)
    
    def _create_comparison_card(self, icon, title, value, bg_color, text_color):
        """Karşılaştırma kartı oluştur - Yazı görünürlüğü düzeltildi"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 2px solid #333333;
                padding: 6px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Icon ve title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 12px; color: {text_color}; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 22px; color: {text_color}; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def _clear_layout(self, layout):
        """Layout'u temizle"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                self._clear_layout(child.layout())
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class DashboardManager:
    """Dashboard yöneticisi"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.cards = {}
        self.advanced_widgets = {}
    
    def create_dashboard_cards(self, parent_layout) -> Dict[str, QWidget]:
        """Dashboard kartlarını oluştur"""
        try:
            # Verileri al
            stats = self._get_dashboard_statistics()
            
            # Kartları oluştur
            cards = {}
            
            # Ana metrik kartları
            cards['total_tezgah'] = AnimatedCard(
                "Toplam Tezgah", 
                str(stats['total_tezgah']), 
                "🏭", 
                "#2196F3"
            )
            
            cards['active_tezgah'] = AnimatedCard(
                "Aktif Tezgah", 
                str(stats['active_tezgah']), 
                "✅", 
                "#4CAF50"
            )
            
            cards['maintenance_count'] = AnimatedCard(
                "Bu Ay Bakım", 
                str(stats['monthly_maintenance']), 
                "🔧", 
                "#FF9800"
            )
            
            cards['battery_warnings'] = AnimatedCard(
                "Pil Uyarısı", 
                str(stats['battery_warnings']), 
                "🔋", 
                "#F44336"
            )
            
            # Trend kartları
            cards['maintenance_trend'] = TrendCard(
                "Bakım Trendi",
                stats['monthly_maintenance'],
                stats['previous_month_maintenance'],
                " bakım",
                "📈"
            )
            
            # Progress kartları
            cards['maintenance_completion'] = ProgressCard(
                "Bakım Tamamlanma",
                stats['completed_maintenance'],
                stats['total_planned_maintenance'],
                " bakım",
                "🎯"
            )
            
            # Alert kartları
            cards['overdue_maintenance'] = AlertCard(
                "Geciken Bakımlar",
                stats['overdue_maintenance'],
                "error"
            )
            
            cards['upcoming_maintenance'] = AlertCard(
                "Yaklaşan Bakımlar",
                stats['upcoming_maintenance'],
                "warning"
            )
            
            # YENİ: Basit ve okunabilir geçmiş arızalar widget'ları
            from simple_widgets import SimpleMaintenanceCard, SimpleTrendCard
            
            cards['maintenance_history'] = SimpleMaintenanceCard()
            cards['maintenance_trend_detailed'] = SimpleTrendCard()
            
            # Geçmiş arızalar verilerini güncelle
            maintenance_stats = self._get_maintenance_statistics()
            cards['maintenance_history'].update_data(maintenance_stats)
            
            # Trend verilerini güncelle
            trend_data = self._get_trend_data()
            cards['maintenance_trend_detailed'].update_trend(
                stats['monthly_maintenance'],
                stats['previous_month_maintenance'],
                trend_data
            )
            
            # YENİ: Gelişmiş widget'ları ekle
            if ADVANCED_WIDGETS_AVAILABLE:
                self.create_advanced_widgets(cards)
            
            self.cards = cards
            return cards
            
        except Exception as e:
            self.logger.error(f"Dashboard cards creation error: {e}")
            return {}
    
    def create_advanced_widgets(self, cards: Dict[str, QWidget]):
        """Gelişmiş widget'ları oluştur"""
        try:
            # Gerçek zamanlı grafik
            cards['realtime_chart'] = MaintenanceTrendChart(self.db_manager)
            
            # Performans metrikleri
            cards['performance_metrics'] = PerformanceMetricsWidget(self.db_manager)
            
            # Uyarı sistemi
            cards['alert_notifications'] = AlertNotificationWidget(self.db_manager)
            
            # Bakım analizi
            cards['maintenance_analysis'] = MaintenanceAnalysisWidget(self.db_manager)
            
            # Uyarı sinyalini bağla
            if 'alert_notifications' in cards:
                cards['alert_notifications'].alert_triggered.connect(self.show_critical_alert)
            
            self.advanced_widgets = {
                'realtime_chart': cards['realtime_chart'],
                'performance_metrics': cards['performance_metrics'],
                'alert_notifications': cards['alert_notifications'],
                'maintenance_analysis': cards['maintenance_analysis']
            }
            
            self.logger.info("Advanced widgets created successfully")
            
        except Exception as e:
            self.logger.error(f"Advanced widgets creation error: {e}")
    
    def show_critical_alert(self, title: str, message: str, level: str):
        """Kritik uyarı göster"""
        try:
            dialog = CriticalAlertDialog(title, message, level)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Critical alert dialog error: {e}")
            # Fallback - basit message box
            if level == 'critical':
                QMessageBox.critical(None, title, message)
            elif level == 'warning':
                QMessageBox.warning(None, title, message)
            else:
                QMessageBox.information(None, title, message)
    
    def _get_maintenance_statistics(self) -> Dict[str, Any]:
        """Detaylı bakım istatistiklerini al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim
                from sqlalchemy import func
                
                # Bu ay bakım sayısı
                current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                monthly_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start
                ).count()
                
                # Toplam bakım sayısı
                total_maintenance = session.query(Bakim).count()
                
                # Tamamlanan bakımlar
                completed_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start,
                    Bakim.durum == 'Tamamlandı'
                ).count()
                
                # En çok arıza olan tezgah
                most_problematic = session.query(
                    Tezgah.numarasi,
                    func.count(Bakim.id).label('ariza_count')
                ).join(Bakim).group_by(Tezgah.id, Tezgah.numarasi).order_by(
                    func.count(Bakim.id).desc()
                ).first()
                
                most_problematic_info = None
                if most_problematic:
                    most_problematic_info = {
                        'tezgah': most_problematic.numarasi,
                        'count': most_problematic.ariza_count
                    }
                
                return {
                    'total_maintenance': total_maintenance,
                    'monthly_maintenance': monthly_maintenance,
                    'completed_maintenance': completed_maintenance,
                    'most_problematic_tezgah': most_problematic_info
                }
                
        except Exception as e:
            self.logger.error(f"Maintenance statistics error: {e}")
            return {
                'total_maintenance': 0,
                'monthly_maintenance': 0,
                'completed_maintenance': 0,
                'most_problematic_tezgah': None
            }
    
    def _get_trend_data(self) -> Dict[str, Any]:
        """Trend verilerini al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Bakim
                
                # Bu hafta bakım sayısı
                week_start = datetime.now() - timedelta(days=7)
                weekly_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= week_start
                ).count()
                
                # Son 30 günlük günlük ortalama
                month_start = datetime.now() - timedelta(days=30)
                monthly_total = session.query(Bakim).filter(
                    Bakim.tarih >= month_start
                ).count()
                daily_average = monthly_total / 30
                
                return {
                    'weekly_trend': weekly_maintenance,
                    'daily_average': round(daily_average, 1)
                }
                
        except Exception as e:
            self.logger.error(f"Trend data error: {e}")
            return {
                'weekly_trend': 0,
                'daily_average': 0
            }
    
    def _get_dashboard_statistics(self) -> Dict[str, int]:
        """Dashboard istatistiklerini al"""
        try:
            with self.db_manager.get_session() as session:
                from database_models import Tezgah, Bakim, Pil
                
                # Temel sayılar
                total_tezgah = session.query(Tezgah).count()
                active_tezgah = session.query(Tezgah).filter(Tezgah.durum == 'Aktif').count()
                
                # Bu ay bakım sayısı
                current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                monthly_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start
                ).count()
                
                # Geçen ay bakım sayısı
                last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
                previous_month_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= last_month_start,
                    Bakim.tarih < current_month_start
                ).count()
                
                # Pil uyarıları (1 yıldan eski)
                old_date = datetime.now(timezone.utc) - timedelta(days=365)
                battery_warnings = session.query(Pil).filter(
                    Pil.durum == 'Aktif',
                    Pil.degisim_tarihi <= old_date
                ).count()
                
                # Bakım tamamlanma
                completed_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start,
                    Bakim.durum == 'Tamamlandı'
                ).count()
                
                total_planned_maintenance = session.query(Bakim).filter(
                    Bakim.tarih >= current_month_start
                ).count()
                
                # Geciken bakımlar (sonraki_bakim_tarihi geçmiş)
                overdue_maintenance = session.query(Tezgah).filter(
                    Tezgah.sonraki_bakim_tarihi < datetime.now(timezone.utc),
                    Tezgah.durum == 'Aktif'
                ).count()
                
                # Yaklaşan bakımlar (7 gün içinde)
                upcoming_date = datetime.now(timezone.utc) + timedelta(days=7)
                upcoming_maintenance = session.query(Tezgah).filter(
                    Tezgah.sonraki_bakim_tarihi <= upcoming_date,
                    Tezgah.sonraki_bakim_tarihi >= datetime.now(timezone.utc),
                    Tezgah.durum == 'Aktif'
                ).count()
                
                return {
                    'total_tezgah': total_tezgah,
                    'active_tezgah': active_tezgah,
                    'monthly_maintenance': monthly_maintenance,
                    'previous_month_maintenance': previous_month_maintenance,
                    'battery_warnings': battery_warnings,
                    'completed_maintenance': completed_maintenance,
                    'total_planned_maintenance': max(1, total_planned_maintenance),  # Sıfır bölme hatası önleme
                    'overdue_maintenance': overdue_maintenance,
                    'upcoming_maintenance': upcoming_maintenance
                }
                
        except Exception as e:
            self.logger.error(f"Dashboard statistics error: {e}")
            return {
                'total_tezgah': 0,
                'active_tezgah': 0,
                'monthly_maintenance': 0,
                'previous_month_maintenance': 0,
                'battery_warnings': 0,
                'completed_maintenance': 0,
                'total_planned_maintenance': 1,
                'overdue_maintenance': 0,
                'upcoming_maintenance': 0
            }
    
    def update_cards(self):
        """Kartları güncelle"""
        try:
            stats = self._get_dashboard_statistics()
            
            if 'total_tezgah' in self.cards:
                self.cards['total_tezgah'].update_value(str(stats['total_tezgah']))
            
            if 'active_tezgah' in self.cards:
                self.cards['active_tezgah'].update_value(str(stats['active_tezgah']))
            
            if 'maintenance_count' in self.cards:
                self.cards['maintenance_count'].update_value(str(stats['monthly_maintenance']))
            
            if 'battery_warnings' in self.cards:
                self.cards['battery_warnings'].update_value(str(stats['battery_warnings']))
            
            # YENİ: Basit geçmiş arızalar widget'larını güncelle
            if 'maintenance_history' in self.cards:
                maintenance_stats = self._get_maintenance_statistics()
                self.cards['maintenance_history'].update_data(maintenance_stats)
            
            if 'maintenance_trend_detailed' in self.cards:
                trend_data = self._get_trend_data()
                self.cards['maintenance_trend_detailed'].update_trend(
                    stats['monthly_maintenance'],
                    stats['previous_month_maintenance'],
                    trend_data
                )
            
            # YENİ: Gelişmiş widget'ları güncelle
            if ADVANCED_WIDGETS_AVAILABLE and self.advanced_widgets:
                # Performans metrikleri otomatik güncelleniyor (kendi timer'ı var)
                # Uyarı sistemi otomatik güncelleniyor (kendi timer'ı var)
                # Bakım analizi otomatik güncelleniyor (kendi timer'ı var)
                # Gerçek zamanlı grafik otomatik güncelleniyor (kendi timer'ı var)
                pass
            
            self.logger.info("Dashboard cards updated successfully")
            
        except Exception as e:
            self.logger.error(f"Dashboard cards update error: {e}")
    
    def get_advanced_widgets(self) -> Dict[str, QWidget]:
        """Gelişmiş widget'ları döndür"""
        return self.advanced_widgets if ADVANCED_WIDGETS_AVAILABLE else {}