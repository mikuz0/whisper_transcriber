"""
formats_dialog.py - Диалог выбора форматов вывода (множественный выбор)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QGroupBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt


class FormatsDialog(QWidget):
    """Диалог выбора форматов вывода (множественный выбор)"""
    
    # Доступные форматы с описанием
    AVAILABLE_FORMATS = {
        'txt': {
            'name': 'TXT',
            'description': 'Простой текст без форматирования',
            'extension': '.txt',
            'icon': '📄'
        },
        'srt': {
            'name': 'SRT',
            'description': 'Субтитры с таймкодами (формат SubRip)',
            'extension': '.srt',
            'icon': '🎬'
        },
        'vtt': {
            'name': 'VTT',
            'description': 'WebVTT формат для видео в браузере',
            'extension': '.vtt',
            'icon': '🌐'
        },
        'docx': {
            'name': 'DOCX',
            'description': 'Документ Microsoft Word с форматированием',
            'extension': '.docx',
            'icon': '📝'
        },
        'json': {
            'name': 'JSON',
            'description': 'Структурированные данные с метаинформацией',
            'extension': '.json',
            'icon': '📊'
        },
        'md': {
            'name': 'Markdown',
            'description': 'Markdown разметка',
            'extension': '.md',
            'icon': '📋'
        },
        'html': {
            'name': 'HTML',
            'description': 'Веб-страница для просмотра в браузере',
            'extension': '.html',
            'icon': '🌍'
        },
        'csv': {
            'name': 'CSV',
            'description': 'Таблица с таймкодами для Excel',
            'extension': '.csv',
            'icon': '📊'
        },
        'txt_timestamps': {
            'name': 'TXT с таймкодами',
            'description': 'Текст с временными метками в начале каждой строки',
            'extension': '.txt',
            'icon': '⏱️'
        }
    }
    
    def __init__(self, config_manager, parent=None, embedded=False):
        super().__init__(parent)
        self.config = config_manager
        self.embedded = embedded
        self.checkboxes = {}
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Информационная метка
        info_label = QLabel("Выберите форматы, в которых будут сохраняться результаты:")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Область с чекбоксами (прокручиваемая)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Создаём чекбоксы для каждого формата
        for fmt_id, fmt_info in self.AVAILABLE_FORMATS.items():
            checkbox = QCheckBox()
            checkbox.setText(f"{fmt_info['icon']} {fmt_info['name']} (.{fmt_info['extension']})")
            checkbox.setToolTip(fmt_info['description'])
            self.checkboxes[fmt_id] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Рекомендация
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("color: #666; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        layout.addWidget(self.recommendation_label)
        
        # Подключаем сигналы для обновления рекомендаций
        for cb in self.checkboxes.values():
            cb.stateChanged.connect(self.update_recommendation)
        
        self.update_recommendation()
    
    def update_recommendation(self):
        """Обновляет рекомендацию на основе выбранных форматов"""
        selected = self.get_selected_formats()
        
        if not selected:
            self.recommendation_label.setText("⚠️ Не выбран ни один формат. Результаты не будут сохранены.")
        elif len(selected) == 1:
            self.recommendation_label.setText(f"ℹ️ Выбран один формат: {selected[0]}")
        else:
            self.recommendation_label.setText(
                f"✅ Выбрано {len(selected)} форматов: {', '.join(selected)}. "
                f"При распознавании будут созданы файлы всех выбранных форматов."
            )
        
        # Специальные рекомендации
        if 'srt' in selected and 'txt_timestamps' in selected:
            self.recommendation_label.setText(
                self.recommendation_label.text() + "\n⚠️ SRT и TXT с таймкодами — схожие форматы. Возможно, достаточно одного."
            )
    
    def load_settings(self):
        """Загружает настройки из конфига"""
        formats = self.config.get('output_formats', ['txt'])
        for fmt_id, checkbox in self.checkboxes.items():
            checkbox.setChecked(fmt_id in formats)
    
    def save_settings(self):
        """Сохраняет настройки в конфиг"""
        formats = self.get_selected_formats()
        self.config.set('output_formats', formats)
    
    def get_selected_formats(self) -> list:
        """Возвращает список выбранных форматов"""
        return [fmt_id for fmt_id, cb in self.checkboxes.items() if cb.isChecked()]
    
    def get_first_format(self) -> str:
        """Возвращает первый выбранный формат (для обратной совместимости)"""
        selected = self.get_selected_formats()
        return selected[0] if selected else 'txt'