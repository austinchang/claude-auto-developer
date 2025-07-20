#!/usr/bin/env python3
"""
Task Analyzer - 任務分析器
智能分析開發需求，評估複雜度和技術需求
"""

import re
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TaskAnalyzer:
    """任務分析器 - 智能分析開發需求"""
    
    def __init__(self):
        self.complexity_keywords = {
            'simple': ['按鈕', '文字', '顏色', '樣式', '簡單', '修改', '調整'],
            'medium': ['功能', '頁面', '組件', '整合', '資料庫', 'API', '介面'],
            'complex': ['系統', '架構', '平台', '引擎', '演算法', '機器學習', 'AI', '自動化'],
            'very_complex': ['分散式', '微服務', '大數據', '即時', '高並發', '區塊鏈']
        }
        
        self.tech_stack_keywords = {
            'frontend': ['前端', '網頁', '界面', 'UI', 'UX', '響應式', '互動', '瀏覽器'],
            'backend': ['後端', '伺服器', 'API', '資料庫', '服務', '邏輯', '處理'],
            'database': ['資料庫', '數據', '儲存', 'SQL', 'MongoDB', 'Redis'],
            'ai_ml': ['AI', '人工智慧', '機器學習', '預測', '分析', '智能', '神經網路'],
            'automation': ['自動化', '腳本', '排程', '監控', '部署', '測試'],
            'mobile': ['手機', '移動', 'App', 'iOS', 'Android', '響應式'],
            'desktop': ['桌面', '桌面應用', 'GUI', 'Tkinter', 'PyQt', 'Electron']
        }
        
        self.time_estimation_rules = {
            'simple': {'min': 1, 'max': 4, 'unit': 'hours'},
            'medium': {'min': 4, 'max': 16, 'unit': 'hours'},
            'complex': {'min': 1, 'max': 5, 'unit': 'days'},
            'very_complex': {'min': 5, 'max': 15, 'unit': 'days'}
        }
    
    def analyze_requirement(self, description: str) -> Dict[str, Any]:
        """
        分析需求描述，返回詳細的分析結果
        
        Args:
            description: 需求描述文字
            
        Returns:
            包含複雜度、技術棧、時間估算等的分析結果
        """
        logger.info(f"開始分析需求: {description}")
        
        analysis = {
            'description': description,
            'complexity': self._analyze_complexity(description),
            'tech_stack': self._identify_tech_stack(description),
            'estimated_time': None,
            'dependencies': self._identify_dependencies(description),
            'risks': self._identify_risks(description),
            'subtasks': self._generate_subtasks(description),
            'timestamp': datetime.now().isoformat()
        }
        
        # 根據複雜度估算時間
        analysis['estimated_time'] = self._estimate_time(analysis['complexity'])
        
        logger.info(f"分析完成: 複雜度={analysis['complexity']}, 技術棧={analysis['tech_stack']}")
        
        return analysis
    
    def _analyze_complexity(self, description: str) -> str:
        """分析複雜度"""
        description_lower = description.lower()
        scores = {
            'simple': 0,
            'medium': 0,
            'complex': 0,
            'very_complex': 0
        }
        
        # 計算關鍵字匹配分數
        for complexity, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    scores[complexity] += 1
        
        # 根據描述長度調整
        if len(description) > 100:
            scores['complex'] += 1
        if len(description) > 200:
            scores['very_complex'] += 1
        
        # 根據特殊模式調整
        if re.search(r'整合|連接|同步', description_lower):
            scores['complex'] += 1
        
        if re.search(r'系統|平台|框架', description_lower):
            scores['very_complex'] += 1
        
        # 返回得分最高的複雜度
        max_complexity = max(scores, key=scores.get)
        return max_complexity if scores[max_complexity] > 0 else 'medium'
    
    def _identify_tech_stack(self, description: str) -> List[str]:
        """識別所需技術棧"""
        description_lower = description.lower()
        identified_stacks = []
        
        for stack_type, keywords in self.tech_stack_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    if stack_type not in identified_stacks:
                        identified_stacks.append(stack_type)
                    break
        
        # 如果沒有識別到任何技術棧，根據常見模式推斷
        if not identified_stacks:
            if re.search(r'網站|web|界面|頁面', description_lower):
                identified_stacks.extend(['frontend', 'backend'])
            elif re.search(r'工具|腳本|程式', description_lower):
                identified_stacks.append('automation')
            else:
                identified_stacks.append('backend')  # 默認後端
        
        return identified_stacks
    
    def _estimate_time(self, complexity: str) -> Dict[str, Any]:
        """根據複雜度估算開發時間"""
        rules = self.time_estimation_rules.get(complexity, self.time_estimation_rules['medium'])
        
        return {
            'min_time': rules['min'],
            'max_time': rules['max'],
            'unit': rules['unit'],
            'confidence': 0.7 if complexity in ['simple', 'medium'] else 0.5
        }
    
    def _identify_dependencies(self, description: str) -> List[str]:
        """識別可能的依賴關係"""
        dependencies = []
        description_lower = description.lower()
        
        # 檢查是否需要現有專案
        existing_projects = [
            'power_meter_gui', 'gomoku_game', 'multi_terminal_tester',
            'enterprise_web_crawler', 'modbus_meter_simulator'
        ]
        
        for project in existing_projects:
            if project.replace('_', ' ') in description_lower or project in description_lower:
                dependencies.append(f"existing_project:{project}")
        
        # 檢查技術依賴
        if '資料庫' in description_lower or 'database' in description_lower:
            dependencies.append("database_setup")
        
        if 'API' in description_lower or 'api' in description_lower:
            dependencies.append("api_design")
        
        if '前端' in description_lower or 'frontend' in description_lower:
            dependencies.append("frontend_framework")
        
        return dependencies
    
    def _identify_risks(self, description: str) -> List[Dict[str, str]]:
        """識別潛在風險"""
        risks = []
        description_lower = description.lower()
        
        # 技術風險
        if any(keyword in description_lower for keyword in ['新技術', '試驗', '實驗']):
            risks.append({
                'type': 'technical',
                'level': 'high',
                'description': '使用新技術或實驗性功能'
            })
        
        # 整合風險
        if any(keyword in description_lower for keyword in ['整合', '連接', '同步']):
            risks.append({
                'type': 'integration', 
                'level': 'medium',
                'description': '需要與現有系統整合'
            })
        
        # 時間風險
        if any(keyword in description_lower for keyword in ['緊急', '急', '立即']):
            risks.append({
                'type': 'timeline',
                'level': 'high', 
                'description': '時間壓力較大'
            })
        
        return risks
    
    def _generate_subtasks(self, description: str) -> List[Dict[str, str]]:
        """生成子任務列表"""
        subtasks = []
        description_lower = description.lower()
        
        # 基礎任務
        subtasks.append({
            'name': '需求分析和設計',
            'type': 'analysis',
            'estimated_time': '2小時'
        })
        
        # 根據技術棧生成對應任務
        if any(keyword in description_lower for keyword in ['前端', 'ui', '界面']):
            subtasks.extend([
                {'name': '前端界面設計', 'type': 'frontend', 'estimated_time': '4小時'},
                {'name': '前端功能實作', 'type': 'frontend', 'estimated_time': '6小時'}
            ])
        
        if any(keyword in description_lower for keyword in ['後端', 'api', '邏輯']):
            subtasks.extend([
                {'name': '後端API設計', 'type': 'backend', 'estimated_time': '3小時'},
                {'name': '後端邏輯實作', 'type': 'backend', 'estimated_time': '5小時'}
            ])
        
        if any(keyword in description_lower for keyword in ['資料庫', '數據', '儲存']):
            subtasks.append({
                'name': '資料庫設計和實作',
                'type': 'database',
                'estimated_time': '3小時'
            })
        
        # 結尾任務
        subtasks.extend([
            {'name': '測試和除錯', 'type': 'testing', 'estimated_time': '3小時'},
            {'name': '文檔撰寫', 'type': 'documentation', 'estimated_time': '2小時'},
            {'name': '部署和發布', 'type': 'deployment', 'estimated_time': '1小時'}
        ])
        
        return subtasks
    
    def validate_requirement(self, description: str) -> Dict[str, Any]:
        """驗證需求描述的完整性"""
        validation = {
            'is_valid': True,
            'score': 0,
            'suggestions': [],
            'missing_info': []
        }
        
        # 檢查描述長度
        if len(description) < 10:
            validation['is_valid'] = False
            validation['suggestions'].append('需求描述太短，請提供更詳細的說明')
        else:
            validation['score'] += 2
        
        # 檢查是否包含動作詞
        action_words = ['增加', '創建', '修改', '改善', '實作', '開發', '建立']
        if any(word in description for word in action_words):
            validation['score'] += 2
        else:
            validation['missing_info'].append('缺少明確的動作說明')
        
        # 檢查是否有具體目標
        if any(word in description for word in ['功能', '系統', '工具', '頁面', '組件']):
            validation['score'] += 2
        else:
            validation['missing_info'].append('缺少具體的開發目標')
        
        # 計算總分
        validation['score'] = min(validation['score'], 10)
        
        if validation['score'] < 4:
            validation['is_valid'] = False
            validation['suggestions'].append('請提供更詳細和明確的需求描述')
        
        return validation