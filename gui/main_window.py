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
from gui.control_buttons import ControlButtons
from gui.log_widget import LogWidget
from gui.progress_widget import ProgressWidget
from gui.dialogs import ConfirmationDialogs
from gui.dialogs import SettingsDialog
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.directory_panel)
        layout.addWidget(self.stats_panel)
        layout.addWidget(self.control_buttons)
        layout.addWidget(self.progress_widget)
        layout.addWidget(self.log_widget)
    
    def connect_signals(self):
        self.directory_panel.directory_changed.connect(self.on_directory_changed)
        
        self.control_buttons.prepare_clicked.connect(self.start_prepare)
        self.control_buttons.transcribe_clicked.connect(self.start_transcribe)
        self.control_buttons.postprocess_clicked.connect(self.start_postprocess)
        self.control_buttons.full_clicked.connect(self.start_full_process)
        
        self.logger.log_signal.connect(self.log_widget.append_message)
    
    def init_menu(self):
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # Меню Настройки
        settings_menu = menubar.addMenu("Настройки")
        
        general_action = QAction("Общие настройки", self)
        general_action.triggered.connect(self.open_settings)
        general_action.setShortcut("Ctrl+,")
        settings_menu.addAction(general_action)
        
        settings_menu.addSeparator()
        
        model_action = QAction("Модель Whisper", self)
        model_action.triggered.connect(lambda: self.open_settings_tab(0))
        settings_menu.addAction(model_action)
        
        formats_action = QAction("Форматы вывода", self)
        formats_action.triggered.connect(lambda: self.open_settings_tab(1))
        settings_menu.addAction(formats_action)
        
        postprocess_action = QAction("Постобработка", self)
        postprocess_action.triggered.connect(lambda: self.open_settings_tab(2))
        settings_menu.addAction(postprocess_action)
        
        # Меню Инструменты
        tools_menu = menubar.addMenu("Инструменты")
        
        editor_action = QAction("Редактор словаря замен", self)
        editor_action.triggered.connect(self.open_replacement_editor)
        tools_menu.addAction(editor_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        dialog.exec_()
    
    def open_settings_tab(self, tab_index: int):
        dialog = SettingsDialog(self.config, self)
        dialog.tab_widget.setCurrentIndex(tab_index)
        dialog.exec_()
    
    def open_replacement_editor(self):
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
    
    def show_about(self):
        QMessageBox.about(
            self, "О программе",
            "Whisper Transcriber\n\n"
            "Версия: 2.0.0\n\n"
            "Программа для распознавания речи из видео и аудио файлов\n"
            "с использованием OpenAI Whisper.\n\n"
            "Функции:\n"
            "• Подготовка аудиофайлов\n"
            "• Распознавание речи\n"
            "• Постобработка текста (очистка, словарь замен, капитализация)\n"
            "• Поддержка множества форматов вывода\n"
            "• Редактируемый словарь замен\n"
            "• Гибкая настройка порядка действий\n\n"
            "© 2024"
        )
    
    def load_initial_config(self):
        ffmpeg_ok, ffmpeg_msg = Validators.check_ffmpeg()
        if ffmpeg_ok:
            self.logger.info(ffmpeg_msg)
        else:
            self.logger.error(ffmpeg_msg)
            QMessageBox.warning(
                self, "ffmpeg не найден",
                "ffmpeg не установлен в системе.\n\n"
                "Для работы программы необходимо установить ffmpeg:\n"
                "Ubuntu/Debian: sudo apt install ffmpeg"
            )
        
        _, ram_warning = Validators.check_ram_available()
        if ram_warning:
            self.logger.warning(ram_warning)
        
        work_dir = self.config.get('work_directory', '')
        if work_dir and Path(work_dir).exists():
            self.directory_panel.set_directory(work_dir)
            self.logger.info(f"Загружена рабочая директория: {work_dir}")
    
    def on_directory_changed(self, work_dir: str):
        self.config.set('work_directory', work_dir)
        work_path = Path(work_dir)
        Validators.ensure_directories(work_path)
        self.stats_panel.set_work_directory(work_dir)
        self.logger.info(f"Рабочая директория установлена: {work_dir}")
    
    def start_prepare(self):
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
    
    def start_transcribe(self):
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        cache_dir = work_path / 'audio_cache'
        
        if not cache_dir.exists() or not any(cache_dir.glob("*.wav")):
            self.dialogs.show_warning("Ошибка", "Нет WAV файлов в audio_cache. Сначала выполните подготовку.")
            return
        
        model = self.config.get('whisper_model', 'base')
        output_formats = self.config.get('output_formats', ['txt'])
        
        force_overwrite = self.dialogs.ask_transcribe_confirmation()
        if force_overwrite is None:
            return
        
        _, ram_warning = Validators.check_model_requirements(model)
        if ram_warning:
            self.logger.warning(ram_warning)
        
        self.current_worker = TranscribeWorker(
            work_path, model, output_formats, force_overwrite
        )
        self.current_worker.signals.progress.connect(self.on_transcribe_progress)
        self.current_worker.signals.finished.connect(self.on_transcribe_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info(f"🚀 Начат этап распознавания (модель: {model}, форматы: {', '.join(output_formats)})...")
    
    def start_postprocess(self):
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        text_dir = work_path / 'text'
        
        if not text_dir.exists() or not any(text_dir.iterdir()):
            self.dialogs.show_warning("Ошибка", "Нет текстовых файлов в папке text. Сначала выполните распознавание.")
            return
        
        postprocess_actions = self.config.get('postprocess_actions', ['cleanup', 'replacement_dict'])
        postprocess_order = self.config.get('postprocess_order', ['cleanup', 'replacement_dict'])
        interactive = False  # LanguageTool отключён
        
        force_overwrite = self.dialogs.ask_postprocess_confirmation()
        if force_overwrite is None:
            return
        
        self.current_worker = PostprocessWorker(
            work_path, postprocess_actions, postprocess_order, 
            force_overwrite, interactive, parent=self
        )
        self.current_worker.signals.progress.connect(self.on_postprocess_progress)
        self.current_worker.signals.finished.connect(self.on_postprocess_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info(f"📝 Начат этап постобработки (действия: {', '.join(postprocess_actions)})...")
    
    def start_full_process(self):
        work_dir = self.directory_panel.get_directory()
        
        if not work_dir:
            self.dialogs.show_warning("Ошибка", "Выберите рабочую директорию")
            return
        
        work_path = Path(work_dir)
        source_dir = work_path / 'video_audio'
        
        if not source_dir.exists() or not any(source_dir.iterdir()):
            self.dialogs.show_warning("Ошибка", "Папка video_audio пуста или не существует")
            return
        
        model = self.config.get('whisper_model', 'base')
        output_formats = self.config.get('output_formats', ['txt'])
        postprocess_actions = self.config.get('postprocess_actions', ['cleanup', 'replacement_dict'])
        postprocess_order = self.config.get('postprocess_order', ['cleanup', 'replacement_dict'])
        interactive = False  # LanguageTool отключён
        
        force_overwrite = self.dialogs.ask_full_confirmation()
        if force_overwrite is None:
            return
        
        _, ram_warning = Validators.check_model_requirements(model)
        if ram_warning:
            self.logger.warning(ram_warning)
        
        self.current_worker = FullProcessWorker(
            work_path, model, output_formats, force_overwrite,
            postprocess_actions, postprocess_order, interactive, parent=self
        )
        self.current_worker.signals.progress.connect(self.on_full_progress)
        self.current_worker.signals.finished.connect(self.on_full_finished)
        self.current_worker.signals.log.connect(self.logger.log)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        
        self.process_handlers.start_process(self.control_buttons, self.progress_widget)
        self.current_worker.start()
        self.logger.info(f"🚀 Начат полный процесс (модель: {model}, форматы: {', '.join(output_formats)})...")
    
    def on_prepare_progress(self, filename: str, current: int, total: int):
        self.progress_widget.update_progress(current, total, f"Подготовка: {filename}")
    
    def on_transcribe_progress(self, filename: str, current: int, total: int):
        self.progress_widget.update_progress(current, total, f"Распознавание: {filename}")
    
    def on_postprocess_progress(self, filename: str, current: int, total: int):
        self.progress_widget.update_progress(current, total, f"Постобработка: {filename}")
    
    def on_full_progress(self, filename: str, current: int, total: int):
        self.progress_widget.update_progress(current, total, f"{filename}")
    
    def on_prepare_finished(self, successful: list, failed: list):
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Подготовка завершена. Успешно: {len(successful)}, Ошибок: {len(failed)}")
    
    def on_transcribe_finished(self, successful: list, failed: list):
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Распознавание завершено. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        self.logger.info(f"📁 Сырые тексты сохранены в папке 'text/'")
    
    def on_postprocess_finished(self, successful: list, failed: list):
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Постобработка завершена. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        self.logger.info(f"📁 Обработанные тексты сохранены в папке 'text_processed/'")
    
    def on_full_finished(self, successful: list, failed: list):
        self.process_handlers.finish_process(self.control_buttons, self.progress_widget, self.stats_panel)
        self.logger.info(f"✅ Полный процесс завершен. Успешно: {len(successful)}, Ошибок: {len(failed)}")
        self.logger.info(f"📁 Сырые тексты: 'text/', обработанные: 'text_processed/'")
    
    def closeEvent(self, event):
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "Выполняется задача",
                "Идёт обработка. Вы уверены, что хотите выйти?",
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
