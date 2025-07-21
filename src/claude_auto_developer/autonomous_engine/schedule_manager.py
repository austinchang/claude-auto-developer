#!/usr/bin/env python3
"""
Schedule Manager - 智能任務排程管理器
基於任務優先級、截止日期、資源可用性智能安排開發時程
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import heapq

from ..file_interface.task_file_parser import ParsedTask, TaskPriority, TaskStatus
from ..file_interface.progress_updater import ProgressUpdater
from ..task_manager.task_analyzer import TaskAnalyzer

logger = logging.getLogger(__name__)

class TimeSlot(Enum):
    """時間段枚舉"""
    EARLY_MORNING = "early_morning"    # 06:00-09:00
    MORNING = "morning"                # 09:00-12:00  
    AFTERNOON = "afternoon"            # 13:00-17:00
    EVENING = "evening"                # 18:00-22:00
    NIGHT = "night"                    # 22:00-06:00

class ResourceType(Enum):
    """資源類型"""
    CPU_INTENSIVE = "cpu_intensive"    # CPU 密集型任務
    IO_INTENSIVE = "io_intensive"      # I/O 密集型任務
    NETWORK_HEAVY = "network_heavy"    # 網路密集型任務
    MEMORY_HEAVY = "memory_heavy"      # 記憶體密集型任務
    INTERACTIVE = "interactive"        # 需要交互的任務

@dataclass
class ScheduledTask:
    """排程任務"""
    task_id: str
    original_task: ParsedTask
    estimated_duration: timedelta     # 預估執行時間
    resource_requirements: List[ResourceType]
    priority_score: float            # 優先級分數 (0-100)
    deadline: Optional[datetime]     # 截止時間
    dependencies: List[str]          # 依賴任務 ID
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3

@dataclass  
class TimeSlotConfig:
    """時間段配置"""
    start_time: time
    end_time: time
    cpu_limit: float = 0.8      # CPU 使用限制 (0-1)
    memory_limit: float = 0.7   # 記憶體使用限制 (0-1)  
    concurrent_limit: int = 3   # 並行任務數限制
    allow_interactive: bool = False  # 是否允許交互任務

@dataclass
class ScheduleConfig:
    """排程配置"""
    # 工作時間配置
    work_hours_start: time = time(9, 0)    # 工作開始時間
    work_hours_end: time = time(18, 0)     # 工作結束時間
    night_work_enabled: bool = True        # 是否啟用夜間工作
    night_hours_start: time = time(22, 0)  # 夜間工作開始
    night_hours_end: time = time(6, 0)     # 夜間工作結束
    
    # 資源限制
    max_concurrent_tasks: int = 3
    cpu_threshold: float = 0.8
    memory_threshold: float = 0.7
    
    # 優先級權重
    priority_weight: float = 0.4      # 優先級權重
    deadline_weight: float = 0.4      # 截止日期權重  
    duration_weight: float = 0.2      # 執行時間權重
    
    # 時間段配置
    time_slots: Dict[TimeSlot, TimeSlotConfig] = None
    
    def __post_init__(self):
        if self.time_slots is None:
            self.time_slots = {
                TimeSlot.EARLY_MORNING: TimeSlotConfig(
                    start_time=time(6, 0), end_time=time(9, 0),
                    cpu_limit=0.6, concurrent_limit=2
                ),
                TimeSlot.MORNING: TimeSlotConfig(
                    start_time=time(9, 0), end_time=time(12, 0),
                    cpu_limit=0.8, concurrent_limit=3, allow_interactive=True
                ),
                TimeSlot.AFTERNOON: TimeSlotConfig(
                    start_time=time(13, 0), end_time=time(17, 0),
                    cpu_limit=0.8, concurrent_limit=3, allow_interactive=True
                ),
                TimeSlot.EVENING: TimeSlotConfig(
                    start_time=time(18, 0), end_time=time(22, 0),
                    cpu_limit=0.7, concurrent_limit=2
                ),
                TimeSlot.NIGHT: TimeSlotConfig(
                    start_time=time(22, 0), end_time=time(6, 0),
                    cpu_limit=0.9, memory_limit=0.8, concurrent_limit=4
                )
            }

class ScheduleManager:
    """智能排程管理器"""
    
    def __init__(self, config: ScheduleConfig = None):
        """
        初始化排程管理器
        
        Args:
            config: 排程配置
        """
        self.config = config or ScheduleConfig()
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[Tuple[float, str]] = []  # 優先級隊列 (priority_score, task_id)
        self.running_tasks: Dict[str, ScheduledTask] = {}
        self.completed_tasks: Dict[str, ScheduledTask] = {}
        self.failed_tasks: Dict[str, ScheduledTask] = {}
        
        # 組件
        self.task_analyzer = TaskAnalyzer()
        self.progress_updater = ProgressUpdater()
        
        # 排程狀態
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.last_schedule_update: Optional[datetime] = None
        
        # 回調函數
        self.task_start_callbacks: List[Callable] = []
        self.task_complete_callbacks: List[Callable] = []
        self.schedule_update_callbacks: List[Callable] = []
        
        # 統計資訊
        self.stats = {
            'total_scheduled': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_duration': 0,
            'resource_utilization': {},
            'schedule_efficiency': 0.0
        }
    
    def add_callback(self, event_type: str, callback: Callable):
        """添加事件回調"""
        if event_type == 'task_start':
            self.task_start_callbacks.append(callback)
        elif event_type == 'task_complete':
            self.task_complete_callbacks.append(callback)
        elif event_type == 'schedule_update':
            self.schedule_update_callbacks.append(callback)
    
    def schedule_task(self, task: ParsedTask) -> str:
        """將任務加入排程"""
        task_id = f"{task.title}_{task.line_number}_{int(datetime.now().timestamp())}"
        
        # 分析任務需求
        analysis = self.task_analyzer.analyze_requirement(task.description)
        
        # 創建排程任務
        scheduled_task = ScheduledTask(
            task_id=task_id,
            original_task=task,
            estimated_duration=self._estimate_duration(task, analysis),
            resource_requirements=self._analyze_resource_requirements(task, analysis),
            priority_score=self._calculate_priority_score(task),
            deadline=task.deadline,
            dependencies=task.dependencies
        )
        
        self.scheduled_tasks[task_id] = scheduled_task
        
        # 加入優先級隊列
        heapq.heappush(self.task_queue, (-scheduled_task.priority_score, task_id))
        
        logger.info(f"任務已加入排程: {task.title} (優先級: {scheduled_task.priority_score:.2f})")
        
        # 觸發排程更新
        asyncio.create_task(self._update_schedule())
        
        self.stats['total_scheduled'] += 1
        return task_id
    
    def _estimate_duration(self, task: ParsedTask, analysis: Dict[str, Any]) -> timedelta:
        """預估任務執行時間"""
        # 基礎時間估算
        if task.estimated_time:
            try:
                # 解析時間字符串 (例如: "2小時", "1天", "30分鐘")
                time_str = task.estimated_time.lower()
                
                if '小時' in time_str or 'hour' in time_str:
                    hours = float(''.join(filter(str.isdigit, time_str.split('小')[0].split('hour')[0])))
                    return timedelta(hours=hours)
                elif '天' in time_str or 'day' in time_str:
                    days = float(''.join(filter(str.isdigit, time_str.split('天')[0].split('day')[0])))
                    return timedelta(days=days)
                elif '分鐘' in time_str or 'minute' in time_str:
                    minutes = float(''.join(filter(str.isdigit, time_str.split('分')[0].split('minute')[0])))
                    return timedelta(minutes=minutes)
            except:
                pass
        
        # 基於任務類型和複雜度估算
        base_hours = 2  # 預設 2 小時
        
        # 根據任務類型調整
        title_lower = task.title.lower()
        if any(keyword in title_lower for keyword in ['系統', 'platform', '架構', 'architecture']):
            base_hours *= 3  # 系統級任務需要更長時間
        elif any(keyword in title_lower for keyword in ['bug', '修復', 'fix']):
            base_hours *= 0.5  # Bug 修復通常較快
        elif any(keyword in title_lower for keyword in ['測試', 'test']):
            base_hours *= 0.8  # 測試任務
        
        # 根據技術棧複雜度調整
        tech_complexity = len(task.tech_stack) * 0.2
        base_hours += tech_complexity
        
        # 根據優先級調整（緊急任務可能需要更精細的工作）
        if task.priority == TaskPriority.URGENT:
            base_hours *= 1.2
        
        return timedelta(hours=base_hours)
    
    def _analyze_resource_requirements(self, task: ParsedTask, analysis: Dict[str, Any]) -> List[ResourceType]:
        """分析任務資源需求"""
        requirements = []
        
        title_desc = (task.title + ' ' + task.description).lower()
        tech_stack = [tech.lower() for tech in task.tech_stack]
        
        # 根據技術棧判斷資源需求
        if any(tech in tech_stack for tech in ['python', 'java', 'go', 'rust', 'c++']):
            requirements.append(ResourceType.CPU_INTENSIVE)
        
        if any(tech in tech_stack for tech in ['postgresql', 'mysql', 'mongodb', 'redis']):
            requirements.append(ResourceType.IO_INTENSIVE)
        
        if any(tech in tech_stack for tech in ['fastapi', 'django', 'express', 'api']):
            requirements.append(ResourceType.NETWORK_HEAVY)
        
        if any(keyword in title_desc for keyword in ['大數據', 'ml', 'ai', 'tensorflow', 'pytorch']):
            requirements.append(ResourceType.MEMORY_HEAVY)
        
        if any(keyword in title_desc for keyword in ['gui', 'interface', '界面', '前端']):
            requirements.append(ResourceType.INTERACTIVE)
        
        # 如果沒有特定需求，設為一般 CPU 密集型
        if not requirements:
            requirements.append(ResourceType.CPU_INTENSIVE)
        
        return requirements
    
    def _calculate_priority_score(self, task: ParsedTask) -> float:
        """計算任務優先級分數 (0-100)"""
        score = 0.0
        
        # 基礎優先級分數
        priority_scores = {
            TaskPriority.URGENT: 90,
            TaskPriority.HIGH: 70,  
            TaskPriority.MEDIUM: 50,
            TaskPriority.LOW: 30
        }
        
        score += priority_scores[task.priority] * self.config.priority_weight
        
        # 截止日期緊急程度
        if task.deadline:
            now = datetime.now()
            time_until_deadline = (task.deadline - now).total_seconds()
            
            if time_until_deadline <= 0:
                deadline_score = 100  # 已逾期
            elif time_until_deadline <= 86400:  # 24小時內
                deadline_score = 90
            elif time_until_deadline <= 604800:  # 7天內
                deadline_score = 70
            elif time_until_deadline <= 2592000:  # 30天內
                deadline_score = 50
            else:
                deadline_score = 30
            
            score += deadline_score * self.config.deadline_weight
        else:
            score += 40 * self.config.deadline_weight  # 無截止日期的預設分數
        
        # 任務持續時間（較短的任務優先級稍高）
        estimated_hours = self._estimate_duration(task, {}).total_seconds() / 3600
        if estimated_hours <= 1:
            duration_score = 80
        elif estimated_hours <= 4:
            duration_score = 60
        elif estimated_hours <= 8:
            duration_score = 40
        else:
            duration_score = 20
        
        score += duration_score * self.config.duration_weight
        
        return min(100.0, max(0.0, score))
    
    async def _update_schedule(self):
        """更新任務排程"""
        if not self.task_queue:
            return
        
        logger.info("更新任務排程...")
        
        # 獲取當前時間和可用時間段
        now = datetime.now()
        available_slots = self._get_available_time_slots(now)
        
        # 重新排程所有待執行任務
        rescheduled_tasks = []
        
        # 按優先級處理任務
        temp_queue = []
        while self.task_queue:
            priority_score, task_id = heapq.heappop(self.task_queue)
            
            if task_id not in self.scheduled_tasks:
                continue
            
            task = self.scheduled_tasks[task_id]
            
            # 檢查依賴
            if not self._check_dependencies(task):
                temp_queue.append((priority_score, task_id))
                continue
            
            # 尋找最佳時間段
            best_slot = self._find_best_time_slot(task, available_slots, now)
            
            if best_slot:
                task.scheduled_start = best_slot[0]
                task.scheduled_end = best_slot[1]
                rescheduled_tasks.append(task)
                
                logger.debug(f"任務 {task.original_task.title} 排程至 {task.scheduled_start}")
            else:
                # 無法立即排程，放回隊列
                temp_queue.append((priority_score, task_id))
        
        # 將未排程的任務放回隊列
        for item in temp_queue:
            heapq.heappush(self.task_queue, item)
        
        self.last_schedule_update = now
        
        # 觸發排程更新回調
        for callback in self.schedule_update_callbacks:
            try:
                callback(rescheduled_tasks)
            except Exception as e:
                logger.error(f"排程更新回調失敗: {str(e)}")
    
    def _get_available_time_slots(self, start_time: datetime) -> List[Tuple[datetime, datetime, TimeSlot]]:
        """獲取可用時間段"""
        slots = []
        current = start_time
        
        # 生成未來 7 天的時間段
        for day in range(7):
            day_start = current.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day)
            
            for time_slot, config in self.config.time_slots.items():
                slot_start = day_start.replace(
                    hour=config.start_time.hour,
                    minute=config.start_time.minute
                )
                
                # 處理跨日的時間段（如夜間）
                if config.end_time < config.start_time:
                    slot_end = slot_start + timedelta(days=1)
                    slot_end = slot_end.replace(
                        hour=config.end_time.hour,
                        minute=config.end_time.minute
                    )
                else:
                    slot_end = slot_start.replace(
                        hour=config.end_time.hour,
                        minute=config.end_time.minute
                    )
                
                # 確保時間段在未來
                if slot_end > current:
                    if slot_start < current:
                        slot_start = current
                    slots.append((slot_start, slot_end, time_slot))
        
        return sorted(slots, key=lambda x: x[0])
    
    def _check_dependencies(self, task: ScheduledTask) -> bool:
        """檢查任務依賴是否已完成"""
        for dep_id in task.dependencies:
            if dep_id in self.completed_tasks:
                continue
            elif dep_id in self.scheduled_tasks:
                dep_task = self.scheduled_tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
            else:
                # 依賴任務不存在
                logger.warning(f"任務 {task.task_id} 的依賴 {dep_id} 不存在")
        
        return True
    
    def _find_best_time_slot(self, 
                           task: ScheduledTask, 
                           available_slots: List[Tuple[datetime, datetime, TimeSlot]], 
                           now: datetime) -> Optional[Tuple[datetime, datetime]]:
        """為任務尋找最佳時間段"""
        
        required_duration = task.estimated_duration
        
        for slot_start, slot_end, time_slot in available_slots:
            slot_config = self.config.time_slots[time_slot]
            
            # 檢查時間段是否足夠
            available_duration = slot_end - slot_start
            if available_duration < required_duration:
                continue
            
            # 檢查資源需求匹配
            if not self._check_resource_compatibility(task, slot_config):
                continue
            
            # 檢查並行任務限制
            if self._count_concurrent_tasks(slot_start, slot_end) >= slot_config.concurrent_limit:
                continue
            
            # 找到合適的時間段
            task_start = max(slot_start, now)
            task_end = task_start + required_duration
            
            # 確保任務在時間段內完成
            if task_end <= slot_end:
                return (task_start, task_end)
        
        return None
    
    def _check_resource_compatibility(self, task: ScheduledTask, slot_config: TimeSlotConfig) -> bool:
        """檢查任務資源需求與時間段配置的兼容性"""
        
        # 檢查是否允許交互任務
        if ResourceType.INTERACTIVE in task.resource_requirements:
            if not slot_config.allow_interactive:
                return False
        
        # 這裡可以添加更多資源兼容性檢查
        return True
    
    def _count_concurrent_tasks(self, start_time: datetime, end_time: datetime) -> int:
        """計算指定時間段內的並行任務數"""
        count = 0
        
        for task in self.scheduled_tasks.values():
            if (task.scheduled_start and task.scheduled_end and
                task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]):
                
                # 檢查時間重疊
                if (task.scheduled_start < end_time and task.scheduled_end > start_time):
                    count += 1
        
        return count
    
    async def start_scheduler(self):
        """啟動排程器"""
        if self.is_running:
            logger.warning("排程器已在運行中")
            return
        
        logger.info("啟動智能任務排程器")
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    def stop_scheduler(self):
        """停止排程器"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.scheduler_task and not self.scheduler_task.done():
            self.scheduler_task.cancel()
        
        logger.info("已停止任務排程器")
    
    async def _scheduler_loop(self):
        """排程器主循環"""
        try:
            while self.is_running:
                await self._check_and_start_tasks()
                await self._check_running_tasks()
                await asyncio.sleep(30)  # 每 30 秒檢查一次
        
        except asyncio.CancelledError:
            logger.info("排程器已取消")
        except Exception as e:
            logger.error(f"排程器運行錯誤: {str(e)}")
    
    async def _check_and_start_tasks(self):
        """檢查並啟動到期的任務"""
        now = datetime.now()
        
        for task in list(self.scheduled_tasks.values()):
            if (task.status == TaskStatus.PENDING and
                task.scheduled_start and
                task.scheduled_start <= now):
                
                await self._start_task(task)
    
    async def _start_task(self, task: ScheduledTask):
        """啟動任務執行"""
        logger.info(f"開始執行任務: {task.original_task.title}")
        
        task.status = TaskStatus.IN_PROGRESS
        task.actual_start = datetime.now()
        
        # 移至運行中任務
        self.running_tasks[task.task_id] = task
        
        # 更新進度文件
        self.progress_updater.mark_task_in_progress(
            task.original_task.title,
            progress_percentage=0
        )
        
        # 觸發任務開始回調
        for callback in self.task_start_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"任務開始回調失敗: {str(e)}")
        
        # 這裡會與執行引擎整合
        # 暫時模擬任務執行
        asyncio.create_task(self._simulate_task_execution(task))
    
    async def _simulate_task_execution(self, task: ScheduledTask):
        """模擬任務執行（稍後與執行引擎整合）"""
        try:
            # 模擬執行時間
            execution_time = task.estimated_duration.total_seconds()
            await asyncio.sleep(min(execution_time, 10))  # 限制最大模擬時間
            
            # 標記任務完成
            await self._complete_task(task, success=True)
            
        except Exception as e:
            await self._complete_task(task, success=False, error=str(e))
    
    async def _complete_task(self, task: ScheduledTask, success: bool, error: str = None):
        """完成任務"""
        task.actual_end = datetime.now()
        
        if success:
            task.status = TaskStatus.COMPLETED
            self.completed_tasks[task.task_id] = task
            logger.info(f"任務執行完成: {task.original_task.title}")
            
            # 更新進度文件
            self.progress_updater.mark_task_completed(
                task.original_task.title,
                completion_notes="自動化執行完成"
            )
            
            self.stats['completed_tasks'] += 1
            
        else:
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                task.status = TaskStatus.PENDING
                task.scheduled_start = None
                task.scheduled_end = None
                
                # 重新加入排程隊列
                heapq.heappush(self.task_queue, (-task.priority_score, task.task_id))
                logger.warning(f"任務執行失敗，將重試: {task.original_task.title} ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                self.failed_tasks[task.task_id] = task
                logger.error(f"任務執行失敗（已達最大重試次數）: {task.original_task.title}")
                
                # 更新進度文件
                self.progress_updater.mark_task_failed(
                    task.original_task.title,
                    error_message=error
                )
                
                self.stats['failed_tasks'] += 1
        
        # 從運行中任務移除
        if task.task_id in self.running_tasks:
            del self.running_tasks[task.task_id]
        
        # 觸發任務完成回調
        for callback in self.task_complete_callbacks:
            try:
                callback(task, success)
            except Exception as e:
                logger.error(f"任務完成回調失敗: {str(e)}")
    
    async def _check_running_tasks(self):
        """檢查運行中的任務狀態"""
        now = datetime.now()
        
        for task in list(self.running_tasks.values()):
            # 檢查任務是否超時
            if (task.scheduled_end and now > task.scheduled_end + timedelta(minutes=30)):
                logger.warning(f"任務執行超時: {task.original_task.title}")
                await self._complete_task(task, success=False, error="執行超時")
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """獲取排程狀態"""
        now = datetime.now()
        
        return {
            'is_running': self.is_running,
            'last_update': self.last_schedule_update.isoformat() if self.last_schedule_update else None,
            'stats': self.stats.copy(),
            'task_counts': {
                'scheduled': len(self.scheduled_tasks),
                'queued': len(self.task_queue),
                'running': len(self.running_tasks),
                'completed': len(self.completed_tasks),
                'failed': len(self.failed_tasks)
            },
            'upcoming_tasks': [
                {
                    'title': task.original_task.title,
                    'scheduled_start': task.scheduled_start.isoformat() if task.scheduled_start else None,
                    'priority_score': task.priority_score,
                    'estimated_duration': str(task.estimated_duration)
                }
                for task in sorted(
                    [t for t in self.scheduled_tasks.values() if t.scheduled_start and t.scheduled_start > now],
                    key=lambda x: x.scheduled_start
                )[:5]  # 顯示接下來 5 個任務
            ]
        }
    
    def export_schedule(self, output_file: str):
        """匯出排程到文件"""
        schedule_data = {
            'export_time': datetime.now().isoformat(),
            'config': asdict(self.config),
            'tasks': {
                task_id: {
                    **asdict(task),
                    'original_task': asdict(task.original_task),
                    'scheduled_start': task.scheduled_start.isoformat() if task.scheduled_start else None,
                    'scheduled_end': task.scheduled_end.isoformat() if task.scheduled_end else None,
                    'actual_start': task.actual_start.isoformat() if task.actual_start else None,
                    'actual_end': task.actual_end.isoformat() if task.actual_end else None
                }
                for task_id, task in self.scheduled_tasks.items()
            },
            'stats': self.stats
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schedule_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"排程已匯出至: {output_file}")

# 使用範例
async def main():
    """測試排程管理器"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建排程管理器
    scheduler = ScheduleManager()
    
    # 添加回調函數
    def on_task_start(task):
        print(f"任務開始: {task.original_task.title}")
    
    def on_task_complete(task, success):
        print(f"任務{'完成' if success else '失敗'}: {task.original_task.title}")
    
    scheduler.add_callback('task_start', on_task_start)
    scheduler.add_callback('task_complete', on_task_complete)
    
    # 啟動排程器
    await scheduler.start_scheduler()
    
    try:
        # 運行一段時間
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("停止排程器...")
    finally:
        scheduler.stop_scheduler()
    
    # 顯示最終狀態
    status = scheduler.get_schedule_status()
    print(f"排程狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())