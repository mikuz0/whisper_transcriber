"""
base.py - Базовый класс постпроцессора с гибкой конфигурацией
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from .text_cleaner import TextCleaner
from .capitalizer import Capitalizer
from .replacement_dict import ReplacementDictionary
from .grammar_checker import GrammarChecker


class TextPostprocessor:
    """
    Гибридный постпроцессор текста с настраиваемыми действиями
    
    Пользователь может выбирать любые действия и устанавливать их порядок.
    """
    
    # Доступные действия и их классы
    ACTION_CLASSES = {
        'cleanup': TextCleaner,
        'replacement_dict': ReplacementDictionary,
        'capitalization': Capitalizer,
        'grammar_check': GrammarChecker
    }
    
    def __init__(self, language: str = 'ru', 
                 actions: List[str] = None,
                 action_order: List[str] = None,
                 cache_dir: Optional[str] = None, 
                 logger_callback=None):
        """
        Args:
            language: язык текста ('ru', 'en')
            actions: список выбранных действий
            action_order: порядок выполнения действий
            cache_dir: директория для кэша
            logger_callback: функция для логирования
        """
        self.language = language
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.logger = logger_callback or print
        
        # Настройка действий
        self.actions = actions or ['cleanup', 'replacement_dict']
        self.action_order = action_order or ['cleanup', 'replacement_dict']
        
        # Инициализация компонентов
        self.action_instances = []
        self._init_actions()
        
        # Статистика
        self.stats = {
            'processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'words_changed': 0,
            'sentences_capitalized': 0,
            'grammar_corrections': 0
        }
    
    def _init_actions(self):
        """Инициализирует выбранные действия в заданном порядке"""
        for action_name in self.action_order:
            if action_name not in self.actions:
                continue
            
            action_class = self.ACTION_CLASSES.get(action_name)
            if not action_class:
                self.logger(f"⚠️ Неизвестное действие: {action_name}", "warning")
                continue
            
            try:
                if action_name == 'cleanup':
                    instance = action_class(language=self.language)
                    self.logger(f"🔧 Инициализировано действие: {action_name}", "info")
                    
                elif action_name == 'replacement_dict':
                    instance = action_class(logger_callback=self.logger)
                    self.logger(f"🔧 Инициализировано действие: {action_name} ({instance.get_count()} записей)", "info")
                    
                elif action_name == 'capitalization':
                    instance = action_class()
                    self.logger(f"🔧 Инициализировано действие: {action_name}", "info")
                    
                elif action_name == 'grammar_check':
                    # ВАЖНО: передаём все параметры для корректной работы
                    lang_code = 'ru-RU' if self.language == 'ru' else 'en-US'
                    instance = GrammarChecker(
                        language=lang_code,
                        logger_callback=self.logger,
                        use_local=True
                    )
                    if instance.tool:
                        self.logger(f"🔧 Инициализировано действие: {action_name} (локальный сервер)", "info")
                    else:
                        self.logger(f"⚠️ Действие {action_name} недоступно", "warning")
                        
                else:
                    instance = action_class()
                    self.logger(f"🔧 Инициализировано действие: {action_name}", "info")
                
                self.action_instances.append((action_name, instance))
                
            except Exception as e:
                self.logger(f"⚠️ Ошибка инициализации {action_name}: {e}", "warning")
    
    def _get_cache_key(self, text: str) -> str:
        """Генерирует ключ для кэша"""
        content = f"{text}_{self.language}_{'_'.join(self.action_order)}"
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
        
        Применяет выбранные действия в заданном порядке.
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
        result = text
        
        # Применяем действия последовательно
        for action_name, action_instance in self.action_instances:
            before = result
            
            try:
                # Очистка текста
                if action_name == 'cleanup':
                    result = action_instance.clean(result)
                    result = action_instance.fix_common_errors(result)
                    
                # Словарь замен
                elif action_name == 'replacement_dict':
                    result = action_instance.apply(result)
                    if before != result:
                        self.stats['words_changed'] += 1
                        
                # Капитализация
                elif action_name == 'capitalization':
                    result = action_instance.capitalize(result)
                    if before != result:
                        self.stats['sentences_capitalized'] += 1
                        
                # Грамматическая проверка
                elif action_name == 'grammar_check':
                    if action_instance.tool:
                        result, changes = action_instance.check_and_report(result)
                        if changes:
                            self.stats['grammar_corrections'] += len(changes)
                            self.logger(f"📝 Грамматические исправления: {len(changes)}", "info")
                    else:
                        # Если LanguageTool не доступен, просто пропускаем
                        pass
                        
                # Универсальный вызов (fallback)
                elif hasattr(action_instance, 'apply'):
                    result = action_instance.apply(result)
                elif hasattr(action_instance, 'process'):
                    result = action_instance.process(result)
                else:
                    # fallback
                    result = action_instance(result) if callable(action_instance) else result
                
                # Логируем изменения для отладки
                if before != result and action_name not in ['grammar_check']:
                    self.logger(f"   Действие '{action_name}': текст изменён", "debug")
                    
            except Exception as e:
                self.logger(f"⚠️ Ошибка в действии '{action_name}': {e}", "warning")
        
        # Сохранение в кэш
        if cache_key and use_cache and self.cache_dir:
            self._save_to_cache(cache_key, result)
        
        self.stats['processed'] += 1
        return result
    
    def process_file(self, input_path: Path, output_path: Path, use_cache: bool = True) -> Tuple[bool, str]:
        """Обрабатывает файл целиком"""
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
        # Получаем количество записей в словаре замен, если он активен
        replacements_count = 0
        for action_name, action_instance in self.action_instances:
            if action_name == 'replacement_dict':
                replacements_count = action_instance.get_count()
                break
        
        return {
            'processed': self.stats['processed'],
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'words_changed': self.stats['words_changed'],
            'sentences_capitalized': self.stats['sentences_capitalized'],
            'grammar_corrections': self.stats['grammar_corrections'],
            'actions': self.actions,
            'action_order': self.action_order,
            'replacements_count': replacements_count
        }
    
    def reset_stats(self):
        """Сбрасывает статистику"""
        self.stats = {
            'processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'words_changed': 0,
            'sentences_capitalized': 0,
            'grammar_corrections': 0
        }