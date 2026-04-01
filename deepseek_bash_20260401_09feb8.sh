cat > ~/src/whisper_transcriber/tools/replacement_editor.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Редактор JSON-файла с заменами (ключ → значение)
Безопасное редактирование с сохранением последней рабочей папки
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog,
    QMessageBox, QLineEdit, QLabel, QHeaderView, QSplitter,
    QFormLayout, QGroupBox, QCheckBox, QStatusBar, QShortcut,
    QMenuBar, QMenu, QAction, QInputDialog
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QKeySequence, QFont, QColor, QBrush


class ReplacementEditor(QMainWindow):
    """Главное окно редактора словаря замен"""
    
    def __init__(self):
        super().__init__()
        self.current_file: Optional[Path] = None
        self.data: Dict[str, str] = {}
        self.modified = False
        self.settings = QSettings('ReplacementEditor', 'Editor')
        
        self.init_ui()
        self.load_last_path()
        self.open_default_file()
        self.update_status_bar()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Редактор словаря замен")
        self.setGeometry(100, 100, 1000, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Панель инструментов
        toolbar_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("📂 Открыть")
        self.btn_open.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.btn_open)
        
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.clicked.connect(self.save_file)
        toolbar_layout.addWidget(self.btn_save)
        
        self.btn_save_as = QPushButton("📄 Сохранить как...")
        self.btn_save_as.clicked.connect(self.save_file_as)
        toolbar_layout.addWidget(self.btn_save_as)
        
        toolbar_layout.addStretch()
        
        self.btn_add = QPushButton("➕ Добавить запись")
        self.btn_add.clicked.connect(self.add_entry)
        toolbar_layout.addWidget(self.btn_add)
        
        self.btn_delete = QPushButton("🗑 Удалить запись")
        self.btn_delete.clicked.connect(self.delete_entry)
        toolbar_layout.addWidget(self.btn_delete)
        
        main_layout.addLayout(toolbar_layout)
        
        # Панель поиска
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по ключу или значению...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        
        self.case_sensitive = QCheckBox("Учитывать регистр")
        search_layout.addWidget(self.case_sensitive)
        search_layout.addStretch()
        
        main_layout.addLayout(search_layout)
        
        # Разделитель для таблицы и панели редактирования
        splitter = QSplitter(Qt.Vertical)
        
        # Таблица для отображения данных
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Ключ (что заменить)", "Значение (на что заменить)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.currentCellChanged.connect(self.on_current_cell_changed)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        splitter.addWidget(self.table)
        
        # Панель редактирования текущей записи
        edit_widget = QWidget()
        edit_layout = QFormLayout(edit_widget)
        edit_layout.setContentsMargins(10, 10, 10, 10)
        
        self.edit_key = QLineEdit()
        self.edit_key.setPlaceholderText("Ключ (слово или фраза для замены)")
        self.edit_key.textChanged.connect(self.on_edit_changed)
        edit_layout.addRow("Ключ (что заменить):", self.edit_key)
        
        self.edit_value = QLineEdit()
        self.edit_value.setPlaceholderText("Значение (на что заменить)")
        self.edit_value.textChanged.connect(self.on_edit_changed)
        edit_layout.addRow("Значение (на что заменить):", self.edit_value)
        
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border-radius: 3px; font-family: monospace; }")
        edit_layout.addRow("Предпросмотр замены:", self.preview_label)
        
        self.edit_buttons = QHBoxLayout()
        self.btn_update = QPushButton("Обновить")
        self.btn_update.clicked.connect(self.update_current_entry)
        self.btn_update.setEnabled(False)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.cancel_edit)
        self.btn_cancel.setEnabled(False)
        self.edit_buttons.addWidget(self.btn_update)
        self.edit_buttons.addWidget(self.btn_cancel)
        edit_layout.addRow("", self.edit_buttons)
        
        splitter.addWidget(edit_widget)
        splitter.setSizes([400, 150])
        
        main_layout.addWidget(splitter)
        
        # Строка состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel()
        self.status_bar.addWidget(self.status_label)
        
        # Горячие клавиши
        QShortcut(QKeySequence.Save, self).activated.connect(self.save_file)
        QShortcut(QKeySequence.Open, self).activated.connect(self.open_file)
        QShortcut(QKeySequence.Delete, self).activated.connect(self.delete_entry)
        QShortcut("Ctrl+N", self).activated.connect(self.add_entry)
        
        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        
        open_action = QAction("Открыть", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut(QKeySequence.Open)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить", self)
        save_action.triggered.connect(self.save_file)
        save_action.setShortcut(QKeySequence.Save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut(QKeySequence.Quit)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Правка")
        
        add_action = QAction("Добавить запись", self)
        add_action.triggered.connect(self.add_entry)
        add_action.setShortcut("Ctrl+N")
        edit_menu.addAction(add_action)
        
        delete_action = QAction("Удалить запись", self)
        delete_action.triggered.connect(self.delete_entry)
        delete_action.setShortcut(QKeySequence.Delete)
        edit_menu.addAction(delete_action)
        
        # Таймер для задержки обновления предпросмотра
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        
        self.current_row = -1
        
    def load_last_path(self):
        """Загрузка последнего использованного пути"""
        last_path = self.settings.value('last_path', '')
        if last_path:
            self.last_path = last_path
        else:
            self.last_path = str(Path.home())
    
    def save_last_path(self):
        """Сохранение последнего использованного пути"""
        if self.current_file:
            self.settings.setValue('last_path', str(self.current_file.parent))
        elif hasattr(self, 'last_path'):
            self.settings.setValue('last_path', self.last_path)
    
    def open_default_file(self):
        """Открывает файл словаря по умолчанию"""
        default_path = Path(__file__).parent.parent / "data" / "replacement_dict.json"
        if default_path.exists():
            self.load_data(default_path)
        else:
            self.status_bar.showMessage("Словарь по умолчанию не найден. Создайте новый или откройте существующий.", 3000)
    
    def update_status_bar(self):
        """Обновление строки состояния"""
        if self.current_file:
            file_info = f"Файл: {self.current_file.name}"
        else:
            file_info = "Файл не открыт"
            
        modified_mark = " *" if self.modified else ""
        entries_count = f" | Записей: {len(self.data)}"
        self.status_label.setText(f"{file_info}{modified_mark}{entries_count}")
        
    def set_modified(self, modified: bool):
        """Установка флага изменений"""
        self.modified = modified
        self.update_status_bar()
        self.setWindowModified(modified)
        
    def load_data(self, file_path: Path):
        """Загрузка данных из JSON-файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.current_file = file_path
            self.set_modified(False)
            self.update_table()
            self.save_last_path()
            
            self.status_bar.showMessage(f"Загружено {len(self.data)} записей", 3000)
            self.setWindowTitle(f"Редактор словаря замен - {file_path.name}")
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Ошибка", f"Неверный формат JSON:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{e}")
            
    def save_data(self, file_path: Path):
        """Сохранение данных в JSON-файл"""
        try:
            # Проверка валидности данных
            for key, value in self.data.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError(f"Некорректные данные для ключа '{key}'")
                if not key.strip():
                    raise ValueError("Ключ не может быть пустым")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            self.current_file = file_path
            self.set_modified(False)
            self.save_last_path()
            
            self.status_bar.showMessage(f"Сохранено в {file_path.name}", 3000)
            self.setWindowTitle(f"Редактор словаря замен - {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
            
    def open_file(self):
        """Открытие файла"""
        if self.modified:
            reply = QMessageBox.question(
                self, "Несохраненные изменения",
                "Имеются несохраненные изменения. Сохранить перед открытием?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                if not self.save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return
                
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть файл",
            self.last_path,
            "JSON файлы (*.json);;Все файлы (*.*)"
        )
        
        if file_path:
            self.load_data(Path(file_path))
            
    def save_file(self) -> bool:
        """Сохранение файла"""
        if not self.current_file:
            return self.save_file_as()
        else:
            self.save_data(self.current_file)
            return True
            
    def save_file_as(self) -> bool:
        """Сохранение файла под новым именем"""
        if self.current_file:
            initial_path = self.current_file.parent / f"{self.current_file.stem}_new.json"
        else:
            initial_path = Path(self.last_path) / "replacement_dict.json"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            str(initial_path),
            "JSON файлы (*.json);;Все файлы (*.*)"
        )
        
        if file_path:
            self.save_data(Path(file_path))
            return True
        return False
        
    def update_table(self):
        """Обновление таблицы данными"""
        self.table.blockSignals(True)
        
        # Фильтрация данных
        search_text = self.search_input.text()
        filtered_data = self.filter_data(search_text)
        
        self.table.setRowCount(len(filtered_data))
        self.table.setUpdatesEnabled(False)
        
        for row, (key, value) in enumerate(filtered_data.items()):
            # Ключ
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Ключ только для чтения
            self.table.setItem(row, 0, key_item)
            
            # Значение
            value_item = QTableWidgetItem(value)
            self.table.setItem(row, 1, value_item)
            
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        
    def filter_data(self, search_text: str) -> Dict[str, str]:
        """Фильтрация данных по поисковому запросу"""
        if not search_text:
            return self.data
            
        filtered = {}
        case_sensitive = self.case_sensitive.isChecked()
        
        for key, value in self.data.items():
            if not case_sensitive:
                search_lower = search_text.lower()
                if search_lower in key.lower() or search_lower in value.lower():
                    filtered[key] = value
            else:
                if search_text in key or search_text in value:
                    filtered[key] = value
                    
        return filtered
        
    def filter_table(self):
        """Обработка изменения поискового запроса"""
        self.update_table()
        
    def on_item_changed(self, item):
        """Обработка изменения значения в таблице"""
        if item.column() != 1:  # Только изменение значения
            return
            
        row = item.row()
        key_item = self.table.item(row, 0)
        if not key_item:
            return
            
        key = key_item.text()
        new_value = item.text()
        
        # Находим оригинальный ключ в данных (учитывая фильтрацию)
        filtered = self.filter_data(self.search_input.text())
        filtered_keys = list(filtered.keys())
        if row < len(filtered_keys):
            original_key = filtered_keys[row]
            
            if original_key in self.data and self.data[original_key] != new_value:
                self.data[original_key] = new_value
                self.set_modified(True)
                
                # Обновляем панель редактирования
                if self.current_row == row:
                    self.edit_key.setText(original_key)
                    self.edit_value.setText(new_value)
                    
    def on_current_cell_changed(self, current_row, current_col, previous_row, previous_col):
        """Обработка смены выбранной строки"""
        if current_row >= 0:
            self.current_row = current_row
            filtered = self.filter_data(self.search_input.text())
            filtered_keys = list(filtered.keys())
            
            if current_row < len(filtered_keys):
                key = filtered_keys[current_row]
                value = self.data[key]
                
                self.edit_key.blockSignals(True)
                self.edit_value.blockSignals(True)
                
                self.edit_key.setText(key)
                self.edit_value.setText(value)
                self.update_preview_text(key, value)
                
                self.edit_key.blockSignals(False)
                self.edit_value.blockSignals(False)
                
                self.btn_update.setEnabled(False)
                self.btn_cancel.setEnabled(False)
                
    def on_edit_changed(self):
        """Обработка изменения в панели редактирования"""
        if self.current_row >= 0:
            self.btn_update.setEnabled(True)
            self.btn_cancel.setEnabled(True)
            self.preview_timer.start(300)
            
    def update_preview(self):
        """Обновление предпросмотра"""
        key = self.edit_key.text()
        value = self.edit_value.text()
        self.update_preview_text(key, value)
        
    def update_preview_text(self, key: str, value: str):
        """Обновление текста предпросмотра"""
        if key and value:
            preview = f'"{key}" → "{value}"'
            self.preview_label.setText(preview)
        else:
            self.preview_label.setText("Введите ключ и значение для предпросмотра")
            
    def update_current_entry(self):
        """Обновление текущей записи"""
        if self.current_row < 0:
            return
            
        new_key = self.edit_key.text().strip()
        new_value = self.edit_value.text().strip()
        
        if not new_key:
            QMessageBox.warning(self, "Ошибка", "Ключ не может быть пустым")
            return
            
        if not new_value:
            QMessageBox.warning(self, "Ошибка", "Значение не может быть пустым")
            return
            
        filtered = self.filter_data(self.search_input.text())
        filtered_keys = list(filtered.keys())
        
        if self.current_row < len(filtered_keys):
            old_key = filtered_keys[self.current_row]
            
            # Проверка на дубликат ключа (если ключ изменен)
            if new_key != old_key and new_key in self.data:
                QMessageBox.warning(
                    self, "Ошибка",
                    f"Ключ '{new_key}' уже существует. Используйте уникальные ключи."
                )
                return
                
            # Обновляем данные
            if new_key != old_key:
                del self.data[old_key]
            self.data[new_key] = new_value
            
            self.set_modified(True)
            self.update_table()
            
            # Находим новую позицию в таблице
            filtered = self.filter_data(self.search_input.text())
            filtered_keys = list(filtered.keys())
            if new_key in filtered_keys:
                new_row = filtered_keys.index(new_key)
                self.table.selectRow(new_row)
                
            self.btn_update.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            
    def cancel_edit(self):
        """Отмена редактирования"""
        if self.current_row >= 0:
            filtered = self.filter_data(self.search_input.text())
            filtered_keys = list(filtered.keys())
            
            if self.current_row < len(filtered_keys):
                key = filtered_keys[self.current_row]
                value = self.data[key]
                
                self.edit_key.blockSignals(True)
                self.edit_value.blockSignals(True)
                
                self.edit_key.setText(key)
                self.edit_value.setText(value)
                self.update_preview_text(key, value)
                
                self.edit_key.blockSignals(False)
                self.edit_value.blockSignals(False)
                
                self.btn_update.setEnabled(False)
                self.btn_cancel.setEnabled(False)
                
    def add_entry(self):
        """Добавление новой записи"""
        key, ok = QInputDialog.getText(
            self, "Добавить запись",
            "Введите ключ (слово или фразу для замены):"
        )
        
        if ok and key:
            if key in self.data:
                QMessageBox.warning(self, "Ошибка", f"Ключ '{key}' уже существует")
                return
                
            value, ok = QInputDialog.getText(
                self, "Добавить запись",
                f"Введите значение для ключа '{key}':"
            )
            
            if ok and value:
                self.data[key] = value
                self.set_modified(True)
                self.update_table()
                self.status_bar.showMessage(f"Добавлена запись: {key} → {value}", 2000)
                
    def delete_entry(self):
        """Удаление текущей записи"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите запись для удаления")
            return
            
        filtered = self.filter_data(self.search_input.text())
        filtered_keys = list(filtered.keys())
        
        if current_row < len(filtered_keys):
            key = filtered_keys[current_row]
            value = self.data[key]
            
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Удалить запись:\n'{key}' → '{value}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.data[key]
                self.set_modified(True)
                self.update_table()
                
                # Очищаем панель редактирования
                self.edit_key.clear()
                self.edit_value.clear()
                self.preview_label.clear()
                self.current_row = -1
                self.btn_update.setEnabled(False)
                self.btn_cancel.setEnabled(False)
                
                self.status_bar.showMessage(f"Удалена запись: {key}", 2000)
                
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.modified:
            reply = QMessageBox.question(
                self, "Несохраненные изменения",
                "Имеются несохраненные изменения. Сохранить перед выходом?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                if not self.save_file():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
                
        self.save_last_path()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ReplacementEditor")
    app.setOrganizationName("ReplacementEditor")
    
    # Установка стиля
    app.setStyle('Fusion')
    
    window = ReplacementEditor()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
EOF