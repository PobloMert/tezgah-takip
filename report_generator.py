#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Rapor Oluşturucu
Kapsamlı raporlama ve analiz sistemi
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QDateEdit, QTextEdit,
                            QTabWidget, QTableWidget, QTableWidgetItem,
                            QSplitter, QGroupBox, QProgressBar, QCheckBox,
                            QSpinBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

# Set matplotlib style
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import seaborn as sns
    import pandas as pd
    import numpy as np
    
    plt.style.use('default')  # seaborn-v0_8 deprecated olabilir
    sns.set_palette("husl")
    PLOTTING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Plotting libraries not available: {e}")
    PLOTTING_AVAILABLE = False

@dataclass
class ReportConfig:
    """Rapor konfigürasyon sınıfı"""
    report_type: str
    start_date: datetime
    end_date: datetime
    include_charts: bool = True
    include_statistics: bool = True
    include_recommendations: bool = True
    tezgah_filter: Optional[List[str]] = None
    status_filter: Optional[List[str]] = None
    export_format: str = "pdf"  # pdf, excel, html

@dataclass
class ReportData:
    """Rapor veri sınıfı"""
    title: str
    period: str
    generated_at: datetime
    summary: Dict[str, Any]
    charts: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    recommendations: List[str]
    raw_data: Dict[str, Any]

class ReportGenerator:
    """Gelişmiş rapor oluşturucu sınıfı"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Matplotlib Türkçe font ayarları
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Tahoma']
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate_dashboard_report(self, config: ReportConfig) -> ReportData:
        """Dashboard özet raporu oluştur"""
        try:
            # Veri toplama
            summary_data = self._collect_summary_data(config)
            chart_data = self._generate_dashboard_charts(config, summary_data)
            table_data = self._generate_summary_tables(config, summary_data)
            recommendations = self._generate_recommendations(summary_data)
            
            report = ReportData(
                title="Dashboard Özet Raporu",
                period=f"{config.start_date.strftime('%d.%m.%Y')} - {config.end_date.strftime('%d.%m.%Y')}",
                generated_at=datetime.now(timezone.utc),
                summary=summary_data,
                charts=chart_data,
                tables=table_data,
                recommendations=recommendations,
                raw_data=summary_data
            )
            
            self.logger.info("Dashboard report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Dashboard report generation failed: {e}")
            raise
    
    def generate_maintenance_report(self, config: ReportConfig) -> ReportData:
        """Bakım raporu oluştur"""
        try:
            # Bakım verilerini topla
            maintenance_data = self._collect_maintenance_data(config)
            
            # Analizler
            maintenance_analysis = self._analyze_maintenance_data(maintenance_data, config)
            
            # Grafikler
            charts = self._generate_maintenance_charts(maintenance_data, config)
            
            # Tablolar
            tables = self._generate_maintenance_tables(maintenance_data, config)
            
            # Öneriler
            recommendations = self._generate_maintenance_recommendations(maintenance_analysis)
            
            report = ReportData(
                title="Bakım Analiz Raporu",
                period=f"{config.start_date.strftime('%d.%m.%Y')} - {config.end_date.strftime('%d.%m.%Y')}",
                generated_at=datetime.now(timezone.utc),
                summary=maintenance_analysis,
                charts=charts,
                tables=tables,
                recommendations=recommendations,
                raw_data=maintenance_data
            )
            
            self.logger.info("Maintenance report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Maintenance report generation failed: {e}")
            raise
    
    def generate_battery_report(self, config: ReportConfig) -> ReportData:
        """Pil analiz raporu oluştur"""
        try:
            # Pil verilerini topla
            battery_data = self._collect_battery_data(config)
            
            # Analizler
            battery_analysis = self._analyze_battery_data(battery_data, config)
            
            # Grafikler
            charts = self._generate_battery_charts(battery_data, config)
            
            # Tablolar
            tables = self._generate_battery_tables(battery_data, config)
            
            # Öneriler
            recommendations = self._generate_battery_recommendations(battery_analysis)
            
            report = ReportData(
                title="Pil Analiz Raporu",
                period=f"{config.start_date.strftime('%d.%m.%Y')} - {config.end_date.strftime('%d.%m.%Y')}",
                generated_at=datetime.now(timezone.utc),
                summary=battery_analysis,
                charts=charts,
                tables=tables,
                recommendations=recommendations,
                raw_data=battery_data
            )
            
            self.logger.info("Battery report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Battery report generation failed: {e}")
            raise
    
    def _collect_summary_data(self, config: ReportConfig) -> Dict[str, Any]:
        """Özet veri toplama"""
        with self.db_manager.get_session() as session:
            from database_models import Tezgah, Bakim, Pil
            
            # Temel istatistikler
            total_tezgah = session.query(Tezgah).count()
            active_tezgah = session.query(Tezgah).filter(Tezgah.durum == 'Aktif').count()
            
            # Bakım istatistikleri
            maintenance_count = session.query(Bakim).filter(
                Bakim.tarih.between(config.start_date, config.end_date)
            ).count()
            
            completed_maintenance = session.query(Bakim).filter(
                Bakim.tarih.between(config.start_date, config.end_date),
                Bakim.durum == 'Tamamlandı'
            ).count()
            
            # Pil istatistikleri
            battery_changes = session.query(Pil).filter(
                Pil.degisim_tarihi.between(config.start_date, config.end_date)
            ).count()
            
            # Eski piller (1 yıldan fazla)
            old_batteries = session.query(Pil).filter(
                Pil.durum == 'Aktif',
                Pil.degisim_tarihi <= datetime.now(timezone.utc) - timedelta(days=365)
            ).count()
            
            return {
                'total_tezgah': total_tezgah,
                'active_tezgah': active_tezgah,
                'inactive_tezgah': total_tezgah - active_tezgah,
                'maintenance_count': maintenance_count,
                'completed_maintenance': completed_maintenance,
                'maintenance_completion_rate': (completed_maintenance / maintenance_count * 100) if maintenance_count > 0 else 0,
                'battery_changes': battery_changes,
                'old_batteries': old_batteries,
                'period_days': (config.end_date - config.start_date).days
            }
    
    def _generate_dashboard_charts(self, config: ReportConfig, data: Dict) -> List[Dict]:
        """Dashboard grafikleri oluştur"""
        charts = []
        
        if not config.include_charts or not PLOTTING_AVAILABLE:
            return charts
        
        try:
            # 1. Tezgah Durum Dağılımı (Pie Chart)
            fig, ax = plt.subplots(figsize=(8, 6))
            
            labels = ['Aktif Tezgahlar', 'Pasif Tezgahlar']
            sizes = [data['active_tezgah'], data['inactive_tezgah']]
            colors = ['#4CAF50', '#FF9800']
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            
            ax.set_title('Tezgah Durum Dağılımı', fontsize=14, fontweight='bold')
            
            # Grafik kaydet
            chart_path = self._save_chart(fig, 'tezgah_durum_dagilimi')
            charts.append({
                'title': 'Tezgah Durum Dağılımı',
                'type': 'pie',
                'path': chart_path,
                'description': f'Toplam {data["total_tezgah"]} tezgahın durum dağılımı'
            })
            
            plt.close(fig)
            
            # 2. Bakım Tamamlanma Oranı (Bar Chart)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = ['Toplam Bakım', 'Tamamlanan', 'Devam Eden/Bekleyen']
            values = [
                data['maintenance_count'],
                data['completed_maintenance'],
                data['maintenance_count'] - data['completed_maintenance']
            ]
            colors = ['#2196F3', '#4CAF50', '#FF9800']
            
            bars = ax.bar(categories, values, color=colors)
            ax.set_title('Bakım İstatistikleri', fontsize=14, fontweight='bold')
            ax.set_ylabel('Bakım Sayısı')
            
            # Bar üzerine değer yaz
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(value)}', ha='center', va='bottom')
            
            chart_path = self._save_chart(fig, 'bakim_istatistikleri')
            charts.append({
                'title': 'Bakım İstatistikleri',
                'type': 'bar',
                'path': chart_path,
                'description': f'Son {data["period_days"]} günlük bakım performansı'
            })
            
            plt.close(fig)
            
            # 3. Pil Durumu (Donut Chart)
            if data['battery_changes'] > 0 or data['old_batteries'] > 0:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                labels = ['Yeni Değişenler', 'Eski Piller (>1 yıl)']
                sizes = [data['battery_changes'], data['old_batteries']]
                colors = ['#4CAF50', '#F44336']
                
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                                autopct='%1.1f%%', startangle=90,
                                                pctdistance=0.85)
                
                # Donut effect
                centre_circle = plt.Circle((0,0), 0.70, fc='white')
                fig.gca().add_artist(centre_circle)
                
                ax.set_title('Pil Durumu Analizi', fontsize=14, fontweight='bold')
                
                chart_path = self._save_chart(fig, 'pil_durumu_analizi')
                charts.append({
                    'title': 'Pil Durumu Analizi',
                    'type': 'donut',
                    'path': chart_path,
                    'description': 'Pil değişim durumu ve eski pil uyarıları'
                })
                
                plt.close(fig)
            
        except Exception as e:
            self.logger.error(f"Chart generation error: {e}")
            # Fallback - grafik olmadan devam et
            charts.append({
                'title': 'Grafik Oluşturulamadı',
                'type': 'error',
                'path': '',
                'description': f'Grafik oluşturulurken hata oluştu: {str(e)[:100]}'
            })
        
        return charts
    
    def _generate_summary_tables(self, config: ReportConfig, data: Dict) -> List[Dict]:
        """Özet tabloları oluştur"""
        tables = []
        
        # Genel İstatistikler Tablosu
        general_stats = {
            'headers': ['Metrik', 'Değer', 'Açıklama'],
            'rows': [
                ['Toplam Tezgah', str(data['total_tezgah']), 'Sistemdeki toplam tezgah sayısı'],
                ['Aktif Tezgah', str(data['active_tezgah']), 'Çalışır durumda olan tezgahlar'],
                ['Bakım Sayısı', str(data['maintenance_count']), f'Son {data["period_days"]} günde yapılan bakım'],
                ['Tamamlanma Oranı', f"{data['maintenance_completion_rate']:.1f}%", 'Bakım tamamlanma yüzdesi'],
                ['Pil Değişimi', str(data['battery_changes']), f'Son {data["period_days"]} günde değişen pil'],
                ['Eski Pil Uyarısı', str(data['old_batteries']), '1 yıldan eski aktif piller']
            ]
        }
        
        tables.append({
            'title': 'Genel İstatistikler',
            'type': 'summary',
            'data': general_stats
        })
        
        return tables
    
    def _generate_recommendations(self, data: Dict) -> List[str]:
        """Öneriler oluştur"""
        recommendations = []
        
        # Bakım tamamlanma oranı kontrolü
        if data['maintenance_completion_rate'] < 80:
            recommendations.append(
                f"⚠️ Bakım tamamlanma oranı %{data['maintenance_completion_rate']:.1f} - "
                "Hedef %90'ın üzerinde olmalı. Bakım süreçlerini gözden geçirin."
            )
        
        # Eski pil kontrolü
        if data['old_batteries'] > 0:
            recommendations.append(
                f"🔋 {data['old_batteries']} adet 1 yıldan eski pil tespit edildi. "
                "Pil değişim planı oluşturun."
            )
        
        # Pasif tezgah kontrolü
        if data['inactive_tezgah'] > data['total_tezgah'] * 0.1:  # %10'dan fazla pasif
            recommendations.append(
                f"🏭 {data['inactive_tezgah']} adet pasif tezgah var. "
                "Tezgah kullanım verimliliğini artırın."
            )
        
        # Pozitif geri bildirimler
        if data['maintenance_completion_rate'] >= 90:
            recommendations.append(
                "✅ Bakım tamamlanma oranı mükemmel seviyede! Bu performansı sürdürün."
            )
        
        if data['old_batteries'] == 0:
            recommendations.append(
                "✅ Tüm piller güncel durumda. İyi pil yönetimi!"
            )
        
        return recommendations
    
    def _save_chart(self, fig, filename: str) -> str:
        """Grafik kaydet"""
        try:
            # Charts klasörü oluştur
            charts_dir = Path("exports/charts")
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            # Dosya adı
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_path = charts_dir / f"{filename}_{timestamp}.png"
            
            # Kaydet
            fig.savefig(chart_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"Chart save error: {e}")
            return ""
    
    def _collect_maintenance_data(self, config: ReportConfig) -> Dict:
        """Bakım verilerini topla"""
        with self.db_manager.get_session() as session:
            from database_models import Bakim, Tezgah
            
            # Bakım kayıtları
            query = session.query(Bakim, Tezgah).join(Tezgah).filter(
                Bakim.tarih.between(config.start_date, config.end_date)
            )
            
            if config.tezgah_filter:
                query = query.filter(Tezgah.numarasi.in_(config.tezgah_filter))
            
            if config.status_filter:
                query = query.filter(Bakim.durum.in_(config.status_filter))
            
            maintenance_records = query.all()
            
            return {
                'records': maintenance_records,
                'count': len(maintenance_records)
            }
    
    def _analyze_maintenance_data(self, data: Dict, config: ReportConfig) -> Dict:
        """Bakım verilerini analiz et"""
        records = data['records']
        
        if not records:
            return {'error': 'Veri bulunamadı'}
        
        # Durum dağılımı
        status_counts = {}
        for bakim, tezgah in records:
            status = bakim.durum
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Teknisyen performansı
        technician_counts = {}
        for bakim, tezgah in records:
            tech = bakim.bakim_yapan
            technician_counts[tech] = technician_counts.get(tech, 0) + 1
        
        # Aylık trend
        monthly_counts = {}
        for bakim, tezgah in records:
            month_key = bakim.tarih.strftime('%Y-%m')
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        
        return {
            'total_maintenance': len(records),
            'status_distribution': status_counts,
            'technician_performance': technician_counts,
            'monthly_trend': monthly_counts,
            'avg_per_day': len(records) / max(1, (config.end_date - config.start_date).days)
        }
    
    def _generate_maintenance_charts(self, data: Dict, config: ReportConfig) -> List[Dict]:
        """Bakım grafiklerini oluştur"""
        # Bu method'u implement edeceğiz
        return []
    
    def _generate_maintenance_tables(self, data: Dict, config: ReportConfig) -> List[Dict]:
        """Bakım tablolarını oluştur"""
        # Bu method'u implement edeceğiz
        return []
    
    def _generate_maintenance_recommendations(self, analysis: Dict) -> List[str]:
        """Bakım önerilerini oluştur"""
        # Bu method'u implement edeceğiz
        return []
    
    def _collect_battery_data(self, config: ReportConfig) -> Dict:
        """Pil verilerini topla"""
        # Bu method'u implement edeceğiz
        return {}
    
    def _analyze_battery_data(self, data: Dict, config: ReportConfig) -> Dict:
        """Pil verilerini analiz et"""
        # Bu method'u implement edeceğiz
        return {}
    
    def _generate_battery_charts(self, data: Dict, config: ReportConfig) -> List[Dict]:
        """Pil grafiklerini oluştur"""
        # Bu method'u implement edeceğiz
        return []
    
    def _generate_battery_tables(self, data: Dict, config: ReportConfig) -> List[Dict]:
        """Pil tablolarını oluştur"""
        # Bu method'u implement edeceğiz
        return []
    
    def _generate_battery_recommendations(self, analysis: Dict) -> List[str]:
        """Pil önerilerini oluştur"""
        # Bu method'u implement edeceğiz
        return []

class ReportWorker(QThread):
    """Background rapor oluşturma thread'i"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    report_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, report_generator, config):
        super().__init__()
        self.report_generator = report_generator
        self.config = config
    
    def run(self):
        """Rapor oluşturma işlemi"""
        try:
            self.status_updated.emit("Rapor oluşturuluyor...")
            self.progress_updated.emit(10)
            
            if self.config.report_type == "dashboard":
                report = self.report_generator.generate_dashboard_report(self.config)
            elif self.config.report_type == "maintenance":
                report = self.report_generator.generate_maintenance_report(self.config)
            elif self.config.report_type == "battery":
                report = self.report_generator.generate_battery_report(self.config)
            else:
                raise ValueError(f"Unknown report type: {self.config.report_type}")
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Rapor hazır!")
            self.report_ready.emit(report)
            
        except Exception as e:
            self.error_occurred.emit(str(e))