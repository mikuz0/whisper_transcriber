"""
process_handlers.py - Обработчики запуска и завершения процессов
"""

from PyQt5.QtCore import QObject


class ProcessHandlers(QObject):
    """Класс для управления состоянием процессов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
    
    def start_process(self, control_buttons, progress_widget):
        """
        Подготавливает интерфейс к запуску процесса
        
        Args:
            control_buttons: объект ControlButtons
            progress_widget: объект ProgressWidget
        """
        progress_widget.start_progress()
        control_buttons.set_enabled(False)
    
    def finish_process(self, control_buttons, progress_widget, stats_panel):
        """
        Восстанавливает интерфейс после завершения процесса
        
        Args:
            control_buttons: объект ControlButtons
            progress_widget: объект ProgressWidget
            stats_panel: объект StatsPanel
        """
        progress_widget.finish_progress()
        control_buttons.set_enabled(True)
        stats_panel.refresh()