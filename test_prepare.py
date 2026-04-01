#!/usr/bin/env python
"""Тест подготовки файлов без GUI"""

from pathlib import Path
from core.audio_preparer import AudioPreparer

def test_prepare():
    work_dir = Path("/home/mikuz/Downloads/whisper_transcriber")
    source_dir = work_dir / 'video_audio'
    cache_dir = work_dir / 'audio_cache'
    
    print(f"Source dir: {source_dir}")
    print(f"Source exists: {source_dir.exists()}")
    print(f"Cache dir: {cache_dir}")
    
    if source_dir.exists():
        files = list(source_dir.iterdir())
        print(f"Files: {[f.name for f in files]}")
    
    def log_callback(msg, level='info'):
        print(f"[{level}] {msg}")
    
    preparer = AudioPreparer(str(cache_dir), log_callback)
    
    def progress_callback(filename, current, total):
        print(f"Progress: {current}/{total} - {filename}")
    
    successful, failed = preparer.prepare_all(source_dir, False, progress_callback)
    
    print(f"\nSuccessful: {successful}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    test_prepare()