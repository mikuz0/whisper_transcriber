"""
lemmatizer.py - Лемматизация текста с использованием pymystem3 и словаря исключений
"""

import re
from typing import Optional, Dict, List


class Lemmatizer:
    """
    Класс для лемматизации текста
    
    Использует pymystem3 для основной лемматизации
    и словарь исключений для исправления проблемных слов
    """
    
    # Словарь исключений для просторечных форм
    EXCEPTIONS = {
        # Просторечные формы глаголов
        'пошол': 'пойти',
        'пришол': 'прийти',
        'ишол': 'идти',
        'пошоть': 'пойти',      # Ошибка Natasha
        'пришоть': 'прийти',    # Ошибка Natasha
        
        # Другие просторечные формы
        'ихний': 'их',
        'евонный': 'его',
        'ейный': 'её',
        
        # Сокращения
        'щас': 'сейчас',
        'ща': 'сейчас',
        'токо': 'только',
        'тока': 'только',
    }
    
    def __init__(self, language: str = 'ru'):
        """
        Args:
            language: язык текста ('ru', 'en')
        """
        self.language = language
        self.mystem = None
        
        if language == 'ru':
            self._init_mystem()
    
    def _init_mystem(self):
        """Инициализирует pymystem3"""
        try:
            from pymystem3 import Mystem
            self.mystem = Mystem()
        except ImportError:
            print("⚠️ pymystem3 не установлен. Лемматизация будет ограничена словарём исключений.")
            self.mystem = None
        except Exception as e:
            print(f"⚠️ Ошибка загрузки pymystem3: {e}")
            self.mystem = None
    
    def lemmatize(self, text: str) -> str:
        """
        Лемматизация текста
        
        Args:
            text: исходный текст
            
        Returns:
            текст с исправленными окончаниями
        """
        if not text or not self.mystem:
            return text
        
        try:
            lemmas = self.mystem.lemmatize(text)
            result = ''.join(lemmas)
            return result
        except Exception as e:
            print(f"⚠️ Ошибка лемматизации: {e}")
            return text
    
    def apply_exceptions(self, text: str) -> str:
        """
        Применяет словарь исключений
        
        Args:
            text: текст после лемматизации
            
        Returns:
            текст с исправленными исключениями
        """
        if not text:
            return text
        
        for wrong, correct in self.EXCEPTIONS.items():
            # Заменяем слово целиком, а не часть
            text = re.sub(r'\b' + wrong + r'\b', correct, text)
        
        return text