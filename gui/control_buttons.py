"""
control_buttons.py - Кнопки управления этапами обработки
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal


class ControlButtons(QWidget):
    """Четыре кнопки управления: Подготовка, Распознавание, Постобработка, Выполнить всё"""
    
    prepare_clicked = pyqtSignal()
    transcribe_clicked = pyqtSignal()
    postprocess_clicked = pyqtSignal()  # НОВАЯ КНОПКА
    full_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.prepare_btn = QPushButton("1. ПОДГОТОВКА")
        self.prepare_btn.setMinimumHeight(50)
        self.prepare_btn.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white;")
        self.prepare_btn.clicked.connect(self.prepare_clicked.emit)
        
        self.transcribe_btn = QPushButton("2. РАСПОЗНАВАНИЕ")
        self.transcribe_btn.setMinimumHeight(50)
        self.transcribe_btn.setStyleSheet("font-weight: bold; background-color: #FF9800; color: white;")
        self.transcribe_btn.clicked.connect(self.transcribe_clicked.emit)
        
        self.postprocess_btn = QPushButton("3. ПОСТОБРАБОТКА")  # НОВАЯ
        self.postprocess_btn.setMinimumHeight(50)
        self.postprocess_btn.setStyleSheet("font-weight: bold; background-color: #9C27B0; color: white;")
        self.postprocess_btn.clicked.connect(self.postprocess_clicked.emit)
        
        self.full_btn = QPushButton("4. ВЫПОЛНИТЬ ВСЁ")
        self.full_btn.setMinimumHeight(50)
        self.full_btn.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        self.full_btn.clicked.connect(self.full_clicked.emit)
        
        layout.addWidget(self.prepare_btn)
        layout.addWidget(self.transcribe_btn)
        layout.addWidget(self.postprocess_btn)
        layout.addWidget(self.full_btn)
        
        self.setLayout(layout)
    
    def set_enabled(self, enabled: bool):
        """Включает/выключает все кнопки"""
        self.prepare_btn.setEnabled(enabled)
        self.transcribe_btn.setEnabled(enabled)
        self.postprocess_btn.setEnabled(enabled)
        self.full_btn.setEnabled(enabled)