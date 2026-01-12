#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Progress Indicator Yöneticisi
Uzun süren işlemler için progress bar ve loading indicator'ları
"""

import logging
import time
from typing import Optional, Callable, Any
from PyQt5.QtWidgets import (QProgressBar, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QDialog, QPushButton, QTextEdit, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QMovie, QPainter, QPen, QColor, QFont

class ProgressWorker(QThread):
    """Background işlemler için worker thread"""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress yüzdesi
    status_updated = pyqtSignal(str)    # Status mesajı
    finished = pyqtSignal(object)       # Sonuç
    error_occurred = pyqtSignal(str)    # Hata mesajı
    
    def __init__(self, task_function: Callable, *args, **kwargs):
        super().__init__()
        self.task_function = task_function
        self.args = args
        self.kwargs = kwargs
        self.is_cancelled = False
        
    def run(self):
        """Thread'i çalıştır"""
        try:
            # Progress callback'i ekle
            self.kwargs['progress_callback'] = self.update_progress
            self.kwargs['status_callback'] = self.update_status
            self.kwargs['cancel_check'] = self.is_task_cancelled
            
            # Task'ı çalıştır
            result = self.task_function(*self.args, **self.kwargs)
            
            if not self.is_cancelled:
                self.finished.emit(result)
                
        except Exception as e:
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def update_progress(self, value: int):
        """Progress güncelle"""
        if not self.is_cancelled:
            self.progress_updated.emit(value)
    
    def update_status(self, message: str):
        """Status güncelle"""
        if not self.is_cancelled:
            self.status_updated.emit(message)
    
    def is_task_cancelled(self) -> bool:
        """Task iptal edildi mi kontrol et"""
        return self.is_cancelled
    
    def cancel(self):
        """Task'ı iptal et"""
        self.is_cancelled = True
        self.quit()
        self.wait()

class LoadingSpinner(QWidget):
    """Dönen loading spinner widget'ı"""
    
    def __init__(self, parent=None, size=50):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.setFixedSize(size, size)
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start(self):
        """Spinner'ı başlat"""
        self.timer.start(50)  # 50ms interval
        self.show()
    
    def stop(self):
        """Spinner'ı durdur"""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """Spinner'ı döndür"""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Spinner'ı çiz"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 5
        
        # Draw spinning arcs
        for i in range(8):
            angle = self.angle + i * 45
            alpha = 255 - (i * 30)
            
            pen = QPen(QColor(76, 175, 80, alpha))
            pen.setWidth(3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Calculate arc position
            start_angle = angle * 16  # Qt uses 1/16 degrees
            span_angle = 30 * 16
            
            painter.drawArc(center_x - radius, center_y - radius, 
                          radius * 2, radius * 2, start_angle, span_angle)

class ProgressDialog(QDialog):
    """Progress dialog penceresi"""
    
    def __init__(self, parent=None, title="İşlem Devam Ediyor", 
                 message="Lütfen bekleyin...", cancellable=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(450, 200)
        
        # Worker thread
        self.worker = None
        self.result = None
        
        self.setup_ui(message, cancellable)
        self.setup_style()
    
    def setup_ui(self, message: str, cancellable: bool):
        """UI'ı oluştur"""
        layout = QVBoxLayout()
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Hazırlanıyor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Spinner ve progress bar container
        spinner_layout = QHBoxLayout()
        
        # Loading spinner
        self.spinner = LoadingSpinner(size=30)
        spinner_layout.addWidget(self.spinner)
        
        # Spacer
        spinner_layout.addStretch()
        
        # Cancel button
        if cancellable:
            self.cancel_button = QPushButton("❌ İptal")
            self.cancel_button.clicked.connect(self.cancel_task)
            spinner_layout.addWidget(self.cancel_button)
        
        layout.addLayout(spinner_layout)
        
        self.setLayout(layout)
    
    def setup_style(self):
        """Dialog stilini ayarla"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
                padding: 5px;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 8px;
                text-align: center;
                background-color: #3c3c3c;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
    
    def start_task(self, task_function: Callable, *args, **kwargs):
        """Task'ı başlat"""
        try:
            # Worker thread oluştur
            self.worker = ProgressWorker(task_function, *args, **kwargs)
            
            # Signal'ları bağla
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.status_updated.connect(self.update_status)
            self.worker.finished.connect(self.task_finished)
            self.worker.error_occurred.connect(self.task_error)
            
            # Spinner'ı başlat
            self.spinner.start()
            
            # Worker'ı başlat
            self.worker.start()
            
        except Exception as e:
            self.task_error(str(e))
    
    def update_progress(self, value: int):
        """Progress bar'ı güncelle"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message: str):
        """Status mesajını güncelle"""
        self.status_label.setText(message)
    
    def task_finished(self, result):
        """Task tamamlandığında"""
        self.spinner.stop()
        self.result = result
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Tamamlandı!")
        
        # 1 saniye bekle ve kapat
        QTimer.singleShot(1000, self.accept)
    
    def task_error(self, error_message: str):
        """Task hata verdiğinde"""
        self.spinner.stop()
        self.progress_bar.setValue(0)
        self.status_label.setText(f"❌ Hata: {error_message}")
        
        # Cancel button'ı Close yap
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setText("❌ Kapat")
            self.cancel_button.clicked.disconnect()
            self.cancel_button.clicked.connect(self.reject)
    
    def cancel_task(self):
        """Task'ı iptal et"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.spinner.stop()
            self.status_label.setText("❌ İptal edildi")
        
        self.reject()
    
    def get_result(self):
        """Task sonucunu al"""
        return self.result

class InlineProgressIndicator(QWidget):
    """Inline progress indicator (tablolar için)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Spinner
        self.spinner = LoadingSpinner(size=20)
        layout.addWidget(self.spinner)
        
        # Message
        self.message_label = QLabel("Yükleniyor...")
        self.message_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.message_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.hide()
    
    def show_loading(self, message: str = "Yükleniyor..."):
        """Loading göster"""
        self.message_label.setText(message)
        self.spinner.start()
        self.show()
    
    def hide_loading(self):
        """Loading gizle"""
        self.spinner.stop()
        self.hide()

class ProgressManager:
    """Progress indicator'ları yöneten sınıf"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_dialogs = []
        self.active_indicators = []
    
    def show_progress_dialog(self, parent=None, title="İşlem Devam Ediyor", 
                           message="Lütfen bekleyin...", cancellable=True) -> ProgressDialog:
        """Progress dialog göster"""
        try:
            dialog = ProgressDialog(parent, title, message, cancellable)
            self.active_dialogs.append(dialog)
            
            # Dialog kapandığında listeden çıkar
            dialog.finished.connect(lambda: self._remove_dialog(dialog))
            
            return dialog
            
        except Exception as e:
            self.logger.error(f"Show progress dialog error: {e}")
            return None
    
    def _remove_dialog(self, dialog: ProgressDialog):
        """Dialog'u listeden çıkar"""
        if dialog in self.active_dialogs:
            self.active_dialogs.remove(dialog)
    
    def create_inline_indicator(self, parent=None) -> InlineProgressIndicator:
        """Inline progress indicator oluştur"""
        try:
            indicator = InlineProgressIndicator(parent)
            self.active_indicators.append(indicator)
            return indicator
            
        except Exception as e:
            self.logger.error(f"Create inline indicator error: {e}")
            return None
    
    def run_task_with_progress(self, parent, task_function: Callable, 
                             title="İşlem Devam Ediyor", message="Lütfen bekleyin...",
                             cancellable=True, *args, **kwargs):
        """Task'ı progress dialog ile çalıştır"""
        try:
            dialog = self.show_progress_dialog(parent, title, message, cancellable)
            
            if dialog:
                dialog.start_task(task_function, *args, **kwargs)
                
                # Dialog'u göster ve sonucu bekle
                if dialog.exec_() == QDialog.Accepted:
                    return True, dialog.get_result()
                else:
                    return False, "İşlem iptal edildi"
            else:
                return False, "Progress dialog oluşturulamadı"
                
        except Exception as e:
            self.logger.error(f"Run task with progress error: {e}")
            return False, str(e)
    
    def close_all_dialogs(self):
        """Tüm aktif dialog'ları kapat"""
        try:
            for dialog in self.active_dialogs[:]:  # Copy list to avoid modification during iteration
                if dialog.worker and dialog.worker.isRunning():
                    dialog.worker.cancel()
                dialog.close()
            
            self.active_dialogs.clear()
            
        except Exception as e:
            self.logger.error(f"Close all dialogs error: {e}")
    
    def hide_all_indicators(self):
        """Tüm inline indicator'ları gizle"""
        try:
            for indicator in self.active_indicators:
                indicator.hide_loading()
                
        except Exception as e:
            self.logger.error(f"Hide all indicators error: {e}")

# Örnek task fonksiyonları
def example_long_task(duration=5, progress_callback=None, status_callback=None, cancel_check=None):
    """Örnek uzun süren task"""
    for i in range(duration * 10):
        # İptal kontrolü
        if cancel_check and cancel_check():
            return "Task cancelled"
        
        # Progress güncelle
        if progress_callback:
            progress_callback(int((i + 1) / (duration * 10) * 100))
        
        # Status güncelle
        if status_callback:
            status_callback(f"İşlem adımı {i + 1}/{duration * 10}")
        
        # Simulate work
        time.sleep(0.1)
    
    return "Task completed successfully"

def example_data_export_task(data_count=1000, progress_callback=None, status_callback=None, cancel_check=None):
    """Örnek veri dışa aktarma task'ı"""
    exported_count = 0
    
    for i in range(data_count):
        # İptal kontrolü
        if cancel_check and cancel_check():
            return f"Export cancelled. {exported_count} records exported."
        
        # Simulate data processing
        time.sleep(0.001)  # Very short delay
        exported_count += 1
        
        # Progress güncelle (her 50 kayıtta bir)
        if i % 50 == 0:
            if progress_callback:
                progress_callback(int((i + 1) / data_count * 100))
            
            if status_callback:
                status_callback(f"Dışa aktarılan kayıt: {exported_count}/{data_count}")
    
    return f"Export completed. {exported_count} records exported."

# Test fonksiyonu
def test_progress_manager():
    """Progress manager'ı test et"""
    print("🧪 Progress Manager Test Başlıyor...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
        
        app = QApplication([])
        
        # Test penceresi
        window = QMainWindow()
        window.setWindowTitle("Progress Manager Test")
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Progress manager
        progress_manager = ProgressManager()
        
        # Test butonları
        def test_dialog():
            success, result = progress_manager.run_task_with_progress(
                window, example_long_task, 
                title="Test Task", 
                message="Test işlemi çalışıyor...",
                duration=3
            )
            print(f"Dialog test result: {success}, {result}")
        
        def test_export():
            success, result = progress_manager.run_task_with_progress(
                window, example_data_export_task,
                title="Veri Dışa Aktarma",
                message="Veriler dışa aktarılıyor...",
                data_count=500
            )
            print(f"Export test result: {success}, {result}")
        
        dialog_btn = QPushButton("Test Progress Dialog")
        dialog_btn.clicked.connect(test_dialog)
        layout.addWidget(dialog_btn)
        
        export_btn = QPushButton("Test Export Progress")
        export_btn.clicked.connect(test_export)
        layout.addWidget(export_btn)
        
        # Inline indicator test
        inline_indicator = progress_manager.create_inline_indicator()
        layout.addWidget(inline_indicator)
        
        def test_inline():
            inline_indicator.show_loading("Test yükleniyor...")
            QTimer.singleShot(3000, inline_indicator.hide_loading)
        
        inline_btn = QPushButton("Test Inline Indicator")
        inline_btn.clicked.connect(test_inline)
        layout.addWidget(inline_btn)
        
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)
        
        window.show()
        
        print("✅ Progress Manager testi başarılı!")
        print("Test penceresini kapatmak için butonları test edin.")
        
        # app.exec_()  # Uncomment to run the test GUI
        
    except Exception as e:
        print(f"❌ Progress Manager testi başarısız: {e}")

if __name__ == "__main__":
    test_progress_manager()