#!/usr/bin/env python3
"""
File Monitor - 文件監控系統
實時監控 TASKS.md 文件變化，觸發任務解析和執行
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .task_file_parser import TaskFileParser, ParsedTask
from ..task_manager.task_planner import TaskPlanner
from ..task_manager.task_analyzer import TaskAnalyzer

logger = logging.getLogger(__name__)

class TaskFileEventHandler(FileSystemEventHandler):
    """任務文件事件處理器"""
    
    def __init__(self, file_monitor: 'FileMonitor'):
        super().__init__()
        self.file_monitor = file_monitor
        self.last_modified = 0
        self.debounce_time = 1.0  # 防抖時間（秒）
    
    def on_modified(self, event):
        """文件修改事件處理"""
        if event.is_directory:
            return
        
        # 檢查是否為目標文件
        if Path(event.src_path).name == "TASKS.md":
            # 防抖處理（避免連續觸發）
            current_time = time.time()
            if current_time - self.last_modified < self.debounce_time:
                return
            
            self.last_modified = current_time
            logger.info(f"檢測到任務文件變化: {event.src_path}")
            
            # 異步處理文件變化
            asyncio.create_task(self.file_monitor._handle_file_change(event.src_path))

class FileMonitor:
    """文件監控器"""
    
    def __init__(self, 
                 file_path: str = "/home/tengjung_chang/TASKS.md",
                 auto_execute: bool = True):
        """
        初始化文件監控器
        
        Args:
            file_path: 要監控的文件路徑
            auto_execute: 是否自動執行檢測到的新任務
        """
        self.file_path = Path(file_path)
        self.auto_execute = auto_execute
        
        # 初始化組件
        self.parser = TaskFileParser(str(self.file_path))
        self.task_planner = TaskPlanner()
        self.task_analyzer = TaskAnalyzer()
        
        # 監控狀態
        self.is_monitoring = False
        self.observer = None
        self.event_handler = None
        
        # 任務狀態追蹤
        self.last_tasks: Dict[str, ParsedTask] = {}
        self.task_change_callbacks: List[Callable] = []
        
        # 統計資訊
        self.stats = {
            'total_events': 0,
            'tasks_added': 0,
            'tasks_updated': 0,
            'tasks_completed': 0,
            'last_check': None,
            'monitoring_since': None
        }
    
    def add_change_callback(self, callback: Callable[[List[ParsedTask], List[ParsedTask]], None]):
        """
        添加任務變化回調函數
        
        Args:
            callback: 回調函數，接收 (new_tasks, updated_tasks) 參數
        """
        self.task_change_callbacks.append(callback)
    
    def start_monitoring(self):
        """開始監控文件變化"""
        if self.is_monitoring:
            logger.warning("文件監控已在運行中")
            return
        
        try:
            # 檢查文件是否存在
            if not self.file_path.exists():
                logger.warning(f"任務文件不存在，創建空文件: {self.file_path}")
                self._create_default_task_file()
            
            # 創建事件處理器和觀察者
            self.event_handler = TaskFileEventHandler(self)
            self.observer = Observer()
            
            # 監控文件所在目錄
            watch_directory = self.file_path.parent
            self.observer.schedule(self.event_handler, str(watch_directory), recursive=False)
            
            # 啟動監控
            self.observer.start()
            self.is_monitoring = True
            self.stats['monitoring_since'] = datetime.now()
            
            logger.info(f"開始監控任務文件: {self.file_path}")
            
            # 執行初始掃描
            asyncio.create_task(self._initial_scan())
            
        except Exception as e:
            logger.error(f"啟動文件監控失敗: {str(e)}")
            self.is_monitoring = False
    
    def stop_monitoring(self):
        """停止監控文件變化"""
        if not self.is_monitoring:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.is_monitoring = False
        logger.info("已停止文件監控")
    
    async def _initial_scan(self):
        """初始掃描任務文件"""
        logger.info("執行初始任務掃描...")
        
        try:
            current_tasks = self.parser.parse_file()
            
            if current_tasks:
                logger.info(f"初始掃描發現 {len(current_tasks)} 個任務")
                
                # 處理所有任務（作為新任務）
                await self._process_new_tasks(current_tasks)
                
                # 更新任務狀態追蹤
                self.last_tasks = {self._get_task_key(task): task for task in current_tasks}
            else:
                logger.info("初始掃描未發現任務")
            
            self.stats['last_check'] = datetime.now()
            
        except Exception as e:
            logger.error(f"初始掃描失敗: {str(e)}")
    
    async def _handle_file_change(self, file_path: str):
        """處理文件變化事件"""
        self.stats['total_events'] += 1
        
        try:
            logger.info("處理任務文件變化...")
            
            # 解析當前文件
            current_tasks = self.parser.parse_file()
            current_task_dict = {self._get_task_key(task): task for task in current_tasks}
            
            # 識別變化
            new_tasks, updated_tasks, completed_tasks = self._identify_changes(
                self.last_tasks, current_task_dict
            )
            
            # 處理變化
            if new_tasks:
                logger.info(f"發現 {len(new_tasks)} 個新任務")
                await self._process_new_tasks(new_tasks)
                self.stats['tasks_added'] += len(new_tasks)
            
            if updated_tasks:
                logger.info(f"發現 {len(updated_tasks)} 個更新任務")
                await self._process_updated_tasks(updated_tasks)
                self.stats['tasks_updated'] += len(updated_tasks)
            
            if completed_tasks:
                logger.info(f"發現 {len(completed_tasks)} 個完成任務")
                await self._process_completed_tasks(completed_tasks)
                self.stats['tasks_completed'] += len(completed_tasks)
            
            # 更新狀態追蹤
            self.last_tasks = current_task_dict
            self.stats['last_check'] = datetime.now()
            
            # 觸發回調
            for callback in self.task_change_callbacks:
                try:
                    callback(new_tasks, updated_tasks)
                except Exception as e:
                    logger.error(f"回調函數執行失敗: {str(e)}")
            
        except Exception as e:
            logger.error(f"處理文件變化失敗: {str(e)}")
    
    def _get_task_key(self, task: ParsedTask) -> str:
        """生成任務唯一標識"""
        # 使用標題和行號組合作為唯一標識
        return f"{task.title}_{task.line_number}"
    
    def _identify_changes(self, 
                         old_tasks: Dict[str, ParsedTask], 
                         new_tasks: Dict[str, ParsedTask]) -> tuple:
        """識別任務變化"""
        
        old_keys = set(old_tasks.keys())
        new_keys = set(new_tasks.keys())
        
        # 新增的任務
        added_keys = new_keys - old_keys
        new_task_list = [new_tasks[key] for key in added_keys]
        
        # 更新的任務（內容發生變化）
        common_keys = old_keys & new_keys
        updated_task_list = []
        
        for key in common_keys:
            old_task = old_tasks[key]
            new_task = new_tasks[key]
            
            # 檢查是否有實質性變化
            if self._task_changed(old_task, new_task):
                updated_task_list.append(new_task)
        
        # 完成的任務（狀態變為已完成）
        completed_task_list = []
        for key in common_keys:
            old_task = old_tasks[key]
            new_task = new_tasks[key]
            
            if (old_task.status.value != 'completed' and 
                new_task.status.value == 'completed'):
                completed_task_list.append(new_task)
        
        return new_task_list, updated_task_list, completed_task_list
    
    def _task_changed(self, old_task: ParsedTask, new_task: ParsedTask) -> bool:
        """檢查任務是否發生變化"""
        # 比較關鍵字段
        return (
            old_task.description != new_task.description or
            old_task.priority != new_task.priority or
            old_task.deadline != new_task.deadline or
            old_task.tech_stack != new_task.tech_stack or
            old_task.status != new_task.status
        )
    
    async def _process_new_tasks(self, tasks: List[ParsedTask]):
        """處理新任務"""
        for task in tasks:
            try:
                logger.info(f"處理新任務: {task.title}")
                
                # 使用任務分析器分析任務
                analysis = self.task_analyzer.analyze_requirement(task.description)
                
                # 創建任務到任務管理系統
                created_task = self.task_planner.create_task(
                    description=task.title + (f" - {task.description}" if task.description else ""),
                    deadline=task.deadline.strftime("%Y-%m-%d %H:%M") if task.deadline else "1週",
                    priority=task.priority.value,
                    task_type="project" if "系統" in task.title or "平台" in task.title else "feature",
                    tags=task.tags + task.tech_stack,
                    analysis=analysis
                )
                
                logger.info(f"任務已加入管理系統: {created_task['id']}")
                
                # 如果啟用自動執行且為緊急任務，立即開始執行
                if (self.auto_execute and 
                    task.priority.value == 'urgent' and 
                    task.status.value == 'pending'):
                    await self._auto_execute_task(created_task['id'])
                
            except Exception as e:
                logger.error(f"處理新任務失敗: {task.title}, 錯誤: {str(e)}")
    
    async def _process_updated_tasks(self, tasks: List[ParsedTask]):
        """處理更新的任務"""
        for task in tasks:
            try:
                logger.info(f"處理更新任務: {task.title}")
                
                # 這裡可以添加更新現有任務的邏輯
                # 例如：更新截止日期、優先級、技術棧等
                
            except Exception as e:
                logger.error(f"處理更新任務失敗: {task.title}, 錯誤: {str(e)}")
    
    async def _process_completed_tasks(self, tasks: List[ParsedTask]):
        """處理完成的任務"""
        for task in tasks:
            try:
                logger.info(f"任務已標記為完成: {task.title}")
                
                # 這裡可以添加任務完成後的處理邏輯
                # 例如：生成報告、更新統計等
                
            except Exception as e:
                logger.error(f"處理完成任務失敗: {task.title}, 錯誤: {str(e)}")
    
    async def _auto_execute_task(self, task_id: str):
        """自動執行任務"""
        try:
            logger.info(f"自動執行緊急任務: {task_id}")
            
            # 這裡會與執行引擎整合
            # 暫時模擬執行過程
            await asyncio.sleep(1)
            
            logger.info(f"任務已加入執行隊列: {task_id}")
            
        except Exception as e:
            logger.error(f"自動執行任務失敗: {task_id}, 錯誤: {str(e)}")
    
    def _create_default_task_file(self):
        """創建預設任務文件"""
        default_content = """# 🤖 Claude Auto Developer - 開發任務清單

> 此文件是您與 Claude Auto Developer 的溝通介面  
> 編輯此文件來新增、修改或檢查開發任務的進度  

## 🔥 緊急項目 (24小時內)

## ⭐ 高優先級 (本週內)

## 📅 一般項目 (兩週內)

## 🔖 低優先級 (一個月內)

---

*最後更新: 2025-07-21*  
*系統狀態: 🟢 正常運行*
"""
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(default_content)
        
        logger.info(f"已創建預設任務文件: {self.file_path}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """獲取監控統計資訊"""
        stats = self.stats.copy()
        stats['is_monitoring'] = self.is_monitoring
        stats['file_path'] = str(self.file_path)
        stats['current_tasks_count'] = len(self.last_tasks)
        
        return stats
    
    def get_current_tasks(self) -> List[ParsedTask]:
        """獲取當前任務列表"""
        return list(self.last_tasks.values())
    
    async def manual_refresh(self):
        """手動刷新任務"""
        logger.info("執行手動任務刷新...")
        await self._handle_file_change(str(self.file_path))

# 使用範例
async def main():
    """測試文件監控器"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建監控器
    monitor = FileMonitor()
    
    # 添加變化回調
    def on_task_change(new_tasks, updated_tasks):
        print(f"檢測到變化: {len(new_tasks)} 個新任務, {len(updated_tasks)} 個更新任務")
    
    monitor.add_change_callback(on_task_change)
    
    # 開始監控
    monitor.start_monitoring()
    
    try:
        # 保持運行
        while True:
            await asyncio.sleep(10)
            
            # 顯示統計資訊
            stats = monitor.get_monitoring_stats()
            print(f"監控統計: {stats}")
            
    except KeyboardInterrupt:
        print("停止監控...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())