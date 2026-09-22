"""
grammar_checker.py - Заглушка (LanguageTool отключён)
"""

from typing import List, Tuple


class GrammarChecker:
    """Заглушка для грамматической проверки (отключена)"""
    
    def __init__(self, language: str = 'ru-RU', logger_callback=None, use_local: bool = False):
        self.language = language
        self.logger = logger_callback or print
        self.tool = None
        self.logger("⚠️ LanguageTool отключён. Грамматическая проверка не будет выполняться.", "warning")
    
    def check(self, text: str) -> List:
        return []
    
    def correct(self, text: str) -> str:
        return text
    
    def check_and_report(self, text: str) -> Tuple[str, List[str]]:
        return text, []
    
    def run_interactive(self, text: str, parent=None) -> str:
        return text
    
    def close(self):
        pass
    
    def get_stats(self) -> dict:
        return {'available': False, 'mode': 'disabled'}
