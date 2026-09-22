"""
config_manager.py - Управление сохранением/загрузкой конфигурации
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Сохранение и загрузка настроек приложения"""
    
    DEFAULT_CONFIG = {
        'work_directory': '',
        'whisper_model': 'base',
        'output_formats': ['txt'],
        'postprocess_actions': ['cleanup', 'replacement_dict'],
        'postprocess_order': ['cleanup', 'replacement_dict'],
        'interactive_mode': False,
        'last_used_tab': 0
    }
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = Path(config_path)
        self.config = self.load()
    
    def load(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(saved_config)
                    return config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self, config: Dict[str, Any]) -> bool:
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value
        self.save(self.config)
    
    def get_postprocess_config(self) -> Dict[str, Any]:
        return {
            'actions': self.get('postprocess_actions', ['cleanup', 'replacement_dict']),
            'order': self.get('postprocess_order', ['cleanup', 'replacement_dict'])
        }
    
    def set_postprocess_config(self, actions: list, order: list):
        self.set('postprocess_actions', actions)
        self.set('postprocess_order', order)
    
    def get_interactive_mode(self) -> bool:
        return self.get('interactive_mode', False)
    
    def set_interactive_mode(self, enabled: bool):
        self.set('interactive_mode', enabled)