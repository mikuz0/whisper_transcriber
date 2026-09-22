#!/bin/bash
# install.sh - Установка Whisper Transcriber в текущей папке

set -e

echo "=== Whisper Transcriber - Установка ==="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Функция для вывода
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[→]${NC} $1"
}

# Получаем текущую директорию
CURRENT_DIR="$(pwd)"
PROJECT_DIR="$CURRENT_DIR"

print_info "Установка в директорию: $PROJECT_DIR"

# 1. Проверка Python
echo -e "\n🐍 Проверка Python..."
PYTHON_BIN="/home/mikuz/soft/src/Python-3.11.9/install/bin/python3.11"

if [ ! -f "$PYTHON_BIN" ]; then
    print_error "Python не найден по пути: $PYTHON_BIN"
    print_info "Попытка найти python в системе..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
        print_status "Найден системный Python: $(python3 --version)"
    else
        print_error "Python3 не найден. Укажите правильный путь к Python."
        exit 1
    fi
else
    print_status "Python найден: $($PYTHON_BIN --version)"
fi

# 2. Создание виртуального окружения в текущей папке
echo -e "\n🐍 Создание виртуального окружения..."
if [ -d "myenv" ]; then
    print_warning "Виртуальное окружение уже существует. Удаляем..."
    rm -rf myenv
fi

$PYTHON_BIN -m venv myenv
print_status "Виртуальное окружение создано"

# Активация окружения
source myenv/bin/activate

# 3. Обновление pip
echo -e "\n📦 Обновление pip..."
pip install --upgrade pip

# 4. Установка Python пакетов
echo -e "\n📦 Установка Python пакетов..."

print_info "Установка PyTorch (CPU версия)..."
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

print_info "Установка Whisper..."
pip install openai-whisper

print_info "Установка GUI..."
pip install PyQt5

print_info "Установка аудио-пакетов..."
pip install ffmpeg-python soundfile

print_info "Установка LanguageTool..."
pip install language-tool-python

print_info "Установка пакетов для обработки текста..."
pip install razdel pymystem3

print_info "Установка DOCX поддержки..."
pip install python-docx

print_info "Установка системных утилит..."
pip install psutil tiktoken more-itertools

print_status "Все Python пакеты установлены"

# 5. Создание файлов конфигурации
echo -e "\n📝 Создание файлов конфигурации..."
mkdir -p data

if [ ! -f "config.json" ]; then
    cat > config.json << 'EOF'
{
  "work_directory": "",
  "whisper_model": "base",
  "output_formats": ["txt"],
  "postprocess_actions": ["cleanup", "replacement_dict"],
  "postprocess_order": ["cleanup", "replacement_dict"],
  "interactive_mode": false,
  "last_used_tab": 0
}
EOF
    print_status "Создан config.json"
else
    print_warning "config.json уже существует, пропускаем"
fi

if [ ! -f "data/replacement_dict.json" ]; then
    cat > data/replacement_dict.json << 'EOF'
{
  "пошол": "пошёл",
  "пришол": "пришёл",
  "ишол": "шёл",
  "щас": "сейчас",
  "ихний": "их",
  "небыло": "не было",
  "немогу": "не могу"
}
EOF
    print_status "Создан data/replacement_dict.json"
else
    print_warning "data/replacement_dict.json уже существует, пропускаем"
fi

# 6. Создание скрипта запуска
echo -e "\n🚀 Создание скрипта запуска..."

cat > run.sh << EOF
#!/bin/bash
# run.sh - Запуск Whisper Transcriber

# Получаем директорию скрипта
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$SCRIPT_DIR"

# Активация окружения
source myenv/bin/activate

# Запуск программы
python main.py
EOF

chmod +x run.sh
print_status "Скрипт запуска создан: ./run.sh"

# 7. Создание скрипта для обновления пакетов
cat > update.sh << 'EOF'
#!/bin/bash
# update.sh - Обновление пакетов

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source myenv/bin/activate

echo "Обновление pip..."
pip install --upgrade pip

echo "Обновление пакетов..."
pip install --upgrade openai-whisper PyQt5 ffmpeg-python soundfile
pip install --upgrade language-tool-python razdel pymystem3 python-docx
pip install --upgrade psutil tiktoken more-itertools

echo "Обновление завершено!"
EOF

chmod +x update.sh
print_status "Скрипт обновления создан: ./update.sh"

# 8. Создание скрипта для проверки установки
cat > check_install.py << 'EOF'
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
EOF

chmod +x check_install.py
print_status "Скрипт проверки создан: ./check_install.py"

# 9. Создание README
cat > README.md << 'EOF'
# Whisper Transcriber

Распознавание речи из видео и аудио файлов с использованием OpenAI Whisper.

## Быстрый старт

### Установка
```bash
./install.sh
