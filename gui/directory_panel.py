"""
Панель выбора рабочей директории
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal
from pathlib import Path


class DirectoryPanel(QWidget):
    """Панель для выбора и отображения рабочей директории"""
    
    directory_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_dir = ""
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Рабочая директория:"))
        
        self.dir_label = QLabel("Не выбрана")
        self.dir_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        layout.addWidget(self.dir_label, 1)
        
        self.select_btn = QPushButton("Выбрать")
        self.select_btn.clicked.connect(self.select_directory)
        layout.addWidget(self.select_btn)
        
        self.setLayout(layout)
    
    def select_directory(self):
        """Открывает диалог выбора папки"""
        current_dir = self.work_dir if self.work_dir else ""
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите рабочую директорию", current_dir
        )
        
        if directory:
            self.set_directory(directory)
    
    def set_directory(self, directory: str):
        """Устанавливает рабочую директорию"""
        self.work_dir = directory
        self.dir_label.setText(directory)
        self.directory_changed.emit(directory)
    
    def get_directory(self) -> str:
        """Возвращает текущую рабочую директорию"""
        return self.work_dir
    
    def clear(self):
        """Очищает выбранную директорию"""
        self.work_dir = ""
        self.dir_label.setText("Не выбрана")