"""
capitalizer.py - Капитализация предложений
"""

import re
from typing import List


class Capitalizer:
    """Класс для капитализации предложений"""
    
    def __init__(self):
        """Инициализация капитализатора"""
        self.razdel_available = self._check_razdel()
    
    def _check_razdel(self) -> bool:
        """Проверяет наличие razdel"""
        try:
            from razdel import sentenize
            return True
        except ImportError:
            print("⚠️ razdel не установлен. Используется простая капитализация.")
            return False
    
    def capitalize(self, text: str) -> str:
        """
        Капитализация предложений
        
        Args:
            text: исходный текст
            
        Returns:
            текст с заглавными буквами в начале предложений
        """
        if not text:
            return text
        
        if self.razdel_available:
            return self._capitalize_with_razdel(text)
        else:
            return self._capitalize_simple(text)
    
    def _capitalize_with_razdel(self, text: str) -> str:
        """Капитализация через razdel"""
        try:
            from razdel import sentenize
            
            sentences = list(sentenize(text))
            capitalized = []
            
            for sent in sentences:
                if sent.text:
                    first_char = sent.text[0].upper()
                    rest = sent.text[1:]
                    capitalized.append(first_char + rest)
            
            return ' '.join(capitalized)
        except Exception:
            return self._capitalize_simple(text)
    
    def _capitalize_simple(self, text: str) -> str:
        """
        Простая капитализация (первое слово текста)
        
        Используется когда razdel недоступен
        """
        if not text:
            return text
        
        # Первая буква заглавная
        result = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Заглавные буквы после точек (упрощённо)
        result = re.sub(r'(\.\s+)([a-zа-я])', lambda m: m.group(1) + m.group(2).upper(), result)
        
        return result