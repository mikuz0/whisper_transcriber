"""
grammar_checker.py - Обёртка для language-tool-python
Проверка грамматики, орфографии и стиля
"""

import time
import os
import warnings
import subprocess
import signal
from typing import List, Tuple
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="language_tool_python")


class GrammarChecker:
    """Класс для проверки и исправления грамматики текста"""
    
    def __init__(self, language: str = 'ru-RU', logger_callback=None, use_local: bool = True):
        self.language = language
        self.logger = logger_callback or print
        self.use_local = use_local
        self.tool = None
        self.last_request_time = 0
        self.min_request_interval = 2.0
        self._init_tool()
    
    def _find_local_server(self) -> Path:
        """Ищет локальную установку LanguageTool"""
        search_paths = [
            Path.home() / ".cache" / "language_tool_python",
            Path.home() / ".cache" / "language_tool",
            Path("/usr/share/languagetool"),
            Path("/usr/local/share/languagetool"),
        ]
        
        for base_path in search_paths:
            if base_path.exists():
                for version_dir in base_path.glob("LanguageTool-*"):
                    if (version_dir / "languagetool-server.jar").exists():
                        return version_dir
        
        env_path = os.environ.get('LANGUAGE_TOOL_PATH')
        if env_path:
            path = Path(env_path)
            if path.exists() and (path / "languagetool-server.jar").exists():
                return path
        
        return None
    
    def _init_tool(self):
        """Инициализирует LanguageTool (без server_path, так как версия не поддерживает)"""
        try:
            import language_tool_python
            
            if self.use_local:
                self.logger(f"🔤 Поиск локального LanguageTool...", "info")
                
                server_path = self._find_local_server()
                
                if server_path:
                    self.logger(f"🔤 Найден локальный сервер: {server_path.name}", "info")
                    # Устанавливаем переменную окружения для пути
                    os.environ['LANGUAGE_TOOL_PATH'] = str(server_path)
                    
                # Создаём инструмент БЕЗ server_path (текущая версия не поддерживает)
                self.tool = language_tool_python.LanguageTool(self.language)
                self.logger(f"🔤 LanguageTool (локальный) загружен", "info")
            else:
                self.logger(f"🔤 LanguageTool (публичный API) загружен", "info")
                self.tool = language_tool_python.LanguageToolPublicAPI(self.language)
                
        except ImportError:
            self.logger("⚠️ language-tool-python не установлен", "warning")
            self.tool = None
        except Exception as e:
            self.logger(f"⚠️ Ошибка загрузки LanguageTool: {e}", "warning")
            self.tool = None
    
    def check_and_report(self, text: str) -> Tuple[str, List[str]]:
        """Проверяет текст и возвращает список изменений (без автозамены)"""
        if not self.tool or not text:
            return text, []
        
        try:
            matches = self.tool.check(text)
            changes = []
            
            # Только собираем информацию об ошибках, но не изменяем текст
            for match in matches:
                if match.replacements:
                    changes.append(f"'{match.context}' → {match.replacements[0]}")
            
            return text, changes
            
        except Exception as e:
            self.logger(f"⚠️ Ошибка проверки грамматики: {e}", "warning")
            return text, []
    
    def check(self, text: str) -> List:
        """Проверяет текст и возвращает список ошибок"""
        if not self.tool or not text:
            return []
        
        try:
            return self.tool.check(text)
        except Exception as e:
            self.logger(f"⚠️ Ошибка проверки грамматики: {e}", "warning")
            return []
    
    def close(self):
        """Закрывает соединение"""
        if self.tool:
            try:
                self.tool.close()
            except:
                pass
    
    def get_stats(self) -> dict:
        """Возвращает статистику"""
        server_path = self._find_local_server()
        return {
            'language': self.language,
            'use_local': self.use_local,
            'available': self.tool is not None,
            'local_server_path': str(server_path) if server_path else None
        }