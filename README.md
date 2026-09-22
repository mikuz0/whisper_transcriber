# Whisper Transcriber

Распознавание речи из видео и аудио файлов с использованием OpenAI Whisper.

## Быстрый старт

### Установка
```bash
./install.sh

pyinstaller --onefile --noconsole \
    --add-data "$(python -c 'import whisper, os; print(os.path.dirname(whisper.__file__))'):whisper" \
    main.py
  
  Исправление проблем с меню:

    QT_QPA_PLATFORM=xcb ./dist/main
