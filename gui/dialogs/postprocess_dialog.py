"""
postprocess_dialog.py - Диалог настройки постобработки
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QGroupBox, QListWidget, QListWidgetItem,
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt


class PostprocessDialog(QWidget):
    """Диалог настройки постобработки (гибкий порядок действий)"""
    
    # Доступные действия
    AVAILABLE_ACTIONS = {
        'cleanup': {
            'name': 'Очистка текста',
            'description': 'Нормализация пробелов, знаков препинания, удаление лишних пробелов',
            'icon': '🧹',
            'recommended_position': 'first'
        },
        'replacement_dict': {
            'name': 'Словарь замен',
            'description': 'Исправление конкретных слов/фраз из JSON-словаря',
            'icon': '📖',
            'recommended_position': 'before_grammar'
        },
        'capitalization': {
            'name': 'Капитализация',
            'description': 'Заглавные буквы в начале предложений',
            'icon': '🔠',
            'recommended_position': 'after_dict'
        },
        'grammar_check': {
            'name': 'Грамматическая проверка',
            'description': 'Проверка и исправление грамматики через LanguageTool',
            'icon': '🔤',
            'recommended_position': 'last'
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
        
        # Информационная метка
        info_label = QLabel(
            "Выберите действия и установите порядок их выполнения.\n"
            "Перетаскивайте элементы мышью для изменения порядка."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Горизонтальное расположение
        main_layout = QHBoxLayout()
        
        # Левая панель: выбор действий
        left_panel = QGroupBox("Доступные действия")
        left_layout = QVBoxLayout(left_panel)
        
        self.action_checkboxes = {}
        for action_id, action_info in self.AVAILABLE_ACTIONS.items():
            cb = QCheckBox()
            cb.setText(f"{action_info['icon']} {action_info['name']}")
            cb.setToolTip(action_info['description'])
            cb.stateChanged.connect(self.update_recommendation)
            self.action_checkboxes[action_id] = cb
            left_layout.addWidget(cb)
        
        left_layout.addStretch()
        
        # Правая панель: порядок выполнения
        right_panel = QGroupBox("Порядок выполнения (перетаскивайте)")
        right_layout = QVBoxLayout(right_panel)
        
        self.order_list = QListWidget()
        self.order_list.setDragDropMode(QListWidget.InternalMove)
        self.order_list.setSelectionMode(QListWidget.SingleSelection)
        self.order_list.setMinimumHeight(200)
        self.order_list.model().rowsMoved.connect(self.update_recommendation)
        right_layout.addWidget(self.order_list)
        
        # Кнопки управления порядком
        order_buttons_layout = QHBoxLayout()
        
        self.btn_up = QPushButton("↑ Вверх")
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down = QPushButton("↓ Вниз")
        self.btn_down.clicked.connect(self.move_down)
        
        order_buttons_layout.addWidget(self.btn_up)
        order_buttons_layout.addWidget(self.btn_down)
        order_buttons_layout.addStretch()
        
        right_layout.addLayout(order_buttons_layout)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        layout.addLayout(main_layout)
        
        # Область рекомендаций
        self.recommendation_area = QFrame()
        self.recommendation_area.setFrameShape(QFrame.Box)
        self.recommendation_area.setStyleSheet("background-color: #f5f5f5; padding: 5px;")
        rec_layout = QVBoxLayout(self.recommendation_area)
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        rec_layout.addWidget(self.recommendation_label)
        layout.addWidget(self.recommendation_area)
        
        # Подключаем сигналы
        for cb in self.action_checkboxes.values():
            cb.stateChanged.connect(self.update_order_list)
        
        self.update_order_list()
    
    def move_up(self):
        """Перемещает выбранный элемент вверх"""
        current_row = self.order_list.currentRow()
        if current_row > 0:
            item = self.order_list.takeItem(current_row)
            self.order_list.insertItem(current_row - 1, item)
            self.order_list.setCurrentRow(current_row - 1)
            self.update_recommendation()
    
    def move_down(self):
        """Перемещает выбранный элемент вниз"""
        current_row = self.order_list.currentRow()
        if current_row < self.order_list.count() - 1:
            item = self.order_list.takeItem(current_row)
            self.order_list.insertItem(current_row + 1, item)
            self.order_list.setCurrentRow(current_row + 1)
            self.update_recommendation()
    
    def update_order_list(self):
        """Обновляет список порядка на основе выбранных действий"""
        self.order_list.clear()
        
        # Получаем выбранные действия
        selected = [aid for aid, cb in self.action_checkboxes.items() if cb.isChecked()]
        
        # Загружаем сохранённый порядок или используем порядок по умолчанию
        saved_order = self.config.get('postprocess_order', None)
        
        if saved_order:
            ordered = [aid for aid in saved_order if aid in selected]
            for aid in selected:
                if aid not in ordered:
                    ordered.append(aid)
            selected = ordered
        
        # Добавляем в список
        for action_id in selected:
            action_info = self.AVAILABLE_ACTIONS.get(action_id, {})
            item = QListWidgetItem(f"{action_info.get('icon', '')} {action_info.get('name', action_id)}")
            item.setData(Qt.UserRole, action_id)
            self.order_list.addItem(item)
    
    def get_order(self) -> list:
        """Возвращает текущий порядок действий"""
        order = []
        for i in range(self.order_list.count()):
            item = self.order_list.item(i)
            action_id = item.data(Qt.UserRole)
            order.append(action_id)
        return order
    
    def get_selected_actions(self) -> list:
        """Возвращает список выбранных действий"""
        return [aid for aid, cb in self.action_checkboxes.items() if cb.isChecked()]
    
    def update_recommendation(self):
        """Обновляет рекомендации на основе выбранных действий и порядка"""
        selected = self.get_selected_actions()
        order = self.get_order()
        recommendations = []
        
        # Проверка 1: Словарь замен до капитализации
        if 'capitalization' in selected and 'replacement_dict' in selected:
            try:
                cap_idx = order.index('capitalization')
                dict_idx = order.index('replacement_dict')
                if cap_idx < dict_idx:
                    recommendations.append({
                        'level': 'warning',
                        'text': '⚠️ Словарь замен лучше применять до капитализации, чтобы не сломать регистр слов.'
                    })
            except ValueError:
                pass
        
        # Проверка 2: Словарь замен до грамматики
        if 'grammar_check' in selected and 'replacement_dict' in selected:
            try:
                grammar_idx = order.index('grammar_check')
                dict_idx = order.index('replacement_dict')
                if grammar_idx < dict_idx:
                    recommendations.append({
                        'level': 'warning',
                        'text': '⚠️ Словарь замен лучше применять до грамматической проверки для лучших результатов.'
                    })
            except ValueError:
                pass
        
        # Проверка 3: Очистка в начале
        if 'cleanup' in selected:
            try:
                cleanup_idx = order.index('cleanup')
                if cleanup_idx > 0:
                    recommendations.append({
                        'level': 'info',
                        'text': 'ℹ️ Очистку текста рекомендуется выполнять первой, чтобы нормализовать пробелы и знаки препинания.'
                    })
            except ValueError:
                pass
        
        # Проверка 4: Грамматика в конце
        if 'grammar_check' in selected:
            try:
                grammar_idx = order.index('grammar_check')
                if grammar_idx < len(order) - 1:
                    recommendations.append({
                        'level': 'info',
                        'text': 'ℹ️ Грамматическую проверку рекомендуется выполнять последней, так как она может изменять текст.'
                    })
            except ValueError:
                pass
        
        # Проверка 5: Только грамматика без словаря
        if 'grammar_check' in selected and 'replacement_dict' not in selected:
            recommendations.append({
                'level': 'info',
                'text': 'ℹ️ LanguageTool не исправляет специфические ошибки. Рекомендуется добавить словарь замен.'
            })
        
        # Проверка 6: Нет выбранных действий
        if not selected:
            recommendations.append({
                'level': 'error',
                'text': '❌ Не выбрано ни одного действия. Текст не будет обработан.'
            })
        
        # Формируем текст рекомендаций
        if recommendations:
            rec_text = '<b>Рекомендации:</b><br><br>'
            for rec in recommendations:
                rec_text += f'{rec["text"]}<br>'
            self.recommendation_label.setText(rec_text)
            if any(r['level'] == 'warning' for r in recommendations):
                self.recommendation_area.setStyleSheet("background-color: #fff3cd; border: 1px solid #ffc107; padding: 5px;")
            elif any(r['level'] == 'error' for r in recommendations):
                self.recommendation_area.setStyleSheet("background-color: #f8d7da; border: 1px solid #dc3545; padding: 5px;")
            else:
                self.recommendation_area.setStyleSheet("background-color: #e6f7e6; border: 1px solid #28a745; padding: 5px;")
        else:
            self.recommendation_label.setText("✅ Оптимальная конфигурация.")
            self.recommendation_area.setStyleSheet("background-color: #e6f7e6; border: 1px solid #28a745; padding: 5px;")
    
    def load_settings(self):
        """Загружает настройки из конфига"""
        # Загружаем выбранные действия
        actions = self.config.get('postprocess_actions', ['cleanup', 'replacement_dict'])
        for action_id, cb in self.action_checkboxes.items():
            cb.setChecked(action_id in actions)
        
        self.update_order_list()
        self.update_recommendation()
    
    def save_settings(self):
        """Сохраняет настройки в конфиг"""
        selected = self.get_selected_actions()
        order = self.get_order()
        
        self.config.set('postprocess_actions', selected)
        self.config.set('postprocess_order', order)
    
    def get_postprocess_config(self) -> dict:
        """Возвращает конфигурацию постобработки"""
        return {
            'actions': self.get_selected_actions(),
            'order': self.get_order()
        }