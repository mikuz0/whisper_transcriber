"""
file_scanner.py - Сканирование файлов и работа с директориями
"""

from pathlib import Path
from typing import Dict, List, Tuple
import hashlib


class FileScanner:
    """Сканирует и сравнивает файлы в папках"""
    
    @staticmethod
    def get_files_info(directory: Path, extensions: List[str] = None) -> Dict[str, Dict]:
        """
        Возвращает информацию о файлах в директории
        
        Returns:
            {filename: {'size': int, 'modified': float, 'path': str}}
        """
        if not directory.exists():
            return {}
        
        files_info = {}
        for file_path in directory.iterdir():
            if file_path.is_file():
                if extensions is None or file_path.suffix.lower() in extensions:
                    stat = file_path.stat()
                    files_info[file_path.name] = {
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'path': str(file_path)
                    }
        return files_info
    
    @staticmethod
    def compare_directories(source_dir: Path, target_dir: Path, 
                           source_extensions: List[str] = None) -> Dict:
        """
        Сравнивает содержимое двух директорий
        
        Returns:
            {
                'only_in_source': [...],
                'only_in_target': [...],
                'common': [...]
            }
        """
        source_files = {f.stem: f for f in source_dir.glob('*') 
                       if f.is_file() and (source_extensions is None or f.suffix.lower() in source_extensions)}
        
        target_files = {f.stem: f for f in target_dir.glob('*') if f.is_file()}
        
        source_names = set(source_files.keys())
        target_names = set(target_files.keys())
        
        return {
            'only_in_source': [source_files[name] for name in (source_names - target_names)],
            'only_in_target': [target_files[name] for name in (target_names - source_names)],
            'common': [source_files[name] for name in (source_names & target_names)]
        }
    
    @staticmethod
    def count_files_in_directories(work_dir: Path) -> Dict[str, int]:
        """
        Подсчитывает количество файлов в стандартных папках
        
        Returns:
            {
                'video_audio': int,
                'audio_cache': int,
                'text': int,
                'text_processed': int
            }
        """
        video_audio_dir = work_dir / 'video_audio'
        audio_cache_dir = work_dir / 'audio_cache'
        text_dir = work_dir / 'text'
        text_processed_dir = work_dir / 'text_processed'
        
        # Поддерживаемые форматы для исходных файлов
        video_audio_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
                                   '.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus', '.aac'}
        
        counts = {
            'video_audio': 0,
            'audio_cache': 0,
            'text': 0,
            'text_processed': 0
        }
        
        if video_audio_dir.exists():
            counts['video_audio'] = len([f for f in video_audio_dir.iterdir() 
                                        if f.is_file() and f.suffix.lower() in video_audio_extensions])
        
        if audio_cache_dir.exists():
            counts['audio_cache'] = len([f for f in audio_cache_dir.glob('*.wav') if f.is_file()])
        
        if text_dir.exists():
            counts['text'] = len([f for f in text_dir.iterdir() if f.is_file()])
        
        if text_processed_dir.exists():
            counts['text_processed'] = len([f for f in text_processed_dir.iterdir() if f.is_file()])
        
        return counts
    
    @staticmethod
    def get_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """
        Вычисляет MD5 хэш файла
        
        Args:
            file_path: путь к файлу
            chunk_size: размер чанка для чтения
            
        Returns:
            хэш в hex формате
        """
        if not file_path.exists():
            return ""
        
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    
    @staticmethod
    def find_orphaned_files(work_dir: Path) -> Dict[str, List[str]]:
        """
        Находит файлы в кэше и обработанных текстах, для которых нет исходников
        
        Returns:
            {
                'orphaned_cache': [...],
                'orphaned_processed': [...]
            }
        """
        video_audio_dir = work_dir / 'video_audio'
        audio_cache_dir = work_dir / 'audio_cache'
        text_processed_dir = work_dir / 'text_processed'
        
        orphaned_cache = []
        orphaned_processed = []
        
        # Файлы в кэше без исходников
        if audio_cache_dir.exists():
            for wav_file in audio_cache_dir.glob('*.wav'):
                original_name = wav_file.stem
                found = False
                for ext in ['.mp4', '.mkv', '.avi', '.mov', '.mp3', '.m4a', '.wav']:
                    if (video_audio_dir / f"{original_name}{ext}").exists():
                        found = True
                        break
                if not found:
                    orphaned_cache.append(wav_file.name)
        
        # Обработанные тексты без сырых текстов
        if text_processed_dir.exists():
            for processed_file in text_processed_dir.iterdir():
                if processed_file.is_file():
                    raw_file = work_dir / 'text' / processed_file.name
                    if not raw_file.exists():
                        orphaned_processed.append(processed_file.name)
        
        return {
            'orphaned_cache': orphaned_cache,
            'orphaned_processed': orphaned_processed
        }