#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper Transcriber - Главный файл запуска
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from gui.main_window import MainWindow


def main():
    """Точка входа в приложение"""
    # Включаем высокое разрешение для экранов
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Whisper Transcriber")
    app.setOrganizationName("WhisperTranscriber")
    
    # Устанавливаем стиль
    app.setStyle('Fusion')
    
    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()