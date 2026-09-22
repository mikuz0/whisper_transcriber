#!/bin/bash
# run.sh - Запуск Whisper Transcriber

# Получаем директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Активация окружения
source myenv/bin/activate

# Запуск программы
python main.py
