#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Dışa Aktarma Yöneticisi
Excel ve PDF rapor oluşturma modülü
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

try:
    import pandas as pd
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    EXCEL_AVAILABLE = True
except ImportError as e:
    EXCEL_AVAILABLE = False
    logging.warning(f"⚠️ Excel desteği için eksik paket: {e}")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    logging.warning(f"⚠️ PDF desteği için eksik paket: {e}")

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    CHART_AVAILABLE = True
except ImportError as e:
    CHART_AVAILABLE = False
    logging.warning(f"⚠️ Grafik desteği için eksik paket: {e}")

class ExportManager:
    """Dışa aktarma işlemlerini yöneten sınıf"""
    
    # Constants
    MAX_RECORDS_LIMIT = 10000
    MAX_FILENAME_LENGTH = 100
    ALLOWED_EXTENSIONS = ['.xlsx', '.pdf', '.png']
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Çıktı klasörü
        self.output_dir = "exports"
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Çıktı klasörünü güvenli şekilde oluştur"""
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, mode=0o755)
                self.logger.info(f"Export directory created: {self.output_dir}")
        except OSError as e:
            self.logger.error(f"Failed to create export directory: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Dosya adını güvenli hale getir"""
        import re
        
        # Tehlikeli karakterleri temizle
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Uzunluk sınırı
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:self.MAX_FILENAME_LENGTH - len(ext)] + ext
        
        return sanitized
    
    def _validate_filters(self, filters: Dict) -> Dict:
        """Filtreleri validate et"""
        if not filters:
            return {}
        
        validated = {}
        
        # Tarih filtreleri
        if 'start_date' in filters:
            start_date = filters['start_date']
            if isinstance(start_date, datetime):
                validated['start_date'] = start_date
            elif isinstance(start_date, str):
                try:
                    validated['start_date'] = datetime.fromisoformat(start_date)
                except ValueError:
                    self.logger.warning(f"Invalid start_date format: {start_date}")
        
        if 'end_date' in filters:
            end_date = filters['end_date']
            if isinstance(end_date, datetime):
                validated['end_date'] = end_date
            elif isinstance(end_date, str):
                try:
                    validated['end_date'] = datetime.fromisoformat(end_date)
                except ValueError:
                    self.logger.warning(f"Invalid end_date format: {end_date}")
        
        # String filtreleri - güvenlik kontrolü ile
        for key in ['durum', 'lokasyon', 'teknisyen']:
            if key in filters and isinstance(filters[key], str):
                # Input sanitization - tehlikeli karakterleri temizle
                import re
                sanitized = re.sub(r'[<>"\';\\]', '', filters[key].strip())[:100]
                if sanitized:
                    validated[key] = sanitized
        
        # Sayısal filtreler
        for key in ['limit', 'offset']:
            if key in filters:
                try:
                    value = int(filters[key])
                    if 0 <= value <= self.MAX_RECORDS_LIMIT:
                        validated[key] = value
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid {key} value: {filters[key]}")
        
        return validated
    
    def export_to_excel(self, data_type: str, filters: Dict = None) -> str:
        """Verileri Excel formatında dışa aktar"""
        if not EXCEL_AVAILABLE:
            raise ImportError("Excel desteği için gerekli paketler yüklü değil")
        
        try:
            # Input validation
            if not data_type or not isinstance(data_type, str):
                raise ValueError("Geçersiz veri tipi")
            
            data_type = data_type.strip().lower()
            if data_type not in ['tezgahlar', 'arizalar', 'piller', 'ozet']:
                raise ValueError(f"Desteklenmeyen veri tipi: {data_type}")
            
            # Filtreleri validate et
            validated_filters = self._validate_filters(filters)
            
            # Veri tipine göre verileri al
            if data_type == "tezgahlar":
                data = self._get_tezgah_data(validated_filters)
                filename = f"tezgahlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            elif data_type == "arizalar":
                data = self._get_ariza_data(validated_filters)
                filename = f"arizalar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            elif data_type == "piller":
                data = self._get_pil_data(validated_filters)
                filename = f"piller_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            elif data_type == "ozet":
                return self._create_summary_excel(validated_filters)
            
            # Dosya adını güvenli hale getir
            filename = self._sanitize_filename(filename)
            filepath = os.path.join(self.output_dir, filename)
            
            # Güvenlik kontrolü - dosya yolu
            if not filepath.startswith(os.path.abspath(self.output_dir)):
                raise ValueError("Güvenlik ihlali: Geçersiz dosya yolu")
            
            # Veri kontrolü
            if not data:
                self.logger.warning(f"No data found for export type: {data_type}")
                raise ValueError("Dışa aktarılacak veri bulunamadı")
            
            # Veri boyutu kontrolü
            if len(data) > self.MAX_RECORDS_LIMIT:
                self.logger.warning(f"Data size exceeds limit: {len(data)} > {self.MAX_RECORDS_LIMIT}")
                data = data[:self.MAX_RECORDS_LIMIT]
            
            # DataFrame oluştur
            df = pd.DataFrame(data)
            
            # Excel dosyası oluştur
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Veriler', index=False)
                
                # Stil uygula
                workbook = writer.book
                worksheet = writer.sheets['Veriler']
                
                # Başlık stili
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
                
                # Başlık satırını stillendir
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                
                # Sütun genişliklerini ayarla
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.logger.info(f"Excel export successful: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Excel export error: {e}")
            raise Exception(f"Excel dışa aktarma hatası: {e}")
    
    def export_to_pdf(self, data_type: str, filters: Dict = None) -> str:
        """Verileri PDF formatında dışa aktar"""
        if not PDF_AVAILABLE:
            raise ImportError("PDF desteği için gerekli paketler yüklü değil")
        
        try:
            # Input validation
            if not data_type or not isinstance(data_type, str):
                raise ValueError("Geçersiz veri tipi")
            
            data_type = data_type.strip().lower()
            if data_type not in ['tezgahlar', 'arizalar', 'piller', 'ozet']:
                raise ValueError(f"Desteklenmeyen veri tipi: {data_type}")
            
            # Filtreleri validate et
            validated_filters = self._validate_filters(filters)
            
            filename = f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filename = self._sanitize_filename(filename)
            filepath = os.path.join(self.output_dir, filename)
            
            # Güvenlik kontrolü - dosya yolu
            if not filepath.startswith(os.path.abspath(self.output_dir)):
                raise ValueError("Güvenlik ihlali: Geçersiz dosya yolu")
            
            # PDF dokümanı oluştur
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            
            # Stil tanımları
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            
            # Başlık
            title_text = f"TezgahTakip - {data_type.title()} Raporu"
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 12))
            
            # Rapor bilgileri
            info_text = f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            story.append(Paragraph(info_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Veri tipine göre içerik oluştur
            if data_type == "tezgahlar":
                data = self._get_tezgah_data(validated_filters)
                headers = ['Tezgah No', 'Açıklama', 'Lokasyon', 'Durum', 'Son Bakım']
            elif data_type == "arizalar":
                data = self._get_ariza_data(validated_filters)
                headers = ['Tezgah', 'Tarih', 'Teknisyen', 'Açıklama']
            elif data_type == "piller":
                data = self._get_pil_data(validated_filters)
                headers = ['Tezgah', 'Eksen', 'Model', 'Değişim Tarihi', 'Değiştiren']
            elif data_type == "ozet":
                return self._create_summary_pdf(validated_filters)
            
            # Veri kontrolü
            if not data:
                self.logger.warning(f"No data found for PDF export: {data_type}")
                raise ValueError("Dışa aktarılacak veri bulunamadı")
            
            # Veri boyutu kontrolü
            if len(data) > self.MAX_RECORDS_LIMIT:
                self.logger.warning(f"PDF data size exceeds limit: {len(data)} > {self.MAX_RECORDS_LIMIT}")
                data = data[:self.MAX_RECORDS_LIMIT]
            
            # Tablo verilerini hazırla
            table_data = [headers]
            for row in data:
                # Güvenli veri çıkarma ve uzunluk sınırı
                safe_row = []
                for h in headers:
                    value = str(row.get(h, ''))[:100]  # Maksimum 100 karakter
                    safe_row.append(value)
                table_data.append(safe_row)
            
            # Tablo oluştur
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            # PDF'i oluştur
            doc.build(story)
            
            self.logger.info(f"PDF export successful: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"PDF export error: {e}")
            raise Exception(f"PDF dışa aktarma hatası: {e}")
    
    def _get_tezgah_data(self, filters: Dict = None) -> List[Dict]:
        """Tezgah verilerini al"""
        from database_models import Tezgah
        
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Tezgah)
                
                # Filtreler uygula
                if filters:
                    if filters.get('durum'):
                        query = query.filter(Tezgah.durum == filters['durum'])
                    if filters.get('lokasyon'):
                        query = query.filter(Tezgah.lokasyon.like(f"%{filters['lokasyon']}%"))
                    if filters.get('limit'):
                        query = query.limit(filters['limit'])
                    if filters.get('offset'):
                        query = query.offset(filters['offset'])
                
                # Güvenlik: Maksimum kayıt sınırı
                query = query.limit(self.MAX_RECORDS_LIMIT)
                
                tezgahlar = query.all()
                
                data = []
                for tezgah in tezgahlar:
                    data.append({
                        'Tezgah No': tezgah.numarasi or '',
                        'Açıklama': tezgah.aciklama or '',
                        'Lokasyon': tezgah.lokasyon or '',
                        'Durum': tezgah.durum or '',
                        'Son Bakım': tezgah.son_bakim_tarihi.strftime('%d.%m.%Y') if tezgah.son_bakim_tarihi else ''
                    })
                
                return data
        except Exception as e:
            self.logger.error(f"Error getting tezgah data: {e}")
            return []
    
    def _get_ariza_data(self, filters: Dict = None) -> List[Dict]:
        """Arıza verilerini al"""
        from database_models import Bakim, Tezgah
        
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Bakim, Tezgah).join(Tezgah, Bakim.tezgah_id == Tezgah.id)
                
                # Filtreler uygula
                if filters:
                    if filters.get('start_date'):
                        query = query.filter(Bakim.tarih >= filters['start_date'])
                    if filters.get('end_date'):
                        query = query.filter(Bakim.tarih <= filters['end_date'])
                    if filters.get('teknisyen'):
                        query = query.filter(Bakim.bakim_yapan.like(f"%{filters['teknisyen']}%"))
                    if filters.get('limit'):
                        query = query.limit(filters['limit'])
                    if filters.get('offset'):
                        query = query.offset(filters['offset'])
                
                # Güvenlik: Maksimum kayıt sınırı
                query = query.limit(self.MAX_RECORDS_LIMIT)
                
                results = query.order_by(Bakim.tarih.desc()).all()
                
                data = []
                for bakim, tezgah in results:
                    data.append({
                        'Tezgah': tezgah.numarasi or '',
                        'Tarih': bakim.tarih.strftime('%d.%m.%Y') if bakim.tarih else '',
                        'Teknisyen': bakim.bakim_yapan or '',
                        'Açıklama': bakim.aciklama or ''
                    })
                
                return data
        except Exception as e:
            self.logger.error(f"Error getting ariza data: {e}")
            return []
    
    def _get_pil_data(self, filters: Dict = None) -> List[Dict]:
        """Pil verilerini al"""
        from database_models import Pil, Tezgah
        
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Pil, Tezgah).join(Tezgah, Pil.tezgah_id == Tezgah.id)
                
                # Filtreler uygula
                if filters:
                    if filters.get('start_date'):
                        query = query.filter(Pil.degisim_tarihi >= filters['start_date'])
                    if filters.get('end_date'):
                        query = query.filter(Pil.degisim_tarihi <= filters['end_date'])
                    if filters.get('limit'):
                        query = query.limit(filters['limit'])
                    if filters.get('offset'):
                        query = query.offset(filters['offset'])
                
                # Güvenlik: Maksimum kayıt sınırı
                query = query.limit(self.MAX_RECORDS_LIMIT)
                
                results = query.order_by(Pil.degisim_tarihi.desc()).all()
                
                data = []
                for pil, tezgah in results:
                    data.append({
                        'Tezgah': tezgah.numarasi or '',
                        'Eksen': pil.eksen or '',
                        'Model': pil.pil_modeli or '',
                        'Değişim Tarihi': pil.degisim_tarihi.strftime('%d.%m.%Y') if pil.degisim_tarihi else '',
                        'Değiştiren': pil.degistiren_kisi or ''
                    })
                
                return data
        except Exception as e:
            self.logger.error(f"Error getting pil data: {e}")
            return []
    
    def _create_summary_excel(self, filters: Dict = None) -> str:
        """Özet rapor Excel dosyası oluştur"""
        filename = f"ozet_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Tezgah özeti
            tezgah_data = self._get_tezgah_data(filters)
            df_tezgah = pd.DataFrame(tezgah_data)
            df_tezgah.to_excel(writer, sheet_name='Tezgahlar', index=False)
            
            # Arıza özeti
            ariza_data = self._get_ariza_data(filters)
            df_ariza = pd.DataFrame(ariza_data)
            df_ariza.to_excel(writer, sheet_name='Arızalar', index=False)
            
            # Pil özeti
            pil_data = self._get_pil_data(filters)
            df_pil = pd.DataFrame(pil_data)
            df_pil.to_excel(writer, sheet_name='Piller', index=False)
            
            # İstatistikler sayfası
            stats_data = {
                'Metrik': ['Toplam Tezgah', 'Toplam Arıza', 'Toplam Pil Değişimi'],
                'Değer': [len(tezgah_data), len(ariza_data), len(pil_data)]
            }
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='İstatistikler', index=False)
        
        return filepath

    def _create_summary_pdf(self, filters: Dict = None) -> str:
        """Özet rapor PDF dosyası oluştur"""
        filename = f"ozet_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # PDF dokümanı oluştur
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Stil tanımları
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            alignment=0  # Left
        )
        
        # Ana başlık
        story.append(Paragraph("TezgahTakip - Özet Rapor", title_style))
        story.append(Spacer(1, 12))
        
        # Rapor bilgileri
        info_text = f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # İstatistikler
        tezgah_data = self._get_tezgah_data(filters)
        ariza_data = self._get_ariza_data(filters)
        pil_data = self._get_pil_data(filters)
        
        story.append(Paragraph("📊 Genel İstatistikler", subtitle_style))
        
        stats_data = [
            ['Metrik', 'Değer'],
            ['Toplam Tezgah', str(len(tezgah_data))],
            ['Toplam Arıza Kaydı', str(len(ariza_data))],
            ['Toplam Pil Kaydı', str(len(pil_data))]
        ]
        
        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Son arızalar (ilk 10)
        if ariza_data:
            story.append(Paragraph("🔧 Son Arızalar (İlk 10)", subtitle_style))
            
            ariza_headers = ['Tezgah', 'Tarih', 'Teknisyen', 'Açıklama']
            ariza_table_data = [ariza_headers]
            
            for i, row in enumerate(ariza_data[:10]):
                ariza_table_data.append([
                    str(row.get('Tezgah', '')),
                    str(row.get('Tarih', '')),
                    str(row.get('Teknisyen', '')),
                    str(row.get('Açıklama', ''))[:50] + '...' if len(str(row.get('Açıklama', ''))) > 50 else str(row.get('Açıklama', ''))
                ])
            
            ariza_table = Table(ariza_table_data)
            ariza_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(ariza_table)
        
        # PDF'i oluştur
        doc.build(story)
        
        return filepath

    def create_chart(self, chart_type: str, filters: Dict = None) -> str:
        """Grafik oluştur"""
        if not CHART_AVAILABLE:
            raise ImportError("Grafik desteği için gerekli paketler yüklü değil")
        
        try:
            # Input validation
            if not chart_type or not isinstance(chart_type, str):
                raise ValueError("Geçersiz grafik tipi")
            
            chart_type = chart_type.strip().lower()
            valid_chart_types = ['ariza_trend', 'pil_degisim', 'teknisyen_performans']
            if chart_type not in valid_chart_types:
                raise ValueError(f"Desteklenmeyen grafik tipi: {chart_type}")
            
            # Filtreleri validate et
            validated_filters = self._validate_filters(filters)
            
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if chart_type == "ariza_trend":
                self._create_ariza_trend_chart(ax, validated_filters)
                title = "Arıza Trend Analizi"
            elif chart_type == "pil_degisim":
                self._create_pil_chart(ax, validated_filters)
                title = "Pil Değişim Analizi"
            elif chart_type == "teknisyen_performans":
                self._create_teknisyen_chart(ax, validated_filters)
                title = "Teknisyen Performans Analizi"
            
            plt.title(title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Grafik dosyasını kaydet
            filename = f"{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filename = self._sanitize_filename(filename)
            filepath = os.path.join(self.output_dir, filename)
            
            # Güvenlik kontrolü - dosya yolu
            if not filepath.startswith(os.path.abspath(self.output_dir)):
                raise ValueError("Güvenlik ihlali: Geçersiz dosya yolu")
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Chart created successfully: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Chart creation error: {e}")
            raise Exception(f"Grafik oluşturma hatası: {e}")
    
    def _create_ariza_trend_chart(self, ax, filters):
        """Arıza trend grafiği oluştur"""
        from database_models import Bakim
        
        try:
            with self.db_manager.get_session() as session:
                # Son 12 ayın verilerini al
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                query = session.query(Bakim).filter(
                    Bakim.tarih >= start_date,
                    Bakim.tarih <= end_date
                )
                
                # Güvenlik: Maksimum kayıt sınırı
                query = query.limit(self.MAX_RECORDS_LIMIT)
                
                bakimlar = query.all()
                
                # Aylık grupla
                monthly_data = {}
                for bakim in bakimlar:
                    if bakim.tarih:
                        month_key = bakim.tarih.strftime('%Y-%m')
                        monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
                
                # Grafik verilerini hazırla
                months = sorted(monthly_data.keys())
                counts = [monthly_data[month] for month in months]
                
                if months and counts:
                    ax.plot(months, counts, marker='o', linewidth=2, markersize=6)
                    ax.set_xlabel('Ay')
                    ax.set_ylabel('Arıza Sayısı')
                    ax.grid(True, alpha=0.3)
                    
                    # X ekseni etiketlerini döndür
                    plt.setp(ax.get_xticklabels(), rotation=45)
                else:
                    ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', transform=ax.transAxes)
        except Exception as e:
            self.logger.error(f"Error creating ariza trend chart: {e}")
            ax.text(0.5, 0.5, 'Grafik oluşturulamadı', ha='center', va='center', transform=ax.transAxes)
    
    def _create_pil_chart(self, ax, filters):
        """Pil değişim grafiği oluştur"""
        from database_models import Pil
        
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Pil).limit(self.MAX_RECORDS_LIMIT)
                piller = query.all()
                
                # Pil yaşlarını hesapla
                ages = []
                for pil in piller:
                    if pil.degisim_tarihi:
                        age = (datetime.now() - pil.degisim_tarihi).days
                        if 0 <= age <= 3650:  # Maksimum 10 yıl
                            ages.append(age)
                
                if ages:
                    # Histogram oluştur
                    ax.hist(ages, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                    ax.set_xlabel('Pil Yaşı (Gün)')
                    ax.set_ylabel('Pil Sayısı')
                    ax.grid(True, alpha=0.3)
                else:
                    ax.text(0.5, 0.5, 'Pil verisi bulunamadı', ha='center', va='center', transform=ax.transAxes)
        except Exception as e:
            self.logger.error(f"Error creating pil chart: {e}")
            ax.text(0.5, 0.5, 'Grafik oluşturulamadı', ha='center', va='center', transform=ax.transAxes)
    
    def _create_teknisyen_chart(self, ax, filters):
        """Teknisyen performans grafiği oluştur"""
        from database_models import Bakim
        
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Bakim).filter(
                    Bakim.bakim_yapan.isnot(None)
                ).limit(self.MAX_RECORDS_LIMIT)
                
                bakimlar = query.all()
                
                # Teknisyen bazında grupla
                teknisyen_data = {}
                for bakim in bakimlar:
                    if bakim.bakim_yapan:
                        teknisyen = bakim.bakim_yapan[:50]  # Maksimum 50 karakter
                        teknisyen_data[teknisyen] = teknisyen_data.get(teknisyen, 0) + 1
                
                if teknisyen_data:
                    # En çok çalışan 10 teknisyeni al
                    sorted_data = sorted(teknisyen_data.items(), key=lambda x: x[1], reverse=True)[:10]
                    
                    teknisyenler = [item[0] for item in sorted_data]
                    counts = [item[1] for item in sorted_data]
                    
                    ax.bar(teknisyenler, counts, color='lightgreen', edgecolor='black')
                    ax.set_xlabel('Teknisyen')
                    ax.set_ylabel('Bakım Sayısı')
                    
                    # X ekseni etiketlerini döndür
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                else:
                    ax.text(0.5, 0.5, 'Teknisyen verisi bulunamadı', ha='center', va='center', transform=ax.transAxes)
        except Exception as e:
            self.logger.error(f"Error creating teknisyen chart: {e}")
            ax.text(0.5, 0.5, 'Grafik oluşturulamadı', ha='center', va='center', transform=ax.transAxes)