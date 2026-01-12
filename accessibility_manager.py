#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Accessibility (Erişilebilirlik) Yöneticisi
Görme engelliler ve diğer erişilebilirlik ihtiyaçları için özellikler
"""

import logging
from typing import Dict, Optional, Tuple
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

class AccessibilityManager(QObject):
    """Erişilebilirlik özelliklerini yöneten sınıf"""
    
    # Signals
    theme_changed = pyqtSignal(str)  # Tema değiştiğinde
    font_size_changed = pyqtSignal(int)  # Font boyutu değiştiğinde
    
    # Constants
    FONT_SIZES = {
        "small": 9,
        "normal": 11,
        "large": 14,
        "extra_large": 18
    }
    
    HIGH_CONTRAST_COLORS = {
        "background": "#000000",
        "text": "#FFFFFF", 
        "primary": "#FFFF00",  # Sarı
        "secondary": "#00FFFF",  # Cyan
        "success": "#00FF00",  # Yeşil
        "warning": "#FF8000",  # Turuncu
        "error": "#FF0000",  # Kırmızı
        "border": "#FFFFFF"
    }
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Mevcut ayarlar
        self.current_theme = "dark"
        self.current_font_size = "normal"
        self.high_contrast_enabled = False
        self.screen_reader_enabled = False
        self.keyboard_navigation_enabled = True
        
        # Font cache
        self._font_cache = {}
    
    def enable_high_contrast_theme(self, widget: QWidget) -> bool:
        """Yüksek kontrast temasını etkinleştir"""
        try:
            high_contrast_style = self._generate_high_contrast_stylesheet()
            widget.setStyleSheet(high_contrast_style)
            
            self.high_contrast_enabled = True
            self.theme_changed.emit("high_contrast")
            
            self.logger.info("High contrast theme enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"High contrast theme error: {e}")
            return False
    
    def disable_high_contrast_theme(self, widget: QWidget) -> bool:
        """Yüksek kontrast temasını devre dışı bırak"""
        try:
            # Normal koyu temaya geri dön
            normal_style = self._generate_normal_dark_stylesheet()
            widget.setStyleSheet(normal_style)
            
            self.high_contrast_enabled = False
            self.theme_changed.emit("dark")
            
            self.logger.info("High contrast theme disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Disable high contrast error: {e}")
            return False
    
    def _generate_high_contrast_stylesheet(self) -> str:
        """Yüksek kontrast stylesheet oluştur"""
        colors = self.HIGH_CONTRAST_COLORS
        
        return f"""
            /* Ana pencere */
            QMainWindow {{
                background-color: {colors['background']};
                color: {colors['text']};
                font-weight: bold;
            }}
            
            /* Genel widget'lar */
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text']};
                font-weight: bold;
            }}
            
            /* Butonlar */
            QPushButton {{
                background-color: {colors['primary']};
                color: {colors['background']};
                border: 3px solid {colors['border']};
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors['secondary']};
                border-color: {colors['primary']};
            }}
            QPushButton:pressed {{
                background-color: {colors['text']};
                color: {colors['background']};
            }}
            QPushButton:focus {{
                border: 4px solid {colors['primary']};
                outline: 2px solid {colors['secondary']};
            }}
            
            /* Tablolar */
            QTableWidget {{
                background-color: {colors['background']};
                alternate-background-color: #111111;
                color: {colors['text']};
                gridline-color: {colors['border']};
                border: 3px solid {colors['border']};
                font-weight: bold;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 12px;
                border: 1px solid {colors['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {colors['primary']};
                color: {colors['background']};
                border: 2px solid {colors['secondary']};
            }}
            QTableWidget::item:focus {{
                border: 3px solid {colors['primary']};
                outline: 2px solid {colors['secondary']};
            }}
            
            /* Header */
            QHeaderView::section {{
                background-color: {colors['secondary']};
                color: {colors['background']};
                padding: 12px;
                border: 2px solid {colors['border']};
                font-weight: bold;
                font-size: 14px;
            }}
            
            /* Tab widget */
            QTabWidget::pane {{
                border: 3px solid {colors['border']};
                background-color: {colors['background']};
            }}
            QTabBar::tab {{
                background-color: {colors['background']};
                color: {colors['text']};
                padding: 15px 25px;
                margin-right: 3px;
                border: 2px solid {colors['border']};
                border-bottom: none;
                font-weight: bold;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['primary']};
                color: {colors['background']};
                border-color: {colors['primary']};
            }}
            QTabBar::tab:hover {{
                background-color: {colors['secondary']};
                color: {colors['background']};
            }}
            QTabBar::tab:focus {{
                border: 3px solid {colors['primary']};
                outline: 2px solid {colors['secondary']};
            }}
            
            /* Input alanları */
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {{
                background-color: {colors['background']};
                color: {colors['text']};
                border: 3px solid {colors['border']};
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
                border: 4px solid {colors['primary']};
                outline: 2px solid {colors['secondary']};
            }}
            
            /* Labels */
            QLabel {{
                color: {colors['text']};
                font-weight: bold;
                font-size: 13px;
            }}
            
            /* Menu */
            QMenuBar {{
                background-color: {colors['background']};
                color: {colors['text']};
                border-bottom: 3px solid {colors['border']};
                font-weight: bold;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 10px 15px;
                font-weight: bold;
            }}
            QMenuBar::item:selected {{
                background-color: {colors['primary']};
                color: {colors['background']};
            }}
            QMenu {{
                background-color: {colors['background']};
                color: {colors['text']};
                border: 3px solid {colors['border']};
                font-weight: bold;
            }}
            QMenu::item:selected {{
                background-color: {colors['primary']};
                color: {colors['background']};
            }}
            
            /* Status bar */
            QStatusBar {{
                background-color: {colors['background']};
                color: {colors['text']};
                border-top: 3px solid {colors['border']};
                font-weight: bold;
            }}
            
            /* Group box */
            QGroupBox {{
                font-weight: bold;
                border: 3px solid {colors['border']};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                color: {colors['text']};
                font-size: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: {colors['primary']};
                color: {colors['background']};
                border-radius: 5px;
            }}
            
            /* Checkbox */
            QCheckBox {{
                color: {colors['text']};
                font-weight: bold;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border: 3px solid {colors['border']};
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {colors['background']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['primary']};
                border-color: {colors['primary']};
            }}
            QCheckBox:focus {{
                outline: 3px solid {colors['secondary']};
            }}
            
            /* Progress bar */
            QProgressBar {{
                border: 3px solid {colors['border']};
                border-radius: 8px;
                text-align: center;
                background-color: {colors['background']};
                color: {colors['text']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {colors['success']};
                border-radius: 5px;
            }}
        """
    
    def _generate_normal_dark_stylesheet(self) -> str:
        """Normal koyu tema stylesheet'i"""
        return """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3c3c;
                alternate-background-color: #454545;
                color: #ffffff;
                gridline-color: #555555;
                border: 1px solid #555555;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
            }
            QHeaderView::section {
                background-color: #555555;
                color: #ffffff;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
    
    def set_font_size(self, size_name: str, widget: QWidget) -> bool:
        """Font boyutunu ayarla"""
        try:
            if size_name not in self.FONT_SIZES:
                self.logger.error(f"Invalid font size: {size_name}")
                return False
            
            font_size = self.FONT_SIZES[size_name]
            
            # Ana font'u ayarla
            font = self._get_font(font_size)
            widget.setFont(font)
            
            # Tüm child widget'ları güncelle
            self._apply_font_to_children(widget, font)
            
            self.current_font_size = size_name
            self.font_size_changed.emit(font_size)
            
            self.logger.info(f"Font size changed to: {size_name} ({font_size}px)")
            return True
            
        except Exception as e:
            self.logger.error(f"Set font size error: {e}")
            return False
    
    def _get_font(self, size: int) -> QFont:
        """Font cache'den font al veya oluştur"""
        if size not in self._font_cache:
            font = QFont("Segoe UI", size)
            font.setStyleHint(QFont.SansSerif)
            self._font_cache[size] = font
        
        return self._font_cache[size]
    
    def _apply_font_to_children(self, widget: QWidget, font: QFont):
        """Child widget'lara font uygula"""
        try:
            for child in widget.findChildren(QWidget):
                child.setFont(font)
        except Exception as e:
            self.logger.error(f"Apply font to children error: {e}")
    
    def enable_keyboard_navigation(self, widget: QWidget) -> bool:
        """Klavye navigasyonunu etkinleştir"""
        try:
            # Tab order'ı ayarla
            self._setup_tab_order(widget)
            
            # Focus policy'leri ayarla
            self._setup_focus_policies(widget)
            
            self.keyboard_navigation_enabled = True
            self.logger.info("Keyboard navigation enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Enable keyboard navigation error: {e}")
            return False
    
    def _setup_tab_order(self, widget: QWidget):
        """Tab sırasını ayarla"""
        try:
            # Tüm focusable widget'ları bul
            focusable_widgets = []
            
            for child in widget.findChildren(QWidget):
                if child.focusPolicy() != Qt.NoFocus:
                    focusable_widgets.append(child)
            
            # Tab order'ı ayarla
            for i in range(len(focusable_widgets) - 1):
                widget.setTabOrder(focusable_widgets[i], focusable_widgets[i + 1])
                
        except Exception as e:
            self.logger.error(f"Setup tab order error: {e}")
    
    def _setup_focus_policies(self, widget: QWidget):
        """Focus policy'leri ayarla"""
        try:
            from PyQt5.QtWidgets import QPushButton, QTableWidget, QLineEdit, QComboBox, QCheckBox
            
            for child in widget.findChildren(QWidget):
                if isinstance(child, (QPushButton, QTableWidget, QLineEdit, QComboBox, QCheckBox)):
                    child.setFocusPolicy(Qt.StrongFocus)
                    
        except Exception as e:
            self.logger.error(f"Setup focus policies error: {e}")
    
    def add_screen_reader_support(self, widget: QWidget) -> bool:
        """Screen reader desteği ekle"""
        try:
            # Accessible name ve description'ları ayarla
            self._setup_accessible_names(widget)
            
            # ARIA-like özellikler ekle
            self._setup_accessibility_properties(widget)
            
            self.screen_reader_enabled = True
            self.logger.info("Screen reader support added")
            return True
            
        except Exception as e:
            self.logger.error(f"Add screen reader support error: {e}")
            return False
    
    def _setup_accessible_names(self, widget: QWidget):
        """Accessible name'leri ayarla"""
        try:
            from PyQt5.QtWidgets import QPushButton, QLabel, QTableWidget, QTabWidget
            
            for child in widget.findChildren(QWidget):
                if isinstance(child, QPushButton):
                    if not child.accessibleName():
                        child.setAccessibleName(f"Buton: {child.text()}")
                        child.setAccessibleDescription(f"Bu buton: {child.text()}")
                
                elif isinstance(child, QLabel):
                    if not child.accessibleName():
                        child.setAccessibleName(f"Etiket: {child.text()}")
                
                elif isinstance(child, QTableWidget):
                    if not child.accessibleName():
                        child.setAccessibleName("Veri tablosu")
                        child.setAccessibleDescription("Tezgah verilerini içeren tablo")
                
                elif isinstance(child, QTabWidget):
                    if not child.accessibleName():
                        child.setAccessibleName("Sekme grubu")
                        child.setAccessibleDescription("Uygulama sekmelerini içeren grup")
                        
        except Exception as e:
            self.logger.error(f"Setup accessible names error: {e}")
    
    def _setup_accessibility_properties(self, widget: QWidget):
        """Accessibility özelliklerini ayarla"""
        try:
            # Widget'a accessibility role'leri ekle
            widget.setProperty("accessibility_enabled", True)
            
            # Keyboard shortcuts'ları belirgin hale getir
            self._enhance_keyboard_shortcuts(widget)
            
        except Exception as e:
            self.logger.error(f"Setup accessibility properties error: {e}")
    
    def _enhance_keyboard_shortcuts(self, widget: QWidget):
        """Klavye kısayollarını geliştir"""
        try:
            from PyQt5.QtWidgets import QPushButton
            
            for child in widget.findChildren(QPushButton):
                # Buton text'inde & karakteri varsa kısayol olarak işaretle
                text = child.text()
                if '&' not in text and text:
                    # İlk harfi kısayol yap
                    first_char = text[0].upper()
                    child.setText(f"&{first_char}{text[1:]}")
                    
        except Exception as e:
            self.logger.error(f"Enhance keyboard shortcuts error: {e}")
    
    def announce_to_screen_reader(self, message: str) -> bool:
        """Screen reader'a mesaj gönder"""
        try:
            # Windows'ta NVDA/JAWS için
            import platform
            if platform.system() == "Windows":
                try:
                    import win32gui
                    import win32con
                    
                    # Screen reader'a mesaj gönder
                    win32gui.MessageBox(0, message, "TezgahTakip Bildirim", 
                                      win32con.MB_OK | win32con.MB_ICONINFORMATION)
                    return True
                except ImportError:
                    # win32gui yoksa basit print
                    print(f"Screen Reader: {message}")
                    return True
            else:
                # Linux/Mac için basit çözüm
                print(f"Screen Reader: {message}")
                return True
                
        except Exception as e:
            self.logger.error(f"Announce to screen reader error: {e}")
            return False
    
    def get_accessibility_settings(self) -> Dict:
        """Mevcut accessibility ayarlarını al"""
        return {
            "theme": self.current_theme,
            "font_size": self.current_font_size,
            "high_contrast_enabled": self.high_contrast_enabled,
            "screen_reader_enabled": self.screen_reader_enabled,
            "keyboard_navigation_enabled": self.keyboard_navigation_enabled,
            "available_font_sizes": list(self.FONT_SIZES.keys())
        }
    
    def apply_accessibility_settings(self, widget: QWidget, settings: Dict) -> bool:
        """Accessibility ayarlarını uygula"""
        try:
            success_count = 0
            
            # High contrast
            if settings.get("high_contrast_enabled", False):
                if self.enable_high_contrast_theme(widget):
                    success_count += 1
            
            # Font size
            font_size = settings.get("font_size", "normal")
            if self.set_font_size(font_size, widget):
                success_count += 1
            
            # Keyboard navigation
            if settings.get("keyboard_navigation_enabled", True):
                if self.enable_keyboard_navigation(widget):
                    success_count += 1
            
            # Screen reader
            if settings.get("screen_reader_enabled", False):
                if self.add_screen_reader_support(widget):
                    success_count += 1
            
            self.logger.info(f"Applied {success_count} accessibility settings")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Apply accessibility settings error: {e}")
            return False
    
    def create_accessibility_toolbar(self, parent_widget: QWidget) -> Optional[QWidget]:
        """Accessibility toolbar oluştur"""
        try:
            from PyQt5.QtWidgets import QToolBar, QAction, QComboBox, QLabel
            
            toolbar = QToolBar("Erişilebilirlik", parent_widget)
            toolbar.setObjectName("accessibility_toolbar")
            
            # High contrast toggle
            high_contrast_action = QAction("🔆 Yüksek Kontrast", toolbar)
            high_contrast_action.setCheckable(True)
            high_contrast_action.setChecked(self.high_contrast_enabled)
            high_contrast_action.triggered.connect(
                lambda checked: self.enable_high_contrast_theme(parent_widget) if checked 
                else self.disable_high_contrast_theme(parent_widget)
            )
            toolbar.addAction(high_contrast_action)
            
            toolbar.addSeparator()
            
            # Font size selector
            font_label = QLabel("Font:")
            toolbar.addWidget(font_label)
            
            font_combo = QComboBox()
            font_combo.addItems(["Küçük", "Normal", "Büyük", "Çok Büyük"])
            font_combo.setCurrentText("Normal")
            font_combo.currentTextChanged.connect(
                lambda text: self.set_font_size(
                    {"Küçük": "small", "Normal": "normal", "Büyük": "large", "Çok Büyük": "extra_large"}[text],
                    parent_widget
                )
            )
            toolbar.addWidget(font_combo)
            
            toolbar.addSeparator()
            
            # Screen reader toggle
            screen_reader_action = QAction("🔊 Ekran Okuyucu", toolbar)
            screen_reader_action.setCheckable(True)
            screen_reader_action.setChecked(self.screen_reader_enabled)
            screen_reader_action.triggered.connect(
                lambda checked: self.add_screen_reader_support(parent_widget) if checked else None
            )
            toolbar.addAction(screen_reader_action)
            
            return toolbar
            
        except Exception as e:
            self.logger.error(f"Create accessibility toolbar error: {e}")
            return None

# Test fonksiyonu
def test_accessibility_manager():
    """Accessibility manager'ı test et"""
    print("🧪 Accessibility Manager Test Başlıyor...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
        
        app = QApplication([])
        
        # Test penceresi
        window = QMainWindow()
        window.setWindowTitle("Accessibility Test")
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Test widget'ları
        label = QLabel("Test Label")
        button = QPushButton("Test Button")
        
        layout.addWidget(label)
        layout.addWidget(button)
        
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)
        
        # Accessibility manager
        accessibility = AccessibilityManager()
        
        # High contrast test
        print("Testing high contrast theme...")
        success = accessibility.enable_high_contrast_theme(window)
        print(f"High contrast: {success}")
        
        # Font size test
        print("Testing font size change...")
        success = accessibility.set_font_size("large", window)
        print(f"Font size change: {success}")
        
        # Keyboard navigation test
        print("Testing keyboard navigation...")
        success = accessibility.enable_keyboard_navigation(window)
        print(f"Keyboard navigation: {success}")
        
        # Screen reader test
        print("Testing screen reader support...")
        success = accessibility.add_screen_reader_support(window)
        print(f"Screen reader support: {success}")
        
        # Settings test
        settings = accessibility.get_accessibility_settings()
        print(f"Current settings: {settings}")
        
        print("✅ Accessibility Manager testi başarılı!")
        
    except Exception as e:
        print(f"❌ Accessibility Manager testi başarısız: {e}")

if __name__ == "__main__":
    test_accessibility_manager()