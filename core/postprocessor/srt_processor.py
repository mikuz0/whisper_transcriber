"""
srt_processor.py - Специализированная обработка SRT субтитров
Выполняет:
- Парсинг SRT файлов
- Слияние коротких блоков для читаемости
- Постобработку текста
- Корректное форматирование таймкодов
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path


class SRTProcessor:
    """
    Класс для постобработки SRT субтитров
    
    Особенности:
    - Объединяет блоки короче MIN_BLOCK_DURATION секунд
    - Объединяет блоки с менее чем MIN_WORDS_COUNT слов
    - Сохраняет границы предложений (не сливает через точку)
    - Форматирует таймкоды без лишних пробелов
    - Разбивает длинные строки для удобного чтения
    """
    
    # Минимальная длительность блока в секундах для слияния
    MIN_BLOCK_DURATION = 2.0
    
    # Минимальное количество слов для слияния
    MIN_WORDS_COUNT = 5
    
    # Максимальная длина строки для переноса (символов)
    MAX_LINE_LENGTH = 42
    
    def __init__(self, postprocessor):
        """
        Args:
            postprocessor: объект TextPostprocessor для обработки текста
        """
        self.postprocessor = postprocessor
    
    def process_srt_file(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Обрабатывает SRT файл целиком
        
        Args:
            input_path: путь к исходному SRT
            output_path: путь для сохранения
            
        Returns:
            (success, message)
        """
        try:
            # Читаем исходный SRT
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим SRT
            blocks = self._parse_srt(content)
            
            if not blocks:
                return False, "Не удалось распарсить SRT файл"
            
            # Сливаем короткие блоки
            merged_blocks = self._merge_short_blocks(blocks)
            
            # Постобработка текста
            for block in merged_blocks:
                block['text'] = self.postprocessor.process(block['text'])
            
            # Форматируем обратно
            output_content = self._format_srt(merged_blocks)
            
            # Сохраняем
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            # Подсчитываем статистику
            original_blocks = len(blocks)
            merged_count = original_blocks - len(merged_blocks)
            
            message = f"Обработан SRT: {Path(input_path).name} (слито {merged_count} блоков)"
            return True, message
            
        except Exception as e:
            return False, f"Ошибка обработки SRT: {str(e)}"
    
    def _parse_srt(self, content: str) -> List[Dict]:
        """
        Парсит SRT файл в список блоков
        
        Формат блока:
        1
        00:00:01,000 --> 00:00:04,000
        Текст субтитра
        
        Returns:
            список блоков с ключами: index, start, end, text
        """
        blocks = []
        
        # Разделяем по пустым строкам
        raw_blocks = re.split(r'\n\s*\n', content.strip())
        
        for raw in raw_blocks:
            lines = raw.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # Номер блока
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue
            
            # Таймкоды (исправляем возможные лишние пробелы)
            time_line = lines[1].strip()
            # Убираем лишние пробелы внутри таймкодов
            time_line = re.sub(r'\s+', ' ', time_line)
            
            # Формат: HH:MM:SS,mmm --> HH:MM:SS,mmm
            time_match = re.match(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                time_line
            )
            if not time_match:
                continue
            
            start = self._time_to_seconds(*time_match.groups()[:4])
            end = self._time_to_seconds(*time_match.groups()[4:])
            
            # Текст (может быть несколько строк)
            text = ' '.join(lines[2:]).strip()
            # Убираем лишние пробелы внутри текста
            text = re.sub(r'\s+', ' ', text)
            
            blocks.append({
                'index': index,
                'start': start,
                'end': end,
                'text': text
            })
        
        return blocks
    
    def _merge_short_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Сливает короткие блоки с соседними
        
        Правила слияния:
        - Блок короче MIN_BLOCK_DURATION секунд
        - Блок содержит меньше MIN_WORDS_COUNT слов
        - НЕ сливаем, если текущий блок заканчивается на точку, ! или ?
        
        Args:
            blocks: список исходных блоков
            
        Returns:
            список блоков после слияния
        """
        if not blocks:
            return blocks
        
        merged = []
        current = blocks[0].copy()
        
        for next_block in blocks[1:]:
            duration = current['end'] - current['start']
            word_count = len(current['text'].split())
            
            # Проверяем, нужно ли сливать
            should_merge = False
            
            # Сливаем если блок короткий
            if duration < self.MIN_BLOCK_DURATION:
                should_merge = True
            
            # Сливаем если мало слов
            if word_count < self.MIN_WORDS_COUNT:
                should_merge = True
            
            # Не сливаем если текущий блок заканчивается на точку, ! или ?
            if current['text'].rstrip().endswith(('.', '!', '?')):
                should_merge = False
            
            if should_merge:
                # Сливаем: объединяем текст и расширяем время конца
                current['end'] = next_block['end']
                current['text'] = current['text'] + ' ' + next_block['text']
            else:
                # Сохраняем текущий блок и начинаем новый
                merged.append(current)
                current = next_block.copy()
        
        # Добавляем последний блок
        merged.append(current)
        
        # Перенумеровываем блоки
        for i, block in enumerate(merged, 1):
            block['index'] = i
        
        return merged
    
    def _format_srt(self, blocks: List[Dict]) -> str:
        """
        Форматирует блоки обратно в SRT
        
        Args:
            blocks: список блоков
            
        Returns:
            строка в формате SRT
        """
        output_parts = []
        
        for block in blocks:
            # Номер блока
            output_parts.append(str(block['index']))
            
            # Таймкоды (без лишних пробелов)
            start_str = self._seconds_to_time(block['start'])
            end_str = self._seconds_to_time(block['end'])
            output_parts.append(f"{start_str} --> {end_str}")
            
            # Текст (разбиваем на строки для читаемости)
            text = block['text']
            if len(text) > self.MAX_LINE_LENGTH:
                text = self._wrap_text(text, self.MAX_LINE_LENGTH)
            
            output_parts.append(text)
            output_parts.append('')  # Пустая строка между блоками
        
        return '\n'.join(output_parts)
    
    @staticmethod
    def _time_to_seconds(hours: str, minutes: str, seconds: str, millis: str) -> float:
        """
        Преобразует время из формата SRT в секунды
        
        Args:
            hours: часы (HH)
            minutes: минуты (MM)
            seconds: секунды (SS)
            millis: миллисекунды (mmm)
            
        Returns:
            время в секундах (float)
        """
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000
    
    @staticmethod
    def _seconds_to_time(seconds: float) -> str:
        """
        Преобразует секунды в формат SRT: HH:MM:SS,mmm
        
        Args:
            seconds: время в секундах
            
        Returns:
            строка в формате SRT
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _wrap_text(text: str, width: int) -> str:
        """
        Разбивает длинный текст на строки по width символов
        
        Args:
            text: исходный текст
            width: максимальная ширина строки в символах
            
        Returns:
            текст с переносами строк
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            # +1 для пробела
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
        """
        Возвращает статистику слияния блоков
        
        Args:
            original_blocks: исходное количество блоков
            merged_blocks: количество блоков после слияния
            
        Returns:
            словарь со статистикой
        """
        return {
            'original': original_blocks,
            'merged': merged_blocks,
            'reduced': original_blocks - merged_blocks,
            'reduction_percent': int((original_blocks - merged_blocks) / original_blocks * 100) if original_blocks > 0 else 0
        }