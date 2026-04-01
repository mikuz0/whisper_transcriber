"""
base.py - Базовый класс постпроцессора
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from .text_cleaner import TextCleaner
from .capitalizer import Capitalizer
from .replacement_dict import ReplacementDictionary


class TextPostprocessor:
    """
    Гибридный постпроцессор текста
    
    Этапы обработки:
    1. Очистка текста (пробелы, знаки препинания)
    2. Исправление типичных ошибок распознавания (встроенный словарь)
    3. Словарь замен (пользовательский JSON)
    4. Капитализация предложений (опционально)
    """
    
    LEVEL_MINIMAL = 'minimal'      # только очистка + словарь замен
    LEVEL_STANDARD = 'standard'    # очистка + словарь замен
    LEVEL_FULL = 'full'            # + капитализация предложений
    
    def __init__(self, language: str = 'ru', level: str = LEVEL_STANDARD, 
                 cache_dir: Optional[str] = None, logger_callback=None):
        """
        Args:
            language: язык текста ('ru', 'en')
            level: уровень постобработки
            cache_dir: директория для кэша
            logger_callback: функция для логирования
        """
        self.language = language
        self.level = level
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.logger = logger_callback or print
        
        # Инициализация компонентов
        self.cleaner = TextCleaner(language=self.language)
        self.replacement_dict = ReplacementDictionary(self.logger)
        self.capitalizer = None
        
        # Капитализация только для полного уровня
        if self.level == self.LEVEL_FULL:
            self.capitalizer = Capitalizer()
        
        # Статистика
        self.stats = {
            'processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'words_changed': 0,
            'sentences_capitalized': 0
        }
    
    def _get_cache_key(self, text: str) -> str:
        """Генерирует ключ для кэша"""
        content = f"{text}_{self.language}_{self.level}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_from_cache(self, key: str) -> Optional[str]:
        """Загружает результат из кэша"""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats['cache_hits'] += 1
                    return data.get('text')
            except Exception:
                pass
        
        self.stats['cache_misses'] += 1
        return None
    
    def _save_to_cache(self, key: str, text: str):
        """Сохраняет результат в кэш"""
        if not self.cache_dir:
            return
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({'text': text}, f, ensure_ascii=False)
        except Exception:
            pass
    
    def process(self, text: str, use_cache: bool = True) -> str:
        """
        Основной метод постобработки текста
        
        Безопасный подход:
        - Исправляет только явные ошибки через словарь замен
        - Не ломает грамматику
        - Только форматирование
        """
        if not text or not text.strip():
            return text
        
        # Проверка кэша
        cache_key = None
        if use_cache and self.cache_dir:
            cache_key = self._get_cache_key(text)
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                return cached
        
        original_text = text
        
        # Этап 1: Очистка текста (пробелы, знаки препинания)
        result = self.cleaner.clean(text)
        
        # Этап 2: Исправление типичных ошибок Whisper (встроенный словарь)
        result = self.cleaner.fix_common_errors(result)
        
        # Этап 3: Словарь замен (пользовательский JSON)
        result = self.replacement_dict.apply(result)
        
        # Подсчёт изменений
        if original_text != result:
            self.stats['words_changed'] += 1
        
        # Этап 4: Капитализация (только для полного уровня)
        if self.capitalizer:
            before_cap = result
            result = self.capitalizer.capitalize(result)
            if before_cap != result:
                self.stats['sentences_capitalized'] += 1
        
        # Сохранение в кэш
        if cache_key and use_cache and self.cache_dir:
            self._save_to_cache(cache_key, result)
        
        self.stats['processed'] += 1
        return result
    
    def process_file(self, input_path: Path, output_path: Path, use_cache: bool = True) -> Tuple[bool, str]:
        """
        Обрабатывает файл целиком
        
        Args:
            input_path: путь к исходному файлу
            output_path: путь для сохранения результата
            use_cache: использовать ли кэш
            
        Returns:
            (success, message)
        """
        if not input_path.exists():
            return False, f"Файл не найден: {input_path}"
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            processed = self.process(content, use_cache)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed)
            
            return True, f"Обработан: {input_path.name}"
            
        except Exception as e:
            return False, f"Ошибка обработки {input_path.name}: {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы постпроцессора"""
        return {
            'processed': self.stats['processed'],
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'words_changed': self.stats['words_changed'],
            'sentences_capitalized': self.stats['sentences_capitalized'],
            'level': self.level,
            'language': self.language,
            'replacements_count': self.replacement_dict.get_count()
        }
    
    def reset_stats(self):
        """Сбрасывает статистику"""
        self.stats = {
            'processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'words_changed': 0,
            'sentences_capitalized': 0
        }
    
    def reload_dictionary(self):
        """Перезагружает словарь замен"""
        self.replacement_dict.reload()
        self.logger(f"🔄 Словарь замен перезагружен: {self.replacement_dict.get_count()} записей", "info")