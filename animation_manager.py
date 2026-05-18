#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Animasyon Yöneticisi
UI bileşenleri için akıcı geçişler
"""
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt5.QtWidgets import QGraphicsOpacityEffect

class AnimationManager:
    @staticmethod
    def fade_in(widget, duration=500):
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()
        return animation

    @staticmethod
    def slide_in(widget, start_pos, end_pos, duration=400):
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        return animation
