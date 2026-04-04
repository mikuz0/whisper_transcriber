"""
workers.py - QThread воркеры для асинхронного выполнения задач
"""

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from pathlib import Path

from core.audio_preparer import AudioPreparer
from core.transcriber import WhisperTranscriber
from core.postprocessor import TextPostprocessor, SRTProcessor
from utils.validators import Validators


class WorkerSignals(QObject):
    """Сигналы для воркеров"""
    finished = pyqtSignal(object, object)
    progress = pyqtSignal(str, int, int)
    log = pyqtSignal(str, str)


class PrepareWorker(QThread):
    """Воркер для этапа подготовки файлов"""
    
    def __init__(self, work_dir: Path, force_overwrite: bool):
        super().__init__()
        self.work_dir = work_dir
        self.force_overwrite = force_overwrite
        self.signals = WorkerSignals()
    
    def run(self):
        source_dir = self.work_dir / 'video_audio'
        cache_dir = self.work_dir / 'audio_cache'
        
        def log_callback(msg, level='info'):
            self.signals.log.emit(msg, level)
        
        preparer = AudioPreparer(str(cache_dir), log_callback)
        
        def progress_callback(filename, current, total):
            self.signals.progress.emit(filename, current, total)
        
        successful, failed = preparer.prepare_all(
            source_dir, self.force_overwrite, progress_callback
        )
        
        self.signals.finished.emit(successful, failed)


class TranscribeWorker(QThread):
    """Воркер для этапа распознавания (с поддержкой нескольких форматов)"""
    
    def __init__(self, work_dir: Path, model: str, output_formats: list, force_overwrite: bool):
        super().__init__()
        self.work_dir = work_dir
        self.model = model
        self.output_formats = output_formats
        self.force_overwrite = force_overwrite
        self.signals = WorkerSignals()
    
    def run(self):
        cache_dir = self.work_dir / 'audio_cache'
        text_dir = self.work_dir / 'text'
        
        text_dir.mkdir(parents=True, exist_ok=True)
        
        def log_callback(msg, level='info'):
            self.signals.log.emit(msg, level)
        
        # Для каждого формата создаём отдельный файл
        # Но распознаём один раз, потом сохраняем в разные форматы
        transcriber = WhisperTranscriber(log_callback)
        
        def progress_callback(filename, current, total):
            self.signals.progress.emit(filename, current, total)
        
        # Получаем все WAV файлы
        wav_files = list(cache_dir.glob("*.wav"))
        
        if not wav_files:
            self.signals.finished.emit([], ["Нет WAV файлов в папке audio_cache"])
            return
        
        successful = []
        failed = []
        
        for idx, wav_path in enumerate(wav_files, 1):
            progress_callback(wav_path.name, idx, len(wav_files))
            
            # Распознаём один раз
            success, result = transcriber.transcribe_raw(str(wav_path), self.model)
            
            if not success:
                failed.append(wav_path.name)
                self.signals.log.emit(f"✗ {result}", "error")
                continue
            
            # Сохраняем в каждый выбранный формат
            for fmt in self.output_formats:
                output_path = text_dir / f"{wav_path.stem}.{transcriber._get_extension(fmt)}"
                
                if output_path.exists() and not self.force_overwrite:
                    self.signals.log.emit(f"⏭️  Пропущен (уже есть): {output_path.name}", "warning")
                    continue
                
                saved = transcriber._save_transcription(result, output_path, fmt, wav_path.stem)
                self.signals.log.emit(f"✓ Сохранено: {output_path.name}", "success")
            
            successful.append(wav_path.name)
        
        self.signals.finished.emit(successful, failed)


class PostprocessWorker(QThread):
    """Воркер для этапа постобработки текстов (гибкая конфигурация)"""
    
    def __init__(self, work_dir: Path, actions: list, order: list, force_overwrite: bool):
        super().__init__()
        self.work_dir = work_dir
        self.actions = actions
        self.order = order
        self.force_overwrite = force_overwrite
        self.signals = WorkerSignals()
    
    def run(self):
        source_dir = self.work_dir / 'text'
        target_dir = self.work_dir / 'text_processed'
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        def log_callback(msg, level='info'):
            self.signals.log.emit(msg, level)
        
        # Создаём постпроцессор с гибкой конфигурацией
        postprocessor = TextPostprocessor(
            language='ru',
            actions=self.actions,
            action_order=self.order,
            logger_callback=log_callback
        )
        
        srt_processor = SRTProcessor(postprocessor)
        
        def progress_callback(filename, current, total):
            self.signals.progress.emit(filename, current, total)
        
        if not source_dir.exists():
            self.signals.finished.emit([], [f"Папка не существует: {source_dir}"])
            return
        
        files = [f for f in source_dir.iterdir() if f.is_file()]
        
        if not files:
            self.signals.finished.emit([], ["Нет текстовых файлов для обработки"])
            return
        
        successful = []
        failed = []
        
        for idx, file_path in enumerate(files, 1):
            progress_callback(file_path.name, idx, len(files))
            
            output_path = target_dir / file_path.name
            
            if output_path.exists() and not self.force_overwrite:
                self.signals.log.emit(f"⏭️  Пропущен (уже есть): {file_path.name}", "warning")
                successful.append(file_path.name)
                continue
            
            try:
                if file_path.suffix.lower() == '.srt':
                    success, message = srt_processor.process_srt_file(
                        str(file_path), str(output_path)
                    )
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    processed = postprocessor.process(content)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(processed)
                    
                    success = True
                    message = f"Обработан: {file_path.name}"
                
                if success:
                    successful.append(file_path.name)
                    self.signals.log.emit(f"✓ {message}", "success")
                else:
                    failed.append(file_path.name)
                    self.signals.log.emit(f"✗ {message}", "error")
                    
            except Exception as e:
                failed.append(file_path.name)
                self.signals.log.emit(f"✗ Ошибка {file_path.name}: {str(e)}", "error")
        
        stats = postprocessor.get_stats()
        if successful:
            self.signals.log.emit(
                f"📊 Статистика постобработки: обработано {stats['processed']} файлов, "
                f"исправлено слов: {stats['words_changed']}, "
                f"исправлено предложений: {stats['sentences_capitalized']}",
                "info"
            )
        
        self.signals.finished.emit(successful, failed)


class FullProcessWorker(QThread):
    """Воркер для полного процесса"""
    
    def __init__(self, work_dir: Path, model: str, output_formats: list,
                 force_overwrite: bool, postprocess_actions: list, postprocess_order: list):
        super().__init__()
        self.work_dir = work_dir
        self.model = model
        self.output_formats = output_formats
        self.force_overwrite = force_overwrite
        self.postprocess_actions = postprocess_actions
        self.postprocess_order = postprocess_order
        self.signals = WorkerSignals()
    
    def run(self):
        source_dir = self.work_dir / 'video_audio'
        cache_dir = self.work_dir / 'audio_cache'
        text_dir = self.work_dir / 'text'
        processed_dir = self.work_dir / 'text_processed'
        
        text_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        def log_callback(msg, level='info'):
            self.signals.log.emit(msg, level)
        
        # ==================== ЭТАП 1: ПОДГОТОВКА ====================
        self.signals.log.emit("📦 ЭТАП 1: Подготовка аудиофайлов...", "info")
        
        preparer = AudioPreparer(str(cache_dir), log_callback)
        
        def prep_progress(filename, current, total):
            self.signals.progress.emit(filename, current, total)
        
        successful_prep, failed_prep = preparer.prepare_all(
            source_dir, self.force_overwrite, prep_progress
        )
        
        # ==================== ЭТАП 2: РАСПОЗНАВАНИЕ ====================
        self.signals.log.emit("\n🎤 ЭТАП 2: Распознавание речи...", "info")
        
        transcriber = WhisperTranscriber(log_callback)
        
        wav_files = list(cache_dir.glob("*.wav"))
        successful_trans = []
        failed_trans = []
        
        for idx, wav_path in enumerate(wav_files, 1):
            self.signals.progress.emit(wav_path.name, idx, len(wav_files))
            
            success, result = transcriber.transcribe_raw(str(wav_path), self.model)
            
            if not success:
                failed_trans.append(wav_path.name)
                continue
            
            for fmt in self.output_formats:
                output_path = text_dir / f"{wav_path.stem}.{transcriber._get_extension(fmt)}"
                transcriber._save_transcription(result, output_path, fmt, wav_path.stem)
            
            successful_trans.append(wav_path.name)
        
        if not successful_trans:
            self.signals.log.emit("❌ Нет успешно распознанных файлов", "error")
            self.signals.finished.emit([], failed_prep + failed_trans)
            return
        
        # ==================== ЭТАП 3: ПОСТОБРАБОТКА ====================
        self.signals.log.emit("\n📝 ЭТАП 3: Постобработка текстов...", "info")
        
        postprocessor = TextPostprocessor(
            language='ru',
            actions=self.postprocess_actions,
            action_order=self.postprocess_order,
            logger_callback=log_callback
        )
        srt_processor = SRTProcessor(postprocessor)
        
        files = [f for f in text_dir.iterdir() if f.is_file()]
        
        successful_post = []
        failed_post = []
        
        for idx, file_path in enumerate(files, 1):
            self.signals.progress.emit(file_path.name, idx, len(files))
            
            output_path = processed_dir / file_path.name
            
            if output_path.exists() and not self.force_overwrite:
                successful_post.append(file_path.name)
                continue
            
            try:
                if file_path.suffix.lower() == '.srt':
                    success, _ = srt_processor.process_srt_file(
                        str(file_path), str(output_path)
                    )
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    processed = postprocessor.process(content)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(processed)
                    
                    success = True
                
                if success:
                    successful_post.append(file_path.name)
                else:
                    failed_post.append(file_path.name)
                    
            except Exception as e:
                failed_post.append(file_path.name)
        
        all_failed = list(set(failed_prep + failed_trans + failed_post))
        self.signals.finished.emit(successful_post, all_failed)