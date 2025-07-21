#!/usr/bin/env python3
"""
Progress Updater - 進度狀態更新器
自動更新 TASKS.md 文件中的任務完成狀態和進度資訊
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .task_file_parser import TaskFileParser, ParsedTask, TaskStatus

logger = logging.getLogger(__name__)

@dataclass
class TaskUpdate:
    """任務更新資訊"""
    task_id: str
    new_status: TaskStatus
    progress_percentage: Optional[int] = None
    completion_time: Optional[datetime] = None
    notes: Optional[str] = None
    github_link: Optional[str] = None

class ProgressUpdater:
    """進度狀態更新器"""
    
    def __init__(self, file_path: str = "/home/tengjung_chang/TASKS.md"):
        """
        初始化進度更新器
        
        Args:
            file_path: 任務文件路徑
        """
        self.file_path = Path(file_path)
        self.parser = TaskFileParser(str(file_path))
        
        # 狀態標記映射
        self.status_markers = {
            TaskStatus.PENDING: '[ ]',
            TaskStatus.IN_PROGRESS: '[~]',
            TaskStatus.COMPLETED: '[x]',
            TaskStatus.FAILED: '[!]'
        }
        
        # 備份設定
        self.backup_enabled = True
        self.max_backups = 10
    
    def update_task_status(self, 
                          task_title: str, 
                          new_status: TaskStatus,
                          progress_percentage: Optional[int] = None,
                          completion_notes: Optional[str] = None,
                          github_link: Optional[str] = None) -> bool:
        """
        更新任務狀態
        
        Args:
            task_title: 任務標題
            new_status: 新狀態
            progress_percentage: 進度百分比
            completion_notes: 完成備註
            github_link: GitHub 專案連結
            
        Returns:
            是否更新成功
        """
        try:
            logger.info(f"更新任務狀態: {task_title} -> {new_status.value}")
            
            # 備份原文件
            if self.backup_enabled:
                self._create_backup()
            
            # 讀取文件內容
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 尋找並更新目標任務
            updated = False
            for i, line in enumerate(lines):
                if self._is_target_task(line, task_title):
                    # 更新狀態標記
                    new_line = self._update_task_line(
                        line, new_status, progress_percentage, 
                        completion_notes, github_link
                    )
                    
                    if new_line != line:
                        lines[i] = new_line
                        updated = True
                        logger.info(f"已更新第 {i+1} 行: {task_title}")
                        break
            
            if updated:
                # 寫回文件
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # 更新文件底部的統計資訊
                self._update_statistics()
                
                logger.info(f"任務狀態更新完成: {task_title}")
                return True
            else:
                logger.warning(f"未找到要更新的任務: {task_title}")
                return False
                
        except Exception as e:
            logger.error(f"更新任務狀態失敗: {str(e)}")
            return False
    
    def batch_update_tasks(self, updates: List[TaskUpdate]) -> Dict[str, bool]:
        """
        批量更新任務狀態
        
        Args:
            updates: 任務更新列表
            
        Returns:
            更新結果字典 {task_id: success}
        """
        results = {}
        
        if not updates:
            return results
        
        logger.info(f"開始批量更新 {len(updates)} 個任務")
        
        try:
            # 備份原文件
            if self.backup_enabled:
                self._create_backup()
            
            # 讀取文件內容
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 處理每個更新
            for update in updates:
                try:
                    updated = False
                    
                    for i, line in enumerate(lines):
                        if self._is_target_task_by_id(line, update.task_id):
                            # 更新狀態標記
                            new_line = self._update_task_line(
                                line, update.new_status, update.progress_percentage,
                                update.notes, update.github_link
                            )
                            
                            if new_line != line:
                                lines[i] = new_line
                                updated = True
                                break
                    
                    results[update.task_id] = updated
                    
                except Exception as e:
                    logger.error(f"更新任務失敗: {update.task_id}, 錯誤: {str(e)}")
                    results[update.task_id] = False
            
            # 寫回文件
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 更新統計資訊
            self._update_statistics()
            
            successful_updates = sum(results.values())
            logger.info(f"批量更新完成: {successful_updates}/{len(updates)} 個任務更新成功")
            
        except Exception as e:
            logger.error(f"批量更新失敗: {str(e)}")
            for update in updates:
                results[update.task_id] = False
        
        return results
    
    def mark_task_completed(self, 
                           task_title: str,
                           github_link: Optional[str] = None,
                           completion_notes: Optional[str] = None) -> bool:
        """
        標記任務為已完成
        
        Args:
            task_title: 任務標題
            github_link: GitHub 專案連結
            completion_notes: 完成備註
            
        Returns:
            是否更新成功
        """
        return self.update_task_status(
            task_title=task_title,
            new_status=TaskStatus.COMPLETED,
            progress_percentage=100,
            completion_notes=completion_notes,
            github_link=github_link
        )
    
    def mark_task_in_progress(self, 
                             task_title: str,
                             progress_percentage: Optional[int] = None) -> bool:
        """
        標記任務為執行中
        
        Args:
            task_title: 任務標題
            progress_percentage: 進度百分比
            
        Returns:
            是否更新成功
        """
        return self.update_task_status(
            task_title=task_title,
            new_status=TaskStatus.IN_PROGRESS,
            progress_percentage=progress_percentage
        )
    
    def mark_task_failed(self, 
                        task_title: str,
                        error_message: Optional[str] = None) -> bool:
        """
        標記任務為失敗
        
        Args:
            task_title: 任務標題
            error_message: 錯誤訊息
            
        Returns:
            是否更新成功
        """
        return self.update_task_status(
            task_title=task_title,
            new_status=TaskStatus.FAILED,
            completion_notes=error_message
        )
    
    def _is_target_task(self, line: str, task_title: str) -> bool:
        """檢查是否為目標任務行"""
        # 檢查是否為任務行格式
        if not re.match(r'^-\s*\[[x~!\s]\]', line.strip(), re.IGNORECASE):
            return False
        
        # 檢查標題是否匹配
        # 提取任務標題（移除 ** 標記）
        title_match = re.search(r'\*\*(.*?)\*\*', line)
        if title_match:
            line_title = title_match.group(1).strip()
            return line_title == task_title.strip()
        
        # 如果沒有 ** 標記，直接檢查是否包含標題
        return task_title.strip() in line
    
    def _is_target_task_by_id(self, line: str, task_id: str) -> bool:
        """根據任務 ID 檢查是否為目標任務行"""
        # 這裡可以實作更複雜的 ID 匹配邏輯
        # 暫時使用標題匹配
        return task_id in line
    
    def _update_task_line(self, 
                         line: str, 
                         new_status: TaskStatus,
                         progress_percentage: Optional[int] = None,
                         completion_notes: Optional[str] = None,
                         github_link: Optional[str] = None) -> str:
        """更新任務行內容"""
        
        # 更新狀態標記
        status_marker = self.status_markers[new_status]
        line = re.sub(r'^(-\s*)\[[x~!\s]\]', rf'\1{status_marker}', line.strip(), flags=re.IGNORECASE)
        
        # 添加進度資訊（如果提供）
        if progress_percentage is not None and new_status == TaskStatus.IN_PROGRESS:
            if '進度:' not in line:
                line = line.rstrip() + f" | 進度: {progress_percentage}%"
            else:
                line = re.sub(r'進度:\s*\d+%', f'進度: {progress_percentage}%', line)
        
        # 添加完成時間（如果是已完成狀態）
        if new_status == TaskStatus.COMPLETED:
            completion_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            if '完成時間:' not in line:
                line = line.rstrip() + f" | 完成時間: {completion_time}"
        
        # 添加 GitHub 連結
        if github_link:
            if 'GitHub:' not in line:
                line = line.rstrip() + f" | GitHub: {github_link}"
        
        # 添加備註
        if completion_notes:
            if '備註:' not in line:
                line = line.rstrip() + f" | 備註: {completion_notes}"
        
        return line + '\n'
    
    def _update_statistics(self):
        """更新文件底部的統計資訊"""
        try:
            # 解析當前任務
            tasks = self.parser.parse_file()
            
            # 統計各狀態任務數量
            stats = {
                'urgent': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'failed': 0
            }
            
            for task in tasks:
                # 優先級統計
                if task.priority.value in stats:
                    stats[task.priority.value] += 1
                
                # 狀態統計
                if task.status.value in stats:
                    stats[task.status.value] += 1
            
            # 讀取文件內容
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新統計區域
            new_stats_section = self._generate_statistics_section(stats, len(tasks))
            
            # 替換統計區域
            stats_pattern = r'## 📊 任務狀態統計.*?(?=\n##|\n---|\Z)'
            if re.search(stats_pattern, content, re.DOTALL):
                content = re.sub(stats_pattern, new_stats_section, content, flags=re.DOTALL)
            else:
                # 如果沒有統計區域，在文件末尾添加
                content = content.rstrip() + '\n\n' + new_stats_section
            
            # 更新最後修改時間
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            content = re.sub(
                r'\*最後更新:.*?\*',
                f'*最後更新: {update_time}*',
                content
            )
            
            # 寫回文件
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
        except Exception as e:
            logger.error(f"更新統計資訊失敗: {str(e)}")
    
    def _generate_statistics_section(self, stats: Dict[str, int], total_tasks: int) -> str:
        """生成統計區域內容"""
        
        pending_count = total_tasks - stats['completed'] - stats['failed']
        completion_rate = (stats['completed'] / total_tasks * 100) if total_tasks > 0 else 0
        
        return f"""## 📊 任務狀態統計

### 優先級分布
- 🔥 緊急: {stats['urgent']} 個
- ⭐ 高優先級: {stats['high']} 個  
- 📅 一般: {stats['medium']} 個
- 🔖 低優先級: {stats['low']} 個

### 執行狀態
- ⏳ 待執行: {pending_count} 個
- 🔄 執行中: {stats['in_progress']} 個
- ✅ 已完成: {stats['completed']} 個
- ❌ 失敗: {stats['failed']} 個

**總計: {total_tasks} 個任務 | 完成率: {completion_rate:.1f}%**"""
    
    def _create_backup(self):
        """創建文件備份"""
        if not self.file_path.exists():
            return
        
        try:
            backup_dir = self.file_path.parent / '.task_backups'
            backup_dir.mkdir(exist_ok=True)
            
            # 生成備份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"TASKS_{timestamp}.md"
            
            # 複製文件
            import shutil
            shutil.copy2(self.file_path, backup_file)
            
            # 清理舊備份（保留最新的 N 個）
            self._cleanup_old_backups(backup_dir)
            
            logger.debug(f"已創建備份: {backup_file}")
            
        except Exception as e:
            logger.error(f"創建備份失敗: {str(e)}")
    
    def _cleanup_old_backups(self, backup_dir: Path):
        """清理舊備份文件"""
        try:
            backup_files = list(backup_dir.glob("TASKS_*.md"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 刪除超過限制的舊備份
            for old_backup in backup_files[self.max_backups:]:
                old_backup.unlink()
                logger.debug(f"已刪除舊備份: {old_backup}")
                
        except Exception as e:
            logger.error(f"清理舊備份失敗: {str(e)}")
    
    def get_task_progress_summary(self) -> Dict[str, Any]:
        """獲取任務進度摘要"""
        try:
            tasks = self.parser.parse_file()
            
            summary = {
                'total_tasks': len(tasks),
                'by_status': {
                    'pending': 0,
                    'in_progress': 0,
                    'completed': 0,
                    'failed': 0
                },
                'by_priority': {
                    'urgent': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                },
                'completion_rate': 0.0,
                'overdue_tasks': 0,
                'last_updated': datetime.now().isoformat()
            }
            
            now = datetime.now()
            
            for task in tasks:
                # 狀態統計
                status = task.status.value
                if status in summary['by_status']:
                    summary['by_status'][status] += 1
                
                # 優先級統計
                priority = task.priority.value
                if priority in summary['by_priority']:
                    summary['by_priority'][priority] += 1
                
                # 逾期任務統計
                if (task.deadline and task.deadline < now and 
                    task.status != TaskStatus.COMPLETED):
                    summary['overdue_tasks'] += 1
            
            # 計算完成率
            if summary['total_tasks'] > 0:
                summary['completion_rate'] = (
                    summary['by_status']['completed'] / summary['total_tasks'] * 100
                )
            
            return summary
            
        except Exception as e:
            logger.error(f"獲取進度摘要失敗: {str(e)}")
            return {}

# 使用範例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 創建進度更新器
    updater = ProgressUpdater()
    
    # 測試更新任務狀態
    success = updater.mark_task_in_progress("電商購物車優化", progress_percentage=30)
    print(f"任務狀態更新: {'成功' if success else '失敗'}")
    
    # 獲取進度摘要
    summary = updater.get_task_progress_summary()
    print(f"任務進度摘要: {summary}")
    
    # 標記任務完成
    success = updater.mark_task_completed(
        "電商購物車優化",
        github_link="https://github.com/austinchang/ecommerce-cart",
        completion_notes="已修復計算bug並新增優惠券功能"
    )
    print(f"任務完成標記: {'成功' if success else '失敗'}")