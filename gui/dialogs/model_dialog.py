"""
model_dialog.py - Диалог выбора модели Whisper
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QGroupBox, QFormLayout, QTextEdit
)
from PyQt5.QtCore import Qt


class ModelDialog(QWidget):
    """Диалог выбора модели Whisper"""
    
    # Информация о моделях
    MODEL_INFO = {
        'tiny': {
            'size': '~75 МБ',
            'ram': '~1 ГБ',
            'speed': 'Очень быстро',
            'accuracy': 'Низкая',
            'description': 'Самая быстрая, но менее точная. Для тестирования.'
        },
        'base': {
            'size': '~145 МБ',
            'ram': '~2 ГБ',
            'speed': 'Быстро',
            'accuracy': 'Средняя',
            'description': 'Хороший баланс для коротких файлов. Рекомендуется.'
        },
        'small': {
            'size': '~488 МБ',
            'ram': '~4 ГБ',
            'speed': 'Средне',
            'accuracy': 'Хорошая',
            'description': 'Выше точность, дольше обработка.'
        },
        'medium': {
            'size': '~1.5 ГБ',
            'ram': '~8 ГБ',
            'speed': 'Медленно',
            'accuracy': 'Высокая',
            'description': 'Высокая точность, требует много RAM.'
        },
        'large': {
            'size': '~3 ГБ',
            'ram': '~16 ГБ',
            'speed': 'Очень медленно',
            'accuracy': 'Максимальная',
            'description': 'Максимальная точность, требует мощного железа.'
        }
    }
    
    def __init__(self, config_manager, parent=None, embedded=False):
        super().__init__(parent)
        self.config = config_manager
        self.embedded = embedded
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Группа выбора модели
        model_group = QGroupBox("Выбор модели")
        model_layout = QFormLayout(model_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addRow("Модель:", self.model_combo)
        
        layout.addWidget(model_group)
        
        # Информация о модели
        info_group = QGroupBox("Информация о модели")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
        
        # Рекомендация
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.recommendation_label)
        
        layout.addStretch()
        
        # Загружаем начальную информацию
        self.on_model_changed(self.model_combo.currentText())
    
    def on_model_changed(self, model_name: str):
        """Обновляет информацию при выборе модели"""
        info = self.MODEL_INFO.get(model_name, {})
        
        text = f"""
        <b>Размер модели:</b> {info.get('size', 'Н/Д')}<br>
        <b>Требуемая RAM:</b> {info.get('ram', 'Н/Д')}<br>
        <b>Скорость:</b> {info.get('speed', 'Н/Д')}<br>
        <b>Точность:</b> {info.get('accuracy', 'Н/Д')}<br>
        <b>Описание:</b> {info.get('description', 'Н/Д')}
        """
        self.info_text.setText(text)
        
        # Рекомендация
        if model_name == 'large':
            self.recommendation_label.setText(
                "⚠️ Рекомендуется: Модель large требует 16+ ГБ RAM и мощного GPU."
            )
        elif model_name == 'tiny':
            self.recommendation_label.setText(
                "ℹ️ Рекомендуется: Модель tiny подходит только для тестирования."
            )
        else:
            self.recommendation_label.setText(
                "✅ Рекомендуется: base или small для большинства задач."
            )
    
    def load_settings(self):
        """Загружает настройки из конфига"""
        model = self.config.get('whisper_model', 'base')
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
    
    def save_settings(self):
        """Сохраняет настройки в конфиг"""
        self.config.set('whisper_model', self.model_combo.currentText())
    
    def get_model(self) -> str:
        """Возвращает выбранную модель"""
        return self.model_combo.currentText()