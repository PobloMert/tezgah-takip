#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Validasyon UI Yardımcısı
Hatalı girişler için anlık görsel geri bildirim
"""
class ValidationUIHelper:
    @staticmethod
    def set_error_state(widget, has_error=True):
        if has_error:
            widget.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee; color: #000000;")
        else:
            widget.setStyleSheet("") # Varsayılan stile dön

    @staticmethod
    def show_smart_error(parent, title, message, solution=None):
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        if solution:
            msg.setInformativeText(f"Önerilen Çözüm: {solution}")
        msg.setStyleSheet("QLabel{min-width: 300px; color: #000000;}")
        msg.exec_()
