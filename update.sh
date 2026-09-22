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
