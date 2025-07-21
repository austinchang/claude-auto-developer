#!/usr/bin/env python3
"""
Resource Optimizer - 智能資源使用優化器
動態調整系統資源使用，避免干擾用戶正常工作
"""

import asyncio
import logging
import psutil
import os
import signal
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
import queue

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """資源類型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    GPU = "gpu"

class OptimizationLevel(Enum):
    """優化級別"""
    MINIMAL = "minimal"      # 最小影響
    CONSERVATIVE = "conservative"  # 保守模式
    BALANCED = "balanced"    # 平衡模式
    AGGRESSIVE = "aggressive"  # 積極優化

class ProcessPriority(Enum):
    """進程優先級"""
    LOW = "low"
    BELOW_NORMAL = "below_normal"
    NORMAL = "normal"
    ABOVE_NORMAL = "above_normal"
    HIGH = "high"

@dataclass
class ResourceThreshold:
    """資源閾值配置"""
    cpu_warning: float = 0.7      # CPU 警告閾值
    cpu_critical: float = 0.9     # CPU 危險閾值
    memory_warning: float = 0.8   # 記憶體警告閾值
    memory_critical: float = 0.95 # 記憶體危險閾值
    disk_io_warning: int = 50_000_000   # 磁碟 I/O 警告閾值 (bytes/s)
    disk_io_critical: int = 100_000_000 # 磁碟 I/O 危險閾值 (bytes/s)
    network_warning: int = 10_000_000   # 網路 I/O 警告閾值 (bytes/s)
    network_critical: int = 50_000_000  # 網路 I/O 危險閾值 (bytes/s)

@dataclass
class ProcessInfo:
    """進程資訊"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    io_counters: Optional[Dict[str, int]]
    priority: int
    status: str
    create_time: float
    is_our_process: bool = False  # 是否為我們的進程

@dataclass
class OptimizationAction:
    """優化動作"""
    action_type: str              # 動作類型
    target_pid: Optional[int]     # 目標進程 PID
    old_value: Any               # 原始值
    new_value: Any               # 新值
    timestamp: datetime          # 執行時間
    success: bool                # 是否成功
    reason: str                  # 執行原因

class ResourceOptimizer:
    """智能資源使用優化器"""
    
    def __init__(self, 
                 optimization_level: OptimizationLevel = OptimizationLevel.BALANCED,
                 thresholds: ResourceThreshold = None):
        """
        初始化資源優化器
        
        Args:
            optimization_level: 優化級別
            thresholds: 資源閾值配置
        """
        self.optimization_level = optimization_level
        self.thresholds = thresholds or ResourceThreshold()
        
        # 運行狀態
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.optimization_task: Optional[asyncio.Task] = None
        
        # 進程追蹤
        self.our_processes: Dict[int, ProcessInfo] = {}  # 我們的進程
        self.monitored_processes: Dict[int, ProcessInfo] = {}  # 監控的其他進程
        self.process_history: Dict[int, List[ProcessInfo]] = {}  # 進程歷史
        
        # 優化歷史
        self.optimization_history: List[OptimizationAction] = []
        self.last_optimization: Optional[datetime] = None
        
        # 系統狀態
        self.system_load_history: List[Dict[str, float]] = []
        self.baseline_performance: Optional[Dict[str, float]] = None
        
        # 配置
        self.monitor_interval = 30  # 監控間隔（秒）
        self.optimization_interval = 60  # 優化間隔（秒）
        self.history_retention_hours = 24  # 歷史記錄保留時間
        
        # 回調函數
        self.resource_alert_callbacks: List[Callable] = []
        self.optimization_callbacks: List[Callable] = []
        
        # 統計資訊
        self.stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'cpu_optimizations': 0,
            'memory_optimizations': 0,
            'io_optimizations': 0,
            'average_cpu_reduction': 0.0,
            'average_memory_reduction': 0.0,
            'user_interruptions': 0,
            'optimization_effectiveness': 0.0
        }
    
    def add_callback(self, event_type: str, callback: Callable):
        """添加事件回調"""
        if event_type == 'resource_alert':
            self.resource_alert_callbacks.append(callback)
        elif event_type == 'optimization':
            self.optimization_callbacks.append(callback)
    
    def register_our_process(self, pid: int, name: str = None):
        """註冊我們的進程"""
        try:
            process = psutil.Process(pid)
            process_info = ProcessInfo(
                pid=pid,
                name=name or process.name(),
                cpu_percent=process.cpu_percent(),
                memory_percent=process.memory_percent(),
                io_counters=process.io_counters()._asdict() if process.io_counters() else None,
                priority=process.nice(),
                status=process.status(),
                create_time=process.create_time(),
                is_our_process=True
            )
            
            self.our_processes[pid] = process_info
            logger.info(f"已註冊進程: {name} (PID: {pid})")
            
        except psutil.NoSuchProcess:
            logger.warning(f"無法註冊進程 PID {pid}: 進程不存在")
        except Exception as e:
            logger.error(f"註冊進程失敗 PID {pid}: {str(e)}")
    
    def unregister_our_process(self, pid: int):
        """取消註冊進程"""
        if pid in self.our_processes:
            process_name = self.our_processes[pid].name
            del self.our_processes[pid]
            logger.info(f"已取消註冊進程: {process_name} (PID: {pid})")
    
    async def start(self):
        """啟動資源優化器"""
        if self.is_running:
            logger.warning("資源優化器已在運行中")
            return
        
        logger.info("啟動智能資源優化器...")
        self.is_running = True
        
        # 建立基準性能指標
        await self._establish_baseline()
        
        # 啟動監控任務
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        # 啟動優化任務
        self.optimization_task = asyncio.create_task(self._optimization_loop())
        
        logger.info("資源優化器已啟動")
    
    def stop(self):
        """停止資源優化器"""
        if not self.is_running:
            return
        
        logger.info("停止資源優化器...")
        self.is_running = False
        
        # 停止所有任務
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        
        if self.optimization_task and not self.optimization_task.done():
            self.optimization_task.cancel()
        
        # 恢復所有優化
        self._restore_all_optimizations()
        
        logger.info("資源優化器已停止")
    
    async def _establish_baseline(self):
        """建立基準性能指標"""
        logger.info("建立系統基準性能指標...")
        
        # 收集一段時間的系統性能數據
        baseline_samples = []
        
        for _ in range(10):  # 收集 10 個樣本
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()
                
                sample = {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_read': disk_io.read_bytes if disk_io else 0,
                    'disk_write': disk_io.write_bytes if disk_io else 0,
                    'network_sent': network_io.bytes_sent if network_io else 0,
                    'network_recv': network_io.bytes_recv if network_io else 0,
                    'timestamp': datetime.now()
                }
                
                baseline_samples.append(sample)
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"收集基準數據失敗: {str(e)}")
        
        # 計算平均值作為基準
        if baseline_samples:
            self.baseline_performance = {
                'cpu_percent': sum(s['cpu_percent'] for s in baseline_samples) / len(baseline_samples),
                'memory_percent': sum(s['memory_percent'] for s in baseline_samples) / len(baseline_samples),
                'disk_io_rate': 0,  # 需要計算變化率
                'network_io_rate': 0  # 需要計算變化率
            }
            
            logger.info(f"基準性能指標已建立: CPU {self.baseline_performance['cpu_percent']:.1f}%, "
                       f"記憶體 {self.baseline_performance['memory_percent']:.1f}%")
    
    async def _monitor_loop(self):
        """監控循環"""
        try:
            while self.is_running:
                await self._collect_system_metrics()
                await self._update_process_info()
                await self._check_resource_thresholds()
                await asyncio.sleep(self.monitor_interval)
        
        except asyncio.CancelledError:
            logger.info("監控循環已取消")
        except Exception as e:
            logger.error(f"監控循環錯誤: {str(e)}")
    
    async def _optimization_loop(self):
        """優化循環"""
        try:
            while self.is_running:
                await self._perform_optimization()
                await asyncio.sleep(self.optimization_interval)
        
        except asyncio.CancelledError:
            logger.info("優化循環已取消")
        except Exception as e:
            logger.error(f"優化循環錯誤: {str(e)}")
    
    async def _collect_system_metrics(self):
        """收集系統指標"""
        try:
            # 收集系統資源使用情況
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            # 創建系統負載記錄
            load_record = {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
                'disk_write_bytes': disk_io.write_bytes if disk_io else 0,
                'network_sent_bytes': network_io.bytes_sent if network_io else 0,
                'network_recv_bytes': network_io.bytes_recv if network_io else 0,
                'load_avg_1m': load_avg[0],
                'load_avg_5m': load_avg[1],
                'load_avg_15m': load_avg[2]
            }
            
            # 添加到歷史記錄
            self.system_load_history.append(load_record)
            
            # 清理舊記錄
            cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
            self.system_load_history = [
                record for record in self.system_load_history
                if record['timestamp'] > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"收集系統指標失敗: {str(e)}")
    
    async def _update_process_info(self):
        """更新進程資訊"""
        try:
            # 更新我們的進程資訊
            for pid in list(self.our_processes.keys()):
                try:
                    process = psutil.Process(pid)
                    
                    updated_info = ProcessInfo(
                        pid=pid,
                        name=process.name(),
                        cpu_percent=process.cpu_percent(),
                        memory_percent=process.memory_percent(),
                        io_counters=process.io_counters()._asdict() if process.io_counters() else None,
                        priority=process.nice(),
                        status=process.status(),
                        create_time=process.create_time(),
                        is_our_process=True
                    )
                    
                    self.our_processes[pid] = updated_info
                    
                    # 添加到歷史記錄
                    if pid not in self.process_history:
                        self.process_history[pid] = []
                    
                    self.process_history[pid].append(updated_info)
                    
                    # 保留最近的記錄
                    if len(self.process_history[pid]) > 100:
                        self.process_history[pid] = self.process_history[pid][-100:]
                
                except psutil.NoSuchProcess:
                    # 進程已結束
                    self.unregister_our_process(pid)
                except Exception as e:
                    logger.warning(f"更新進程資訊失敗 PID {pid}: {str(e)}")
            
            # 監控高資源使用的其他進程
            await self._monitor_high_usage_processes()
            
        except Exception as e:
            logger.error(f"更新進程資訊失敗: {str(e)}")
    
    async def _monitor_high_usage_processes(self):
        """監控高資源使用的進程"""
        try:
            # 獲取所有進程並按資源使用排序
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 10 or pinfo['memory_percent'] > 5:  # 閾值過濾
                        processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按 CPU 使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # 更新監控列表（只保留前 20 個高使用率進程）
            self.monitored_processes.clear()
            
            for proc_info in processes[:20]:
                try:
                    pid = proc_info['pid']
                    if pid not in self.our_processes:  # 不監控我們自己的進程
                        process = psutil.Process(pid)
                        
                        monitored_info = ProcessInfo(
                            pid=pid,
                            name=proc_info['name'],
                            cpu_percent=proc_info['cpu_percent'],
                            memory_percent=proc_info['memory_percent'],
                            io_counters=process.io_counters()._asdict() if process.io_counters() else None,
                            priority=process.nice(),
                            status=process.status(),
                            create_time=process.create_time(),
                            is_our_process=False
                        )
                        
                        self.monitored_processes[pid] = monitored_info
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        except Exception as e:
            logger.error(f"監控高使用率進程失敗: {str(e)}")
    
    async def _check_resource_thresholds(self):
        """檢查資源閾值"""
        if not self.system_load_history:
            return
        
        current_load = self.system_load_history[-1]
        alerts = []
        
        # 檢查 CPU 使用率
        cpu_percent = current_load['cpu_percent']
        if cpu_percent > self.thresholds.cpu_critical * 100:
            alerts.append(('cpu', 'critical', cpu_percent))
        elif cpu_percent > self.thresholds.cpu_warning * 100:
            alerts.append(('cpu', 'warning', cpu_percent))
        
        # 檢查記憶體使用率
        memory_percent = current_load['memory_percent']
        if memory_percent > self.thresholds.memory_critical * 100:
            alerts.append(('memory', 'critical', memory_percent))
        elif memory_percent > self.thresholds.memory_warning * 100:
            alerts.append(('memory', 'warning', memory_percent))
        
        # 檢查磁碟和網路 I/O（需要計算變化率）
        if len(self.system_load_history) >= 2:
            prev_load = self.system_load_history[-2]
            time_diff = (current_load['timestamp'] - prev_load['timestamp']).total_seconds()
            
            if time_diff > 0:
                # 磁碟 I/O 速率
                disk_rate = (
                    (current_load['disk_read_bytes'] - prev_load['disk_read_bytes']) +
                    (current_load['disk_write_bytes'] - prev_load['disk_write_bytes'])
                ) / time_diff
                
                if disk_rate > self.thresholds.disk_io_critical:
                    alerts.append(('disk_io', 'critical', disk_rate))
                elif disk_rate > self.thresholds.disk_io_warning:
                    alerts.append(('disk_io', 'warning', disk_rate))
                
                # 網路 I/O 速率
                network_rate = (
                    (current_load['network_sent_bytes'] - prev_load['network_sent_bytes']) +
                    (current_load['network_recv_bytes'] - prev_load['network_recv_bytes'])
                ) / time_diff
                
                if network_rate > self.thresholds.network_critical:
                    alerts.append(('network_io', 'critical', network_rate))
                elif network_rate > self.thresholds.network_warning:
                    alerts.append(('network_io', 'warning', network_rate))
        
        # 觸發警告回調
        if alerts:
            for callback in self.resource_alert_callbacks:
                try:
                    callback(alerts, current_load)
                except Exception as e:
                    logger.error(f"資源警告回調失敗: {str(e)}")
    
    async def _perform_optimization(self):
        """執行優化"""
        try:
            if not self.system_load_history:
                return
            
            current_load = self.system_load_history[-1]
            optimizations = []
            
            # 根據優化級別決定策略
            if self.optimization_level == OptimizationLevel.MINIMAL:
                # 只在極端情況下優化
                if current_load['cpu_percent'] > 95 or current_load['memory_percent'] > 98:
                    optimizations.extend(await self._optimize_critical_resources())
            
            elif self.optimization_level == OptimizationLevel.CONSERVATIVE:
                # 保守優化
                if current_load['cpu_percent'] > 80 or current_load['memory_percent'] > 90:
                    optimizations.extend(await self._optimize_our_processes())
            
            elif self.optimization_level == OptimizationLevel.BALANCED:
                # 平衡優化
                if current_load['cpu_percent'] > 70 or current_load['memory_percent'] > 80:
                    optimizations.extend(await self._optimize_our_processes())
                    optimizations.extend(await self._optimize_system_resources())
            
            elif self.optimization_level == OptimizationLevel.AGGRESSIVE:
                # 積極優化
                optimizations.extend(await self._optimize_our_processes())
                optimizations.extend(await self._optimize_system_resources())
                optimizations.extend(await self._optimize_background_processes())
            
            # 執行優化動作
            if optimizations:
                await self._execute_optimizations(optimizations)
            
            self.last_optimization = datetime.now()
            
        except Exception as e:
            logger.error(f"執行優化失敗: {str(e)}")
    
    async def _optimize_our_processes(self) -> List[OptimizationAction]:
        """優化我們的進程"""
        optimizations = []
        
        for pid, process_info in self.our_processes.items():
            try:
                # 降低 CPU 密集型進程的優先級
                if process_info.cpu_percent > 50:
                    new_priority = min(process_info.priority + 5, 19)  # 降低優先級
                    
                    action = OptimizationAction(
                        action_type='lower_priority',
                        target_pid=pid,
                        old_value=process_info.priority,
                        new_value=new_priority,
                        timestamp=datetime.now(),
                        success=False,
                        reason=f'高 CPU 使用率: {process_info.cpu_percent:.1f}%'
                    )
                    optimizations.append(action)
                
                # 內存使用過高的進程優化
                if process_info.memory_percent > 20:
                    # 這裡可以添加記憶體優化邏輯
                    # 例如：觸發垃圾回收、清理緩存等
                    pass
            
            except Exception as e:
                logger.warning(f"優化進程 {pid} 失敗: {str(e)}")
        
        return optimizations
    
    async def _optimize_system_resources(self) -> List[OptimizationAction]:
        """優化系統資源"""
        optimizations = []
        
        try:
            # 清理系統緩存（如果需要）
            current_load = self.system_load_history[-1]
            
            if current_load['memory_percent'] > 85:
                # 建議系統進行記憶體清理
                action = OptimizationAction(
                    action_type='memory_cleanup',
                    target_pid=None,
                    old_value=current_load['memory_percent'],
                    new_value=None,
                    timestamp=datetime.now(),
                    success=False,
                    reason='記憶體使用率過高'
                )
                optimizations.append(action)
        
        except Exception as e:
            logger.warning(f"系統資源優化失敗: {str(e)}")
        
        return optimizations
    
    async def _optimize_background_processes(self) -> List[OptimizationAction]:
        """優化背景進程（謹慎使用）"""
        optimizations = []
        
        # 只在積極模式下才會優化其他進程
        if self.optimization_level != OptimizationLevel.AGGRESSIVE:
            return optimizations
        
        try:
            # 找出資源使用最高的非關鍵進程
            high_usage_processes = [
                (pid, info) for pid, info in self.monitored_processes.items()
                if info.cpu_percent > 30 and not self._is_critical_process(info.name)
            ]
            
            # 按 CPU 使用率排序
            high_usage_processes.sort(key=lambda x: x[1].cpu_percent, reverse=True)
            
            # 只優化前幾個進程
            for pid, process_info in high_usage_processes[:3]:
                try:
                    # 降低優先級
                    new_priority = min(process_info.priority + 3, 19)
                    
                    action = OptimizationAction(
                        action_type='lower_external_priority',
                        target_pid=pid,
                        old_value=process_info.priority,
                        new_value=new_priority,
                        timestamp=datetime.now(),
                        success=False,
                        reason=f'外部進程高 CPU 使用: {process_info.cpu_percent:.1f}%'
                    )
                    optimizations.append(action)
                
                except Exception as e:
                    logger.warning(f"優化外部進程 {pid} 失敗: {str(e)}")
        
        except Exception as e:
            logger.warning(f"背景進程優化失敗: {str(e)}")
        
        return optimizations
    
    async def _optimize_critical_resources(self) -> List[OptimizationAction]:
        """優化關鍵資源（緊急情況）"""
        optimizations = []
        
        try:
            current_load = self.system_load_history[-1]
            
            # 極端情況下的緊急優化
            if current_load['cpu_percent'] > 95:
                # 暫停非關鍵的我們的進程
                for pid, process_info in self.our_processes.items():
                    if process_info.cpu_percent > 20:
                        action = OptimizationAction(
                            action_type='pause_process',
                            target_pid=pid,
                            old_value='running',
                            new_value='paused',
                            timestamp=datetime.now(),
                            success=False,
                            reason='緊急 CPU 優化'
                        )
                        optimizations.append(action)
        
        except Exception as e:
            logger.warning(f"關鍵資源優化失敗: {str(e)}")
        
        return optimizations
    
    def _is_critical_process(self, process_name: str) -> bool:
        """判斷是否為關鍵系統進程"""
        critical_processes = {
            'systemd', 'kernel', 'init', 'kthreadd', 'ksoftirqd',
            'sshd', 'networkmanager', 'dbus', 'systemd-logind',
            'chrome', 'firefox', 'code', 'pycharm'  # 用戶常用應用
        }
        
        process_name_lower = process_name.lower()
        return any(critical in process_name_lower for critical in critical_processes)
    
    async def _execute_optimizations(self, optimizations: List[OptimizationAction]):
        """執行優化動作"""
        successful_optimizations = 0
        
        for action in optimizations:
            try:
                success = await self._execute_single_optimization(action)
                action.success = success
                
                if success:
                    successful_optimizations += 1
                    logger.info(f"優化成功: {action.action_type} PID:{action.target_pid} - {action.reason}")
                else:
                    logger.warning(f"優化失敗: {action.action_type} PID:{action.target_pid}")
                
                # 添加到歷史記錄
                self.optimization_history.append(action)
                
                # 觸發優化回調
                for callback in self.optimization_callbacks:
                    try:
                        callback(action)
                    except Exception as e:
                        logger.error(f"優化回調失敗: {str(e)}")
            
            except Exception as e:
                logger.error(f"執行優化動作失敗: {str(e)}")
                action.success = False
                self.optimization_history.append(action)
        
        # 更新統計
        self.stats['total_optimizations'] += len(optimizations)
        self.stats['successful_optimizations'] += successful_optimizations
        
        # 清理舊的優化歷史
        cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
        self.optimization_history = [
            action for action in self.optimization_history
            if action.timestamp > cutoff_time
        ]
    
    async def _execute_single_optimization(self, action: OptimizationAction) -> bool:
        """執行單個優化動作"""
        try:
            if action.action_type == 'lower_priority':
                # 降低進程優先級
                process = psutil.Process(action.target_pid)
                process.nice(action.new_value)
                return True
            
            elif action.action_type == 'lower_external_priority':
                # 降低外部進程優先級（需要權限）
                try:
                    process = psutil.Process(action.target_pid)
                    process.nice(action.new_value)
                    return True
                except psutil.AccessDenied:
                    logger.warning(f"無權限修改進程 {action.target_pid} 優先級")
                    return False
            
            elif action.action_type == 'pause_process':
                # 暫停進程
                try:
                    process = psutil.Process(action.target_pid)
                    process.suspend()
                    
                    # 設定定時器恢復進程
                    def resume_process():
                        try:
                            process.resume()
                            logger.info(f"已恢復暫停的進程 {action.target_pid}")
                        except:
                            pass
                    
                    # 60秒後恢復
                    timer = threading.Timer(60.0, resume_process)
                    timer.start()
                    
                    return True
                except psutil.AccessDenied:
                    return False
            
            elif action.action_type == 'memory_cleanup':
                # 觸發記憶體清理
                # 這裡可以實作特定的記憶體清理邏輯
                import gc
                gc.collect()
                return True
            
            else:
                logger.warning(f"未知的優化動作類型: {action.action_type}")
                return False
        
        except psutil.NoSuchProcess:
            logger.warning(f"進程 {action.target_pid} 不存在")
            return False
        except Exception as e:
            logger.error(f"執行優化動作失敗: {str(e)}")
            return False
    
    def _restore_all_optimizations(self):
        """恢復所有優化（在停止時調用）"""
        logger.info("恢復所有優化...")
        
        restored_count = 0
        
        for action in reversed(self.optimization_history):
            try:
                if action.success and action.action_type in ['lower_priority', 'lower_external_priority']:
                    # 恢復原始優先級
                    try:
                        process = psutil.Process(action.target_pid)
                        process.nice(action.old_value)
                        restored_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                elif action.success and action.action_type == 'pause_process':
                    # 恢復暫停的進程
                    try:
                        process = psutil.Process(action.target_pid)
                        if process.status() == psutil.STATUS_STOPPED:
                            process.resume()
                            restored_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            except Exception as e:
                logger.warning(f"恢復優化失敗: {str(e)}")
        
        logger.info(f"已恢復 {restored_count} 個優化")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取資源優化器狀態"""
        current_load = self.system_load_history[-1] if self.system_load_history else {}
        
        return {
            'is_running': self.is_running,
            'optimization_level': self.optimization_level.value,
            'thresholds': asdict(self.thresholds),
            'stats': self.stats.copy(),
            'current_load': current_load,
            'our_processes_count': len(self.our_processes),
            'monitored_processes_count': len(self.monitored_processes),
            'recent_optimizations': [
                asdict(action) for action in self.optimization_history[-5:]
            ],
            'baseline_performance': self.baseline_performance,
            'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None
        }
    
    def get_resource_trends(self, hours: int = 1) -> Dict[str, List[float]]:
        """獲取資源使用趨勢"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_loads = [
            load for load in self.system_load_history
            if load['timestamp'] > cutoff_time
        ]
        
        if not recent_loads:
            return {}
        
        return {
            'timestamps': [load['timestamp'].isoformat() for load in recent_loads],
            'cpu_percent': [load['cpu_percent'] for load in recent_loads],
            'memory_percent': [load['memory_percent'] for load in recent_loads],
            'load_avg_1m': [load.get('load_avg_1m', 0) for load in recent_loads]
        }
    
    def export_optimization_report(self, output_file: str):
        """匯出優化報告"""
        report_data = {
            'export_time': datetime.now().isoformat(),
            'optimization_level': self.optimization_level.value,
            'configuration': asdict(self.thresholds),
            'statistics': self.stats.copy(),
            'optimization_history': [
                asdict(action) for action in self.optimization_history
            ],
            'system_load_history': self.system_load_history[-100:],  # 最近100筆記錄
            'baseline_performance': self.baseline_performance,
            'current_status': self.get_status()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"優化報告已匯出至: {output_file}")

# 使用範例
async def main():
    """測試資源優化器"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建資源優化器
    optimizer = ResourceOptimizer(
        optimization_level=OptimizationLevel.BALANCED,
        thresholds=ResourceThreshold(
            cpu_warning=0.6,
            cpu_critical=0.8,
            memory_warning=0.7,
            memory_critical=0.9
        )
    )
    
    # 註冊當前進程
    optimizer.register_our_process(os.getpid(), "test_process")
    
    # 添加回調函數
    def on_resource_alert(alerts, current_load):
        print(f"資源警告: {alerts}")
    
    def on_optimization(action):
        print(f"優化執行: {action.action_type} - {action.reason}")
    
    optimizer.add_callback('resource_alert', on_resource_alert)
    optimizer.add_callback('optimization', on_optimization)
    
    # 啟動優化器
    await optimizer.start()
    
    try:
        # 運行一段時間
        await asyncio.sleep(180)  # 運行 3 分鐘
    except KeyboardInterrupt:
        print("停止資源優化器...")
    finally:
        optimizer.stop()
    
    # 顯示最終狀態
    status = optimizer.get_status()
    print(f"最終狀態: {json.dumps(status, indent=2, ensure_ascii=False, default=str)}")
    
    # 匯出報告
    optimizer.export_optimization_report("optimization_report.json")

if __name__ == "__main__":
    asyncio.run(main())