"""
validators.py - Валидаторы для проверки файлов и системы
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class Validators:
    """Различные проверки"""
    
    @staticmethod
    def check_ffmpeg() -> Tuple[bool, str]:
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, f"✓ ffmpeg найден: {version_line[:50]}"
            return False, "✗ ffmpeg не отвечает"
        except FileNotFoundError:
            return False, "✗ ffmpeg не установлен. Установите: sudo apt install ffmpeg"
        except Exception as e:
            return False, f"✗ Ошибка проверки ffmpeg: {str(e)}"
    
    @staticmethod
    def check_ram_available() -> Tuple[float, str]:
        try:
            import psutil
            available_ram = psutil.virtual_memory().available / (1024**3)
            warning = ""
            
            if available_ram < 2:
                warning = f"⚠️ Доступно всего {available_ram:.1f} ГБ RAM. Для длинных файлов может не хватить памяти."
            elif available_ram < 4:
                warning = f"⚠️ Доступно {available_ram:.1f} ГБ RAM. Рекомендуется использовать модель 'tiny' или 'base'."
            
            return available_ram, warning
        except ImportError:
            return 0, "⚠️ psutil не установлен, проверка RAM недоступна"
        except Exception:
            return 0, "Не удалось определить доступную RAM"
    
    @staticmethod
    def check_model_requirements(model_name: str) -> Tuple[bool, str]:
        ram_required = {
            'tiny': 1,
            'base': 2,
            'small': 4,
            'medium': 8,
            'large': 16
        }
        
        required = ram_required.get(model_name, 4)
        
        try:
            import psutil
            available_ram = psutil.virtual_memory().available / (1024**3)
            
            if available_ram < required:
                warning = f"⚠️ Модель {model_name} требует ~{required} ГБ RAM, доступно {available_ram:.1f} ГБ. Возможны проблемы."
                return False, warning
            
            return True, f"Достаточно RAM для модели {model_name}"
        except ImportError:
            return True, "psutil не установлен, проверка RAM пропущена"
        except Exception:
            return True, "Не удалось проверить RAM"
    
    @staticmethod
    def check_file_duration(duration_seconds: float, model_name: str = 'base') -> str:
        minutes = duration_seconds / 60
        
        if minutes > 60:
            return f"⚠️ Файл длится {minutes:.1f} минут. Это очень долго, может не хватить RAM."
        elif minutes > 30:
            return f"⚠️ Файл длится {minutes:.1f} минут. Потребуется много RAM (>2-3 ГБ)."
        elif minutes > 15:
            return f"⚠️ Файл длится {minutes:.1f} минут. Ожидайте длительной обработки."
        
        return ""
    
    @staticmethod
    def ensure_directories(work_dir: Path) -> Tuple[Path, Path, Path, Path]:
        video_audio_dir = work_dir / 'video_audio'
        audio_cache_dir = work_dir / 'audio_cache'
        text_dir = work_dir / 'text'
        text_processed_dir = work_dir / 'text_processed'
        
        video_audio_dir.mkdir(parents=True, exist_ok=True)
        audio_cache_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)
        text_processed_dir.mkdir(parents=True, exist_ok=True)
        
        return video_audio_dir, audio_cache_dir, text_dir, text_processed_dir
    
    @staticmethod
    def validate_work_directory(work_dir: Path) -> Tuple[bool, str]:
        if not work_dir.exists():
            return False, f"Директория не существует: {work_dir}"
        
        if not os.access(work_dir, os.R_OK):
            return False, f"Нет прав на чтение: {work_dir}"
        
        if not os.access(work_dir, os.W_OK):
            return False, f"Нет прав на запись: {work_dir}"
        
        return True, "Директория доступна"