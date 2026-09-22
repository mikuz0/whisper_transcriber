#!/usr/bin/env python3
"""Проверка установки зависимостей"""

import sys
import subprocess

def check_module(module_name, package_name):
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError:
        print(f"❌ {module_name} - pip install {package_name}")
        return False

def main():
    print("=== Проверка зависимостей Whisper Transcriber ===\n")
    
    modules = [
        ('whisper', 'openai-whisper'),
        ('torch', 'torch'),
        ('PyQt5', 'PyQt5'),
        ('ffmpeg', 'ffmpeg-python'),
        ('soundfile', 'soundfile'),
        ('language_tool_python', 'language-tool-python'),
        ('razdel', 'razdel'),
        ('pymystem3', 'pymystem3'),
        ('docx', 'python-docx'),
        ('psutil', 'psutil'),
    ]
    
    all_ok = True
    for module, package in modules:
        if not check_module(module, package):
            all_ok = False
    
    # Проверка ffmpeg в системе
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ ffmpeg (системный)")
        else:
            print("⚠️ ffmpeg (проблема с выполнением)")
    except FileNotFoundError:
        print("⚠️ ffmpeg не найден в системе")
    except Exception:
        print("⚠️ ffmpeg не доступен")
    
    print(f"\n{'✅ Всё готово!' if all_ok else '⚠️ Есть проблемы'}")
    
    if all_ok:
        print("\nЗапуск программы:")
        print("  ./run.sh")

if __name__ == '__main__':
    main()
