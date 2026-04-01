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
    finished = pyqtSignal(object, object)  # (successful_list, failed_list)
    progress = pyqtSignal(str, int, int)   # (filename, current, total)
    log = pyqtSignal(str, str)             # (message, level)


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
    """Воркер для этапа распознавания (без постобработки)"""
    
    def __init__(self, work_dir: Path, model: str, language: str, 
                 output_format: str, force_overwrite: bool):
        super().__init__()
        self.work_dir = work_dir
        self.model = model
        self.language = language
        self.output_format = output_format
        self.force_overwrite = force_overwrite
        self.signals = WorkerSignals()
    
    def run(self):
        cache_dir = self.work_dir / 'audio_cache'
        text_dir = self.work_dir / 'text'
        
        text_dir.mkdir(parents=True, exist_ok=True)
        
        def log_callback(msg, level='info'):
            self.signals.log.emit(msg, level)
        
        transcriber = WhisperTranscriber(log_callback, postprocess_level='minimal')
        
        def progress_callback(filename, current, total):
            self.signals.progress.emit(filename, current, total)
        
        successful, failed = transcriber.transcribe_all(
            cache_dir, text_dir, self.model, self.language,
            self.output_format, self.force_overwrite, progress_callback,
            post_process=False
        )
        
        self.signals.finished.emit(successful, failed)


class PostprocessWorker(QThread):
    """Воркер для этапа постобработки текстов (с поддержкой SRT)"""
    
    def __init__(self, work_dir: Path, postprocess_level: str, force_overwrite: bool):
        super().__init__()
        self.work_dir = work_dir
        self.postprocess_level = postprocess_level
        self.force_overwrite = force_overwrite
        self.signals = WorkerSignals()
    
    def run(self):
        source_dir = self.work_dir / 'text'
        target_dir = self.work_dir / 'text_processed'
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        def log_callback(msg, level='info'):
            self.signals.log.emit(msg, level)
        
        postprocessor = TextPostprocessor(language='ru', level=self.postprocess_level)
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
    """Воркер для полного процесса (подготовка + распознавание + постобработка)"""
    
    def __init__(self, work_dir: Path, model: str, language: str,
                 output_format: str, force_overwrite: bool, postprocess_level: str = 'standard'):
        super().__init__()
        self.work_dir = work_dir
        self.model = model
        self.language = language
        self.output_format = output_format
        self.force_overwrite = force_overwrite
        self.postprocess_level = postprocess_level
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
            # Для подготовки используем сигнал с 3 аргументами (filename, current, total)
            self.signals.progress.emit(filename, current, total)
        
        successful_prep, failed_prep = preparer.prepare_all(
            source_dir, self.force_overwrite, prep_progress
        )
        
        # ==================== ЭТАП 2: РАСПОЗНАВАНИЕ ====================
        self.signals.log.emit("\n🎤 ЭТАП 2: Распознавание речи...", "info")
        
        transcriber = WhisperTranscriber(log_callback, postprocess_level='minimal')
        
        def trans_progress(filename, current, total):
            self.signals.progress.emit(filename, current, total)
        
        successful_trans, failed_trans = transcriber.transcribe_all(
            cache_dir, text_dir, self.model, self.language,
            self.output_format, self.force_overwrite, trans_progress,
            post_process=False
        )
        
        if not successful_trans:
            self.signals.log.emit("❌ Нет успешно распознанных файлов", "error")
            self.signals.finished.emit([], failed_prep + failed_trans)
            return
        
        # ==================== ЭТАП 3: ПОСТОБРАБОТКА ====================
        self.signals.log.emit("\n📝 ЭТАП 3: Постобработка текстов...", "info")
        
        postprocessor = TextPostprocessor(language='ru', level=self.postprocess_level)
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
                    successful_post.append(file_path.name)
                    self.signals.log.emit(f"✓ {message}", "success")
                else:
                    failed_post.append(file_path.name)
                    self.signals.log.emit(f"✗ {message}", "error")
                    
            except Exception as e:
                failed_post.append(file_path.name)
                self.signals.log.emit(f"✗ Ошибка {file_path.name}: {str(e)}", "error")
        
        stats = postprocessor.get_stats()
        if successful_post:
            self.signals.log.emit(
                f"📊 Статистика постобработки: обработано {stats['processed']} файлов, "
                f"исправлено слов: {stats['words_changed']}, "
                f"исправлено предложений: {stats['sentences_capitalized']}",
                "info"
            )
        
        all_failed = list(set(failed_prep + failed_trans + failed_post))
        self.signals.finished.emit(successful_post, all_failed)