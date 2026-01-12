#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Basit ve Okunabilir Widget'lar
Yazı görünürlük sorunu çözümü
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

class SimpleMaintenanceCard(QFrame):
    """Basit ve okunabilir geçmiş arızalar kartı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """Basit UI kurulumu"""
        self.setFixedSize(400, 180)
        
        # Çok basit stil - sadece beyaz arka plan ve koyu kenarlık
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 4px solid #2c3e50;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Başlık - Büyük ve koyu
        title_label = QLabel("🔧 Geçmiş Arızalar")
        title_label.setStyleSheet("""
            font-size: 20px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
            padding: 8px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # İstatistikler için alan
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(8)
        self.stats_widget.setLayout(self.stats_layout)
        layout.addWidget(self.stats_widget)
        
        self.setLayout(layout)
    
    def update_data(self, maintenance_stats):
        """Veri güncelleme - Çok basit"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.stats_layout.count())):
            child = self.stats_layout.itemAt(i)
            if child and child.widget():
                child.widget().setParent(None)
        
        # Toplam arıza - Büyük kutu
        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fd;
                border: 3px solid #1976d2;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(10, 5, 10, 5)
        
        total_text = QLabel(f"📊 Toplam: {maintenance_stats.get('total_maintenance', 0)} arıza")
        total_text.setStyleSheet("""
            font-size: 16px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
        """)
        total_layout.addWidget(total_text)
        
        total_frame.setLayout(total_layout)
        self.stats_layout.addWidget(total_frame)
        
        # Bu ay - Orta kutu
        month_frame = QFrame()
        month_frame.setStyleSheet("""
            QFrame {
                background-color: #fff8e1;
                border: 3px solid #f57c00;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        month_layout = QHBoxLayout()
        month_layout.setContentsMargins(10, 5, 10, 5)
        
        month_text = QLabel(f"📅 Bu Ay: {maintenance_stats.get('monthly_maintenance', 0)} arıza")
        month_text.setStyleSheet("""
            font-size: 14px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
        """)
        month_layout.addWidget(month_text)
        
        month_frame.setLayout(month_layout)
        self.stats_layout.addWidget(month_frame)
        
        # Tamamlanan - Yeşil kutu
        completed_frame = QFrame()
        completed_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e8;
                border: 3px solid #4caf50;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        completed_layout = QHBoxLayout()
        completed_layout.setContentsMargins(10, 5, 10, 5)
        
        completed_text = QLabel(f"✅ Tamamlanan: {maintenance_stats.get('completed_maintenance', 0)}")
        completed_text.setStyleSheet("""
            font-size: 14px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
        """)
        completed_layout.addWidget(completed_text)
        
        completed_frame.setLayout(completed_layout)
        self.stats_layout.addWidget(completed_frame)
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

class SimpleTrendCard(QFrame):
    """Basit trend kartı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shadow()
    
    def setup_ui(self):
        """Basit UI kurulumu"""
        self.setFixedSize(350, 180)
        
        # Çok basit stil
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 4px solid #2c3e50;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Başlık
        title_label = QLabel("📈 Arıza Trendi")
        title_label.setStyleSheet("""
            font-size: 20px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
            padding: 8px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Trend bilgisi için alan
        self.trend_widget = QWidget()
        self.trend_layout = QVBoxLayout()
        self.trend_layout.setSpacing(10)
        self.trend_widget.setLayout(self.trend_layout)
        layout.addWidget(self.trend_widget)
        
        self.setLayout(layout)
    
    def update_trend(self, current_month, previous_month, trend_data):
        """Trend güncelleme - Çok basit"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.trend_layout.count())):
            child = self.trend_layout.itemAt(i)
            if child and child.widget():
                child.widget().setParent(None)
        
        # Trend hesaplama
        if previous_month > 0:
            change_percent = ((current_month - previous_month) / previous_month) * 100
        else:
            change_percent = 0 if current_month == 0 else 100
        
        # Ana trend kutusu
        trend_frame = QFrame()
        if change_percent > 0:
            # Artış - Kırmızı
            trend_frame.setStyleSheet("""
                QFrame {
                    background-color: #ffebee;
                    border: 4px solid #f44336;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            trend_icon = "📈"
            trend_text = f"+{change_percent:.1f}% ARTIŞ"
        elif change_percent < 0:
            # Azalış - Yeşil
            trend_frame.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e8;
                    border: 4px solid #4caf50;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            trend_icon = "📉"
            trend_text = f"{change_percent:.1f}% AZALIŞ"
        else:
            # Değişim yok - Gri
            trend_frame.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border: 4px solid #666666;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            trend_icon = "📊"
            trend_text = "DEĞİŞİM YOK"
        
        trend_layout = QVBoxLayout()
        trend_layout.setContentsMargins(5, 5, 5, 5)
        
        # Icon ve trend
        icon_text_layout = QHBoxLayout()
        
        icon_label = QLabel(trend_icon)
        icon_label.setStyleSheet("font-size: 24px;")
        icon_text_layout.addWidget(icon_label)
        
        trend_label = QLabel(trend_text)
        trend_label.setStyleSheet("""
            font-size: 16px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
        """)
        icon_text_layout.addWidget(trend_label)
        icon_text_layout.addStretch()
        
        trend_layout.addLayout(icon_text_layout)
        
        # Karşılaştırma
        comparison_label = QLabel(f"Bu Ay: {current_month} | Geçen Ay: {previous_month}")
        comparison_label.setStyleSheet("""
            font-size: 12px; 
            color: #000000; 
            font-weight: bold;
            background-color: transparent;
        """)
        trend_layout.addWidget(comparison_label)
        
        trend_frame.setLayout(trend_layout)
        self.trend_layout.addWidget(trend_frame)
        
        # Haftalık bilgi (eğer varsa)
        if 'weekly_trend' in trend_data:
            weekly_frame = QFrame()
            weekly_frame.setStyleSheet("""
                QFrame {
                    background-color: #fff3e0;
                    border: 2px solid #ff9800;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            
            weekly_layout = QHBoxLayout()
            weekly_layout.setContentsMargins(8, 4, 8, 4)
            
            weekly_text = QLabel(f"📊 Bu Hafta: {trend_data['weekly_trend']} arıza")
            weekly_text.setStyleSheet("""
                font-size: 12px; 
                color: #000000; 
                font-weight: bold;
                background-color: transparent;
            """)
            weekly_layout.addWidget(weekly_text)
            
            weekly_frame.setLayout(weekly_layout)
            self.trend_layout.addWidget(weekly_frame)
    
    def setup_shadow(self):
        """Gölge efekti"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)