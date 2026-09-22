"""
text_cleaner.py - Очистка текста и исправление типичных ошибок
"""

import re
from typing import Dict


class TextCleaner:
    """Класс для очистки текста и исправления типичных ошибок"""
    
    COMMON_ERRORS = {
        'всеголиш': 'всего лишь',
        'всего лиш': 'всего лишь',
        'какбы': 'как бы',
        'как бы': 'как бы',
        'потомучто': 'потому что',
        'потомучта': 'потому что',
        'длятогочтобы': 'для того чтобы',
        'для того что бы': 'для того чтобы',
        'изза': 'из-за',
        'из за': 'из-за',
        'чтоб': 'чтобы',
        'что бы': 'чтобы',
        'таккак': 'так как',
        'так как': 'так как',
        'небыло': 'не было',
        'небудет': 'не будет',
        'немогу': 'не могу',
        'незнаю': 'не знаю',
        'нехочу': 'не хочу',
        'ненадо': 'не надо',
        
        # Английские ошибки
        'gonna': 'going to',
        'wanna': 'want to',
        'gotta': 'got to',
    }
    
    def __init__(self, language: str = 'ru'):
        self.language = language
    
    def clean(self, text: str) -> str:
        """Нормализация пробелов и знаков препинания"""
        if not text:
            return text
        
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Добавляем пробел после знаков препинания
        text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)
        
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем пробелы в начале и конце
        text = text.strip()
        
        # Убираем множественные знаки препинания
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        # Исправляем кавычки для русского языка
        if self.language == 'ru':
            text = text.replace('«', '"').replace('»', '"')
        
        return text
    
    def fix_common_errors(self, text: str) -> str:
        """Исправляет типичные ошибки распознавания"""
        if not text:
            return text
        
        for wrong, correct in self.COMMON_ERRORS.items():
            text = text.replace(wrong, correct)
        
        return text