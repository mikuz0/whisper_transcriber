"""
stats_panel.py - Панель статистики файлов
"""

from PyQt5.QtWidgets import QLabel
from pathlib import Path

from core.file_scanner import FileScanner


class StatsPanel(QLabel):
    """Виджет для отображения статистики файлов в рабочей директории"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_dir = None
        self.setText("📁 Файлы: видео/аудио: 0 | кэш WAV: 0 | тексты: 0 | обработанные: 0")
        self.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f0f0f0; border-radius: 5px;")
    
    def set_work_directory(self, work_dir: str):
        """Устанавливает рабочую директорию и обновляет статистику"""
        self.work_dir = Path(work_dir) if work_dir else None
        self.update_stats()
    
    def update_stats(self):
        """Обновляет отображение статистики"""
        if not self.work_dir or not self.work_dir.exists():
            self.setText("📁 Файлы: видео/аудио: 0 | кэш WAV: 0 | тексты: 0 | обработанные: 0")
            return
        
        counts = FileScanner.count_files_in_directories(self.work_dir)
        
        # Проверяем наличие папки с обработанными текстами
        processed_dir = self.work_dir / 'text_processed'
        processed_count = len([f for f in processed_dir.glob('*') if f.is_file()]) if processed_dir.exists() else 0
        
        self.setText(
            f"📁 Файлы: видео/аудио: {counts['video_audio']} | "
            f"кэш WAV: {counts['audio_cache']} | "
            f"тексты: {counts['text']} | "
            f"обработанные: {processed_count}"
        )
        
        # Добавляем подсказку с информацией о папках
        self.setToolTip(
            f"video_audio: {counts['video_audio']} файлов\n"
            f"audio_cache: {counts['audio_cache']} WAV\n"
            f"text: {counts['text']} текстов\n"
            f"text_processed: {processed_count} обработанных"
        )
    
    def refresh(self):
        """Принудительно обновляет статистику"""
        self.update_stats()
    
    def get_counts(self) -> dict:
        """
        Возвращает текущие счетчики файлов
        
        Returns:
            dict с ключами: video_audio, audio_cache, text, text_processed
        """
        if not self.work_dir or not self.work_dir.exists():
            return {'video_audio': 0, 'audio_cache': 0, 'text': 0, 'text_processed': 0}
        
        counts = FileScanner.count_files_in_directories(self.work_dir)
        processed_dir = self.work_dir / 'text_processed'
        counts['text_processed'] = len([f for f in processed_dir.glob('*') if f.is_file()]) if processed_dir.exists() else 0
        
        return counts