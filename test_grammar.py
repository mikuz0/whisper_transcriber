#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_grammar.py - Тестирование работы LanguageTool
Проверяет публичный API и локальный сервер
"""

import sys
import time
from pathlib import Path


def test_public_api():
    """Тестирует публичный API LanguageTool"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Публичный API LanguageTool")
    print("="*60)
    
    try:
        import language_tool_python
        
        print("✓ language-tool-python импортирован")
        
        # Создаём инструмент для публичного API
        print("Создание LanguageToolPublicAPI...")
        tool = language_tool_python.LanguageToolPublicAPI('ru-RU')
        
        # Тестовые тексты
        test_texts = [
            "Я пошол в магазин.",
            "Они пришол домой.",
            "Мой ихний дом.",
            "Ваимя Господа."
        ]
        
        print("\nРезультаты проверки:")
        print("-"*40)
        
        for text in test_texts:
            print(f"\nТекст: {text}")
            matches = tool.check(text)
            
            if matches:
                print(f"  Найдено ошибок: {len(matches)}")
                for match in matches[:3]:  # Показываем первые 3
                    print(f"    - {match.message[:80]}")
                    if match.replacements:
                        print(f"      Предложение: {match.replacements[0]}")
            else:
                print("  Ошибок не найдено")
        
        tool.close()
        print("\n✓ Публичный API работает")
        return True
        
    except ImportError:
        print("✗ language-tool-python не установлен")
        return False
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


def test_local_server():
    """Тестирует локальный сервер LanguageTool"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Локальный сервер LanguageTool")
    print("="*60)
    
    try:
        import language_tool_python
        
        print("✓ language-tool-python импортирован")
        
        # Проверяем наличие скачанного сервера
        cache_dir = Path.home() / ".cache" / "language_tool"
        server_dir = cache_dir / "LanguageTool-6.4"
        
        if server_dir.exists():
            print(f"✓ Найден локальный сервер: {server_dir}")
            # Проверяем наличие Java
            import subprocess
            try:
                subprocess.run(['java', '-version'], capture_output=True, check=True)
                print("✓ Java установлена")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("✗ Java не найдена. Локальный сервер не может работать без Java")
                print("  Установите Java: sudo apt install default-jre")
                return False
        else:
            print(f"⚠ Локальный сервер не найден: {server_dir}")
            print("  Будет использована автоматическая загрузка...")
        
        print("\nСоздание LanguageTool (локальный)...")
        print("Это может занять время при первой загрузке...")
        
        start_time = time.time()
        
        # Пробуем создать локальный инструмент
        tool = language_tool_python.LanguageTool('ru-RU')
        
        elapsed = time.time() - start_time
        print(f"✓ LanguageTool загружен за {elapsed:.1f} сек")
        
        # Тестовые тексты
        test_texts = [
            "Я пошол в магазин.",
            "Они пришол домой.",
            "Мой ихний дом.",
            "Ваимя Господа."
        ]
        
        print("\nРезультаты проверки:")
        print("-"*40)
        
        for text in test_texts:
            print(f"\nТекст: {text}")
            matches = tool.check(text)
            
            if matches:
                print(f"  Найдено ошибок: {len(matches)}")
                for match in matches[:3]:  # Показываем первые 3
                    print(f"    - {match.message[:80]}")
                    if match.replacements:
                        print(f"      Предложение: {match.replacements[0]}")
            else:
                print("  Ошибок не найдено")
        
        tool.close()
        print("\n✓ Локальный сервер работает")
        return True
        
    except ImportError:
        print("✗ language-tool-python не установлен")
        return False
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


def test_with_dictionary():
    """Тестирует совместную работу словаря замен и LanguageTool"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Словарь замен + LanguageTool")
    print("="*60)
    
    try:
        # Импортируем компоненты
        from core.postprocessor.replacement_dict import ReplacementDictionary
        from core.postprocessor.grammar_checker import GrammarChecker
        
        # Создаём словарь замен
        print("Создание словаря замен...")
        rep_dict = ReplacementDictionary()
        print(f"✓ Словарь загружен: {rep_dict.get_count()} записей")
        
        # Создаём грамматический проверяльщик (публичный API)
        print("\nСоздание GrammarChecker...")
        grammar = GrammarChecker(use_local=False)
        
        if not grammar.tool:
            print("✗ GrammarChecker не инициализирован")
            return False
        
        print("✓ GrammarChecker готов")
        
        # Тестовый текст
        test_text = "Я пошол в магазин. Они пришол домой. Мой ихний дом."
        
        print(f"\nИсходный текст: {test_text}")
        
        # Этап 1: Словарь замен
        print("\nЭтап 1: Словарь замен")
        after_dict = rep_dict.apply(test_text)
        print(f"Результат: {after_dict}")
        
        # Этап 2: Грамматическая проверка
        print("\nЭтап 2: Грамматическая проверка")
        after_grammar, changes = grammar.check_and_report(after_dict)
        print(f"Результат: {after_grammar}")
        
        if changes:
            print(f"\nИзменения:")
            for change in changes:
                print(f"  {change}")
        
        print("\n✓ Совместная работа работает")
        return True
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ LANGUAGE TOOL")
    print("="*60)
    
    # Проверка Python
    print(f"\nPython: {sys.version}")
    
    # Проверка установки
    try:
        import language_tool_python
        print(f"language-tool-python: установлен")
    except ImportError:
        print("language-tool-python: НЕ УСТАНОВЛЕН")
        print("Установите: pip install language-tool-python")
        return
    
    # Тест 1: Публичный API
    api_ok = test_public_api()
    
    # Тест 2: Локальный сервер
    local_ok = test_local_server()
    
    # Тест 3: Совместная работа
    if api_ok:
        dict_ok = test_with_dictionary()
    else:
        print("\n" + "="*60)
        print("ТЕСТ 3: Пропущен (публичный API не работает)")
        print("="*60)
        dict_ok = False
    
    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    print(f"Публичный API: {'✓ РАБОТАЕТ' if api_ok else '✗ НЕ РАБОТАЕТ'}")
    print(f"Локальный сервер: {'✓ РАБОТАЕТ' if local_ok else '✗ НЕ РАБОТАЕТ'}")
    print(f"Совместная работа: {'✓ РАБОТАЕТ' if dict_ok else '✗ НЕ РАБОТАЕТ'}")
    
    if api_ok:
        print("\n✅ Рекомендуется использовать Публичный API (use_local=False)")
    elif local_ok:
        print("\n✅ Рекомендуется использовать Локальный сервер (use_local=True)")
    else:
        print("\n❌ LanguageTool недоступен. Грамматическая проверка будет отключена.")


if __name__ == "__main__":
    main()