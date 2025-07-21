"""
File Interface Module - 文件介面模組
提供基於文件的溝通介面，讓用戶通過編輯 TASKS.md 來規劃開發任務
"""

from .task_file_parser import TaskFileParser
from .file_monitor import FileMonitor
from .progress_updater import ProgressUpdater

__all__ = [
    'TaskFileParser',
    'FileMonitor', 
    'ProgressUpdater'
]

__version__ = "1.0.0"