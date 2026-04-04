"""
transcriber.py - Модуль для распознавания речи через Whisper
С поддержкой множества форматов вывода и пост-обработки
"""

import os
import time
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import whisper
import torch


class WhisperTranscriber:
    """Распознавание аудио через OpenAI Whisper"""
    
    AVAILABLE_MODELS = ['tiny', 'base', 'small', 'medium', 'large']
    AVAILABLE_LANGUAGES = ['auto', 'ru', 'en', 'de', 'fr', 'es', 'it', 'ja', 'zh']
    OUTPUT_FORMATS = ['txt', 'srt', 'vtt', 'docx', 'json', 'md', 'html', 'csv', 'txt_timestamps']
    
    def __init__(self, logger_callback=None):
        """
        Args:
            logger_callback: функция для логирования
        """
        self.logger = logger_callback or print
        self.model = None
        self.current_model_name = None
        
        # Определяем устройство и тип данных
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Настройка типа данных
        if self.device == "cuda":
            self.compute_type = "float16"
            gpu_name = torch.cuda.get_device_name(0)
            self.logger(f"🔧 Используется GPU: {gpu_name}", "info")
            self.logger(f"   Тип данных: FP16 (ускорение в 2-3 раза)", "info")
        else:
            self.compute_type = "float32"
            self.logger(f"🔧 Используется устройство: CPU", "info")
            self.logger(f"   Тип данных: FP32 (совместимость)", "info")
    
    def load_model(self, model_name: str) -> bool:
        """
        Загружает модель Whisper
        
        Returns:
            True если успешно, False если ошибка
        """
        if model_name not in self.AVAILABLE_MODELS:
            self.logger(f"Ошибка: неизвестная модель {model_name}", "error")
            return False
        
        # Если модель уже загружена и та же - не перезагружаем
        if self.model is not None and self.current_model_name == model_name:
            return True
        
        try:
            self.logger(f"📥 Загрузка модели {model_name}...", "info")
            start_time = time.time()
            
            # Директория для кэша моделей
            cache_dir = os.path.expanduser("~/.cache/whisper")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Загружаем модель
            self.model = whisper.load_model(
                model_name, 
                device=self.device,
                download_root=cache_dir
            )
            
            # Для CPU принудительно используем FP32
            if self.device == "cpu":
                self.model = self.model.float()
            
            self.current_model_name = model_name
            
            elapsed = time.time() - start_time
            self.logger(f"✓ Модель {model_name} загружена за {elapsed:.1f} сек", "success")
            return True
            
        except Exception as e:
            self.logger(f"✗ Ошибка загрузки модели {model_name}: {str(e)}", "error")
            return False
    
    def _get_extension(self, format_type: str) -> str:
        """Возвращает расширение файла для формата"""
        extensions = {
            'txt': 'txt',
            'srt': 'srt',
            'vtt': 'vtt',
            'docx': 'docx',
            'json': 'json',
            'md': 'md',
            'html': 'html',
            'csv': 'csv',
            'txt_timestamps': 'txt'
        }
        return extensions.get(format_type, 'txt')
    
    def _get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """Получает длительность аудиофайла"""
        try:
            import soundfile as sf
            info = sf.info(str(audio_path))
            return info.duration
        except:
            try:
                import wave
                with wave.open(str(audio_path), 'rb') as wav:
                    frames = wav.getnframes()
                    rate = wav.getframerate()
                    return frames / float(rate)
            except:
                return None
    
    def transcribe(self, audio_path: str, model_name: str = 'base',
                  language: str = 'auto', task: str = 'transcribe',
                  output_format: str = 'txt', output_path: Optional[str] = None,
                  post_process: bool = False) -> Tuple[bool, str]:
        """
        Распознает аудио файл и сохраняет результат
        
        Args:
            audio_path: путь к WAV файлу
            model_name: модель Whisper
            language: язык ('auto' для автоопределения)
            task: 'transcribe' или 'translate'
            output_format: формат вывода
            output_path: путь для сохранения
            post_process: применять пост-обработку текста (по умолчанию False)
        
        Returns:
            (success, message_or_path)
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return False, f"Файл не найден: {audio_path}"
        
        if audio_path.suffix.lower() != '.wav':
            return False, f"Файл должен быть в формате WAV: {audio_path}"
        
        if not self.load_model(model_name):
            return False, "Не удалось загрузить модель"
        
        language_code = None if language == 'auto' else language
        
        try:
            duration = self._get_audio_duration(audio_path)
            if duration:
                self.logger(f"🎤 Распознавание: {audio_path.name} ({duration:.1f} сек)", "info")
            else:
                self.logger(f"🎤 Распознавание: {audio_path.name}", "info")
            
            self.logger(f"   Модель: {model_name}, язык: {language}, устройство: {self.device.upper()}", "info")
            start_time = time.time()
            
            # Выполняем распознавание
            result = self.model.transcribe(
                str(audio_path),
                language=language_code,
                task=task,
                verbose=False,
                fp16=(self.device == "cuda")
            )
            
            elapsed = time.time() - start_time
            
            # Пост-обработка текста (только если явно запрошено)
            if post_process:
                self.logger("📝 Применяется постобработка текста...", "info")
                # Постобработка будет применяться в другом месте
                # Здесь оставляем как есть
            
            if duration:
                self.logger(f"✓ Распознано за {elapsed:.1f} сек (в {duration/elapsed:.1f}x реального времени)", "success")
            else:
                self.logger(f"✓ Распознано за {elapsed:.1f} сек", "success")
            
            # Сохраняем результат
            if output_path is None:
                output_path = audio_path.parent.parent / 'text' / f"{audio_path.stem}.{self._get_extension(output_format)}"
            else:
                output_path = Path(output_path)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем в нужном формате
            saved_path = self._save_transcription(result, output_path, output_format, audio_path.stem)
            
            return True, str(saved_path)
            
        except Exception as e:
            error_msg = f"Ошибка распознавания {audio_path.name}: {str(e)}"
            self.logger(f"✗ {error_msg}", "error")
            return False, error_msg
    
    def transcribe_raw(self, audio_path: str, model_name: str = 'base',
                       language: str = 'auto', task: str = 'transcribe') -> Tuple[bool, Dict]:
        """
        Распознаёт аудио и возвращает сырой результат (без сохранения)
        
        Args:
            audio_path: путь к WAV файлу
            model_name: модель Whisper
            language: язык ('auto' для автоопределения)
            task: 'transcribe' или 'translate'
        
        Returns:
            (success, result_dict) - результат распознавания в виде словаря
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return False, {"error": f"Файл не найден: {audio_path}"}
        
        if audio_path.suffix.lower() != '.wav':
            return False, {"error": f"Файл должен быть в формате WAV: {audio_path}"}
        
        if not self.load_model(model_name):
            return False, {"error": "Не удалось загрузить модель"}
        
        language_code = None if language == 'auto' else language
        
        try:
            duration = self._get_audio_duration(audio_path)
            if duration:
                self.logger(f"🎤 Распознавание: {audio_path.name} ({duration:.1f} сек)", "info")
            else:
                self.logger(f"🎤 Распознавание: {audio_path.name}", "info")
            
            self.logger(f"   Модель: {model_name}, язык: {language}, устройство: {self.device.upper()}", "info")
            start_time = time.time()
            
            # Выполняем распознавание
            result = self.model.transcribe(
                str(audio_path),
                language=language_code,
                task=task,
                verbose=False,
                fp16=(self.device == "cuda")
            )
            
            elapsed = time.time() - start_time
            
            if duration:
                self.logger(f"✓ Распознано за {elapsed:.1f} сек (в {duration/elapsed:.1f}x реального времени)", "success")
            else:
                self.logger(f"✓ Распознано за {elapsed:.1f} сек", "success")
            
            return True, result
            
        except Exception as e:
            error_msg = f"Ошибка распознавания {audio_path.name}: {str(e)}"
            self.logger(f"✗ {error_msg}", "error")
            return False, {"error": error_msg}
    
    def _save_transcription(self, result: Dict, output_path: Path, format_type: str, filename: str) -> Path:
        """Сохраняет результат распознавания в нужном формате"""
        
        if format_type == 'txt':
            self._save_txt(result, output_path)
        
        elif format_type == 'srt':
            self._save_srt(result, output_path)
        
        elif format_type == 'vtt':
            self._save_vtt(result, output_path)
        
        elif format_type == 'docx':
            self._save_docx(result, output_path, filename)
        
        elif format_type == 'json':
            self._save_json(result, output_path, filename)
        
        elif format_type == 'md':
            self._save_markdown(result, output_path, filename)
        
        elif format_type == 'html':
            self._save_html(result, output_path, filename)
        
        elif format_type == 'csv':
            self._save_csv(result, output_path)
        
        elif format_type == 'txt_timestamps':
            self._save_txt_with_timestamps(result, output_path)
        
        return output_path
    
    def _save_txt(self, result: Dict, output_path: Path):
        """Сохраняет как простой текст"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])
    
    def _save_srt(self, result: Dict, output_path: Path):
        """Сохраняет как SRT субтитры"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result['segments'], 1):
                start = self._format_time_srt(segment['start'])
                end = self._format_time_srt(segment['end'])
                f.write(f"{i}\n{start} --> {end}\n{segment['text'].strip()}\n\n")
    
    def _save_vtt(self, result: Dict, output_path: Path):
        """Сохраняет как WebVTT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for segment in result['segments']:
                start = self._format_time_vtt(segment['start'])
                end = self._format_time_vtt(segment['end'])
                f.write(f"{start} --> {end}\n{segment['text'].strip()}\n\n")
    
    def _save_docx(self, result: Dict, output_path: Path, filename: str):
        """Сохраняет как DOCX (требуется python-docx)"""
        try:
            from docx import Document
            from docx.shared import Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            self.logger("⚠️ python-docx не установлен. Установите: pip install python-docx", "warning")
            self._save_txt(result, output_path.with_suffix('.txt'))
            return
        
        doc = Document()
        
        # Заголовок
        title = doc.add_heading(f'Транскрибация: {filename}', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Информация
        if result['segments']:
            doc.add_paragraph(f'Длительность: {result["segments"][-1]["end"]:.1f} сек')
        doc.add_paragraph(f'Язык: {result.get("language", "unknown")}')
        doc.add_paragraph('')
        
        # Текст с таймкодами
        for segment in result['segments']:
            time_str = f"[{self._format_time_srt(segment['start'])}]"
            p = doc.add_paragraph()
            run_time = p.add_run(time_str)
            run_time.bold = True
            run_time.font.size = Pt(10)
            p.add_run(f" {segment['text'].strip()}")
        
        doc.save(str(output_path))
    
    def _save_json(self, result: Dict, output_path: Path, filename: str):
        """Сохраняет как JSON с метаданными"""
        output_data = {
            'filename': filename,
            'language': result.get('language', 'unknown'),
            'text': result['text'],
            'segments': result.get('segments', []),
            'word_timestamps': result.get('word_timestamps', []),
            'metadata': {
                'model': self.current_model_name,
                'device': self.device,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def _save_markdown(self, result: Dict, output_path: Path, filename: str):
        """Сохраняет как Markdown"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Транскрибация: {filename}\n\n")
            if result['segments']:
                f.write(f"**Длительность:** {result['segments'][-1]['end']:.1f} сек\n\n")
            f.write(f"**Язык:** {result.get('language', 'unknown')}\n\n")
            f.write("---\n\n")
            
            for segment in result['segments']:
                time_str = self._format_time_srt(segment['start'])
                f.write(f"**`[{time_str}]`** {segment['text'].strip()}\n\n")
    
    def _save_html(self, result: Dict, output_path: Path, filename: str):
        """Сохраняет как HTML страницу"""
        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Транскрибация: {filename}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; }}
        .segment {{ margin: 15px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }}
        .timestamp {{ color: #4CAF50; font-weight: bold; font-family: monospace; }}
        .text {{ margin-top: 5px; line-height: 1.6; }}
        .metadata {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>🎙️ Транскрибация: {filename}</h1>
    <div class="metadata">
        <p>📅 {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>🤖 Модель: {self.current_model_name}</p>
        <p>💻 Устройство: {self.device.upper()}</p>
    </div>
"""
        
        for segment in result['segments']:
            html_content += f"""
    <div class="segment">
        <div class="timestamp">[{self._format_time_srt(segment['start'])}]</div>
        <div class="text">{segment['text'].strip()}</div>
    </div>
"""
        
        html_content += """
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _save_csv(self, result: Dict, output_path: Path):
        """Сохраняет как CSV с таймкодами"""
        import csv
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['№', 'Начало', 'Конец', 'Текст'])
            
            for i, segment in enumerate(result['segments'], 1):
                writer.writerow([
                    i,
                    self._format_time_srt(segment['start']),
                    self._format_time_srt(segment['end']),
                    segment['text'].strip()
                ])
    
    def _save_txt_with_timestamps(self, result: Dict, output_path: Path):
        """Сохраняет как TXT с временными метками"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in result['segments']:
                time_str = self._format_time_srt(segment['start'])
                f.write(f"[{time_str}] {segment['text'].strip()}\n")
    
    @staticmethod
    def _format_time_srt(seconds: float) -> str:
        """Форматирует время для SRT (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_time_vtt(seconds: float) -> str:
        """Форматирует время для WebVTT (00:00:00.000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def transcribe_all(self, cache_dir: Path, text_dir: Path, 
                      model_name: str = 'base',
                      language: str = 'auto',
                      output_format: str = 'txt',
                      force_overwrite: bool = False,
                      progress_callback=None,
                      post_process: bool = False) -> Tuple[List[str], List[str]]:
        """
        Распознает все WAV файлы из cache_dir
        
        Args:
            cache_dir: папка с WAV файлами
            text_dir: папка для сохранения результатов
            model_name: модель Whisper
            language: язык
            output_format: формат вывода
            force_overwrite: перезаписывать существующие файлы
            progress_callback: функция для обновления прогресса
            post_process: применять постобработку (по умолчанию False)
        
        Returns:
            (successful_files, failed_files)
        """
        if not cache_dir.exists():
            return [], [f"Папка кэша не существует: {cache_dir}"]
        
        # Получаем все WAV файлы
        wav_files = list(cache_dir.glob("*.wav"))
        
        if not wav_files:
            return [], ["Нет WAV файлов в папке audio_cache"]
        
        successful = []
        failed = []
        
        for idx, wav_path in enumerate(wav_files, 1):
            if progress_callback:
                progress_callback(wav_path.name, idx, len(wav_files))
            
            ext = self._get_extension(output_format)
            output_path = text_dir / f"{wav_path.stem}.{ext}"
            
            # Проверяем существование
            if output_path.exists() and not force_overwrite:
                self.logger(f"⏭️  Пропущен (уже есть текст): {wav_path.name}", "warning")
                successful.append(wav_path.name)
                continue
            
            success, result = self.transcribe(
                str(wav_path), model_name, language, 'transcribe', 
                output_format, str(output_path), post_process
            )
            
            if success:
                successful.append(wav_path.name)
                self.logger(f"✓ Сохранено: {output_path.name}", "success")
            else:
                failed.append(wav_path.name)
                self.logger(f"✗ {result}", "error")
        
        return successful, failed