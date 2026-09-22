"""
dialogs - Модуль диалоговых окон
"""

from .settings_dialog import SettingsDialog
from .model_dialog import ModelDialog
from .formats_dialog import FormatsDialog
from .postprocess_dialog import PostprocessDialog
from .confirmation_dialog import ConfirmationDialogs

__all__ = [
    'SettingsDialog', 
    'ModelDialog', 
    'FormatsDialog', 
    'PostprocessDialog',
    'ConfirmationDialogs'
]