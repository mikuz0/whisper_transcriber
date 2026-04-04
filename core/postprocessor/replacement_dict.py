"""
replacement_dict.py - Загрузчик и менеджер словаря замен
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class ReplacementDictionary:
    """
    Словарь замен для исправления типичных ошибок распознавания
    """
    
    def __init__(self, logger_callback=None, lt_tool=None):
        self.logger = logger_callback or print
        self.lt_tool = lt_tool
        self.data: Dict[str, str] = {}
        self.dict_path = self._get_dict_path()
        self._load()
    
    def _get_dict_path(self) -> Path:
        current_dir = Path(__file__).parent
        return current_dir.parent.parent / "data" / "replacement_dict.json"
    
    def _get_languagetool_config_dir(self) -> Path:
        config_dir = Path.home() / ".config" / "languagetool"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def _get_ignore_file_path(self) -> Path:
        return self._get_languagetool_config_dir() / "ignore.txt"
    
    def _get_rules_path(self) -> Path:
        cache_dir = Path.home() / ".cache" / "language_tool_python"
        
        for version_dir in cache_dir.glob("LanguageTool-*"):
            rules_path = version_dir / "org" / "languagetool" / "rules" / "ru" / "user_rules.xml"
            if rules_path.parent.exists() or version_dir == list(cache_dir.glob("LanguageTool-*"))[0]:
                return rules_path
        
        default_path = cache_dir / "LanguageTool-6.4" / "org" / "languagetool" / "rules" / "ru" / "user_rules.xml"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        return default_path
    
    def _sanitize_id(self, text: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '_', text)
    
    def _generate_rules_xml(self) -> str:
        if not self.data:
            return '<?xml version="1.0" encoding="UTF-8"?>\n<rules lang="ru"/>'
        
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<rules lang="ru" xsi:noNamespaceSchemaLocation="../../../../../schemas/rules.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <category name="Пользовательский словарь замен" id="REPLACEMENT_DICT" type="misspelling">
'''
        
        for wrong, correct in self.data.items():
            wrong_esc = wrong.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            correct_esc = correct.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            rule_id = f"REPLACE_{self._sanitize_id(wrong)}"
            
            xml += f'''
        <rule id="{rule_id}" name="Замена '{wrong_esc}' на '{correct_esc}'">
            <pattern>
                <marker>
                    <token>{wrong_esc}</token>
                </marker>
            </pattern>
            <message>Возможно, вы имели в виду <suggestion>{correct_esc}</suggestion>?</message>
            <example correction="{correct_esc}"><marker>{wrong_esc}</marker></example>
        </rule>
'''
        
        xml += '''
    </category>
</rules>'''
        return xml
    
    def _update_ignore_file(self) -> bool:
        """Обновляет файл ignore.txt для LanguageTool"""
        try:
            ignore_path = self._get_ignore_file_path()
            
            # Собираем все уникальные правильные слова
            correct_words = set(self.data.values())
            
            existing_words = set()
            if ignore_path.exists():
                with open(ignore_path, 'r', encoding='utf-8') as f:
                    existing_words = set(line.strip() for line in f if line.strip())
            
            all_words = existing_words.union(correct_words)
            
            with open(ignore_path, 'w', encoding='utf-8') as f:
                for word in sorted(all_words):
                    f.write(f"{word}\n")
            
            self.logger(f"📝 Обновлён ignore.txt: {len(all_words)} слов", "info")
            return True
            
        except Exception as e:
            self.logger(f"⚠️ Ошибка обновления ignore.txt: {e}", "warning")
            return False
    
    def _sync_with_languagetool(self) -> bool:
        """Синхронизирует словарь с локальным LanguageTool"""
        try:
            # 1. Обновляем ignore.txt
            self._update_ignore_file()
            
            # 2. Генерируем XML правила
            rules_xml = self._generate_rules_xml()
            rules_path = self._get_rules_path()
            rules_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(rules_path, 'w', encoding='utf-8') as f:
                f.write(rules_xml)
            
            self.logger(f"🔄 Словарь синхронизирован с LanguageTool: {len(self.data)} правил", "info")
            return True
            
        except Exception as e:
            self.logger(f"⚠️ Ошибка синхронизации с LanguageTool: {e}", "warning")
            return False
    
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
    
    def save(self) -> bool:
        """Сохраняет словарь в JSON-файл и синхронизирует с LanguageTool"""
        try:
            self.dict_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dict_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            self._sync_with_languagetool()
            
            self.logger(f"💾 Словарь замен сохранён: {len(self.data)} записей", "success")
            return True
            
        except Exception as e:
            self.logger(f"✗ Ошибка сохранения словаря: {e}", "error")
            return False
    
    def reload(self):
        """Перезагружает словарь из файла и синхронизирует"""
        self._load()
        self._sync_with_languagetool()
    
    def apply(self, text: str) -> str:
        """Применяет все замены из словаря к тексту"""
        if not text or not self.data:
            return text
        
        result = text
        sorted_keys = sorted(self.data.keys(), key=len, reverse=True)
        
        for wrong in sorted_keys:
            correct = self.data[wrong]
            result = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, result)
        
        return result
    
    def add_replacement(self, wrong: str, correct: str) -> bool:
        if not wrong or not correct:
            return False
        
        self.data[wrong] = correct
        return self.save()
    
    def remove_replacement(self, wrong: str) -> bool:
        if wrong in self.data:
            del self.data[wrong]
            return self.save()
        return False
    
    def get_all(self) -> Dict[str, str]:
        return self.data.copy()
    
    def get_count(self) -> int:
        return len(self.data)
    
    def get_ignore_file_path(self) -> Path:
        return self._get_ignore_file_path()
    
    def get_rules_file_path(self) -> Optional[Path]:
        rules_path = self._get_rules_path()
        if rules_path.exists():
            return rules_path
        return None