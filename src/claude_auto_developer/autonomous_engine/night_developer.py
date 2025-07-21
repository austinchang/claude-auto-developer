#!/usr/bin/env python3
"""
Night Developer - 夜間自主開發引擎
在用戶休息時間進行智能開發，最大化開發效率
"""

import asyncio
import logging
import psutil
import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from .schedule_manager import ScheduleManager, ScheduledTask, ScheduleConfig
from ..file_interface.task_file_parser import ParsedTask, TaskPriority, TaskStatus
from ..file_interface.progress_updater import ProgressUpdater
from ..file_interface.github_sync import GitHubTaskSync, GitHubConfig
from ..task_manager.task_analyzer import TaskAnalyzer

logger = logging.getLogger(__name__)

class WorkingMode(Enum):
    """工作模式"""
    NORMAL = "normal"          # 正常模式 - 用戶在線時
    NIGHT = "night"            # 夜間模式 - 用戶休息時
    AGGRESSIVE = "aggressive"  # 積極模式 - 最大化資源利用
    STEALTH = "stealth"       # 隱藏模式 - 最小化影響

class SystemState(Enum):
    """系統狀態"""
    IDLE = "idle"             # 空閒
    WORKING = "working"       # 工作中
    SLEEPING = "sleeping"     # 休眠
    MONITORING = "monitoring" # 監控中

@dataclass
class NightConfig:
    """夜間開發配置"""
    # 工作時間配置
    night_start_time: time = time(22, 0)    # 夜間開始時間
    night_end_time: time = time(6, 0)       # 夜間結束時間
    weekend_enabled: bool = True             # 週末是否啟用
    holiday_enabled: bool = False            # 假日是否啟用
    
    # 資源使用限制（夜間模式）
    max_cpu_usage: float = 0.9             # 最大 CPU 使用率
    max_memory_usage: float = 0.8          # 最大記憶體使用率
    max_disk_io: float = 0.7               # 最大磁碟 I/O
    max_network_io: float = 0.6            # 最大網路 I/O
    
    # 用戶活動檢測
    user_activity_check_interval: int = 300  # 用戶活動檢測間隔（秒）
    user_idle_threshold: int = 1800          # 用戶空閒閾值（秒）
    
    # 任務配置
    priority_tasks_only: bool = False       # 是否只執行高優先級任務
    max_concurrent_tasks: int = 2           # 最大並行任務數
    task_timeout: int = 3600                # 任務超時時間（秒）
    
    # 安全配置
    auto_commit_enabled: bool = True        # 自動提交程式碼
    auto_push_enabled: bool = False         # 自動推送到遠端
    backup_enabled: bool = True             # 自動備份
    
    # GitHub 同步配置
    github_sync_enabled: bool = True        # GitHub 同步功能
    sync_interval: int = 600                # 同步間隔（秒）

@dataclass
class ResourceMonitor:
    """資源監控資料"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    active_processes: int
    user_active: bool

class NightDeveloper:
    """夜間自主開發引擎"""
    
    def __init__(self, config: NightConfig = None):
        """
        初始化夜間開發引擎
        
        Args:
            config: 夜間開發配置
        """
        self.config = config or NightConfig()
        self.state = SystemState.IDLE
        self.working_mode = WorkingMode.NORMAL
        
        # 組件初始化
        schedule_config = ScheduleConfig(
            night_work_enabled=True,
            max_concurrent_tasks=self.config.max_concurrent_tasks,
            cpu_threshold=self.config.max_cpu_usage,
            memory_threshold=self.config.max_memory_usage
        )
        self.schedule_manager = ScheduleManager(schedule_config)
        self.progress_updater = ProgressUpdater()
        self.task_analyzer = TaskAnalyzer()
        
        # GitHub 同步器（如果啟用）
        self.github_sync: Optional[GitHubTaskSync] = None
        if self.config.github_sync_enabled:
            try:
                github_config = GitHubConfig.from_env()
                self.github_sync = GitHubTaskSync(github_config)
            except Exception as e:
                logger.warning(f"GitHub 同步初始化失敗: {str(e)}")
        
        # 運行狀態
        self.is_running = False
        self.main_task: Optional[asyncio.Task] = None
        self.resource_monitor_task: Optional[asyncio.Task] = None
        self.github_sync_task: Optional[asyncio.Task] = None
        
        # 資源監控
        self.resource_history: List[ResourceMonitor] = []
        self.last_user_activity: Optional[datetime] = None
        
        # 統計資訊
        self.stats = {
            'total_working_hours': 0.0,
            'tasks_completed_night': 0,
            'tasks_failed_night': 0,
            'average_task_duration': 0.0,
            'resource_efficiency': 0.0,
            'user_disruptions': 0,
            'auto_commits': 0,
            'github_syncs': 0
        }
        
        # 事件回調
        self.mode_change_callbacks: List[Callable] = []
        self.task_complete_callbacks: List[Callable] = []
        self.resource_alert_callbacks: List[Callable] = []
    
    def add_callback(self, event_type: str, callback: Callable):
        """添加事件回調"""
        if event_type == 'mode_change':
            self.mode_change_callbacks.append(callback)
        elif event_type == 'task_complete':
            self.task_complete_callbacks.append(callback)
        elif event_type == 'resource_alert':
            self.resource_alert_callbacks.append(callback)
    
    async def start(self):
        """啟動夜間開發引擎"""
        if self.is_running:
            logger.warning("夜間開發引擎已在運行中")
            return
        
        logger.info("啟動夜間自主開發引擎...")
        self.is_running = True
        
        # 啟動排程管理器
        await self.schedule_manager.start_scheduler()
        
        # 啟動主工作循環
        self.main_task = asyncio.create_task(self._main_loop())
        
        # 啟動資源監控
        self.resource_monitor_task = asyncio.create_task(self._resource_monitor_loop())
        
        # 啟動 GitHub 同步（如果啟用）
        if self.github_sync:
            self.github_sync_task = asyncio.create_task(self._github_sync_loop())
        
        # 註冊排程管理器回調
        self.schedule_manager.add_callback('task_start', self._on_task_start)
        self.schedule_manager.add_callback('task_complete', self._on_task_complete)
        
        logger.info("夜間開發引擎已啟動")
    
    def stop(self):
        """停止夜間開發引擎"""
        if not self.is_running:
            return
        
        logger.info("停止夜間開發引擎...")
        self.is_running = False
        
        # 停止所有任務
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
        
        if self.resource_monitor_task and not self.resource_monitor_task.done():
            self.resource_monitor_task.cancel()
        
        if self.github_sync_task and not self.github_sync_task.done():
            self.github_sync_task.cancel()
        
        # 停止排程管理器
        self.schedule_manager.stop_scheduler()
        
        logger.info("夜間開發引擎已停止")
    
    async def _main_loop(self):
        """主工作循環"""
        try:
            while self.is_running:
                # 檢查當前時間和工作模式
                current_mode = self._determine_working_mode()
                
                if current_mode != self.working_mode:
                    await self._switch_working_mode(current_mode)
                
                # 根據模式執行不同的邏輯
                if self.working_mode == WorkingMode.NIGHT:
                    await self._night_work_cycle()
                elif self.working_mode == WorkingMode.NORMAL:
                    await self._normal_work_cycle()
                
                # 等待下一個檢查週期
                await asyncio.sleep(60)  # 每分鐘檢查一次
        
        except asyncio.CancelledError:
            logger.info("主工作循環已取消")
        except Exception as e:
            logger.error(f"主工作循環錯誤: {str(e)}")
    
    def _determine_working_mode(self) -> WorkingMode:
        """判斷當前應該使用的工作模式"""
        now = datetime.now()
        current_time = now.time()
        
        # 檢查是否在夜間時段
        if self._is_night_time(current_time):
            # 檢查用戶是否活躍
            if self._is_user_active():
                return WorkingMode.STEALTH  # 用戶在夜間仍活躍，使用隱藏模式
            else:
                return WorkingMode.NIGHT    # 夜間且用戶不活躍，全力工作
        else:
            # 日間時段
            if self._is_user_active():
                return WorkingMode.NORMAL   # 用戶活躍，正常模式
            else:
                return WorkingMode.AGGRESSIVE  # 日間但用戶不活躍，積極模式
    
    def _is_night_time(self, current_time: time) -> bool:
        """檢查是否為夜間時段"""
        night_start = self.config.night_start_time
        night_end = self.config.night_end_time
        
        # 處理跨日的夜間時段（如 22:00 到 06:00）
        if night_start > night_end:
            return current_time >= night_start or current_time <= night_end
        else:
            return night_start <= current_time <= night_end
    
    def _is_user_active(self) -> bool:
        """檢查用戶是否活躍"""
        try:
            # 檢查 CPU 使用率（用戶活動通常會導致 CPU 使用率上升）
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 檢查活動進程數量
            active_processes = len([p for p in psutil.process_iter() if p.status() == 'running'])
            
            # 簡單的用戶活動判斷邏輯
            # 實際實作中可能需要更複雜的檢測方式（如鍵盤滑鼠活動等）
            user_active = cpu_percent > 50 or active_processes > 100
            
            if user_active:
                self.last_user_activity = datetime.now()
            
            # 如果最近有用戶活動，認為用戶仍活躍
            if self.last_user_activity:
                time_since_activity = (datetime.now() - self.last_user_activity).total_seconds()
                return time_since_activity < self.config.user_idle_threshold
            
            return user_active
            
        except Exception as e:
            logger.warning(f"用戶活動檢測失敗: {str(e)}")
            return True  # 保守策略：檢測失敗時假設用戶活躍
    
    async def _switch_working_mode(self, new_mode: WorkingMode):
        """切換工作模式"""
        old_mode = self.working_mode
        self.working_mode = new_mode
        
        logger.info(f"切換工作模式: {old_mode.value} -> {new_mode.value}")
        
        # 根據新模式調整資源使用策略
        if new_mode == WorkingMode.NIGHT:
            # 夜間模式：最大化資源利用
            self.schedule_manager.config.max_concurrent_tasks = self.config.max_concurrent_tasks
            self.schedule_manager.config.cpu_threshold = self.config.max_cpu_usage
        
        elif new_mode == WorkingMode.STEALTH:
            # 隱藏模式：最小化資源使用
            self.schedule_manager.config.max_concurrent_tasks = 1
            self.schedule_manager.config.cpu_threshold = 0.3
        
        elif new_mode == WorkingMode.NORMAL:
            # 正常模式：平衡模式
            self.schedule_manager.config.max_concurrent_tasks = 2
            self.schedule_manager.config.cpu_threshold = 0.6
        
        elif new_mode == WorkingMode.AGGRESSIVE:
            # 積極模式：較高資源使用
            self.schedule_manager.config.max_concurrent_tasks = 3
            self.schedule_manager.config.cpu_threshold = 0.8
        
        # 觸發模式切換回調
        for callback in self.mode_change_callbacks:
            try:
                callback(old_mode, new_mode)
            except Exception as e:
                logger.error(f"模式切換回調失敗: {str(e)}")
    
    async def _night_work_cycle(self):
        """夜間工作週期"""
        logger.debug("執行夜間工作週期")
        
        # 更新狀態
        if self.state != SystemState.WORKING:
            self.state = SystemState.WORKING
            logger.info("進入夜間工作狀態")
        
        # 檢查是否有待執行的任務
        pending_tasks = self._get_pending_night_tasks()
        
        if pending_tasks:
            logger.info(f"夜間模式：找到 {len(pending_tasks)} 個待執行任務")
            
            # 排程任務執行
            for task in pending_tasks:
                try:
                    task_id = self.schedule_manager.schedule_task(task)
                    logger.info(f"已排程夜間任務: {task.title} (ID: {task_id})")
                except Exception as e:
                    logger.error(f"排程任務失敗: {task.title}, 錯誤: {str(e)}")
        
        # 監控資源使用情況
        await self._monitor_resource_usage()
    
    async def _normal_work_cycle(self):
        """正常工作週期"""
        logger.debug("執行正常工作週期")
        
        # 更新狀態
        if self.state != SystemState.MONITORING:
            self.state = SystemState.MONITORING
            logger.info("進入監控狀態")
        
        # 正常模式下主要進行監控和維護工作
        await self._monitor_resource_usage()
    
    def _get_pending_night_tasks(self) -> List[ParsedTask]:
        """獲取適合夜間執行的待處理任務"""
        try:
            # 從文件解析器獲取任務
            from ..file_interface.task_file_parser import TaskFileParser
            parser = TaskFileParser()
            all_tasks = parser.parse_file()
            
            # 過濾適合夜間執行的任務
            night_tasks = []
            
            for task in all_tasks:
                # 只處理待執行的任務
                if task.status != TaskStatus.PENDING:
                    continue
                
                # 如果配置為只執行優先級任務
                if self.config.priority_tasks_only:
                    if task.priority not in [TaskPriority.URGENT, TaskPriority.HIGH]:
                        continue
                
                # 檢查任務是否適合自動化執行
                if self._is_task_suitable_for_automation(task):
                    night_tasks.append(task)
            
            # 按優先級和截止時間排序
            night_tasks.sort(key=lambda t: (
                t.priority.value,
                t.deadline or datetime.max,
                t.line_number
            ))
            
            return night_tasks
            
        except Exception as e:
            logger.error(f"獲取夜間任務失敗: {str(e)}")
            return []
    
    def _is_task_suitable_for_automation(self, task: ParsedTask) -> bool:
        """判斷任務是否適合自動化執行"""
        # 檢查任務描述中是否包含不適合自動化的關鍵字
        automation_unfriendly_keywords = [
            '需要確認', '需要討論', '需要人工', '手動', '確認', '討論',
            'confirm', 'manual', 'discuss', 'review', '測試', 'test'
        ]
        
        description_lower = task.description.lower()
        title_lower = task.title.lower()
        
        for keyword in automation_unfriendly_keywords:
            if keyword in description_lower or keyword in title_lower:
                return False
        
        # 檢查技術棧是否支援自動化
        supported_tech = [
            'python', 'javascript', 'react', 'vue', 'node.js',
            'fastapi', 'django', 'flask', 'express'
        ]
        
        if task.tech_stack:
            tech_lower = [tech.lower() for tech in task.tech_stack]
            if any(tech in supported_tech for tech in tech_lower):
                return True
        
        # 預設認為可以自動化
        return True
    
    async def _monitor_resource_usage(self):
        """監控資源使用情況"""
        try:
            # 收集系統資源資訊
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            
            # 創建監控記錄
            monitor_data = ResourceMonitor(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io_read=disk_io.read_bytes if disk_io else 0,
                disk_io_write=disk_io.write_bytes if disk_io else 0,
                network_sent=network_io.bytes_sent if network_io else 0,
                network_recv=network_io.bytes_recv if network_io else 0,
                active_processes=len(list(psutil.process_iter())),
                user_active=self._is_user_active()
            )
            
            # 添加到歷史記錄
            self.resource_history.append(monitor_data)
            
            # 保留最近 24 小時的記錄
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.resource_history = [
                record for record in self.resource_history
                if record.timestamp > cutoff_time
            ]
            
            # 檢查資源使用是否超過閾值
            await self._check_resource_thresholds(monitor_data)
            
        except Exception as e:
            logger.error(f"資源監控失敗: {str(e)}")
    
    async def _check_resource_thresholds(self, monitor_data: ResourceMonitor):
        """檢查資源使用閾值"""
        alerts = []
        
        # 檢查 CPU 使用率
        if monitor_data.cpu_percent > self.config.max_cpu_usage * 100:
            alerts.append(f"CPU 使用率過高: {monitor_data.cpu_percent:.1f}%")
        
        # 檢查記憶體使用率
        if monitor_data.memory_percent > self.config.max_memory_usage * 100:
            alerts.append(f"記憶體使用率過高: {monitor_data.memory_percent:.1f}%")
        
        # 如果有警告，觸發回調並調整工作策略
        if alerts:
            logger.warning(f"資源使用警告: {', '.join(alerts)}")
            
            # 觸發資源警告回調
            for callback in self.resource_alert_callbacks:
                try:
                    callback(monitor_data, alerts)
                except Exception as e:
                    logger.error(f"資源警告回調失敗: {str(e)}")
            
            # 如果在夜間模式且資源使用過高，切換到隱藏模式
            if self.working_mode == WorkingMode.NIGHT:
                await self._switch_working_mode(WorkingMode.STEALTH)
    
    async def _resource_monitor_loop(self):
        """資源監控循環"""
        try:
            while self.is_running:
                await self._monitor_resource_usage()
                await asyncio.sleep(self.config.user_activity_check_interval)
        
        except asyncio.CancelledError:
            logger.info("資源監控循環已取消")
        except Exception as e:
            logger.error(f"資源監控循環錯誤: {str(e)}")
    
    async def _github_sync_loop(self):
        """GitHub 同步循環"""
        if not self.github_sync:
            return
        
        try:
            async with self.github_sync:
                while self.is_running:
                    try:
                        result = await self.github_sync.sync_once()
                        
                        if result.success:
                            logger.debug(f"GitHub 同步成功: {result.action}")
                            self.stats['github_syncs'] += 1
                        else:
                            logger.warning(f"GitHub 同步失敗: {result.message}")
                    
                    except Exception as e:
                        logger.error(f"GitHub 同步錯誤: {str(e)}")
                    
                    await asyncio.sleep(self.config.sync_interval)
        
        except asyncio.CancelledError:
            logger.info("GitHub 同步循環已取消")
        except Exception as e:
            logger.error(f"GitHub 同步循環錯誤: {str(e)}")
    
    def _on_task_start(self, task: ScheduledTask):
        """任務開始回調"""
        logger.info(f"夜間任務開始: {task.original_task.title}")
        
        # 更新統計
        if self.working_mode == WorkingMode.NIGHT:
            # 記錄夜間工作時間
            pass
    
    def _on_task_complete(self, task: ScheduledTask, success: bool):
        """任務完成回調"""
        logger.info(f"夜間任務{'完成' if success else '失敗'}: {task.original_task.title}")
        
        # 更新統計
        if self.working_mode == WorkingMode.NIGHT:
            if success:
                self.stats['tasks_completed_night'] += 1
            else:
                self.stats['tasks_failed_night'] += 1
        
        # 如果啟用自動提交
        if success and self.config.auto_commit_enabled:
            asyncio.create_task(self._auto_commit_task(task))
        
        # 觸發任務完成回調
        for callback in self.task_complete_callbacks:
            try:
                callback(task, success)
            except Exception as e:
                logger.error(f"任務完成回調失敗: {str(e)}")
    
    async def _auto_commit_task(self, task: ScheduledTask):
        """自動提交任務結果"""
        try:
            logger.info(f"自動提交任務結果: {task.original_task.title}")
            
            # 這裡會與 Git 整合，自動提交程式碼變更
            # 實際實作中需要檢查工作區變更並創建有意義的提交訊息
            
            # 暫時模擬自動提交
            await asyncio.sleep(1)
            
            self.stats['auto_commits'] += 1
            logger.info(f"任務結果已自動提交: {task.original_task.title}")
            
        except Exception as e:
            logger.error(f"自動提交失敗: {task.original_task.title}, 錯誤: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取夜間開發引擎狀態"""
        return {
            'is_running': self.is_running,
            'state': self.state.value,
            'working_mode': self.working_mode.value,
            'config': asdict(self.config),
            'stats': self.stats.copy(),
            'resource_summary': self._get_resource_summary(),
            'github_sync_status': (
                self.github_sync.get_sync_status() 
                if self.github_sync else None
            ),
            'schedule_status': self.schedule_manager.get_schedule_status()
        }
    
    def _get_resource_summary(self) -> Dict[str, Any]:
        """獲取資源使用摘要"""
        if not self.resource_history:
            return {}
        
        recent_records = self.resource_history[-10:]  # 最近 10 筆記錄
        
        return {
            'avg_cpu_usage': sum(r.cpu_percent for r in recent_records) / len(recent_records),
            'avg_memory_usage': sum(r.memory_percent for r in recent_records) / len(recent_records),
            'user_active_ratio': sum(1 for r in recent_records if r.user_active) / len(recent_records),
            'total_records': len(self.resource_history),
            'monitoring_duration_hours': (
                (self.resource_history[-1].timestamp - self.resource_history[0].timestamp).total_seconds() / 3600
                if len(self.resource_history) > 1 else 0
            )
        }
    
    def export_stats(self, output_file: str):
        """匯出統計資料"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'config': asdict(self.config),
            'stats': self.stats.copy(),
            'resource_history': [
                asdict(record) for record in self.resource_history
            ],
            'status': self.get_status()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"統計資料已匯出至: {output_file}")

# 使用範例
async def main():
    """測試夜間開發引擎"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建配置
    config = NightConfig(
        night_start_time=time(22, 0),
        night_end_time=time(6, 0),
        max_cpu_usage=0.8,
        max_memory_usage=0.7,
        github_sync_enabled=False  # 測試時關閉 GitHub 同步
    )
    
    # 創建夜間開發引擎
    night_dev = NightDeveloper(config)
    
    # 添加回調函數
    def on_mode_change(old_mode, new_mode):
        print(f"工作模式變更: {old_mode.value} -> {new_mode.value}")
    
    def on_task_complete(task, success):
        print(f"任務{'完成' if success else '失敗'}: {task.original_task.title}")
    
    night_dev.add_callback('mode_change', on_mode_change)
    night_dev.add_callback('task_complete', on_task_complete)
    
    # 啟動引擎
    await night_dev.start()
    
    try:
        # 運行一段時間
        await asyncio.sleep(300)  # 運行 5 分鐘
    except KeyboardInterrupt:
        print("停止夜間開發引擎...")
    finally:
        night_dev.stop()
    
    # 顯示最終狀態
    status = night_dev.get_status()
    print(f"最終狀態: {json.dumps(status, indent=2, ensure_ascii=False, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())