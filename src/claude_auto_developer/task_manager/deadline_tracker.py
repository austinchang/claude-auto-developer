#!/usr/bin/env python3
"""
Deadline Tracker - 期限追蹤器
監控任務期限，提供預警和自動調整建議
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DeadlineTracker:
    """期限追蹤器 - 智能期限管理和預警系統"""
    
    def __init__(self):
        self.warning_thresholds = {
            'critical': timedelta(hours=1),    # 1小時內
            'urgent': timedelta(hours=6),      # 6小時內
            'warning': timedelta(days=1),      # 1天內
            'notice': timedelta(days=3)        # 3天內
        }
        
        self.auto_adjust_rules = {
            'scope_reduction': {
                'time_ratio': 0.8,  # 剩餘時間不足80%時考慮縮減範圍
                'complexity_threshold': 'complex'
            },
            'priority_boost': {
                'time_ratio': 0.5,  # 剩餘時間不足50%時提升優先級
            },
            'resource_allocation': {
                'time_ratio': 0.3,  # 剩餘時間不足30%時分配更多資源
            }
        }
    
    def check_deadlines(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        檢查所有任務的期限狀態
        
        Args:
            tasks: 任務列表
            
        Returns:
            按警告級別分類的任務字典
        """
        now = datetime.now()
        deadline_status = {
            'overdue': [],
            'critical': [],
            'urgent': [],
            'warning': [],
            'notice': [],
            'normal': []
        }
        
        for task in tasks:
            deadline_str = task.get('deadline')
            if not deadline_str:
                deadline_status['normal'].append(task)
                continue
            
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                time_remaining = deadline - now
                
                # 分類任務
                if time_remaining.total_seconds() < 0:
                    deadline_status['overdue'].append(task)
                elif time_remaining <= self.warning_thresholds['critical']:
                    deadline_status['critical'].append(task)
                elif time_remaining <= self.warning_thresholds['urgent']:
                    deadline_status['urgent'].append(task)
                elif time_remaining <= self.warning_thresholds['warning']:
                    deadline_status['warning'].append(task)
                elif time_remaining <= self.warning_thresholds['notice']:
                    deadline_status['notice'].append(task)
                else:
                    deadline_status['normal'].append(task)
                
                # 添加時間資訊到任務中
                task['time_remaining'] = time_remaining
                task['deadline_status'] = self._get_deadline_status(time_remaining)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"無法解析任務 {task.get('id')} 的期限: {deadline_str}, 錯誤: {e}")
                deadline_status['normal'].append(task)
        
        logger.info(f"期限檢查完成: 逾期 {len(deadline_status['overdue'])}, "
                   f"緊急 {len(deadline_status['critical']) + len(deadline_status['urgent'])}")
        
        return deadline_status
    
    def get_deadline_warnings(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        獲取期限預警列表
        
        Args:
            tasks: 任務列表
            
        Returns:
            預警資訊列表
        """
        warnings = []
        deadline_status = self.check_deadlines(tasks)
        
        # 逾期任務
        for task in deadline_status['overdue']:
            warnings.append({
                'level': 'critical',
                'type': 'overdue',
                'task_id': task['id'],
                'message': f"任務已逾期: {task['description'][:50]}...",
                'recommendation': '立即處理或重新規劃期限'
            })
        
        # 緊急任務
        for task in deadline_status['critical']:
            time_remaining = task.get('time_remaining', timedelta(0))
            warnings.append({
                'level': 'critical',
                'type': 'critical_deadline',
                'task_id': task['id'],
                'message': f"任務將在 {self._format_time_remaining(time_remaining)} 內到期",
                'recommendation': '需要立即關注和資源分配'
            })
        
        # 緊急預警
        for task in deadline_status['urgent']:
            time_remaining = task.get('time_remaining', timedelta(0))
            warnings.append({
                'level': 'warning',
                'type': 'urgent_deadline',
                'task_id': task['id'],
                'message': f"任務將在 {self._format_time_remaining(time_remaining)} 內到期",
                'recommendation': '考慮提升優先級或分配更多資源'
            })
        
        return warnings
    
    def suggest_deadline_adjustments(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        建議期限調整
        
        Args:
            tasks: 任務列表
            
        Returns:
            調整建議列表
        """
        adjustments = []
        
        for task in tasks:
            if task.get('status') not in ['pending', 'in_progress']:
                continue
            
            deadline_str = task.get('deadline')
            if not deadline_str:
                continue
            
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                now = datetime.now()
                time_remaining = deadline - now
                
                # 估算完成時間
                estimated_time = self._estimate_completion_time(task)
                
                if estimated_time and time_remaining.total_seconds() > 0:
                    time_ratio = time_remaining.total_seconds() / estimated_time.total_seconds()
                    
                    # 根據時間比例提出建議
                    if time_ratio < 0.5:  # 時間嚴重不足
                        adjustments.append({
                            'task_id': task['id'],
                            'type': 'scope_reduction',
                            'urgency': 'high',
                            'message': '建議縮減任務範圍或延長期限',
                            'details': {
                                'current_deadline': deadline_str,
                                'estimated_completion': (now + estimated_time).isoformat(),
                                'suggested_deadline': (now + estimated_time * 1.2).isoformat()
                            }
                        })
                    elif time_ratio < 0.8:  # 時間緊張
                        adjustments.append({
                            'task_id': task['id'],
                            'type': 'priority_boost',
                            'urgency': 'medium',
                            'message': '建議提升任務優先級',
                            'details': {
                                'current_priority': task.get('priority'),
                                'suggested_priority': self._suggest_priority_boost(task.get('priority'))
                            }
                        })
                    elif time_ratio > 2.0:  # 時間充裕
                        adjustments.append({
                            'task_id': task['id'],
                            'type': 'scope_expansion',
                            'urgency': 'low',
                            'message': '可考慮擴展任務範圍或降低優先級',
                            'details': {
                                'available_time': self._format_time_remaining(time_remaining - estimated_time)
                            }
                        })
                
            except (ValueError, TypeError) as e:
                logger.warning(f"處理任務 {task.get('id')} 期限調整時出錯: {e}")
                continue
        
        return adjustments
    
    def calculate_completion_probability(self, task: Dict[str, Any]) -> float:
        """
        計算任務按時完成的機率
        
        Args:
            task: 任務資訊
            
        Returns:
            完成機率 (0.0 - 1.0)
        """
        deadline_str = task.get('deadline')
        if not deadline_str:
            return 0.8  # 無期限任務默認80%機率
        
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            now = datetime.now()
            time_remaining = deadline - now
            
            if time_remaining.total_seconds() < 0:
                return 0.0  # 已逾期
            
            estimated_time = self._estimate_completion_time(task)
            if not estimated_time:
                return 0.5  # 無法估算時間
            
            time_ratio = time_remaining.total_seconds() / estimated_time.total_seconds()
            
            # 基於時間比例計算機率
            if time_ratio >= 2.0:
                probability = 0.95
            elif time_ratio >= 1.5:
                probability = 0.85
            elif time_ratio >= 1.0:
                probability = 0.7
            elif time_ratio >= 0.8:
                probability = 0.5
            elif time_ratio >= 0.5:
                probability = 0.3
            else:
                probability = 0.1
            
            # 根據複雜度調整
            complexity = task.get('complexity', 'medium')
            complexity_adjustment = {
                'simple': 0.1,
                'medium': 0.0,
                'complex': -0.1,
                'very_complex': -0.2
            }.get(complexity, 0.0)
            
            probability += complexity_adjustment
            
            # 根據風險調整
            risks = task.get('risks', [])
            high_risk_count = sum(1 for risk in risks if risk.get('level') == 'high')
            probability -= high_risk_count * 0.1
            
            return max(0.0, min(1.0, probability))
            
        except (ValueError, TypeError):
            return 0.5
    
    def _get_deadline_status(self, time_remaining: timedelta) -> str:
        """獲取期限狀態"""
        if time_remaining.total_seconds() < 0:
            return 'overdue'
        elif time_remaining <= self.warning_thresholds['critical']:
            return 'critical'
        elif time_remaining <= self.warning_thresholds['urgent']:
            return 'urgent'
        elif time_remaining <= self.warning_thresholds['warning']:
            return 'warning'
        elif time_remaining <= self.warning_thresholds['notice']:
            return 'notice'
        else:
            return 'normal'
    
    def _format_time_remaining(self, time_remaining: timedelta) -> str:
        """格式化剩餘時間"""
        total_seconds = int(time_remaining.total_seconds())
        
        if total_seconds < 0:
            return "已逾期"
        elif total_seconds < 3600:  # 小於1小時
            minutes = total_seconds // 60
            return f"{minutes} 分鐘"
        elif total_seconds < 86400:  # 小於1天
            hours = total_seconds // 3600
            return f"{hours} 小時"
        else:  # 大於1天
            days = total_seconds // 86400
            return f"{days} 天"
    
    def _estimate_completion_time(self, task: Dict[str, Any]) -> Optional[timedelta]:
        """估算任務完成時間"""
        estimated_time_info = task.get('estimated_time', {})
        
        if not estimated_time_info:
            # 根據複雜度提供默認估算
            complexity = task.get('complexity', 'medium')
            default_hours = {
                'simple': 4,
                'medium': 16,
                'complex': 40,
                'very_complex': 80
            }.get(complexity, 16)
            
            return timedelta(hours=default_hours)
        
        try:
            max_time = estimated_time_info.get('max_time', 0)
            unit = estimated_time_info.get('unit', 'hours')
            
            if unit == 'hours':
                return timedelta(hours=max_time)
            elif unit == 'days':
                return timedelta(days=max_time)
            elif unit == 'minutes':
                return timedelta(minutes=max_time)
            else:
                return timedelta(hours=max_time)  # 默認小時
                
        except (ValueError, TypeError):
            return None
    
    def _suggest_priority_boost(self, current_priority: str) -> str:
        """建議提升優先級"""
        priority_order = ['low', 'medium', 'high', 'urgent']
        
        try:
            current_index = priority_order.index(current_priority)
            if current_index < len(priority_order) - 1:
                return priority_order[current_index + 1]
        except (ValueError, IndexError):
            pass
        
        return current_priority
    
    def get_deadline_statistics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """獲取期限統計資訊"""
        deadline_status = self.check_deadlines(tasks)
        
        total_tasks = len(tasks)
        tasks_with_deadlines = sum(len(deadline_status[status]) 
                                 for status in deadline_status if status != 'normal')
        
        # 計算平均完成機率
        probabilities = [self.calculate_completion_probability(task) for task in tasks]
        avg_probability = sum(probabilities) / len(probabilities) if probabilities else 0
        
        return {
            'total_tasks': total_tasks,
            'tasks_with_deadlines': tasks_with_deadlines,
            'overdue_count': len(deadline_status['overdue']),
            'critical_count': len(deadline_status['critical']),
            'urgent_count': len(deadline_status['urgent']),
            'warning_count': len(deadline_status['warning']),
            'notice_count': len(deadline_status['notice']),
            'average_completion_probability': round(avg_probability, 2),
            'deadline_compliance_rate': round(
                (total_tasks - len(deadline_status['overdue'])) / total_tasks if total_tasks > 0 else 1.0, 2
            )
        }