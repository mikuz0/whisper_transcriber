"""
srt_processor.py - Специализированная обработка SRT субтитров
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path


class SRTProcessor:
    """Класс для постобработки SRT субтитров"""
    
    MIN_BLOCK_DURATION = 2.0
    MIN_WORDS_COUNT = 5
    MAX_LINE_LENGTH = 42
    
    def __init__(self, postprocessor):
        self.postprocessor = postprocessor
    
    def process_srt_file(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            blocks = self._parse_srt(content)
            
            if not blocks:
                return False, "Не удалось распарсить SRT файл"
            
            merged_blocks = self._merge_short_blocks(blocks)
            
            for block in merged_blocks:
                block['text'] = self.postprocessor.process(block['text'])
            
            output_content = self._format_srt(merged_blocks)
            
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            original_count = len(blocks)
            merged_count = original_count - len(merged_blocks)
            
            message = f"Обработан SRT: {Path(input_path).name} (слито {merged_count} блоков)"
            return True, message
            
        except Exception as e:
            return False, f"Ошибка обработки SRT: {str(e)}"
    
    def _parse_srt(self, content: str) -> List[Dict]:
        blocks = []
        raw_blocks = re.split(r'\n\s*\n', content.strip())
        
        for raw in raw_blocks:
            lines = raw.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue
            
            time_line = lines[1].strip()
            time_line = re.sub(r'\s+', ' ', time_line)
            
            time_match = re.match(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                time_line
            )
            if not time_match:
                continue
            
            start = self._time_to_seconds(*time_match.groups()[:4])
            end = self._time_to_seconds(*time_match.groups()[4:])
            
            text = ' '.join(lines[2:]).strip()
            text = re.sub(r'\s+', ' ', text)
            
            blocks.append({
                'index': index,
                'start': start,
                'end': end,
                'text': text
            })
        
        return blocks
    
    def _merge_short_blocks(self, blocks: List[Dict]) -> List[Dict]:
        if not blocks:
            return blocks
        
        merged = []
        current = blocks[0].copy()
        
        for next_block in blocks[1:]:
            duration = current['end'] - current['start']
            word_count = len(current['text'].split())
            
            should_merge = False
            
            if duration < self.MIN_BLOCK_DURATION:
                should_merge = True
            
            if word_count < self.MIN_WORDS_COUNT:
                should_merge = True
            
            if current['text'].rstrip().endswith(('.', '!', '?')):
                should_merge = False
            
            if should_merge:
                current['end'] = next_block['end']
                current['text'] = current['text'] + ' ' + next_block['text']
            else:
                merged.append(current)
                current = next_block.copy()
        
        merged.append(current)
        
        for i, block in enumerate(merged, 1):
            block['index'] = i
        
        return merged
    
    def _format_srt(self, blocks: List[Dict]) -> str:
        output_parts = []
        
        for block in blocks:
            output_parts.append(str(block['index']))
            
            start_str = self._seconds_to_time(block['start'])
            end_str = self._seconds_to_time(block['end'])
            output_parts.append(f"{start_str} --> {end_str}")
            
            text = block['text']
            if len(text) > self.MAX_LINE_LENGTH:
                text = self._wrap_text(text, self.MAX_LINE_LENGTH)
            
            output_parts.append(text)
            output_parts.append('')
        
        return '\n'.join(output_parts)
    
    @staticmethod
    def _time_to_seconds(hours: str, minutes: str, seconds: str, millis: str) -> float:
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000
    
    @staticmethod
    def _seconds_to_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _wrap_text(text: str, width: int) -> str:
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def get_merge_stats(self, original_blocks: int, merged_blocks: int) -> Dict[str, int]:
        return {
            'original': original_blocks,
            'merged': merged_blocks,
            'reduced': original_blocks - merged_blocks,
            'reduction_percent': int((original_blocks - merged_blocks) / original_blocks * 100) if original_blocks > 0 else 0
        }