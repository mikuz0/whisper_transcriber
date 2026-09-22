"""
logger.py - Модуль логирования для GUI приложения
"""

from PyQt5.QtCore import QObject, pyqtSignal


class GUILogger(QObject):
    """Логгер для GUI приложения"""
    
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
    
    def log(self, message: str, level: str = 'info'):
        self.log_signal.emit(message, level)
    
    def info(self, message: str):
        self.log_signal.emit(message, 'info')
    
    def success(self, message: str):
        self.log_signal.emit(message, 'success')
    
    def warning(self, message: str):
        self.log_signal.emit(message, 'warning')
    
    def error(self, message: str):
        self.log_signal.emit(message, 'error')
    
    def debug(self, message: str):
        self.log_signal.emit(message, 'debug')
    
    def get_callback(self):
        return self.log