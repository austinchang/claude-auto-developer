#!/usr/bin/env python3
"""
Task File Parser - 任務文件解析器
解析 Markdown 格式的任務列表，提取項目資訊和優先級
"""

import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """任務優先級枚舉"""
    URGENT = "urgent"       # 🔥 緊急
    HIGH = "high"          # ⭐ 高優先級  
    MEDIUM = "medium"      # 📅 一般
    LOW = "low"           # 🔖 低優先級

class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"     # - [ ] 待執行
    IN_PROGRESS = "in_progress"  # - [~] 執行中
    COMPLETED = "completed" # - [x] 已完成
    FAILED = "failed"      # - [!] 失敗

@dataclass
class ParsedTask:
    """解析後的任務資料結構"""
    raw_text: str                    # 原始文本
    title: str                       # 任務標題
    description: str                 # 詳細描述
    priority: TaskPriority          # 優先級
    status: TaskStatus              # 狀態
    deadline: Optional[datetime]    # 截止日期
    tech_stack: List[str]           # 技術棧
    tags: List[str]                 # 標籤
    estimated_time: Optional[str]   # 預估時間
    line_number: int                # 在文件中的行號
    section: str                    # 所屬章節
    dependencies: List[str]         # 依賴項目
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        data = asdict(self)
        # 處理特殊字段
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['deadline'] = self.deadline.isoformat() if self.deadline else None
        return data

class TaskFileParser:
    """任務文件解析器"""
    
    def __init__(self, default_file_path: Optional[str] = None):
        """
        初始化解析器
        
        Args:
            default_file_path: 預設的任務文件路徑
        """
        self.default_file_path = default_file_path or "/home/tengjung_chang/TASKS.md"
        
        # 優先級標識映射
        self.priority_markers = {
            '🔥': TaskPriority.URGENT,
            '⭐': TaskPriority.HIGH,
            '📅': TaskPriority.MEDIUM,
            '🔖': TaskPriority.LOW,
            'urgent': TaskPriority.URGENT,
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW
        }
        
        # 狀態標識映射
        self.status_markers = {
            '[ ]': TaskStatus.PENDING,
            '[~]': TaskStatus.IN_PROGRESS,
            '[x]': TaskStatus.COMPLETED,
            '[X]': TaskStatus.COMPLETED,
            '[!]': TaskStatus.FAILED
        }
        
        # 日期解析模式
        self.date_patterns = [
            (r'明天', lambda: datetime.now() + timedelta(days=1)),
            (r'後天', lambda: datetime.now() + timedelta(days=2)),
            (r'今天', lambda: datetime.now()),
            (r'週([一二三四五六日])', self._parse_weekday),
            (r'下週([一二三四五六日])', self._parse_next_weekday),
            (r'(\d+)天後', lambda m: datetime.now() + timedelta(days=int(m.group(1)))),
            (r'(\d+)小時後', lambda m: datetime.now() + timedelta(hours=int(m.group(1)))),
            (r'(\d+)月(\d+)日', self._parse_date),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', self._parse_iso_date)
        ]
        
        # 技術棧關鍵字識別
        self.tech_keywords = {
            'frontend': ['React', 'Vue', 'Angular', 'HTML', 'CSS', 'JavaScript', 'TypeScript', 'Next.js', 'Nuxt'],
            'backend': ['FastAPI', 'Django', 'Flask', 'Express', 'Node.js', 'Python', 'Java', 'Go', 'Rust'],
            'database': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite', 'DynamoDB'],
            'ai_ml': ['OpenAI', 'GPT', 'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'NumPy'],
            'cloud': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform'],
            'mobile': ['React Native', 'Flutter', 'iOS', 'Android', 'Swift', 'Kotlin']
        }
    
    def parse_file(self, file_path: Optional[str] = None) -> List[ParsedTask]:
        """
        解析任務文件
        
        Args:
            file_path: 文件路徑，如果不提供則使用預設路徑
            
        Returns:
            解析後的任務列表
        """
        file_path = file_path or self.default_file_path
        logger.info(f"開始解析任務文件: {file_path}")
        
        try:
            # 檢查文件是否存在
            if not Path(file_path).exists():
                logger.warning(f"任務文件不存在: {file_path}")
                return []
            
            # 讀取文件內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析任務
            tasks = self._parse_content(content)
            
            logger.info(f"成功解析 {len(tasks)} 個任務")
            return tasks
            
        except Exception as e:
            logger.error(f"解析任務文件失敗: {str(e)}")
            return []
    
    def _parse_content(self, content: str) -> List[ParsedTask]:
        """解析文件內容"""
        tasks = []
        lines = content.split('\n')
        current_section = "未分類"
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 跳過空行和註釋
            if not line or line.startswith('<!--'):
                continue
            
            # 檢查是否為章節標題
            if line.startswith('#'):
                current_section = self._extract_section_title(line)
                continue
            
            # 檢查是否為任務行
            task = self._parse_task_line(line, line_num, current_section)
            if task:
                tasks.append(task)
        
        return tasks
    
    def _extract_section_title(self, line: str) -> str:
        """提取章節標題"""
        # 移除 # 符號和 emoji
        title = re.sub(r'^#+\s*', '', line)
        title = re.sub(r'[🔥⭐📅🔖]', '', title).strip()
        return title
    
    def _parse_task_line(self, line: str, line_num: int, section: str) -> Optional[ParsedTask]:
        """解析任務行"""
        # 檢查是否為任務行（以 - [ ], - [x] 等開始）
        task_pattern = r'^-\s*\[([x~!\s])\]\s*(.+)'
        match = re.match(task_pattern, line, re.IGNORECASE)
        
        if not match:
            return None
        
        status_char = match.group(1).strip()
        task_content = match.group(2).strip()
        
        # 解析狀態
        status_key = f'[{status_char.lower()}]'
        status = self.status_markers.get(status_key, TaskStatus.PENDING)
        
        # 解析任務內容（格式：**標題** | 截止日期: XXX | 技術: XXX | 描述: XXX）
        parts = [part.strip() for part in task_content.split('|')]
        
        # 提取標題（移除 ** 標記）
        title = re.sub(r'\*\*(.*?)\*\*', r'\1', parts[0]) if parts else "未命名任務"
        
        # 初始化任務資料
        task_data = {
            'raw_text': line,
            'title': title,
            'description': '',
            'priority': self._detect_priority(line, section),
            'status': status,
            'deadline': None,
            'tech_stack': [],
            'tags': [],
            'estimated_time': None,
            'line_number': line_num,
            'section': section,
            'dependencies': []
        }
        
        # 解析其他部分
        for part in parts[1:]:
            self._parse_task_attribute(part, task_data)
        
        return ParsedTask(**task_data)
    
    def _detect_priority(self, line: str, section: str) -> TaskPriority:
        """檢測任務優先級"""
        # 先檢查行中的 emoji 標記
        for marker, priority in self.priority_markers.items():
            if marker in line:
                return priority
        
        # 根據章節名稱推斷優先級
        section_lower = section.lower()
        if any(keyword in section_lower for keyword in ['緊急', 'urgent', '🔥']):
            return TaskPriority.URGENT
        elif any(keyword in section_lower for keyword in ['高優先', 'high', '重要', '⭐']):
            return TaskPriority.HIGH
        elif any(keyword in section_lower for keyword in ['低優先', 'low', '🔖']):
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM
    
    def _parse_task_attribute(self, part: str, task_data: Dict[str, Any]):
        """解析任務屬性"""
        part = part.strip()
        
        # 截止日期
        if '截止日期:' in part or 'deadline:' in part.lower():
            date_str = re.sub(r'(截止日期|deadline):\s*', '', part, flags=re.IGNORECASE)
            task_data['deadline'] = self._parse_deadline(date_str)
        
        # 技術棧
        elif '技術:' in part or 'tech:' in part.lower():
            tech_str = re.sub(r'(技術|tech):\s*', '', part, flags=re.IGNORECASE)
            task_data['tech_stack'] = self._parse_tech_stack(tech_str)
        
        # 描述
        elif '描述:' in part or 'description:' in part.lower():
            desc = re.sub(r'(描述|description):\s*', '', part, flags=re.IGNORECASE)
            task_data['description'] = desc
        
        # 預估時間
        elif '時間:' in part or 'time:' in part.lower():
            time_str = re.sub(r'(時間|time):\s*', '', part, flags=re.IGNORECASE)
            task_data['estimated_time'] = time_str
        
        # 標籤
        elif '標籤:' in part or 'tags:' in part.lower():
            tags_str = re.sub(r'(標籤|tags):\s*', '', part, flags=re.IGNORECASE)
            task_data['tags'] = [tag.strip() for tag in tags_str.split(',')]
        
        # 依賴
        elif '依賴:' in part or 'depends:' in part.lower():
            deps_str = re.sub(r'(依賴|depends):\s*', '', part, flags=re.IGNORECASE)
            task_data['dependencies'] = [dep.strip() for dep in deps_str.split(',')]
    
    def _parse_deadline(self, date_str: str) -> Optional[datetime]:
        """解析截止日期"""
        date_str = date_str.strip()
        
        # 嘗試各種日期格式
        for pattern, parser in self.date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if callable(parser):
                        if parser.__code__.co_argcount > 0:
                            return parser(match)
                        else:
                            return parser()
                    else:
                        return parser
                except Exception as e:
                    logger.warning(f"解析日期失敗: {date_str}, 錯誤: {str(e)}")
                    continue
        
        logger.warning(f"無法解析日期: {date_str}")
        return None
    
    def _parse_weekday(self, match) -> datetime:
        """解析週幾"""
        weekday_map = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6}
        target_weekday = weekday_map.get(match.group(1))
        
        if target_weekday is not None:
            today = datetime.now()
            days_ahead = target_weekday - today.weekday()
            if days_ahead <= 0:  # 如果是今天之前的日子，指向下週
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        
        return datetime.now()
    
    def _parse_next_weekday(self, match) -> datetime:
        """解析下週幾"""
        weekday_map = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6}
        target_weekday = weekday_map.get(match.group(1))
        
        if target_weekday is not None:
            today = datetime.now()
            days_ahead = target_weekday - today.weekday() + 7
            return today + timedelta(days=days_ahead)
        
        return datetime.now()
    
    def _parse_date(self, match) -> datetime:
        """解析月日格式（假設為當前年份）"""
        month = int(match.group(1))
        day = int(match.group(2))
        year = datetime.now().year
        
        try:
            target_date = datetime(year, month, day)
            # 如果日期已過，則指向明年
            if target_date < datetime.now():
                target_date = datetime(year + 1, month, day)
            return target_date
        except ValueError:
            return datetime.now()
    
    def _parse_iso_date(self, match) -> datetime:
        """解析 ISO 日期格式"""
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        
        try:
            return datetime(year, month, day)
        except ValueError:
            return datetime.now()
    
    def _parse_tech_stack(self, tech_str: str) -> List[str]:
        """解析技術棧"""
        # 使用多種分隔符分割
        techs = re.split(r'[,+&\s]+', tech_str)
        
        # 清理和正規化技術名稱
        normalized_techs = []
        for tech in techs:
            tech = tech.strip()
            if tech:
                # 標準化技術名稱（例如：react -> React）
                normalized_tech = self._normalize_tech_name(tech)
                normalized_techs.append(normalized_tech)
        
        return normalized_techs
    
    def _normalize_tech_name(self, tech: str) -> str:
        """標準化技術名稱"""
        # 建立技術名稱映射
        tech_mapping = {
            'react': 'React',
            'vue': 'Vue.js',
            'angular': 'Angular',
            'nodejs': 'Node.js',
            'node': 'Node.js',
            'python': 'Python',
            'fastapi': 'FastAPI',
            'django': 'Django',
            'flask': 'Flask',
            'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL',
            'mysql': 'MySQL',
            'mongodb': 'MongoDB',
            'redis': 'Redis',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'aws': 'AWS',
            'gcp': 'GCP',
            'azure': 'Azure'
        }
        
        tech_lower = tech.lower()
        return tech_mapping.get(tech_lower, tech)
    
    def get_tasks_by_priority(self, tasks: List[ParsedTask], priority: TaskPriority) -> List[ParsedTask]:
        """根據優先級篩選任務"""
        return [task for task in tasks if task.priority == priority]
    
    def get_tasks_by_status(self, tasks: List[ParsedTask], status: TaskStatus) -> List[ParsedTask]:
        """根據狀態篩選任務"""
        return [task for task in tasks if task.status == status]
    
    def get_urgent_tasks(self, tasks: List[ParsedTask]) -> List[ParsedTask]:
        """獲取緊急任務（24小時內到期）"""
        now = datetime.now()
        urgent_tasks = []
        
        for task in tasks:
            if task.deadline and task.deadline <= now + timedelta(hours=24):
                if task.status != TaskStatus.COMPLETED:
                    urgent_tasks.append(task)
        
        # 按截止時間排序
        urgent_tasks.sort(key=lambda x: x.deadline or datetime.max)
        return urgent_tasks
    
    def validate_tasks(self, tasks: List[ParsedTask]) -> Dict[str, Any]:
        """驗證任務列表"""
        validation_report = {
            'total_tasks': len(tasks),
            'valid_tasks': 0,
            'warnings': [],
            'errors': [],
            'statistics': {
                'by_priority': {},
                'by_status': {},
                'with_deadlines': 0,
                'with_tech_stack': 0
            }
        }
        
        # 統計各種任務
        for priority in TaskPriority:
            validation_report['statistics']['by_priority'][priority.value] = len(
                self.get_tasks_by_priority(tasks, priority)
            )
        
        for status in TaskStatus:
            validation_report['statistics']['by_status'][status.value] = len(
                self.get_tasks_by_status(tasks, status)
            )
        
        # 驗證每個任務
        for task in tasks:
            task_valid = True
            
            # 檢查標題
            if not task.title or task.title == "未命名任務":
                validation_report['warnings'].append(f"行 {task.line_number}: 任務缺少明確標題")
                task_valid = False
            
            # 檢查描述
            if not task.description:
                validation_report['warnings'].append(f"行 {task.line_number}: 任務 '{task.title}' 缺少描述")
            
            # 檢查截止日期
            if task.deadline:
                validation_report['statistics']['with_deadlines'] += 1
                if task.deadline < datetime.now() and task.status != TaskStatus.COMPLETED:
                    validation_report['warnings'].append(f"行 {task.line_number}: 任務 '{task.title}' 已逾期")
            
            # 檢查技術棧
            if task.tech_stack:
                validation_report['statistics']['with_tech_stack'] += 1
            else:
                validation_report['warnings'].append(f"行 {task.line_number}: 任務 '{task.title}' 未指定技術棧")
            
            if task_valid:
                validation_report['valid_tasks'] += 1
        
        return validation_report
    
    def export_tasks_to_json(self, tasks: List[ParsedTask], output_file: str):
        """匯出任務到 JSON 文件"""
        import json
        
        tasks_data = [task.to_dict() for task in tasks]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已匯出 {len(tasks)} 個任務到: {output_file}")

# 使用範例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 創建解析器
    parser = TaskFileParser()
    
    # 解析任務文件
    tasks = parser.parse_file()
    
    if tasks:
        print(f"解析到 {len(tasks)} 個任務：")
        
        for task in tasks:
            print(f"- {task.title} ({task.priority.value}) - {task.status.value}")
            if task.deadline:
                print(f"  截止日期: {task.deadline.strftime('%Y-%m-%d %H:%M')}")
            if task.tech_stack:
                print(f"  技術棧: {', '.join(task.tech_stack)}")
            print()
        
        # 驗證任務
        validation = parser.validate_tasks(tasks)
        print(f"驗證結果: {validation['valid_tasks']}/{validation['total_tasks']} 個有效任務")
        
        if validation['warnings']:
            print("警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
    else:
        print("沒有找到任務或解析失敗")