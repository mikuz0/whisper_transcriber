#!/usr/bin/env python3
"""
Whisper Transcriber - GUI приложение для распознавания речи
с поддержкой видео/аудио файлов
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Добавляем корень проекта в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    app.setApplicationName("Whisper Transcriber")
    app.setOrganizationName("WhisperTools")
    
    # Устанавливаем стиль для лучшего вида (опционально)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()