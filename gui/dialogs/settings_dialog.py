"""
settings_dialog.py - Главное окно настроек с вкладками
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from .model_dialog import ModelDialog
from .formats_dialog import FormatsDialog
from .postprocess_dialog import PostprocessDialog


class SettingsDialog(QDialog):
    """Главное окно настроек с вкладками"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setWindowTitle("Настройки")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Создаём вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка: Модель Whisper
        self.model_tab = ModelDialog(self.config, parent=self, embedded=True)
        self.tab_widget.addTab(self.model_tab, "Модель Whisper")
        
        # Вкладка: Форматы вывода
        self.formats_tab = FormatsDialog(self.config, parent=self, embedded=True)
        self.tab_widget.addTab(self.formats_tab, "Форматы вывода")
        
        # Вкладка: Постобработка
        self.postprocess_tab = PostprocessDialog(self.config, parent=self, embedded=True)
        self.tab_widget.addTab(self.postprocess_tab, "Постобработка")
        
        layout.addWidget(self.tab_widget)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_settings(self):
        """Загружает настройки во вкладки"""
        self.model_tab.load_settings()
        self.formats_tab.load_settings()
        self.postprocess_tab.load_settings()
    
    def accept(self):
        """Сохраняет настройки и закрывает окно"""
        self.model_tab.save_settings()
        self.formats_tab.save_settings()
        self.postprocess_tab.save_settings()
        super().accept()