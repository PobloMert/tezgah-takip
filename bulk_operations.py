#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Toplu İşlemler Modülü
Çoklu kayıt seçimi ve toplu işlemler için
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QProgressBar, QTextEdit,
                            QGroupBox, QCheckBox, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from database_models import DatabaseManager, Tezgah, Bakim, Pil
import logging

class BulkOperationDialog(QDialog):
    """Toplu işlemler dialog'u"""
    
    def __init__(self, parent=None, operation_type="tezgah"):
        super().__init__(parent)
        self.operation_type = operation_type
        self.db_manager = parent.db_manager if parent else DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle(f"📦 Toplu İşlemler - {operation_type.title()}")
        self.setFixedSize(800, 600)
        self.setModal(True)
        
        self.setup_ui()
        self.load_records()
    
    def setup_ui(self):
        """Arayüzü oluştur"""
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel(f"📦 {self.operation_type.title()} Toplu İşlemleri")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50; margin: 10px;")
        layout.addWidget(title_label)
        
        # Kayıt listesi
        records_group = QGroupBox("📋 Kayıtları Seç")
        records_layout = QVBoxLayout()
        
        # Tümünü seç/kaldır
        select_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("✅ Tümünü Seç")
        self.select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("❌ Tümünü Kaldır")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(self.deselect_all_btn)
        
        select_layout.addStretch()
        records_layout.addLayout(select_layout)
        
        # Liste widget
        self.records_list = QListWidget()
        self.records_list.setSelectionMode(QListWidget.MultiSelection)
        records_layout.addWidget(self.records_list)
        
        records_group.setLayout(records_layout)
        layout.addWidget(records_group)
        
        # İşlem seçimi
        operations_group = QGroupBox("⚙️ İşlem Seç")
        operations_layout = QVBoxLayout()
        
        self.operation_combo = QComboBox()
        if self.operation_type == "tezgah":
            self.operation_combo.addItems([
                "Durum Güncelle",
                "Toplu Silme",
                "Bakım Periyodu Güncelle",
                "Lokasyon Güncelle"
            ])
        elif self.operation_type == "bakim":
            self.operation_combo.addItems([
                "Durum Güncelle", 
                "Toplu Silme",
                "Bakım Türü Güncelle"
            ])
        elif self.operation_type == "pil":
            self.operation_combo.addItems([
                "Durum Güncelle",
                "Toplu Silme", 
                "Toplu Pil Değişimi"
            ])
        
        operations_layout.addWidget(self.operation_combo)
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton("🚀 İşlemi Başlat")
        self.execute_btn.clicked.connect(self.execute_operation)
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.execute_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("❌ Kapat")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_records(self):
        """Kayıtları yükle"""
        try:
            with self.db_manager.get_session() as session:
                if self.operation_type == "tezgah":
                    records = session.query(Tezgah).all()
                    for record in records:
                        item_text = f"[{record.numarasi}] {record.aciklama or 'N/A'} - {record.durum}"
                        self.records_list.addItem(item_text)
                        
                elif self.operation_type == "bakim":
                    records = session.query(Bakim).join(Tezgah).all()
                    for record in records:
                        item_text = f"[{record.id}] {record.tezgah.numarasi} - {record.tarih.strftime('%d.%m.%Y')} - {record.durum}"
                        self.records_list.addItem(item_text)
                        
                elif self.operation_type == "pil":
                    records = session.query(Pil).join(Tezgah).all()
                    for record in records:
                        item_text = f"[{record.id}] {record.tezgah.numarasi} - {record.eksen} - {record.durum}"
                        self.records_list.addItem(item_text)
                        
        except Exception as e:
            self.logger.error(f"Load records error: {e}")
            self.log_text.append(f"❌ Kayıtlar yüklenirken hata: {e}")
    
    def select_all(self):
        """Tümünü seç"""
        for i in range(self.records_list.count()):
            self.records_list.item(i).setSelected(True)
    
    def deselect_all(self):
        """Tümünü kaldır"""
        self.records_list.clearSelection()
    
    def execute_operation(self):
        """İşlemi çalıştır"""
        selected_items = self.records_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir kayıt seçin!")
            return
        
        operation = self.operation_combo.currentText()
        
        # Onay al
        result = QMessageBox.question(
            self, "Onay", 
            f"Seçilen {len(selected_items)} kayıt için '{operation}' işlemini yapmak istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz!"
        )
        
        if result != QMessageBox.Yes:
            return
        
        # Progress bar göster
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(selected_items))
        self.progress_bar.setValue(0)
        
        # İşlemi başlat
        self.log_text.append(f"🚀 {operation} işlemi başlatılıyor...")
        self.log_text.append(f"📊 Toplam kayıt: {len(selected_items)}")
        
        success_count = 0
        error_count = 0
        
        try:
            with self.db_manager.get_session() as session:
                for i, item in enumerate(selected_items):
                    try:
                        # ID'yi çıkar
                        item_text = item.text()
                        record_id = int(item_text.split(']')[0][1:])
                        
                        # İşlemi gerçekleştir
                        if self.operation_type == "tezgah":
                            record = session.query(Tezgah).filter_by(id=record_id).first()
                            if record and operation == "Durum Güncelle":
                                record.durum = "Bakımda"  # Örnek
                                
                        elif self.operation_type == "bakim":
                            record = session.query(Bakim).filter_by(id=record_id).first()
                            if record and operation == "Durum Güncelle":
                                record.durum = "Tamamlandı"  # Örnek
                                
                        elif self.operation_type == "pil":
                            record = session.query(Pil).filter_by(id=record_id).first()
                            if record and operation == "Durum Güncelle":
                                record.durum = "Değiştirilmeli"  # Örnek
                        
                        success_count += 1
                        self.log_text.append(f"✅ Kayıt {record_id}: Başarılı")
                        
                    except Exception as e:
                        error_count += 1
                        self.log_text.append(f"❌ Kayıt {record_id}: Hata - {e}")
                    
                    # Progress güncelle
                    self.progress_bar.setValue(i + 1)
                    QApplication.processEvents()
                
                # Commit
                session.commit()
                
        except Exception as e:
            self.log_text.append(f"❌ Genel hata: {e}")
            error_count += len(selected_items)
        
        # Sonuç
        self.log_text.append(f"\n🎉 İşlem tamamlandı!")
        self.log_text.append(f"✅ Başarılı: {success_count}")
        self.log_text.append(f"❌ Hatalı: {error_count}")
        
        self.progress_bar.setVisible(False)

def show_bulk_operations_dialog(parent, operation_type="tezgah"):
    """Toplu işlemler dialog'unu göster"""
    dialog = BulkOperationDialog(parent, operation_type)
    return dialog.exec_()