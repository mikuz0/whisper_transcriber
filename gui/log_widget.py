"""
Виджет для отображения логов с цветовой подсветкой
"""

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt


class LogWidget(QTextEdit):
    """Виджет для отображения сообщений лога с цветовой кодировкой"""
    
    # Цвета для разных уровней логирования
    COLOR_MAP = {
        'info': 'black',
        'success': 'green',
        'warning': 'orange',
        'error': 'red'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(300)
        self.setFontFamily("Courier New")
        self.setStyleSheet("background-color: #f5f5f5;")
    
    def append_message(self, message: str, level: str = 'info'):
        """
        Добавляет сообщение в лог с соответствующим цветом
        
        Args:
            message: текст сообщения
            level: уровень ('info', 'success', 'warning', 'error')
        """
        color = self.COLOR_MAP.get(level, 'black')
        formatted = f'<span style="color:{color};">{message}</span>'
        self.append(formatted)
        
        # Автопрокрутка вниз
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Очищает лог"""
        self.clear()