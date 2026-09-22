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
    
    AVAILABLE_ACTIONS = {
        'cleanup': {
            'name': 'Очистка текста',
            'description': 'Нормализация пробелов, знаков препинания',
            'icon': '🧹'
        },
        'replacement_dict': {
            'name': 'Словарь замен',
            'description': 'Исправление слов из JSON-словаря',
            'icon': '📖'
        },
        'capitalization': {
            'name': 'Капитализация',
            'description': 'Заглавные буквы в начале предложений',
            'icon': '🔠'
        }
    }
    
    def __init__(self, config_manager, parent=None, embedded=False):
        super().__init__(parent)
        self.config = config_manager
        self.embedded = embedded
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(
            "Выберите действия и установите порядок их выполнения.\n"
            "Перетаскивайте элементы мышью для изменения порядка."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        main_layout = QHBoxLayout()
        
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
        
        right_panel = QGroupBox("Порядок выполнения")
        right_layout = QVBoxLayout(right_panel)
        
        self.order_list = QListWidget()
        self.order_list.setDragDropMode(QListWidget.InternalMove)
        self.order_list.setSelectionMode(QListWidget.SingleSelection)
        self.order_list.setMinimumHeight(200)
        right_layout.addWidget(self.order_list)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        layout.addLayout(main_layout)
        
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("color: #666; padding: 5px; background-color: #f5f5f5;")
        layout.addWidget(self.recommendation_label)
        
        for cb in self.action_checkboxes.values():
            cb.stateChanged.connect(self.update_order_list)
        
        self.update_order_list()
    
    def update_order_list(self):
        self.order_list.clear()
        selected = [aid for aid, cb in self.action_checkboxes.items() if cb.isChecked()]
        for action_id in selected:
            action_info = self.AVAILABLE_ACTIONS.get(action_id, {})
            item = QListWidgetItem(f"{action_info.get('icon', '')} {action_info.get('name', action_id)}")
            item.setData(Qt.UserRole, action_id)
            self.order_list.addItem(item)
    
    def get_order(self) -> list:
        order = []
        for i in range(self.order_list.count()):
            item = self.order_list.item(i)
            action_id = item.data(Qt.UserRole)
            order.append(action_id)
        return order
    
    def get_selected_actions(self) -> list:
        return [aid for aid, cb in self.action_checkboxes.items() if cb.isChecked()]
    
    def update_recommendation(self):
        selected = self.get_selected_actions()
        if not selected:
            self.recommendation_label.setText("⚠️ Не выбрано ни одного действия")
        else:
            self.recommendation_label.setText(f"✅ Выбрано действий: {len(selected)}")
    
    def load_settings(self):
        actions = self.config.get('postprocess_actions', ['cleanup', 'replacement_dict'])
        for action_id, cb in self.action_checkboxes.items():
            cb.setChecked(action_id in actions)
        self.update_order_list()
    
    def save_settings(self):
        selected = self.get_selected_actions()
        order = self.get_order()
        self.config.set('postprocess_actions', selected)
        self.config.set('postprocess_order', order)
