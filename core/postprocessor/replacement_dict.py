"""
replacement_dict.py - Загрузчик и менеджер словаря замен
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional


class ReplacementDictionary:
    """
    Словарь замен для исправления типичных ошибок распознавания
    
    Все замены хранятся в JSON-файле data/replacement_dict.json
    Пользователь может редактировать словарь через встроенный редактор
    """
    
    def __init__(self, logger_callback=None):
        """
        Args:
            logger_callback: функция для логирования
        """
        self.logger = logger_callback or print
        self.data: Dict[str, str] = {}
        self.dict_path = self._get_dict_path()
        self._load()
    
    def _get_dict_path(self) -> Path:
        """Возвращает путь к файлу словаря"""
        # Путь относительно этого файла: core/postprocessor/ -> ../../data/
        current_dir = Path(__file__).parent
        return current_dir.parent.parent / "data" / "replacement_dict.json"
    
    def _load(self):
        """Загружает словарь из JSON-файла"""
        try:
            if self.dict_path.exists():
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                self.logger(f"📖 Загружен словарь замен: {len(self.data)} записей", "info")
            else:
                self.logger(f"⚠️ Словарь замен не найден: {self.dict_path}", "warning")
                self.data = {}
        except json.JSONDecodeError as e:
            self.logger(f"✗ Ошибка загрузки словаря: {e}", "error")
            self.data = {}
        except Exception as e:
            self.logger(f"✗ Ошибка загрузки словаря: {e}", "error")
            self.data = {}
    
    def reload(self):
        """Перезагружает словарь (полезно после редактирования)"""
        self._load()
    
    def apply(self, text: str) -> str:
        """
        Применяет все замены из словаря к тексту
        
        Args:
            text: исходный текст
            
        Returns:
            текст с применёнными заменами
        """
        if not text or not self.data:
            return text
        
        result = text
        
        # Сортируем по длине ключа (от больших к меньшим)
        # чтобы "всего лиш" заменялось раньше, чем "лиш"
        sorted_keys = sorted(self.data.keys(), key=len, reverse=True)
        
        for wrong in sorted_keys:
            correct = self.data[wrong]
            # Заменяем слово целиком, используя границы слов
            # \b - граница слова
            result = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, result)
        
        return result
    
    def add_replacement(self, wrong: str, correct: str) -> bool:
        """
        Добавляет новую замену в словарь
        
        Args:
            wrong: неправильное слово/фраза
            correct: правильный вариант
            
        Returns:
            True если успешно
        """
        if not wrong or not correct:
            return False
        
        self.data[wrong] = correct
        return self._save()
    
    def remove_replacement(self, wrong: str) -> bool:
        """
        Удаляет замену из словаря
        
        Args:
            wrong: ключ для удаления
            
        Returns:
            True если успешно
        """
        if wrong in self.data:
            del self.data[wrong]
            return self._save()
        return False
    
    def _save(self) -> bool:
        """Сохраняет словарь в JSON-файл"""
        try:
            self.dict_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dict_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger(f"✗ Ошибка сохранения словаря: {e}", "error")
            return False
    
    def get_all(self) -> Dict[str, str]:
        """Возвращает все замены"""
        return self.data.copy()
    
    def get_count(self) -> int:
        """Возвращает количество замен"""
        return len(self.data)