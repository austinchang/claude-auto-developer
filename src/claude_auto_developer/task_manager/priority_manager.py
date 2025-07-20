#!/usr/bin/env python3
"""
Priority Manager - 優先級管理器
智能管理任務優先級，動態調整執行順序
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PriorityManager:
    """優先級管理器 - 智能任務排程和優先級管理"""
    
    def __init__(self):
        self.priority_weights = {
            'urgent': 1000,
            'high': 100,
            'medium': 10,
            'low': 1
        }
        
        self.complexity_weights = {
            'simple': 1,
            'medium': 2,
            'complex': 4,
            'very_complex': 8
        }
        
        self.type_weights = {
            'bugfix': 50,      # Bug 修復優先級較高
            'feature': 10,     # 新功能
            'enhancement': 5,  # 改善
            'project': 1       # 專案（通常較大，優先級較低）
        }
    
    def calculate_priority_score(self, task: Dict[str, Any]) -> float:
        """
        計算任務的優先級分數
        
        Args:
            task: 任務資訊
            
        Returns:
            優先級分數（越高越優先）
        """
        score = 0
        
        # 基礎優先級分數
        priority = task.get('priority', 'medium')
        score += self.priority_weights.get(priority, 10)
        
        # 任務類型加成
        task_type = task.get('type', 'feature')
        score += self.type_weights.get(task_type, 1)
        
        # 期限緊迫性加成
        deadline_score = self._calculate_deadline_urgency(task.get('deadline'))
        score += deadline_score
        
        # 複雜度影響（複雜度越低，優先級可以稍微提高）
        complexity = task.get('complexity', 'medium')
        complexity_weight = self.complexity_weights.get(complexity, 2)
        score += max(0, 10 - complexity_weight)  # 簡單任務獲得額外分數
        
        # 依賴關係影響
        dependencies = task.get('dependencies', [])
        if not dependencies:  # 無依賴的任務優先級更高
            score += 20
        
        # 風險影響
        risks = task.get('risks', [])
        high_risk_count = sum(1 for risk in risks if risk.get('level') == 'high')
        score -= high_risk_count * 10  # 高風險任務優先級降低
        
        logger.debug(f"任務 {task.get('id')} 優先級分數: {score}")
        return score
    
    def sort_tasks_by_priority(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根據優先級排序任務
        
        Args:
            tasks: 任務列表
            
        Returns:
            排序後的任務列表
        """
        # 計算每個任務的優先級分數
        task_scores = []
        for task in tasks:
            score = self.calculate_priority_score(task)
            task_scores.append((task, score))
        
        # 按分數降序排序
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        sorted_tasks = [task for task, score in task_scores]
        
        logger.info(f"已排序 {len(sorted_tasks)} 個任務")
        return sorted_tasks
    
    def get_next_executable_tasks(self, tasks: List[Dict[str, Any]], 
                                 max_concurrent: int = 4) -> List[Dict[str, Any]]:
        """
        獲取下一批可執行的任務
        
        Args:
            tasks: 待執行任務列表
            max_concurrent: 最大併發數
            
        Returns:
            可同時執行的任務列表
        """
        # 先按優先級排序
        sorted_tasks = self.sort_tasks_by_priority(tasks)
        
        executable_tasks = []
        used_resources = set()
        
        for task in sorted_tasks:
            if len(executable_tasks) >= max_concurrent:
                break
            
            # 檢查資源衝突
            if self._check_resource_conflict(task, used_resources):
                continue
            
            # 檢查依賴關係
            if not self._check_dependencies_satisfied(task, executable_tasks):
                continue
            
            executable_tasks.append(task)
            used_resources.update(self._get_task_resources(task))
        
        logger.info(f"選出 {len(executable_tasks)} 個可執行任務")
        return executable_tasks
    
    def adjust_priority_by_deadline(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根據期限動態調整優先級
        
        Args:
            tasks: 任務列表
            
        Returns:
            調整後的任務列表
        """
        now = datetime.now()
        
        for task in tasks:
            deadline_str = task.get('deadline')
            if not deadline_str:
                continue
            
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                time_remaining = deadline - now
                
                # 根據剩餘時間調整優先級
                if time_remaining.total_seconds() < 3600:  # 1小時內
                    task['priority'] = 'urgent'
                elif time_remaining.total_seconds() < 86400:  # 1天內
                    if task['priority'] in ['low', 'medium']:
                        task['priority'] = 'high'
                elif time_remaining.total_seconds() < 259200:  # 3天內
                    if task['priority'] == 'low':
                        task['priority'] = 'medium'
                
                logger.debug(f"任務 {task.get('id')} 優先級已根據期限調整為: {task['priority']}")
                
            except (ValueError, TypeError) as e:
                logger.warning(f"無法解析任務期限: {deadline_str}, 錯誤: {e}")
                continue
        
        return tasks
    
    def _calculate_deadline_urgency(self, deadline_str: str) -> float:
        """計算期限緊迫性分數"""
        if not deadline_str:
            return 0
        
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            now = datetime.now()
            time_remaining = deadline - now
            
            total_seconds = time_remaining.total_seconds()
            
            if total_seconds < 0:  # 已過期
                return 500
            elif total_seconds < 3600:  # 1小時內
                return 200
            elif total_seconds < 86400:  # 1天內
                return 100
            elif total_seconds < 259200:  # 3天內
                return 50
            elif total_seconds < 604800:  # 1週內
                return 20
            else:
                return 0
                
        except (ValueError, TypeError):
            return 0
    
    def _check_resource_conflict(self, task: Dict[str, Any], used_resources: set) -> bool:
        """檢查資源衝突"""
        task_resources = self._get_task_resources(task)
        return bool(task_resources & used_resources)
    
    def _get_task_resources(self, task: Dict[str, Any]) -> set:
        """獲取任務所需資源"""
        resources = set()
        
        # 根據技術棧確定資源需求
        tech_stack = task.get('tech_stack', [])
        
        if 'frontend' in tech_stack:
            resources.add('frontend_dev')
        if 'backend' in tech_stack:
            resources.add('backend_dev')
        if 'database' in tech_stack:
            resources.add('database_access')
        if 'ai_ml' in tech_stack:
            resources.add('gpu_compute')
        
        # 檢查是否需要特定專案資源
        dependencies = task.get('dependencies', [])
        for dep in dependencies:
            if dep.startswith('existing_project:'):
                project_name = dep.split(':', 1)[1]
                resources.add(f'project_lock:{project_name}')
        
        return resources
    
    def _check_dependencies_satisfied(self, task: Dict[str, Any], 
                                    selected_tasks: List[Dict[str, Any]]) -> bool:
        """檢查依賴關係是否滿足"""
        dependencies = task.get('dependencies', [])
        
        # 簡化版依賴檢查：如果有專案依賴，確保沒有其他任務在使用相同專案
        for dep in dependencies:
            if dep.startswith('existing_project:'):
                project_name = dep.split(':', 1)[1]
                
                # 檢查已選中的任務是否使用相同專案
                for selected_task in selected_tasks:
                    selected_deps = selected_task.get('dependencies', [])
                    for selected_dep in selected_deps:
                        if (selected_dep.startswith('existing_project:') and 
                            selected_dep.split(':', 1)[1] == project_name):
                            return False
        
        return True
    
    def get_priority_statistics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """獲取優先級統計資訊"""
        stats = {
            'total_tasks': len(tasks),
            'priority_distribution': {'urgent': 0, 'high': 0, 'medium': 0, 'low': 0},
            'type_distribution': {},
            'complexity_distribution': {},
            'overdue_tasks': 0,
            'urgent_deadline_tasks': 0
        }
        
        now = datetime.now()
        
        for task in tasks:
            # 優先級分布
            priority = task.get('priority', 'medium')
            stats['priority_distribution'][priority] += 1
            
            # 類型分布
            task_type = task.get('type', 'feature')
            stats['type_distribution'][task_type] = stats['type_distribution'].get(task_type, 0) + 1
            
            # 複雜度分布
            complexity = task.get('complexity', 'medium')
            stats['complexity_distribution'][complexity] = stats['complexity_distribution'].get(complexity, 0) + 1
            
            # 期限統計
            deadline_str = task.get('deadline')
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                    if deadline < now:
                        stats['overdue_tasks'] += 1
                    elif (deadline - now).total_seconds() < 86400:  # 24小時內
                        stats['urgent_deadline_tasks'] += 1
                except (ValueError, TypeError):
                    pass
        
        return stats