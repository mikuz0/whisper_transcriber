"""
Управление сохранением/загрузкой конфигурации
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
        'language': 'auto',
        'output_format': 'txt',
        'last_used_tab': 0
    }
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = Path(config_path)
        self.config = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Объединяем с дефолтными значениями
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(saved_config)
                    return config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self, config: Dict[str, Any]) -> bool:
        """Сохраняет конфигурацию в файл"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Получает значение из конфигурации"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Устанавливает значение в конфигурации и сохраняет"""
        self.config[key] = value
        self.save(self.config)