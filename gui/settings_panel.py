"""
settings_panel.py - Панель настроек (модель, язык, формат вывода, уровень постобработки)
"""

from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QRadioButton, QButtonGroup, QScrollArea, QWidget
)
from PyQt5.QtCore import pyqtSignal

from core.transcriber import WhisperTranscriber


class SettingsPanel(QGroupBox):
    """Панель с настройками распознавания"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__("Настройки распознавания")
        self.config = config_manager
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Инициализирует элементы управления"""
        # Используем QScrollArea если форматов много
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
        
        content_widget = QWidget()
        layout = QHBoxLayout(content_widget)
        
        # === Модель Whisper ===
        model_layout = QVBoxLayout()
        model_layout.addWidget(QLabel("Модель Whisper:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(WhisperTranscriber.AVAILABLE_MODELS)
        
        self.model_combo.setToolTip(
            "tiny: самая быстрая, но менее точная\n"
            "base: хороший баланс для коротких файлов\n"
            "small: выше точность, дольше\n"
            "medium: высокая точность, много RAM\n"
            "large: максимальная точность, требует 10+ ГБ RAM"
        )
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # === Язык ===
        lang_layout = QVBoxLayout()
        lang_layout.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(WhisperTranscriber.AVAILABLE_LANGUAGES)
        self.lang_combo.setToolTip("auto: автоопределение (медленнее)")
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        # === Формат вывода ===
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("Формат текста:"))
        
        self.format_group = QButtonGroup()
        
        # Основные форматы
        self.format_txt = QRadioButton(".txt (простой текст)")
        self.format_srt = QRadioButton(".srt (субтитры)")
        self.format_vtt = QRadioButton(".vtt (WebVTT)")
        
        # Дополнительные форматы
        self.format_docx = QRadioButton(".docx (Word документ)")
        self.format_json = QRadioButton(".json (структурированный)")
        self.format_md = QRadioButton(".md (Markdown)")
        self.format_html = QRadioButton(".html (веб-страница)")
        self.format_csv = QRadioButton(".csv (таблица)")
        self.format_txt_ts = QRadioButton(".txt с таймкодами")
        
        self.format_group.addButton(self.format_txt)
        self.format_group.addButton(self.format_srt)
        self.format_group.addButton(self.format_vtt)
        self.format_group.addButton(self.format_docx)
        self.format_group.addButton(self.format_json)
        self.format_group.addButton(self.format_md)
        self.format_group.addButton(self.format_html)
        self.format_group.addButton(self.format_csv)
        self.format_group.addButton(self.format_txt_ts)
        
        # Добавляем подсказки для форматов
        self.format_txt.setToolTip("Простой текст без форматирования")
        self.format_srt.setToolTip("Субтитры с таймкодами (формат SubRip)")
        self.format_vtt.setToolTip("WebVTT формат для видео в браузере")
        self.format_docx.setToolTip("Документ Microsoft Word с форматированием (требуется python-docx)")
        self.format_json.setToolTip("Структурированные данные с метаинформацией")
        self.format_md.setToolTip("Markdown разметка")
        self.format_html.setToolTip("Веб-страница для просмотра в браузере")
        self.format_csv.setToolTip("Таблица с таймкодами для Excel")
        self.format_txt_ts.setToolTip("Текст с временными метками в начале каждой строки")
        
        format_layout.addWidget(self.format_txt)
        format_layout.addWidget(self.format_srt)
        format_layout.addWidget(self.format_vtt)
        format_layout.addWidget(self.format_docx)
        format_layout.addWidget(self.format_json)
        format_layout.addWidget(self.format_md)
        format_layout.addWidget(self.format_html)
        format_layout.addWidget(self.format_csv)
        format_layout.addWidget(self.format_txt_ts)
        
        layout.addLayout(format_layout)
        
        # === Уровень постобработки ===
        postprocess_layout = QVBoxLayout()
        postprocess_layout.addWidget(QLabel("Уровень постобработки:"))
        
        self.postprocess_group = QButtonGroup()
        
        self.pp_minimal = QRadioButton("Минимальный (только очистка)")
        self.pp_standard = QRadioButton("Стандартный (очистка + словарь исключений)")
        self.pp_full = QRadioButton("Полный (очистка + словарь + заглавные буквы)")
        
        self.pp_minimal.setToolTip(
            "Только удаление лишних пробелов и исправление типичных ошибок Whisper.\n"
            "Самый безопасный вариант, не изменяет смысл текста."
        )
        self.pp_standard.setToolTip(
            "Добавляет исправление конкретных слов (пошол→пошёл, ихний→их и т.д.)\n"
            "Безопасный вариант, исправляет только явные ошибки."
        )
        self.pp_full.setToolTip(
            "Добавляет заглавные буквы в начале предложений.\n"
            "Безопасный вариант, только форматирование."
        )
        
        self.postprocess_group.addButton(self.pp_minimal)
        self.postprocess_group.addButton(self.pp_standard)
        self.postprocess_group.addButton(self.pp_full)
        
        # По умолчанию стандартный
        self.pp_standard.setChecked(True)
        
        postprocess_layout.addWidget(self.pp_minimal)
        postprocess_layout.addWidget(self.pp_standard)
        postprocess_layout.addWidget(self.pp_full)
        
        layout.addLayout(postprocess_layout)
        
        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
        
        # Подключаем сигналы
        self.model_combo.currentTextChanged.connect(self.on_settings_changed)
        self.lang_combo.currentTextChanged.connect(self.on_settings_changed)
        
        # Подключаем все радио-кнопки форматов
        for btn in self.format_group.buttons():
            btn.toggled.connect(self.on_settings_changed)
        
        # Подключаем радио-кнопки постобработки
        for btn in self.postprocess_group.buttons():
            btn.toggled.connect(self.on_settings_changed)
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        self.save_settings()
        self.settings_changed.emit()
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        model = self.config.get('whisper_model', 'base')
        language = self.config.get('language', 'auto')
        output_format = self.config.get('output_format', 'txt')
        postprocess_level = self.config.get('postprocess_level', 'standard')
        
        # Модель
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        # Язык
        index = self.lang_combo.findText(language)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        
        # Формат вывода
        if output_format == 'txt':
            self.format_txt.setChecked(True)
        elif output_format == 'srt':
            self.format_srt.setChecked(True)
        elif output_format == 'vtt':
            self.format_vtt.setChecked(True)
        elif output_format == 'docx':
            self.format_docx.setChecked(True)
        elif output_format == 'json':
            self.format_json.setChecked(True)
        elif output_format == 'md':
            self.format_md.setChecked(True)
        elif output_format == 'html':
            self.format_html.setChecked(True)
        elif output_format == 'csv':
            self.format_csv.setChecked(True)
        elif output_format == 'txt_timestamps':
            self.format_txt_ts.setChecked(True)
        else:
            self.format_txt.setChecked(True)
        
        # Уровень постобработки
        if postprocess_level == 'minimal':
            self.pp_minimal.setChecked(True)
        elif postprocess_level == 'standard':
            self.pp_standard.setChecked(True)
        elif postprocess_level == 'full':
            self.pp_full.setChecked(True)
        else:
            self.pp_standard.setChecked(True)
    
    def save_settings(self):
        """Сохраняет текущие настройки"""
        self.config.set('whisper_model', self.get_model())
        self.config.set('language', self.get_language())
        self.config.set('output_format', self.get_output_format())
        self.config.set('postprocess_level', self.get_postprocess_level())
    
    def get_model(self) -> str:
        """Возвращает выбранную модель"""
        return self.model_combo.currentText()
    
    def get_language(self) -> str:
        """Возвращает выбранный язык"""
        return self.lang_combo.currentText()
    
    def get_output_format(self) -> str:
        """Возвращает выбранный формат вывода"""
        if self.format_txt.isChecked():
            return 'txt'
        elif self.format_srt.isChecked():
            return 'srt'
        elif self.format_vtt.isChecked():
            return 'vtt'
        elif self.format_docx.isChecked():
            return 'docx'
        elif self.format_json.isChecked():
            return 'json'
        elif self.format_md.isChecked():
            return 'md'
        elif self.format_html.isChecked():
            return 'html'
        elif self.format_csv.isChecked():
            return 'csv'
        elif self.format_txt_ts.isChecked():
            return 'txt_timestamps'
        return 'txt'
    
    def get_postprocess_level(self) -> str:
        """Возвращает выбранный уровень постобработки"""
        if self.pp_minimal.isChecked():
            return 'minimal'
        elif self.pp_standard.isChecked():
            return 'standard'
        elif self.pp_full.isChecked():
            return 'full'
        return 'standard'