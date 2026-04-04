"""
confirmation_dialog.py - Диалоги подтверждения для пользователя
"""

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal


class ConfirmationDialogs(QObject):
    """Класс для отображения диалогов подтверждения"""
    
    prepare_confirmed = pyqtSignal(bool)
    transcribe_confirmed = pyqtSignal(bool)
    postprocess_confirmed = pyqtSignal(bool)
    full_confirmed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
    
    def ask_prepare_confirmation(self) -> bool:
        reply = QMessageBox.question(
            self.parent, "Подтверждение подготовки",
            "Перезаписывать существующие файлы в кэше?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        if reply == QMessageBox.Cancel:
            return None
        return reply == QMessageBox.Yes
    
    def ask_transcribe_confirmation(self) -> bool:
        reply = QMessageBox.question(
            self.parent, "Подтверждение распознавания",
            "Перезаписывать существующие текстовые файлы в папке 'text'?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        if reply == QMessageBox.Cancel:
            return None
        return reply == QMessageBox.Yes
    
    def ask_postprocess_confirmation(self) -> bool:
        reply = QMessageBox.question(
            self.parent, "Подтверждение постобработки",
            "Перезаписывать существующие файлы в папке 'text_processed'?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        if reply == QMessageBox.Cancel:
            return None
        return reply == QMessageBox.Yes
    
    def ask_full_confirmation(self) -> bool:
        reply = QMessageBox.question(
            self.parent, "Подтверждение полного процесса",
            "Перезаписывать существующие файлы (кэш, сырые тексты, обработанные тексты)?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        if reply == QMessageBox.Cancel:
            return None
        return reply == QMessageBox.Yes
    
    def show_warning(self, title: str, message: str):
        QMessageBox.warning(self.parent, title, message)
    
    def show_error(self, title: str, message: str):
        QMessageBox.critical(self.parent, title, message)
