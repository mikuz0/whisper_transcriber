"""
main_window.py - Главное окно приложения Whisper Transcriber
"""

import subprocess
import sys
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMenuBar, QAction, QMessageBox
)
from PyQt5.QtCore import QThreadPool

from gui.directory_panel import DirectoryPanel
from gui.stats_panel import StatsPanel
from gui.settings_panel import SettingsPanel
from gui.control_buttons import ControlButtons
from gui.log_widget import LogWidget
from gui.progress_widget import ProgressWidget
from gui.dialogs import ConfirmationDialogs
from gui.workers import PrepareWorker, TranscribeWorker, PostprocessWorker, FullProcessWorker
from gui.process_handlers import ProcessHandlers

from utils.logger import GUILogger
from utils.config_manager import ConfigManager
from utils.validators import Validators


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        
        self.config = ConfigManager()
        self.logger = GUILogger()
        self.current_worker = None
        
        self.setWindowTitle("Whisper Transcriber - Распознавание речи")
        self.setMinimumSize(900, 700)
        
        self.directory_panel = DirectoryPanel()
        self.stats_panel = StatsPanel()
        self.settings_panel = SettingsPanel(self.config)
        self.control_buttons = ControlButtons()
        self.progress_widget = ProgressWidget()
        self.log_widget = LogWidget()
        self.dialogs = ConfirmationDialogs(self)
        
        self.process_handlers = ProcessHandlers(self)
        
        self.setup_layout()
        self.connect_signals()
        self.init_menu()
        self.load_initial_config()
    
    def setup_layout(self):
        """Настраивает компоновку виджетов"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.directory_panel)
        layout.addWidget(self.stats_panel)
        layout.addWidget(self.settings_panel)
        layout.addWidget(self.control_buttons)
        layout.addWidget(self.progress_widget)
        layout.addWidget(self.log_widget)
    
    def connect_signals(self):
        """Подключает все сигналы к слотам"""
        self.directory_panel.directory_changed.connect(self.on_directory_changed)
        
        self.control_buttons.prepare_clicked.connect(self.start_prepare)
        self.control_buttons.transcribe_clicked.connect(self.start_transcribe)
        self.control_buttons.postprocess_clicked.connect(self.start_postprocess)
        self.control_buttons.full_clicked.connect(self.start_full_process)
        
        self.logger.log_signal.connect(self.log_widget.append_message)
    
    def init_menu(self):
        """Создаёт меню приложения"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # Меню Инструменты
        tools_menu = menubar.addMenu("Инструменты")
        
        # Пункт: Редактор словаря замен
        editor_action = QAction("Редактор словаря замен", self)
        editor_action.triggered.connect(self.open_replacement_editor)
        editor_action.setStatusTip("Открыть редактор для управления словарём замен")
        tools_menu.addAction(editor_action)
        
        # Разделитель
        tools_menu.addSeparator()
        
        # Пункт: Перезагрузить словарь
        reload_action = QAction("Перезагрузить словарь замен", self)
        reload_action.triggered.connect(self.reload_dictionary)
        reload_action.setStatusTip("Перезагрузить словарь замен из файла")
        tools_menu.addAction(reload_action)
        
        # Статус словаря
        self.dict_status_action = QAction("", self)
        self.dict_status_action.setEnabled(False)
        tools_menu.addAction(self.dict_status_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Обновляем статус словаря
        self.update_dict_status()
    
    def open_replacement_editor(self):
        """Открывает редактор словаря замен"""
        editor_path = Path(__file__).parent.parent / "tools" / "replacement_editor.py"
        
        if not editor_path.exists():
            self.logger.error(f"Редактор не найден: {editor_path}")
            QMessageBox.warning(
                self, "Редактор не найден",
                f"Файл редактора не найден:\n{editor_path}\n\n"
                "Убедитесь, что файл replacement_editor.py находится в папке tools/"
            )
            return
        
        try:
            subprocess.Popen([sys.executable, str(editor_path)])
            self.logger.info("📝 Открыт редактор словаря замен")
        except Exception as e:
            self.logger.error(f"Не удалось открыть редактор: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактор:\n{e}")
    
    def reload_dictionary(self):
        """Перезагружает словарь замен"""
        if hasattr(self, 'current_worker') and self.current_worker and self.current_worker.isRunning():
            self.logger.warning("Словарь нельзя перезагрузить во время выполнения задачи")
            QMessageBox.warning(
                self, "Невозможно перезагрузить",
                "Словарь нельзя перезагрузить во время выполнения задачи.\n"
                "Дождитесь завершения текущей операции."
            )
            return
        
        # Обновляем статус словаря
        self.update_dict_status()
        self.logger.info("🔄 Словарь замен будет использован при следующей постобработке")
    
    def update_dict_status(self):
        """Обновляет статус словаря в меню"""
        dict_path = Path(__file__).parent.parent / "data" / "replacement_dict.json"
        
        if dict_path.exists():
            try:
                with open(dict_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = len(data)
                self.dict_status_action.setText(f"📖 Словарь замен: {count} записей")
            except Exception as e:
                self.dict_status_action.setText("📖 Словарь: ошибка чтения")
                self.logger.warning(f"Ошибка чтения словаря: {e}")
        else:
            self.dict_status_action.setText("📖 Словарь: не найден")
            self.logger.warning(f"Словарь замен не найден: {dict_path}")
    
    def show_about(self):
        """Показывает диалог "О программе" """
        QMessageBox.about(
            self, "О программе",
            "Whisper Transcriber\n\n"
            "Версия: 1.0.0\n\n"
            "Программа для распознавания речи из видео и аудио файлов\n"
            "с использованием OpenAI Whisper.\n\n"
            "Функции:\n"
            "• Подготовка аудиофайлов\n"
            "• Распознавание речи\n"
            "• Постобработка текста\n"
            "• Поддержка множества форматов вывода\n"
            "• Редактируемый словарь замен\n\n"
            "© 2024"
        )
    
    def load_initial_config(self):
        """Загружает сохраненную рабочую директорию и проверяет систему"""
        # Проверяем ffmpeg
        ffmpeg_ok, ffmpeg_msg = Validators.check_ffmpeg()
        if ffmpeg_ok:
            self.logger.info(ffmpeg_msg)
        else:
            self.logger.error(ffmpeg_msg)
            QMessageBox.warning(
                self, "ffmpeg не найден",
                "ffmpeg не установлен в системе.\n\n"
                "Для работы программы необходимо установить ffmpeg:\n"
                "Ubuntu/Debian: sudo apt install ffmpeg\n"
                "Windows: скачайте с https://ffmpeg.org/download.html\n"
                "macOS: brew install ffmpeg"
            )
        
        # Проверяем RAM
        _, ram_warning = Validators.check_ram_available()
        if ram_warning:
            self.logger.warning(ram_warning)
        
        # Загружаем рабочую директорию
        work_dir = self.config.get('work_directory', '')
        if work_dir and Path(work_dir).exists():
            self.directory_panel.set_directory(work_dir)
            self.logger.info(f"Загружена рабочая директория: {work_dir}")
    
    def on_directory_changed(self, work_dir: str):
        """Обработчик изменения рабочей директории"""
        self.config.set('work_directory', work_dir)
        work_path = Path(work_dir)
        Validators.ensure_directories(work_path)
        self.stats_panel.set_work_directory(work_dir)
        self.logger.info(f"Рабочая директория установлена: {work_dir}")
    
    # ==================== ПОДГОТОВКА ====================
    
    def start_prepare(self):
        """Запускает этап подготовки файлов"""
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        source_dir = work_path / 'video_audio'
        
        if not source_dir.exists() or not any(source_dir.iterdir()):
            self.dialogs.show_warning("Ошибка", "Папка video_audio пуста или не существует")
            return
        
        force_overwrite = self.dialogs.ask_prepare_confirmation()
        if force_overwrite is None:
            return
        
        self.current_worker = PrepareWorker(work_path, force_overwrite)
        self.current_worker.signals.progress.connect(self.on_prepare_progress)
        self.current_worker.signals.finished.connect(self.on_prepare_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info("🚀 Начат этап подготовки файлов...")
    
    # ==================== РАСПОЗНАВАНИЕ ====================
    
    def start_transcribe(self):
        """Запускает этап распознавания"""
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        cache_dir = work_path / 'audio_cache'
        
        if not cache_dir.exists() or not any(cache_dir.glob("*.wav")):
            self.dialogs.show_warning("Ошибка", "Нет WAV файлов в audio_cache. Сначала выполните подготовку.")
            return
        
        model = self.settings_panel.get_model()
        language = self.settings_panel.get_language()
        output_format = self.settings_panel.get_output_format()
        
        force_overwrite = self.dialogs.ask_transcribe_confirmation()
        if force_overwrite is None:
            return
        
        _, ram_warning = Validators.check_model_requirements(model)
        if ram_warning:
            self.logger.warning(ram_warning)
        
        self.current_worker = TranscribeWorker(
            work_path, model, language, output_format, force_overwrite
        )
        self.current_worker.signals.progress.connect(self.on_transcribe_progress)
        self.current_worker.signals.finished.connect(self.on_transcribe_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info(f"🚀 Начат этап распознавания (модель: {model}, язык: {language})...")
    
    # ==================== ПОСТОБРАБОТКА ====================
    
    def start_postprocess(self):
        """Запускает этап постобработки"""
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        text_dir = work_path / 'text'
        
        if not text_dir.exists() or not any(text_dir.iterdir()):
            self.dialogs.show_warning("Ошибка", "Нет текстовых файлов в папке text. Сначала выполните распознавание.")
            return
        
        postprocess_level = self.settings_panel.get_postprocess_level()
        
        force_overwrite = self.dialogs.ask_postprocess_confirmation()
        if force_overwrite is None:
            return
        
        self.current_worker = PostprocessWorker(work_path, postprocess_level, force_overwrite)
        self.current_worker.signals.progress.connect(self.on_postprocess_progress)
        self.current_worker.signals.finished.connect(self.on_postprocess_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info(f"📝 Начат этап постобработки (уровень: {postprocess_level})...")
    
    # ==================== ПОЛНЫЙ ПРОЦЕСС ====================
    
    def start_full_process(self):
        """Запускает полный процесс (подготовка + распознавание + постобработка)"""
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        source_dir = work_path / 'video_audio'
        
        if not source_dir.exists() or not any(source_dir.iterdir()):
            self.dialogs.show_warning("Ошибка", "Папка video_audio пуста или не существует")
            return
        
        model = self.settings_panel.get_model()
        language = self.settings_panel.get_language()
        output_format = self.settings_panel.get_output_format()
        postprocess_level = self.settings_panel.get_postprocess_level()
        
        force_overwrite = self.dialogs.ask_full_confirmation()
        if force_overwrite is None:
            return
        
        _, ram_warning = Validators.check_model_requirements(model)
        if ram_warning:
            self.logger.warning(ram_warning)
        
        self.current_worker = FullProcessWorker(
            work_path, model, language, output_format, force_overwrite, postprocess_level
        )
        self.current_worker.signals.progress.connect(self.on_full_progress)
        self.current_worker.signals.finished.connect(self.on_full_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info(f"🚀 Начат полный процесс (модель: {model}, язык: {language}, постобработка: {postprocess_level})...")
    
    # ==================== ОБРАБОТЧИКИ ПРОГРЕССА ====================
    
    def on_prepare_progress(self, filename: str, current: int, total: int):
        """Обновляет прогресс подготовки"""
        self.progress_widget.update_progress(current, total, f"Подготовка: {filename}")
    
    def on_transcribe_progress(self, filename: str, current: int, total: int):
        """Обновляет прогресс распознавания"""
        self.progress_widget.update_progress(current, total, f"Распознавание: {filename}")
    
    def on_postprocess_progress(self, filename: str, current: int, total: int):
        """Обновляет прогресс постобработки"""
        self.progress_widget.update_progress(current, total, f"Постобработка: {filename}")
    
    def on_full_progress(self, filename: str, current: int, total: int):
        """Обновляет прогресс полного процесса"""
        self.progress_widget.update_progress(current, total, f"{filename}")
    
    # ==================== ОБРАБОТЧИКИ ЗАВЕРШЕНИЯ ====================
    
    def on_prepare_finished(self, successful: list, failed: list):
        """Завершение подготовки"""
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Подготовка завершена. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        if failed:
            self.logger.warning(f"Не удалось обработать: {', '.join(failed[:5])}")
    
    def on_transcribe_finished(self, successful: list, failed: list):
        """Завершение распознавания"""
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Распознавание завершено. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        self.logger.info(f"📁 Сырые тексты сохранены в папке 'text/'")
        if failed:
            self.logger.warning(f"Не удалось распознать: {', '.join(failed[:5])}")
    
    def on_postprocess_finished(self, successful: list, failed: list):
        """Завершение постобработки"""
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Постобработка завершена. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        self.logger.info(f"📁 Обработанные тексты сохранены в папке 'text_processed/'")
        if failed:
            self.logger.warning(f"Не удалось обработать: {', '.join(failed[:5])}")
    
    def on_full_finished(self, successful: list, failed: list):
        """Завершение полного процесса"""
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Полный процесс завершен. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        self.logger.info(f"📁 Сырые тексты: 'text/', обработанные: 'text_processed/'")
        if failed:
            self.logger.warning(f"Не удалось обработать: {', '.join(failed[:5])}")
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "Выполняется задача",
                "Идёт обработка. Вы уверены, что хотите выйти?\n"
                "Несохранённые данные могут быть потеряны.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.current_worker.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()