"""
progress_widget.py - Виджет отображения прогресса выполнения задач
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import Qt


class ProgressWidget(QWidget):
    """Виджет с прогресс-баром и меткой состояния"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setVisible(False)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)
        
        self.setLayout(layout)
    
    def start_progress(self):
        """Показывает и сбрасывает прогресс"""
        self.progress_bar.setValue(0)
        self.setVisible(True)
    
    def update_progress(self, current: int, total: int, label: str = ""):
        """Обновляет прогресс"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        if label:
            self.progress_label.setText(label)
    
    def finish_progress(self):
        """Скрывает прогресс-бар"""
        self.setVisible(False)
        self.progress_label.setText("")
    
    def set_enabled(self, enabled: bool):
        """Включает/выключает виджет"""
        self.setVisible(enabled)