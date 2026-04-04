#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_languagetool.py - Скрипт проверки доступности и установки LanguageTool
Запускается отдельно, не в составе основного приложения

Источники:
1. Публичный API LanguageTool (быстро, но с лимитами)
2. Зеркало GitHub (стабильные релизы)
3. Зеркало Google Storage
4. Официальный сайт LanguageTool
"""

import sys
import subprocess
import os
from pathlib import Path
import time
import json
import socket
import urllib.request
import urllib.error
import shutil
import zipfile
import tempfile
from typing import Optional, Tuple


class Colors:
    """Цвета для вывода в терминал"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Печатает заголовок"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_success(text):
    """Печатает сообщение об успехе"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Печатает сообщение об ошибке"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Печатает предупреждение"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """Печатает информационное сообщение"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} - требуется Python 3.8+")
        return False


def check_network():
    """Проверяет доступность интернета"""
    print_info("Проверка интернет-соединения...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print_success("Интернет-соединение доступно")
        return True
    except OSError:
        print_warning("Интернет-соединение недоступно")
        return False


def check_languagetool_installed():
    """Проверяет, установлен ли language-tool-python"""
    try:
        import language_tool_python
        print_success("language-tool-python - установлен")
        return True
    except ImportError:
        print_warning("language-tool-python не установлен")
        return False


def install_languagetool():
    """Устанавливает language-tool-python через pip"""
    print_info("Установка language-tool-python...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "language-tool-python"])
        print_success("language-tool-python установлен")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка установки: {e}")
        return False


def test_public_api():
    """Тестирует публичный API LanguageTool"""
    print_info("Тестирование публичного API LanguageTool...")
    
    try:
        import language_tool_python
        
        tool = language_tool_python.LanguageToolPublicAPI('ru-RU')
        
        test_text = "Я пошол в магазин."
        matches = tool.check(test_text)
        
        print_success(f"Публичный API доступен. Найдено ошибок: {len(matches)}")
        
        if matches:
            print_info("Пример исправления:")
            for match in matches[:3]:
                replacements = match.replacements[:3] if match.replacements else []
                if replacements:
                    print(f"  {match.context} → {replacements[0]}")
                else:
                    print(f"  {match.context} → (нет предложений)")
        
        tool.close()
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            print_warning("Публичный API: превышен лимит запросов")
        else:
            print_error(f"Ошибка подключения к публичному API: {e}")
        return False


def download_with_progress(url: str, dest: Path, timeout: int = 60) -> bool:
    """Скачивает файл с отображением прогресса"""
    try:
        print_info(f"Загрузка: {url}")
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(dest, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_len = 30
                        filled = int(bar_len * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_len - filled)
                        print(f"\r  [{bar}] {percent:.1f}%", end='', flush=True)
            
            print()  # новая строка после прогресса
            return True
            
    except Exception as e:
        print_error(f"Ошибка загрузки: {e}")
        return False


def download_languagetool_github(dest_dir: Path) -> Tuple[bool, str]:
    """Скачивает LanguageTool с GitHub (стабильный релиз)"""
    print_info("Источник: GitHub (стабильный релиз)")
    
    # Последняя стабильная версия
    version = "6.4"
    url = f"https://github.com/languagetool-org/languagetool/releases/download/v{version}/LanguageTool-{version}.zip"
    
    dest_file = dest_dir / f"LanguageTool-{version}.zip"
    
    if download_with_progress(url, dest_file):
        return True, str(dest_file)
    
    return False, ""


def download_languagetool_google(dest_dir: Path) -> Tuple[bool, str]:
    """Скачивает LanguageTool с Google Storage"""
    print_info("Источник: Google Storage (зеркало)")
    
    version = "6.4"
    url = f"https://storage.googleapis.com/languagetool/LanguageTool-{version}.zip"
    
    dest_file = dest_dir / f"LanguageTool-{version}.zip"
    
    if download_with_progress(url, dest_file):
        return True, str(dest_file)
    
    return False, ""


def download_languagetool_official(dest_dir: Path) -> Tuple[bool, str]:
    """Скачивает LanguageTool с официального сайта"""
    print_info("Источник: languagetool.org (официальный)")
    
    version = "6.4"
    url = f"https://languagetool.org/download/LanguageTool-{version}.zip"
    
    dest_file = dest_dir / f"LanguageTool-{version}.zip"
    
    if download_with_progress(url, dest_file):
        return True, str(dest_file)
    
    return False, ""


def extract_zip(zip_path: Path, dest_dir: Path) -> bool:
    """Распаковывает ZIP архив"""
    try:
        print_info(f"Распаковка {zip_path.name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        print_success("Распаковка завершена")
        return True
    except Exception as e:
        print_error(f"Ошибка распаковки: {e}")
        return False


def setup_local_server():
    """Настраивает локальный сервер LanguageTool"""
    print_info("Настройка локального сервера LanguageTool...")
    
    cache_dir = Path.home() / ".cache" / "language_tool"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Проверяем, есть ли уже установленный сервер
    existing = list(cache_dir.glob("LanguageTool-*"))
    if existing:
        print_info(f"Найден существующий сервер: {existing[0].name}")
        # Создаём символическую ссылку на текущую версию
        current_link = cache_dir / "current"
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        current_link.symlink_to(existing[0])
        print_success("Локальный сервер уже настроен")
        return True
    
    # Пробуем скачать из разных источников
    sources = [
        download_languagetool_github,
        download_languagetool_google,
        download_languagetool_official
    ]
    
    for source in sources:
        print()
        success, zip_path = source(cache_dir)
        if success:
            zip_file = Path(zip_path)
            if extract_zip(zip_file, cache_dir):
                # Находим распакованную папку
                extracted_dirs = [d for d in cache_dir.iterdir() if d.is_dir() and d.name.startswith("LanguageTool-")]
                if extracted_dirs:
                    current_link = cache_dir / "current"
                    if current_link.exists() or current_link.is_symlink():
                        current_link.unlink()
                    current_link.symlink_to(extracted_dirs[0])
                    
                    # Удаляем ZIP файл
                    zip_file.unlink()
                    
                    print_success(f"Локальный сервер установлен: {extracted_dirs[0].name}")
                    return True
    
    print_error("Не удалось загрузить локальный сервер ни из одного источника")
    return False


def test_local_server():
    """Тестирует локальный сервер LanguageTool"""
    print_info("Тестирование локального сервера LanguageTool...")
    
    try:
        import language_tool_python
        
        cache_dir = Path.home() / ".cache" / "language_tool"
        server_jar = cache_dir / "current" / "languagetool-server.jar"
        
        if not server_jar.exists():
            print_warning("Локальный сервер не найден. Попытка установки...")
            if not setup_local_server():
                return False
        
        print_info("Загрузка локального сервера...")
        start_time = time.time()
        
        tool = language_tool_python.LanguageTool(
            'ru-RU',
            server_path=str(server_jar)
        )
        
        elapsed = time.time() - start_time
        test_text = "Я пошол в магазин."
        matches = tool.check(test_text)
        
        print_success(f"Локальный сервер готов за {elapsed:.1f} сек. Найдено ошибок: {len(matches)}")
        
        if matches:
            print_info("Пример исправления:")
            for match in matches[:3]:
                replacements = match.replacements[:3] if match.replacements else []
                if replacements:
                    print(f"  {match.context} → {replacements[0]}")
                else:
                    print(f"  {match.context} → (нет предложений)")
        
        tool.close()
        return True
        
    except ImportError:
        print_error("language-tool-python не установлен")
        return False
    except Exception as e:
        print_error(f"Ошибка локального сервера: {e}")
        return False


def check_cache_size():
    """Проверяет размер кэша LanguageTool"""
    cache_dir = Path.home() / ".cache" / "language_tool"
    if cache_dir.exists():
        size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        size_mb = size / (1024 * 1024)
        print_info(f"Кэш LanguageTool: {size_mb:.1f} МБ")
        return size_mb
    else:
        print_info("Кэш LanguageTool не найден")
        return 0


def clear_cache():
    """Очищает кэш LanguageTool"""
    cache_dir = Path.home() / ".cache" / "language_tool"
    if cache_dir.exists():
        print_info("Очистка кэша...")
        shutil.rmtree(cache_dir)
        print_success("Кэш очищен")
    else:
        print_warning("Кэш не найден")


def show_usage():
    """Показывает справку по использованию"""
    print_header("Справка")
    print(f"""
    Использование: python check_languagetool.py [опция]

    Опции:
        --install       Установить language-tool-python
        --test-api      Тестировать только публичный API
        --test-local    Тестировать только локальный сервер
        --setup-local   Скачать и настроить локальный сервер
        --cache-size    Показать размер кэша
        --clear-cache   Очистить кэш LanguageTool
        --help          Показать эту справку

    Без опций выполняет полную проверку.
    """)


def main():
    """Основная функция"""
    print_header("LanguageTool - Проверка и установка")
    
    # Проверяем аргументы командной строки
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        show_usage()
        return
    
    if '--install' in args:
        if install_languagetool():
            print_success("Установка завершена")
        return
    
    if '--setup-local' in args:
        if setup_local_server():
            print_success("Локальный сервер настроен")
        return
    
    if '--cache-size' in args:
        check_cache_size()
        return
    
    if '--clear-cache' in args:
        clear_cache()
        return
    
    if '--test-api' in args:
        test_public_api()
        return
    
    if '--test-local' in args:
        test_local_server()
        return
    
    # Полная проверка
    print_info("Выполняется полная проверка...")
    
    # 1. Проверка Python
    if not check_python_version():
        sys.exit(1)
    
    # 2. Проверка интернета
    has_network = check_network()
    
    # 3. Проверка установки
    installed = check_languagetool_installed()
    
    if not installed and has_network:
        print()
        response = input("Установить language-tool-python? [y/N]: ").strip().lower()
        if response == 'y':
            if install_languagetool():
                installed = True
    
    if not installed:
        print_error("language-tool-python не установлен. Запустите с --install для установки.")
        sys.exit(1)
    
    # 4. Проверка публичного API
    print()
    print_header("Тестирование публичного API")
    api_ok = test_public_api()
    
    # 5. Проверка локального сервера
    print()
    print_header("Тестирование локального сервера")
    cache_size = check_cache_size()
    
    if has_network and cache_size < 100:  # Если кэш маленький или отсутствует
        print_info("Локальный сервер не загружен.")
        response = input("Скачать и настроить локальный сервер? [y/N]: ").strip().lower()
        if response == 'y':
            if setup_local_server():
                test_local_server()
        else:
            print_info("Пропуск загрузки локального сервера")
    elif cache_size >= 100:
        test_local_server()
    else:
        print_warning("Нет интернета, локальный сервер не может быть загружен")
    
    # 6. Итог
    print()
    print_header("Итог проверки")
    
    print(f"language-tool-python: {'установлен' if installed else 'не установлен'}")
    print(f"Публичный API: {'доступен' if api_ok else 'недоступен'}")
    
    if api_ok:
        print_success("\nРекомендуется использовать Публичный API (быстрая настройка)")
        print_info("В проекте используйте LanguageToolPublicAPI вместо LanguageTool")
    elif has_network:
        print_warning("\nРекомендуется настроить локальный сервер")
        print_info("Запустите: python check_languagetool.py --setup-local")
    else:
        print_error("\nНет интернет-соединения. Грамматическая проверка недоступна.")


if __name__ == "__main__":
    main()