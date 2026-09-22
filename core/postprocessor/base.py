"""
base.py - Базовый класс постпроцессора
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
    """Постпроцессор текста с настраиваемыми действиями"""
    
    ACTION_CLASSES = {
        'cleanup': TextCleaner,
        'replacement_dict': ReplacementDictionary,
        'capitalization': Capitalizer,
        'grammar_check': GrammarChecker  # Заглушка, не будет работать
    }
    
    def __init__(self, language: str = 'ru', 
                 actions: List[str] = None,
                 action_order: List[str] = None,
                 cache_dir: Optional[str] = None, 
                 logger_callback=None):
        self.language = language
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.logger = logger_callback or print
        
        self.actions = actions or ['cleanup', 'replacement_dict']
        self.action_order = action_order or ['cleanup', 'replacement_dict']
        
        self.action_instances = []
        self._init_actions()
        
        self.stats = {
            'processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'words_changed': 0,
            'sentences_capitalized': 0,
            'grammar_corrections': 0
        }
    
    def _init_actions(self):
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
                    self.logger(f"🔧 Инициализировано: {action_name}", "info")
                elif action_name == 'replacement_dict':
                    instance = action_class(logger_callback=self.logger)
                    self.logger(f"🔧 Инициализировано: {action_name} ({instance.get_count()} записей)", "info")
                elif action_name == 'capitalization':
                    instance = action_class()
                    self.logger(f"🔧 Инициализировано: {action_name}", "info")
                elif action_name == 'grammar_check':
                    instance = action_class(logger_callback=self.logger)
                    self.logger(f"⚠️ {action_name} отключён (заглушка)", "warning")
                else:
                    instance = action_class()
                    self.logger(f"🔧 Инициализировано: {action_name}", "info")
                
                self.action_instances.append((action_name, instance))
            except Exception as e:
                self.logger(f"⚠️ Ошибка инициализации {action_name}: {e}", "warning")
    
    def process(self, text: str, use_cache: bool = True) -> str:
        if not text or not text.strip():
            return text
        
        result = text
        
        for action_name, action_instance in self.action_instances:
            try:
                if action_name == 'cleanup':
                    result = action_instance.clean(result)
                    result = action_instance.fix_common_errors(result)
                elif action_name == 'replacement_dict':
                    result = action_instance.apply(result)
                elif action_name == 'capitalization':
                    result = action_instance.capitalize(result)
                elif action_name == 'grammar_check':
                    # Заглушка - ничего не делает
                    pass
                elif hasattr(action_instance, 'apply'):
                    result = action_instance.apply(result)
                elif hasattr(action_instance, 'process'):
                    result = action_instance.process(result)
            except Exception as e:
                self.logger(f"⚠️ Ошибка в {action_name}: {e}", "warning")
        
        self.stats['processed'] += 1
        return result
    
    def process_interactive(self, text: str, parent=None) -> str:
        return self.process(text, use_cache=False)
    
    def process_file(self, input_path: Path, output_path: Path, use_cache: bool = True) -> Tuple[bool, str]:
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
            return False, f"Ошибка: {str(e)}"
    
    def process_file_interactive(self, input_path: Path, output_path: Path, parent=None) -> Tuple[bool, str]:
        return self.process_file(input_path, output_path, use_cache=False)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'processed': self.stats['processed'],
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'words_changed': self.stats['words_changed'],
            'sentences_capitalized': self.stats['sentences_capitalized'],
            'grammar_corrections': self.stats['grammar_corrections'],
            'actions': self.actions,
            'action_order': self.action_order
        }
    
    def reset_stats(self):
        self.stats = {
            'processed': 0, 'cache_hits': 0, 'cache_misses': 0,
            'words_changed': 0, 'sentences_capitalized': 0, 'grammar_corrections': 0
        }
