"""
Модуль для конвертации видео/аудио в WAV (16kHz, mono, PCM)
"""

import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
import tempfile

import ffmpeg


class AudioPreparer:
    """Подготовка аудио: конвертация в WAV формат для Whisper"""
    
    SUPPORTED_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',  # Видео
        '.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus', '.aac'   # Аудио
    }
    
    def __init__(self, cache_dir: str, logger_callback=None):
        """
        Args:
            cache_dir: путь к папке audio_cache
            logger_callback: функция для логирования
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger_callback or print
        
        # Проверяем наличие ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Проверяет доступность ffmpeg в системе"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL, 
                                  check=True,
                                  timeout=5)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.logger("⚠️  ВНИМАНИЕ: ffmpeg не найден в системе!", "warning")
            self.logger("   Установите ffmpeg: sudo apt install ffmpeg", "warning")
            return False
    
    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """Получает длительность аудио/видео файла в секундах"""
        if not self.ffmpeg_available:
            return None
        
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            self.logger(f"⚠️  Не удалось определить длительность {Path(file_path).name}: {e}", "warning")
            return None
    
    def convert_to_wav(self, input_file: str, output_file: str, 
                       overwrite: bool = False) -> Tuple[bool, str]:
        """
        Конвертирует файл в WAV (16kHz, mono, PCM)
        
        Returns:
            (success, message)
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        # Проверяем существование выходного файла
        if output_path.exists() and not overwrite:
            return False, f"Файл уже существует: {output_path.name}"
        
        if not self.ffmpeg_available:
            return False, "ffmpeg не доступен. Установите ffmpeg."
        
        try:
            # Используем прямой вызов ffmpeg для всех типов файлов
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vn',  # отключаем видео
                '-ar', '16000',  # частота 16 kHz
                '-ac', '1',  # моно
                '-c:a', 'pcm_s16le',  # PCM 16-bit
                '-y' if overwrite else '-n',
                str(output_path)
            ]
            
            # Запускаем процесс
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 минут таймаут
            )
            
            if result.returncode != 0:
                error_msg = result.stderr[:300] if result.stderr else "Неизвестная ошибка"
                return False, f"Ошибка ffmpeg: {error_msg}"
            
            # Проверяем, что файл создался и не пустой
            if output_path.exists() and output_path.stat().st_size > 0:
                return True, f"Успешно сконвертирован: {input_path.name}"
            else:
                return False, f"Ошибка: выходной файл пуст или не создан"
                
        except subprocess.TimeoutExpired:
            return False, f"Превышено время ожидания при конвертации {input_path.name}"
        except Exception as e:
            return False, f"Ошибка при конвертации {input_path.name}: {str(e)}"
    
    def prepare_file(self, source_dir: Path, filename: str, 
                     force_overwrite: bool = False) -> Tuple[bool, str]:
        """
        Подготавливает один файл (конвертирует в WAV если нужно)
        
        Returns:
            (success, message)
        """
        source_path = source_dir / filename
        
        # Проверяем расширение
        if source_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False, f"Неподдерживаемый формат: {filename}"
        
        # Проверяем существование исходного файла
        if not source_path.exists():
            return False, f"Исходный файл не найден: {filename}"
        
        # Генерируем имя выходного файла
        wav_path = self.cache_dir / f"{source_path.stem}.wav"
        
        # Проверяем, нужно ли конвертировать
        if wav_path.exists() and not force_overwrite:
            return False, f"Пропущен (уже в кэше): {filename}"
        
        # Для MP3 файлов выводим дополнительную информацию
        if source_path.suffix.lower() == '.mp3':
            self.logger(f"  Обработка MP3 файла: {filename}", "info")
        
        # Проверяем длительность
        duration = self.get_audio_duration(str(source_path))
        if duration and duration > 1800:  # 30 минут
            self.logger(f"⚠️  Файл {filename} длится {duration/60:.1f} минут. Может потребоваться много RAM.", "warning")
        
        # Конвертируем
        return self.convert_to_wav(str(source_path), str(wav_path), overwrite=force_overwrite)
    
    def prepare_all(self, source_dir: Path, force_overwrite: bool = False,
                   progress_callback=None) -> Tuple[List[str], List[str]]:
        """
        Подготавливает все файлы из source_dir
        
        Returns:
            (successful_files, failed_files)
        """
        if not source_dir.exists():
            return [], [f"Папка не существует: {source_dir}"]
        
        # Получаем все поддерживаемые файлы
        files = [f for f in source_dir.iterdir() 
                if f.suffix.lower() in self.SUPPORTED_EXTENSIONS and f.is_file()]
        
        if not files:
            return [], ["Нет поддерживаемых файлов в папке video_audio"]
        
        successful = []
        failed = []
        
        for idx, file_path in enumerate(files, 1):
            if progress_callback:
                progress_callback(file_path.name, idx, len(files))
            
            success, message = self.prepare_file(source_dir, file_path.name, force_overwrite)
            if success:
                successful.append(file_path.name)
                self.logger(f"✓ {message}", "success")
            else:
                failed.append(file_path.name)
                level = "error" if "Ошибка" in message or "ffmpeg" in message else "warning"
                self.logger(f"✗ {message}", level)
        
        return successful, failed