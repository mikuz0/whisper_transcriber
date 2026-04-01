"""
logger.py - Модуль логирования для GUI приложения Whisper Transcriber
Обеспечивает отправку сообщений из рабочих потоков в главное окно через сигналы
"""

from PyQt5.QtCore import QObject, pyqtSignal


class GUILogger(QObject):
    """
    Логгер для GUI приложения.
    Отправляет сообщения через сигнал log_signal, который должен быть подключен
    к слоту отображения в главном окне.
    
    Уровни логирования:
    - info: обычные информационные сообщения
    - success: успешное выполнение операций
    - warning: предупреждения (не критические проблемы)
    - error: ошибки
    """
    
    # Сигнал: (message: str, level: str)
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        """Инициализация логгера"""
        super().__init__()
    
    def log(self, message: str, level: str = 'info'):
        """
        Отправляет сообщение с указанным уровнем
        
        Args:
            message: текст сообщения
            level: уровень логирования ('info', 'success', 'warning', 'error')
        """
        self.log_signal.emit(message, level)
    
    def info(self, message: str):
        """
        Отправляет информационное сообщение
        
        Args:
            message: текст сообщения
        """
        self.log_signal.emit(message, 'info')
    
    def success(self, message: str):
        """
        Отправляет сообщение об успешной операции
        
        Args:
            message: текст сообщения
        """
        self.log_signal.emit(message, 'success')
    
    def warning(self, message: str):
        """
        Отправляет предупреждение
        
        Args:
            message: текст сообщения
        """
        self.log_signal.emit(message, 'warning')
    
    def error(self, message: str):
        """
        Отправляет сообщение об ошибке
        
        Args:
            message: текст сообщения
        """
        self.log_signal.emit(message, 'error')
    
    def get_callback(self):
        """
        Возвращает функцию обратного вызова для использования в других модулях
        (например, в AudioPreparer или WhisperTranscriber)
        
        Returns:
            callable: функция с сигнатурой (message, level)
        """
        return self.log