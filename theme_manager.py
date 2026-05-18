#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Tema Yöneticisi
Açık ve Koyu tema desteği
"""
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    @staticmethod
    def get_dark_palette():
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        return dark_palette

    @staticmethod
    def get_dark_stylesheet():
        return """
            QMainWindow { background-color: #2d2d2d; }
            QTabWidget::pane { border: 1px solid #444; top: -1px; background: #2d2d2d; }
            QTabBar::tab { background: #3d3d3d; color: #bbb; padding: 10px; border: 1px solid #444; }
            QTabBar::tab:selected { background: #2d2d2d; color: white; border-bottom-color: #2d2d2d; }
            QPushButton { background-color: #4CAF50; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #45a049; }
            QLineEdit, QTextEdit, QComboBox, QDateEdit { background-color: #3d3d3d; color: white; border: 1px solid #555; border-radius: 3px; padding: 5px; }
            QTableWidget { background-color: #3d3d3d; color: white; gridline-color: #555; }
            QHeaderView::section { background-color: #454545; color: white; padding: 5px; border: 1px solid #555; }
        """
