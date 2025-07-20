#!/usr/bin/env python3
"""
Task Planner - 任務規劃器
負責任務的創建、管理、排程和狀態追蹤
"""

import json
import uuid
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TaskPlanner:
    """任務規劃器 - 管理任務的完整生命週期"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # 使用專案根目錄下的資料庫
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / "logs" / "tasks.db"
            db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """初始化資料庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    deadline TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    estimated_time TEXT,
                    complexity TEXT,
                    tech_stack TEXT,
                    dependencies TEXT,
                    risks TEXT,
                    subtasks TEXT,
                    progress INTEGER DEFAULT 0,
                    assigned_thread TEXT,
                    tags TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)
            
            conn.commit()
    
    def create_task(self, description: str, deadline: str, priority: str, 
                   task_type: str, tags: List[str] = None, 
                   analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        創建新任務
        
        Args:
            description: 任務描述
            deadline: 完成期限
            priority: 優先級
            task_type: 任務類型
            tags: 標籤列表
            analysis: 任務分析結果
            
        Returns:
            創建的任務資訊
        """
        task_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        # 處理 deadline
        deadline_dt = self._parse_deadline(deadline)
        
        task = {
            'id': task_id,
            'description': description,
            'priority': priority,
            'type': task_type,
            'status': 'pending',
            'deadline': deadline_dt.isoformat() if deadline_dt else None,
            'created_at': now,
            'updated_at': now,
            'estimated_time': json.dumps(analysis.get('estimated_time', {})) if analysis else '{}',
            'complexity': analysis.get('complexity', 'medium') if analysis else 'medium',
            'tech_stack': json.dumps(analysis.get('tech_stack', [])) if analysis else '[]',
            'dependencies': json.dumps(analysis.get('dependencies', [])) if analysis else '[]',
            'risks': json.dumps(analysis.get('risks', [])) if analysis else '[]',
            'subtasks': json.dumps(analysis.get('subtasks', [])) if analysis else '[]',
            'progress': 0,
            'assigned_thread': None,
            'tags': json.dumps(tags or [])
        }
        
        # 儲存到資料庫
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tasks 
                (id, description, priority, type, status, deadline, created_at, updated_at,
                 estimated_time, complexity, tech_stack, dependencies, risks, subtasks,
                 progress, assigned_thread, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task['id'], task['description'], task['priority'], task['type'],
                task['status'], task['deadline'], task['created_at'], task['updated_at'],
                task['estimated_time'], task['complexity'], task['tech_stack'],
                task['dependencies'], task['risks'], task['subtasks'],
                task['progress'], task['assigned_thread'], task['tags']
            ))
            
            # 記錄創建日誌
            self._log_task_event(task['id'], 'created', f"任務已創建: {description}")
            
            conn.commit()
        
        logger.info(f"任務已創建: {task_id} - {description}")
        return self._format_task_output(task)
    
    def get_tasks(self, filter_condition: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        獲取任務列表
        
        Args:
            filter_condition: 過濾條件
            limit: 數量限制
            
        Returns:
            任務列表
        """
        query = "SELECT * FROM tasks"
        params = []
        
        if filter_condition:
            if filter_condition in ['urgent', 'high', 'medium', 'low']:
                query += " WHERE priority = ?"
                params.append(filter_condition)
            elif filter_condition in ['feature', 'project', 'bugfix', 'enhancement']:
                query += " WHERE type = ?"
                params.append(filter_condition)
            elif filter_condition in ['pending', 'in_progress', 'completed', 'failed']:
                query += " WHERE status = ?"
                params.append(filter_condition)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            tasks = [dict(row) for row in cursor.fetchall()]
        
        return [self._format_task_output(task) for task in tasks]
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """獲取待執行任務"""
        return self.get_tasks(filter_condition='pending')
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """獲取執行中任務"""
        return self.get_tasks(filter_condition='in_progress')
    
    def update_task_status(self, task_id: str, status: str, progress: int = None) -> bool:
        """
        更新任務狀態
        
        Args:
            task_id: 任務ID
            status: 新狀態
            progress: 進度百分比
            
        Returns:
            是否更新成功
        """
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                logger.error(f"任務不存在: {task_id}")
                return False
            
            update_fields = ["status = ?", "updated_at = ?"]
            params = [status, now]
            
            if progress is not None:
                update_fields.append("progress = ?")
                params.append(progress)
            
            params.append(task_id)
            
            conn.execute(f"""
                UPDATE tasks 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
            
            # 記錄狀態變更日誌
            self._log_task_event(task_id, 'status_change', 
                               f"狀態變更為: {status}" + (f", 進度: {progress}%" if progress is not None else ""))
            
            conn.commit()
        
        logger.info(f"任務狀態已更新: {task_id} -> {status}")
        return True
    
    def assign_task_to_thread(self, task_id: str, thread_id: str) -> bool:
        """分配任務給執行緒"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE tasks 
                SET assigned_thread = ?, updated_at = ?
                WHERE id = ?
            """, (thread_id, now, task_id))
            
            self._log_task_event(task_id, 'assigned', f"分配給執行緒: {thread_id}")
            conn.commit()
        
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        with sqlite3.connect(self.db_path) as conn:
            # 統計各狀態任務數量
            status_counts = {}
            cursor = conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            for row in cursor.fetchall():
                status_counts[f"{row[0]}_tasks"] = row[1]
            
            # 獲取系統資源使用情況（模擬）
            import psutil
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # 統計活躍執行緒
            active_threads = len([task for task in self.get_running_tasks() 
                                if task.get('assigned_thread')])
        
        return {
            'running_tasks': status_counts.get('in_progress_tasks', 0),
            'pending_tasks': status_counts.get('pending_tasks', 0),
            'completed_tasks': status_counts.get('completed_tasks', 0),
            'failed_tasks': status_counts.get('failed_tasks', 0),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'active_threads': active_threads,
            'last_update': datetime.now().isoformat()
        }
    
    def _parse_deadline(self, deadline_str: str) -> Optional[datetime]:
        """解析期限字串"""
        now = datetime.now()
        deadline_str = deadline_str.lower().strip()
        
        try:
            if '分鐘' in deadline_str or 'minute' in deadline_str:
                minutes = int(''.join(filter(str.isdigit, deadline_str)))
                return now + timedelta(minutes=minutes)
            elif '小時' in deadline_str or 'hour' in deadline_str:
                hours = int(''.join(filter(str.isdigit, deadline_str)))
                return now + timedelta(hours=hours)
            elif '天' in deadline_str or 'day' in deadline_str:
                days = int(''.join(filter(str.isdigit, deadline_str)))
                return now + timedelta(days=days)
            elif '週' in deadline_str or 'week' in deadline_str:
                weeks = int(''.join(filter(str.isdigit, deadline_str)))
                return now + timedelta(weeks=weeks)
            elif '月' in deadline_str or 'month' in deadline_str:
                months = int(''.join(filter(str.isdigit, deadline_str)))
                return now + timedelta(days=months*30)
        except ValueError:
            logger.warning(f"無法解析期限: {deadline_str}")
        
        return None
    
    def _log_task_event(self, task_id: str, event_type: str, message: str):
        """記錄任務事件"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO task_logs (task_id, event_type, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (task_id, event_type, message, datetime.now().isoformat()))
    
    def _format_task_output(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """格式化任務輸出"""
        # 解析 JSON 字段
        try:
            task['tech_stack'] = json.loads(task.get('tech_stack', '[]'))
            task['dependencies'] = json.loads(task.get('dependencies', '[]'))
            task['risks'] = json.loads(task.get('risks', '[]'))
            task['subtasks'] = json.loads(task.get('subtasks', '[]'))
            task['tags'] = json.loads(task.get('tags', '[]'))
            task['estimated_time'] = json.loads(task.get('estimated_time', '{}'))
        except json.JSONDecodeError:
            # 如果解析失敗，使用默認值
            task['tech_stack'] = []
            task['dependencies'] = []
            task['risks'] = []
            task['subtasks'] = []
            task['tags'] = []
            task['estimated_time'] = {}
        
        return task
    
    def get_task_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """獲取任務日誌"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM task_logs 
                WHERE task_id = ? 
                ORDER BY timestamp DESC
            """, (task_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_task(self, task_id: str) -> bool:
        """刪除任務"""
        with sqlite3.connect(self.db_path) as conn:
            # 先刪除相關日誌
            conn.execute("DELETE FROM task_logs WHERE task_id = ?", (task_id,))
            
            # 再刪除任務
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"任務已刪除: {task_id}")
                return True
            else:
                logger.warning(f"任務不存在: {task_id}")
                return False