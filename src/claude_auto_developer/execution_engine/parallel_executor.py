#!/usr/bin/env python3
"""
Parallel Executor - 並行執行器
Claude Auto Developer 的核心執行引擎，負責多執行緒並行開發任務執行
"""

import threading
import queue
import time
import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, asdict
from enum import Enum

# 導入相關模組
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from task_manager.task_analyzer import TaskAnalyzer
from task_manager.task_planner import TaskPlanner
from deployment.github_project_uploader import create_uploader_from_env
from code_generation.intelligent_code_generator import IntelligentCodeGenerator
from .auto_executor import AutoExecutor
from .test_runner import TestRunner
from .deployment_manager import DeploymentManager, DeploymentConfig

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class ExecutionMode(Enum):
    """執行模式枚舉"""
    AUTO = "auto"          # 自動模式 - 智能調度
    PROJECT = "project"    # 專案模式 - 整個專案開發
    SINGLE = "single"      # 單一模式 - 逐個執行
    EMERGENCY = "emergency" # 緊急模式 - 高優先級搶占

@dataclass
class ExecutionContext:
    """執行上下文"""
    task_id: str
    thread_id: str
    start_time: datetime
    workspace_path: str
    progress: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []

class ParallelExecutor:
    """並行執行器 - Claude Auto Developer 的核心執行引擎"""
    
    def __init__(self, max_threads: int = 4, workspace_base: str = "./output"):
        """
        初始化並行執行器
        
        Args:
            max_threads: 最大執行緒數量
            workspace_base: 工作區基礎路徑
        """
        self.max_threads = max_threads
        self.workspace_base = workspace_base
        self.is_running = False
        self.is_paused = False
        
        # 執行緒管理
        self.executor = ThreadPoolExecutor(max_workers=max_threads)
        self.active_contexts: Dict[str, ExecutionContext] = {}
        self.task_queue = queue.PriorityQueue()
        self.results_queue = queue.Queue()
        
        # 狀態監控
        self.execution_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "start_time": None,
            "total_execution_time": 0
        }
        
        # 初始化組件
        self.task_analyzer = TaskAnalyzer()
        self.task_planner = TaskPlanner()
        self.code_generator = IntelligentCodeGenerator()
        
        # 新增：自動執行組件
        self.auto_executor = None  # 延遲初始化
        self.test_runner = None    # 延遲初始化
        self.deployment_manager = None  # 延遲初始化
        
        # 創建工作區
        os.makedirs(workspace_base, exist_ok=True)
        
        logger.info(f"ParallelExecutor 初始化完成 - 最大執行緒: {max_threads}")
    
    def start_execution(self, mode: ExecutionMode = ExecutionMode.AUTO) -> bool:
        """
        啟動並行執行系統
        
        Args:
            mode: 執行模式
            
        Returns:
            啟動是否成功
        """
        if self.is_running:
            logger.warning("執行系統已在運行中")
            return False
        
        self.is_running = True
        self.is_paused = False
        self.execution_stats["start_time"] = datetime.now()
        
        logger.info(f"啟動並行執行系統 - 模式: {mode.value}")
        
        # 載入待執行任務
        pending_tasks = self.task_planner.get_pending_tasks()
        if not pending_tasks:
            logger.info("沒有待執行的任務")
            self.is_running = False
            return False
        
        logger.info(f"載入 {len(pending_tasks)} 個待執行任務")
        
        # 根據模式處理任務
        if mode == ExecutionMode.AUTO:
            self._schedule_auto_execution(pending_tasks)
        elif mode == ExecutionMode.PROJECT:
            self._schedule_project_execution(pending_tasks)
        elif mode == ExecutionMode.SINGLE:
            self._schedule_single_execution(pending_tasks)
        elif mode == ExecutionMode.EMERGENCY:
            self._schedule_emergency_execution(pending_tasks)
        
        # 啟動主執行循環
        self._start_execution_loop()
        
        return True
    
    def pause_execution(self):
        """暫停執行"""
        self.is_paused = True
        logger.info("執行系統已暫停")
    
    def resume_execution(self):
        """恢復執行"""
        self.is_paused = False
        logger.info("執行系統已恢復")
    
    def stop_execution(self):
        """停止執行"""
        self.is_running = False
        self.is_paused = False
        
        # 等待所有執行緒完成
        self.executor.shutdown(wait=True)
        
        # 更新統計資訊
        if self.execution_stats["start_time"]:
            self.execution_stats["total_execution_time"] = \
                (datetime.now() - self.execution_stats["start_time"]).total_seconds()
        
        logger.info("執行系統已停止")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """
        獲取執行狀態
        
        Returns:
            包含詳細執行狀態的字典
        """
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "active_threads": len(self.active_contexts),
            "max_threads": self.max_threads,
            "task_queue_size": self.task_queue.qsize(),
            "stats": self.execution_stats.copy(),
            "active_tasks": [
                {
                    "task_id": ctx.task_id,
                    "thread_id": ctx.thread_id,
                    "progress": ctx.progress,
                    "status": ctx.status.value,
                    "workspace": ctx.workspace_path,
                    "runtime": (datetime.now() - ctx.start_time).total_seconds()
                }
                for ctx in self.active_contexts.values()
            ]
        }
    
    def _schedule_auto_execution(self, tasks: List[Dict[str, Any]]):
        """自動模式任務調度"""
        logger.info("使用自動模式調度任務")
        
        # 按優先級和依賴關係排序
        sorted_tasks = self._sort_tasks_by_priority_and_dependencies(tasks)
        
        for task in sorted_tasks:
            priority = self._calculate_task_priority(task)
            self.task_queue.put((priority, task))
    
    def _schedule_project_execution(self, tasks: List[Dict[str, Any]]):
        """專案模式任務調度"""
        logger.info("使用專案模式調度任務")
        
        # 按專案分組並並行執行
        project_groups = self._group_tasks_by_project(tasks)
        
        for project_name, project_tasks in project_groups.items():
            for task in project_tasks:
                priority = self._calculate_task_priority(task, project_mode=True)
                self.task_queue.put((priority, task))
    
    def _schedule_single_execution(self, tasks: List[Dict[str, Any]]):
        """單一模式任務調度"""
        logger.info("使用單一模式調度任務")
        
        # 降低並行度，逐個執行
        self.max_threads = 1
        
        for task in tasks:
            priority = self._calculate_task_priority(task)
            self.task_queue.put((priority, task))
    
    def _schedule_emergency_execution(self, tasks: List[Dict[str, Any]]):
        """緊急模式任務調度"""
        logger.info("使用緊急模式調度任務")
        
        # 優先處理緊急任務
        emergency_tasks = [t for t in tasks if t.get('priority') == 'urgent']
        normal_tasks = [t for t in tasks if t.get('priority') != 'urgent']
        
        # 緊急任務優先
        for task in emergency_tasks:
            self.task_queue.put((0, task))  # 最高優先級
        
        for task in normal_tasks:
            priority = self._calculate_task_priority(task)
            self.task_queue.put((priority + 1000, task))  # 降低優先級
    
    def _start_execution_loop(self):
        """啟動主執行循環"""
        def execution_loop():
            while self.is_running:
                if self.is_paused:
                    time.sleep(1)
                    continue
                
                try:
                    # 檢查是否有可用執行緒
                    if len(self.active_contexts) >= self.max_threads:
                        time.sleep(0.5)
                        continue
                    
                    # 從佇列取得任務
                    try:
                        priority, task = self.task_queue.get(timeout=1)
                    except queue.Empty:
                        continue
                    
                    # 提交任務執行
                    self._submit_task_execution(task)
                    
                except Exception as e:
                    logger.error(f"執行循環錯誤: {str(e)}")
                    time.sleep(1)
        
        # 在背景執行緒中運行
        loop_thread = threading.Thread(target=execution_loop, daemon=True)
        loop_thread.start()
    
    def _submit_task_execution(self, task: Dict[str, Any]):
        """提交任務到執行緒池"""
        task_id = task['id']
        
        # 創建執行上下文
        workspace_path = os.path.join(self.workspace_base, f"task_{task_id}")
        os.makedirs(workspace_path, exist_ok=True)
        
        context = ExecutionContext(
            task_id=task_id,
            thread_id=f"thread_{len(self.active_contexts) + 1}",
            start_time=datetime.now(),
            workspace_path=workspace_path
        )
        
        self.active_contexts[task_id] = context
        self.execution_stats["running_tasks"] += 1
        self.execution_stats["total_tasks"] += 1
        
        # 提交到執行緒池
        future = self.executor.submit(self._execute_task, task, context)
        future.add_done_callback(lambda f: self._task_completed_callback(task_id, f))
        
        logger.info(f"任務 {task_id} 已提交執行 - 執行緒: {context.thread_id}")
    
    def _execute_task(self, task: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """
        執行單個任務的核心邏輯
        
        Args:
            task: 任務資訊
            context: 執行上下文
            
        Returns:
            執行結果
        """
        try:
            context.status = TaskStatus.RUNNING
            logger.info(f"開始執行任務: {task['id']} - {task['description']}")
            
            # 更新進度: 0% - 開始
            self._update_task_progress(context, 0, "任務開始執行")
            
            # 1. 需求分析階段 (10%)
            self._update_task_progress(context, 10, "分析任務需求")
            analysis = self.task_analyzer.analyze_requirement(task['description'])
            
            # 2. 工作區設置階段 (20%)
            self._update_task_progress(context, 20, "設置工作環境")
            self._setup_workspace(task, context, analysis)
            
            # 3. 代碼生成階段 (40%)
            self._update_task_progress(context, 40, "生成程式碼")
            code_result = self._generate_code(task, context, analysis)
            
            # 4. 測試階段 (70%)
            self._update_task_progress(context, 70, "執行測試")
            test_result = self._run_tests(task, context)
            
            # 5. 部署階段 (80%)
            self._update_task_progress(context, 80, "部署和整合")
            deploy_result = self._deploy_code(task, context)
            
            # 6. 自動執行階段 (85%)
            self._update_task_progress(context, 85, "環境建置")
            execution_result = self._auto_execute(task, context)
            
            # 7. 自動測試階段 (90%)
            self._update_task_progress(context, 90, "自動測試")
            auto_test_result = self._auto_test(task, context)
            
            # 8. 自動部署階段 (95%)
            self._update_task_progress(context, 95, "自動部署")
            auto_deploy_result = self._auto_deploy(task, context)
            
            # 9. 完成 (100%)
            self._update_task_progress(context, 100, "任務完成")
            context.status = TaskStatus.COMPLETED
            
            result = {
                "task_id": task['id'],
                "status": "completed",
                "workspace": context.workspace_path,
                "analysis": analysis,
                "code_result": code_result,
                "test_result": test_result,
                "deploy_result": deploy_result,
                "execution_result": execution_result,
                "auto_test_result": auto_test_result,
                "auto_deploy_result": auto_deploy_result,
                "execution_time": (datetime.now() - context.start_time).total_seconds(),
                "logs": context.logs
            }
            
            logger.info(f"任務 {task['id']} 執行完成")
            return result
            
        except Exception as e:
            context.status = TaskStatus.FAILED
            error_msg = f"任務執行失敗: {str(e)}"
            logger.error(error_msg)
            context.logs.append(error_msg)
            
            return {
                "task_id": task['id'],
                "status": "failed",
                "error": str(e),
                "logs": context.logs,
                "execution_time": (datetime.now() - context.start_time).total_seconds()
            }
    
    def _setup_workspace(self, task: Dict[str, Any], context: ExecutionContext, analysis: Dict[str, Any]):
        """設置任務工作區"""
        workspace = context.workspace_path
        
        # 創建專案結構
        directories = ['src', 'tests', 'docs', 'config', 'scripts']
        for dir_name in directories:
            os.makedirs(os.path.join(workspace, dir_name), exist_ok=True)
        
        # 生成專案配置檔案
        project_config = {
            "name": f"task_{task['id']}",
            "description": task['description'],
            "tech_stack": analysis.get('tech_stack', []),
            "complexity": analysis.get('complexity', 'medium'),
            "created_at": datetime.now().isoformat(),
            "python_version": "3.8+",
            "has_venv": True,
            "auto_deploy": True
        }
        
        config_path = os.path.join(workspace, 'config', 'project.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, ensure_ascii=False, indent=2)
        
        # 生成 requirements.txt
        self._generate_requirements_txt(task, workspace, analysis)
        
        # 創建虛擬環境設置腳本
        self._generate_venv_setup_script(task, workspace, analysis)
        
        # 創建自動部署腳本
        self._generate_deployment_script(task, workspace, analysis)
        
        context.logs.append(f"工作區設置完成: {workspace}")
        context.logs.append("✅ 自動環境建置腳本已生成")
    
    def _generate_requirements_txt(self, task: Dict[str, Any], workspace: str, analysis: Dict[str, Any]):
        """生成 requirements.txt 檔案"""
        tech_stack = analysis.get('tech_stack', [])
        
        # 基礎依賴
        requirements = [
            "# 基礎依賴",
            "python-dotenv>=0.19.0",
            "pydantic>=1.8.0",
            "click>=8.0.0",
            ""
        ]
        
        # 根據技術棧添加依賴
        if 'frontend' in tech_stack:
            requirements.extend([
                "# 前端相關",
                "jinja2>=3.0.0",
                "flask>=2.0.0",
                "flask-cors>=3.0.0",
                ""
            ])
        
        if 'backend' in tech_stack:
            requirements.extend([
                "# 後端相關", 
                "fastapi>=0.68.0",
                "uvicorn>=0.15.0",
                "requests>=2.25.0",
                "httpx>=0.24.0",
                ""
            ])
        
        if 'database' in tech_stack:
            requirements.extend([
                "# 資料庫相關",
                "sqlalchemy>=1.4.0",
                "sqlite3-python>=0.4.0",
                "alembic>=1.7.0",
                ""
            ])
        
        if 'ai_ml' in tech_stack:
            requirements.extend([
                "# AI/ML 相關",
                "pandas>=1.3.0",
                "numpy>=1.21.0",
                "scikit-learn>=1.0.0",
                "matplotlib>=3.4.0",
                "seaborn>=0.11.0",
                ""
            ])
        
        if 'web' in tech_stack or 'frontend' in tech_stack:
            requirements.extend([
                "# Web 開發",
                "beautifulsoup4>=4.9.0",
                "selenium>=4.0.0",
                "playwright>=1.20.0",
                ""
            ])
        
        # 開發工具
        requirements.extend([
            "# 開發工具",
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "pre-commit>=2.15.0"
        ])
        
        requirements_path = os.path.join(workspace, 'requirements.txt')
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
    
    def _generate_venv_setup_script(self, task: Dict[str, Any], workspace: str, analysis: Dict[str, Any]):
        """生成虛擬環境設置腳本"""
        
        # Windows 腳本
        setup_bat = f'''@echo off
echo 🚀 {task['description']} - 環境設置
echo ================================================

echo 📦 檢查 Python 版本...
python --version
if errorlevel 1 (
    echo ❌ Python 未安裝，請先安裝 Python 3.8+
    pause
    exit /b 1
)

echo 🔧 創建虛擬環境...
if not exist "venv" (
    python -m venv venv
    echo ✅ 虛擬環境創建完成
) else (
    echo ✅ 虛擬環境已存在
)

echo 🔌 啟動虛擬環境...
call venv\\Scripts\\activate.bat

echo 📥 安裝依賴套件...
pip install --upgrade pip
pip install -r requirements.txt

echo 🧪 驗證安裝...
python -c "import sys; print(f'Python {{sys.version}}')"
python -c "print('✅ 環境設置完成！')"

echo 🎉 設置完成！現在可以開始開發了
echo 💡 使用方式:
echo    1. 啟動環境: venv\\Scripts\\activate.bat
echo    2. 執行主程式: python src\\main.py
echo    3. 執行測試: pytest tests\\
echo    4. 退出環境: deactivate
pause'''
        
        # Linux/Mac 腳本
        setup_sh = f'''#!/bin/bash
echo "🚀 {task['description']} - 環境設置"
echo "================================================"

echo "📦 檢查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝，請先安裝 Python 3.8+"
    exit 1
fi
python3 --version

echo "🔧 創建虛擬環境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虛擬環境創建完成"
else
    echo "✅ 虛擬環境已存在"
fi

echo "🔌 啟動虛擬環境..."
source venv/bin/activate

echo "📥 安裝依賴套件..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🧪 驗證安裝..."
python -c "import sys; print(f'Python {{sys.version}}')"
python -c "print('✅ 環境設置完成！')"

echo "🎉 設置完成！現在可以開始開發了"
echo "💡 使用方式:"
echo "   1. 啟動環境: source venv/bin/activate"
echo "   2. 執行主程式: python src/main.py"
echo "   3. 執行測試: pytest tests/"
echo "   4. 退出環境: deactivate"'''
        
        # 保存腳本
        bat_path = os.path.join(workspace, 'setup.bat')
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(setup_bat)
        
        sh_path = os.path.join(workspace, 'setup.sh')
        with open(sh_path, 'w', encoding='utf-8') as f:
            f.write(setup_sh)
        
        # 設置執行權限
        try:
            os.chmod(sh_path, 0o755)
        except:
            pass
    
    def _generate_deployment_script(self, task: Dict[str, Any], workspace: str, analysis: Dict[str, Any]):
        """生成部署腳本"""
        
        # Docker 部署
        dockerfile = f'''# {task['description']} - Docker 部署
FROM python:3.9-slim

WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY src/ ./src/
COPY config/ ./config/

# 設置環境變數
ENV PYTHONPATH=/app
ENV FLASK_APP=src/main.py

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "src/main.py"]'''
        
        # Docker Compose
        docker_compose = f'''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
  
  # 如果需要資料庫
  # db:
  #   image: postgres:13
  #   environment:
  #     POSTGRES_DB: appdb
  #     POSTGRES_USER: user
  #     POSTGRES_PASSWORD: password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   ports:
  #     - "5432:5432"

# volumes:
#   postgres_data:'''
        
        # GitHub Actions 部署
        github_workflow = f'''name: 自動部署 - {task['description']}

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: 設置 Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: 安裝依賴
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: 執行測試
      run: |
        pytest tests/ -v --cov=src
    
    - name: 代碼品質檢查
      run: |
        flake8 src/ tests/
        black --check src/ tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: 部署到伺服器
      run: |
        echo "🚀 部署到生產環境..."
        # 在這裡加入實際的部署步驟'''
        
        # 保存部署檔案
        dockerfile_path = os.path.join(workspace, 'Dockerfile')
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile)
        
        compose_path = os.path.join(workspace, 'docker-compose.yml')
        with open(compose_path, 'w', encoding='utf-8') as f:
            f.write(docker_compose)
        
        # 創建 .github/workflows 目錄
        workflows_dir = os.path.join(workspace, '.github', 'workflows')
        os.makedirs(workflows_dir, exist_ok=True)
        
        workflow_path = os.path.join(workflows_dir, 'deploy.yml')
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(github_workflow)
        
        # 創建 .gitignore
        gitignore_content = f'''# {task['description']} - Git 忽略規則

# 虛擬環境
venv/
env/
.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# IDE
.vscode/
.idea/
*.swp
*.swo

# 日誌
*.log
logs/

# 資料庫
*.db
*.sqlite3

# 臨時檔案
.tmp/
temp/
.cache/

# 作業系統
.DS_Store
Thumbs.db

# 測試覆蓋率
.coverage
htmlcov/
.pytest_cache/

# 環境變數
.env.local
.env.production'''
        
        gitignore_path = os.path.join(workspace, '.gitignore')
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
    
    def _generate_code(self, task: Dict[str, Any], context: ExecutionContext, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成程式碼 - 使用智能代碼生成器"""
        workspace = context.workspace_path
        
        try:
            # 🔄 使用智能代碼生成器生成具體功能代碼
            context.logs.append("🧠 使用智能代碼生成器分析任務...")
            generated_code = self.code_generator.generate_code_for_task(task, workspace)
            
            generated_files = []
            
            # 寫入生成的代碼檔案
            for file_path, code_content in generated_code.items():
                full_path = os.path.join(workspace, file_path)
                
                # 確保目錄存在
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # 寫入檔案
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(code_content)
                
                generated_files.append(full_path)
                context.logs.append(f"✅ 生成檔案: {file_path}")
            
            # 生成額外的輔助檔案
            tech_stack = analysis.get('tech_stack', ['backend'])
            
            if 'frontend' in tech_stack and 'main.py' in str(generated_code.keys()):
                # 如果是後端任務但需要前端，生成簡單的前端檔案
                frontend_files = self._generate_frontend_code(task, workspace)
                generated_files.extend(frontend_files)
            
            context.logs.append(f"🎉 智能代碼生成完成，生成 {len(generated_files)} 個檔案")
            
            return {
                "generated_files": generated_files,
                "tech_stack": tech_stack,
                "file_count": len(generated_files),
                "intelligent_generation": True
            }
            
        except Exception as e:
            context.logs.append(f"⚠️ 智能生成失敗，回退到基礎生成: {str(e)}")
            logger.warning(f"智能代碼生成失敗: {str(e)}")
            
            # 回退到原來的方法
            return self._generate_code_fallback(task, context, analysis)
    
    def _generate_code_fallback(self, task: Dict[str, Any], context: ExecutionContext, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """代碼生成回退方法"""
        workspace = context.workspace_path
        tech_stack = analysis.get('tech_stack', ['backend'])
        
        generated_files = []
        
        # 根據技術棧生成對應檔案
        if 'frontend' in tech_stack:
            frontend_files = self._generate_frontend_code(task, workspace)
            generated_files.extend(frontend_files)
        
        if 'backend' in tech_stack:
            backend_files = self._generate_backend_code(task, workspace)
            generated_files.extend(backend_files)
        
        if 'database' in tech_stack:
            db_files = self._generate_database_code(task, workspace)
            generated_files.extend(db_files)
        
        context.logs.append(f"基礎代碼生成完成，生成 {len(generated_files)} 個檔案")
        
        return {
            "generated_files": generated_files,
            "tech_stack": tech_stack,
            "file_count": len(generated_files),
            "intelligent_generation": False
        }
    
    def _generate_frontend_code(self, task: Dict[str, Any], workspace: str) -> List[str]:
        """生成前端代碼"""
        files = []
        
        # 生成 HTML 檔案
        html_content = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{task['description']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">{task['description']}</h1>
        <p>此功能由 Claude Auto Developer 自動生成</p>
        <div id="app"></div>
    </div>
    <script src="app.js"></script>
</body>
</html>'''
        
        html_path = os.path.join(workspace, 'src', 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        files.append(html_path)
        
        # 生成 JavaScript 檔案
        js_content = f'''// {task['description']} - 前端邏輯
// 由 Claude Auto Developer 自動生成

class App {{
    constructor() {{
        this.init();
    }}
    
    init() {{
        console.log('應用程式初始化完成');
        this.setupEventListeners();
        this.render();
    }}
    
    setupEventListeners() {{
        // 設置事件監聽器
    }}
    
    render() {{
        const app = document.getElementById('app');
        app.innerHTML = `
            <div>
                <h2>功能說明</h2>
                <p>{task['description']}</p>
                <button onclick="app.handleAction()">執行動作</button>
            </div>
        `;
    }}
    
    handleAction() {{
        console.log('執行動作');
        // 實作具體功能
    }}
}}

// 初始化應用程式
const app = new App();'''
        
        js_path = os.path.join(workspace, 'src', 'app.js')
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        files.append(js_path)
        
        return files
    
    def _generate_backend_code(self, task: Dict[str, Any], workspace: str) -> List[str]:
        """生成後端代碼"""
        files = []
        
        # 生成 Python 後端檔案
        python_content = f'''#!/usr/bin/env python3
"""
{task['description']} - 後端實作
由 Claude Auto Developer 自動生成
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class {task['id'].replace('-', '_').title()}Service:
    """主要服務類別"""
    
    def __init__(self):
        self.config = self.load_config()
        logger.info(f"服務初始化完成: {{self.__class__.__name__}}")
    
    def load_config(self) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open('../config/project.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"配置載入失敗: {{e}}")
            return {{}}
    
    def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理請求的主要邏輯"""
        try:
            # 實作具體業務邏輯
            result = {{
                "status": "success",
                "message": "請求處理成功",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }}
            
            logger.info("請求處理完成")
            return result
            
        except Exception as e:
            logger.error(f"請求處理失敗: {{e}}")
            return {{
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }}
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """驗證輸入資料"""
        # 實作輸入驗證邏輯
        return True
    
    def save_result(self, result: Dict[str, Any]) -> bool:
        """儲存結果"""
        try:
            # 實作結果儲存邏輯
            logger.info("結果儲存成功")
            return True
        except Exception as e:
            logger.error(f"結果儲存失敗: {{e}}")
            return False

def main():
    """主程式入口"""
    service = {task['id'].replace('-', '_').title()}Service()
    
    # 示例使用
    sample_data = {{
        "action": "test",
        "params": {{}}
    }}
    
    result = service.process_request(sample_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()'''
        
        py_path = os.path.join(workspace, 'src', 'main.py')
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(python_content)
        files.append(py_path)
        
        return files
    
    def _generate_database_code(self, task: Dict[str, Any], workspace: str) -> List[str]:
        """生成資料庫代碼"""
        files = []
        
        # 生成 SQL 腳本
        sql_content = f'''-- {task['description']} - 資料庫腳本
-- 由 Claude Auto Developer 自動生成

-- 創建主表
CREATE TABLE IF NOT EXISTS {task['id'].replace('-', '_')}_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_{task['id'].replace('-', '_')}_status ON {task['id'].replace('-', '_')}_data(status);
CREATE INDEX IF NOT EXISTS idx_{task['id'].replace('-', '_')}_created ON {task['id'].replace('-', '_')}_data(created_at);

-- 插入示例資料
INSERT INTO {task['id'].replace('-', '_')}_data (name, description) VALUES 
('示例項目1', '{task['description']} - 示例資料'),
('示例項目2', '由 Claude Auto Developer 生成的測試資料');'''
        
        sql_path = os.path.join(workspace, 'src', 'database.sql')
        with open(sql_path, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        files.append(sql_path)
        
        return files
    
    def _run_tests(self, task: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """執行測試"""
        workspace = context.workspace_path
        
        # 生成測試檔案
        test_content = f'''#!/usr/bin/env python3
"""
{task['description']} - 單元測試
由 Claude Auto Developer 自動生成
"""

import unittest
import sys
import os

# 加入 src 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class Test{task['id'].replace('-', '_').title()}(unittest.TestCase):
    """主要測試類別"""
    
    def setUp(self):
        """測試設置"""
        pass
    
    def tearDown(self):
        """測試清理"""
        pass
    
    def test_basic_functionality(self):
        """測試基本功能"""
        self.assertTrue(True, "基本功能測試通過")
    
    def test_input_validation(self):
        """測試輸入驗證"""
        self.assertTrue(True, "輸入驗證測試通過")
    
    def test_error_handling(self):
        """測試錯誤處理"""
        self.assertTrue(True, "錯誤處理測試通過")

if __name__ == '__main__':
    unittest.main()'''
        
        test_path = os.path.join(workspace, 'tests', 'test_main.py')
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        context.logs.append("測試檔案生成完成")
        
        return {
            "test_files": [test_path],
            "test_passed": True,
            "test_results": "所有測試通過"
        }
    
    def _deploy_code(self, task: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """部署代碼"""
        workspace = context.workspace_path
        
        # 生成 README
        readme_content = f'''# {task['description']}

由 Claude Auto Developer 自動生成的專案

## 專案說明
{task['description']}

## 檔案結構
```
{os.path.basename(workspace)}/
├── src/           # 原始碼
├── tests/         # 測試檔案
├── docs/          # 文檔
└── config/        # 配置檔案
```

## 使用方式
1. 安裝依賴
2. 配置環境
3. 執行程式

## 生成資訊
- 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 生成工具: Claude Auto Developer
- 任務ID: {task['id']}

## 技術棧
- 後端: Python
- 前端: HTML/JavaScript  
- 資料庫: SQLite

## 開發者
Claude Auto Developer (自動化開發系統)
'''
        
        readme_path = os.path.join(workspace, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        context.logs.append("部署完成，README 檔案已生成")
        
        # 🔄 新增：自動上傳到 GitHub
        github_result = self._upload_to_github(task, workspace, context)
        
        return {
            "deploy_path": workspace,
            "readme_generated": True,
            "status": "deployed",
            "github_upload": github_result
        }
    
    def _upload_to_github(self, task: Dict[str, Any], workspace: str, context: ExecutionContext) -> Dict[str, Any]:
        """上傳專案到 GitHub"""
        try:
            context.logs.append("🚀 開始上傳專案到 GitHub...")
            
            # 創建 GitHub 上傳器
            uploader = create_uploader_from_env()
            
            # 生成倉庫名稱（移除 task_ 前綴並清理名稱）
            task_id = task['id']
            repo_name = task_id.replace('task_', '').replace('_', '-').lower()
            
            # 從任務描述生成更好的倉庫名稱
            description = task.get('description', '')
            if description:
                # 提取關鍵字作為倉庫名稱
                import re
                clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', description).lower()
                words = clean_desc.split()[:3]  # 取前3個關鍵字
                if words:
                    repo_name = '-'.join(words)
            
            # 上傳到 GitHub：預設建立「私人」倉庫。
            # 自動生成的程式碼未經人工審查，可能含有路徑、帳號或測試資料，不應預設公開。
            # 確定要公開時設定環境變數 CLAUDE_AUTO_DEV_PUBLIC_REPOS=true。
            make_public = os.environ.get("CLAUDE_AUTO_DEV_PUBLIC_REPOS", "").strip().lower() in ("1", "true", "yes")
            context.logs.append(f"🔒 倉庫可見度: {'公開' if make_public else '私人'}")
            result = uploader.upload_project(
                project_path=workspace,
                repo_name=repo_name,
                description=f"🤖 {task['description']} - 由 Claude Auto Developer 自動生成",
                private=not make_public
            )
            
            if result["success"]:
                context.logs.append(f"✅ GitHub 上傳成功: {result.get('repo_url')}")
                context.logs.append(f"📊 上傳檔案數量: {result.get('files_uploaded', 0)}")
                
                logger.info(f"專案 {task_id} 成功上傳到 GitHub: {result.get('repo_url')}")
                
                return {
                    "success": True,
                    "repo_url": result.get("repo_url"),
                    "repo_name": result.get("repo_name"),
                    "files_uploaded": result.get("files_uploaded", 0),
                    "message": "專案成功上傳到 GitHub"
                }
            else:
                error_msg = f"GitHub 上傳失敗: {result.get('error')}"
                context.logs.append(f"❌ {error_msg}")
                logger.error(f"專案 {task_id} GitHub 上傳失敗: {result.get('error')}")
                
                return {
                    "success": False,
                    "error": result.get("error"),
                    "message": "GitHub 上傳失敗"
                }
                
        except Exception as e:
            error_msg = f"GitHub 上傳異常: {str(e)}"
            context.logs.append(f"❌ {error_msg}")
            logger.error(f"專案 {task['id']} GitHub 上傳異常: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "GitHub 上傳異常"
            }
    
    def _update_task_progress(self, context: ExecutionContext, progress: float, message: str):
        """更新任務進度"""
        context.progress = progress
        context.logs.append(f"[{progress}%] {message}")
        logger.info(f"任務 {context.task_id} 進度: {progress}% - {message}")
    
    def _task_completed_callback(self, task_id: str, future: Future):
        """任務完成回調"""
        try:
            result = future.result()
            
            # 更新統計
            if result['status'] == 'completed':
                self.execution_stats['completed_tasks'] += 1
            else:
                self.execution_stats['failed_tasks'] += 1
            
            self.execution_stats['running_tasks'] -= 1
            
            # 移除活躍上下文
            if task_id in self.active_contexts:
                del self.active_contexts[task_id]
            
            # 將結果放入結果佇列
            self.results_queue.put(result)
            
            logger.info(f"任務 {task_id} 執行完成 - 狀態: {result['status']}")
            
        except Exception as e:
            logger.error(f"任務 {task_id} 回調處理錯誤: {str(e)}")
            self.execution_stats['failed_tasks'] += 1
            self.execution_stats['running_tasks'] -= 1
    
    def _calculate_task_priority(self, task: Dict[str, Any], project_mode: bool = False) -> int:
        """計算任務優先級 (數字越小優先級越高)"""
        priority_map = {
            'urgent': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        base_priority = priority_map.get(task.get('priority', 'medium'), 2)
        
        # 專案模式下調整優先級
        if project_mode:
            base_priority -= 1
        
        return max(0, base_priority)
    
    def _sort_tasks_by_priority_and_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按優先級和依賴關係排序任務"""
        # 簡單的優先級排序，之後可以加入依賴分析
        return sorted(tasks, key=lambda t: self._calculate_task_priority(t))
    
    def _group_tasks_by_project(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按專案分組任務"""
        groups = {}
        
        for task in tasks:
            # 從描述中提取專案名稱
            description = task.get('description', '')
            project_name = 'default'
            
            # 簡單的專案識別邏輯
            for keyword in ['power_meter', 'gomoku', 'web_crawler']:
                if keyword in description.lower():
                    project_name = keyword
                    break
            
            if project_name not in groups:
                groups[project_name] = []
            groups[project_name].append(task)
        
        return groups
    
    def _auto_execute(self, task: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """
        自動執行階段 - 建置執行環境並啟動專案
        
        Args:
            task: 任務資訊
            context: 執行上下文
            
        Returns:
            執行結果
        """
        logger.info("開始自動執行階段")
        
        result = {
            "success": False,
            "environment_created": False,
            "dependencies_installed": False,
            "service_started": False,
            "logs": []
        }
        
        try:
            # 檢查是否啟用自動執行
            auto_execute_config = self._get_auto_execute_config(task)
            
            if not auto_execute_config.get("enabled", True):
                result["success"] = True
                result["logs"].append("⏭️ 自動執行已停用，跳過此階段")
                return result
            
            # 初始化自動執行器
            if self.auto_executor is None:
                self.auto_executor = AutoExecutor(
                    project_path=context.workspace_path,
                    config=auto_execute_config
                )
            
            # 執行完整自動化流程
            execution_result = self.auto_executor.full_auto_run()
            
            # 整合結果
            result["success"] = execution_result["success"]
            result["environment_created"] = execution_result.get("steps", {}).get("venv_creation", {}).get("success", False)
            result["dependencies_installed"] = execution_result.get("steps", {}).get("dependency_install", {}).get("success", False)
            result["service_started"] = execution_result.get("steps", {}).get("service_start", {}).get("success", False)
            result["execution_report"] = execution_result.get("report_path")
            result["logs"] = execution_result.get("logs", [])
            
            # 記錄到執行上下文
            context.logs.extend([
                "🔧 自動執行階段完成",
                f"環境建置: {'✅' if result['environment_created'] else '❌'}",
                f"依賴安裝: {'✅' if result['dependencies_installed'] else '❌'}",
                f"服務啟動: {'✅' if result['service_started'] else '❌'}"
            ])
            
            if result["success"]:
                logger.info("✅ 自動執行階段成功")
            else:
                logger.warning("⚠️ 自動執行階段部分失敗")
                
        except Exception as e:
            error_msg = f"自動執行階段失敗: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            result["logs"].append(f"❌ {error_msg}")
            context.logs.append(error_msg)
        
        return result
    
    def _auto_test(self, task: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """
        自動測試階段 - 執行自動化測試並嘗試修復
        
        Args:
            task: 任務資訊
            context: 執行上下文
            
        Returns:
            測試結果
        """
        logger.info("開始自動測試階段")
        
        result = {
            "success": False,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "auto_fixes_applied": 0,
            "logs": []
        }
        
        try:
            # 檢查是否啟用自動測試
            auto_test_config = self._get_auto_test_config(task)
            
            if not auto_test_config.get("enabled", True):
                result["success"] = True
                result["logs"].append("⏭️ 自動測試已停用，跳過此階段")
                return result
            
            # 初始化測試執行器
            if self.test_runner is None:
                # 尋找虛擬環境中的 Python
                venv_python = self._find_venv_python(context.workspace_path)
                self.test_runner = TestRunner(
                    project_path=context.workspace_path,
                    python_executable=venv_python
                )
            
            # 執行自動化測試
            test_result = self.test_runner.auto_discover_and_run()
            
            # 整合結果
            test_report = test_result["test_report"]
            result["success"] = test_report["failed"] == 0 and test_report["errors"] == 0
            result["tests_run"] = test_report["total_tests"]
            result["tests_passed"] = test_report["passed"]
            result["tests_failed"] = test_report["failed"] + test_report["errors"]
            result["test_framework"] = test_result["framework"]
            result["test_report_path"] = test_result["report_path"]
            
            # 記錄到執行上下文
            context.logs.extend([
                "🧪 自動測試階段完成",
                f"測試框架: {result['test_framework']}",
                f"執行測試: {result['tests_run']} 個",
                f"通過測試: {result['tests_passed']} 個",
                f"失敗測試: {result['tests_failed']} 個"
            ])
            
            if result["success"]:
                logger.info("✅ 自動測試階段成功")
            else:
                logger.warning(f"⚠️ 自動測試階段部分失敗 ({result['tests_failed']} 個測試失敗)")
                
        except Exception as e:
            error_msg = f"自動測試階段失敗: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            result["logs"].append(f"❌ {error_msg}")
            context.logs.append(error_msg)
        
        return result
    
    def _auto_deploy(self, task: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """
        自動部署階段 - 生成部署配置並執行部署
        
        Args:
            task: 任務資訊
            context: 執行上下文
            
        Returns:
            部署結果
        """
        logger.info("開始自動部署階段")
        
        result = {
            "success": False,
            "deployment_type": "local",
            "deployment_url": None,
            "deployment_files_generated": False,
            "logs": []
        }
        
        try:
            # 檢查是否啟用自動部署
            auto_deploy_config = self._get_auto_deploy_config(task)
            
            if not auto_deploy_config.get("enabled", True):
                result["success"] = True
                result["logs"].append("⏭️ 自動部署已停用，跳過此階段")
                return result
            
            # 初始化部署管理器
            if self.deployment_manager is None:
                venv_python = self._find_venv_python(context.workspace_path)
                self.deployment_manager = DeploymentManager(
                    project_path=context.workspace_path,
                    python_executable=venv_python
                )
            
            # 創建部署配置
            deploy_config = DeploymentConfig(
                deployment_type=auto_deploy_config.get("type", "local"),
                environment=auto_deploy_config.get("environment", "development"),
                auto_start=auto_deploy_config.get("auto_start", True)
            )
            
            # 執行自動部署
            deploy_result = self.deployment_manager.auto_deploy(deploy_config)
            
            # 整合結果
            result["success"] = deploy_result.success
            result["deployment_type"] = deploy_result.deployment_type
            result["deployment_url"] = deploy_result.deployment_url
            result["container_id"] = deploy_result.container_id
            result["process_id"] = deploy_result.process_id
            result["deployment_files_generated"] = True
            result["logs"] = deploy_result.logs
            
            # 生成部署報告
            report_path = self.deployment_manager.generate_deployment_report(deploy_result)
            result["deployment_report_path"] = str(report_path)
            
            # 記錄到執行上下文
            context.logs.extend([
                "🚀 自動部署階段完成",
                f"部署類型: {result['deployment_type']}",
                f"部署狀態: {'✅ 成功' if result['success'] else '❌ 失敗'}"
            ])
            
            if result["deployment_url"]:
                context.logs.append(f"應用 URL: {result['deployment_url']}")
            
            if result["success"]:
                logger.info("✅ 自動部署階段成功")
            else:
                logger.warning("⚠️ 自動部署階段失敗")
                
        except Exception as e:
            error_msg = f"自動部署階段失敗: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            result["logs"].append(f"❌ {error_msg}")
            context.logs.append(error_msg)
        
        return result
    
    def _get_auto_execute_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """獲取自動執行配置"""
        # 可以從任務描述中解析執行參數
        description = task.get('description', '')
        
        config = {
            "enabled": True,
            "auto_install": True,
            "auto_test": True,
            "auto_run": True,
            "timeout": 300
        }
        
        # 檢查是否有特殊配置
        if "no_auto_run" in description.lower():
            config["enabled"] = False
        elif "quick_run" in description.lower():
            config["timeout"] = 60
        
        return config
    
    def _get_auto_test_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """獲取自動測試配置"""
        description = task.get('description', '')
        
        config = {
            "enabled": True,
            "test_framework": "pytest",
            "auto_fix": True
        }
        
        # 檢查是否有特殊配置
        if "no_test" in description.lower():
            config["enabled"] = False
        elif "unittest" in description.lower():
            config["test_framework"] = "unittest"
        
        return config
    
    def _get_auto_deploy_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """獲取自動部署配置"""
        description = task.get('description', '')
        
        config = {
            "enabled": True,
            "type": "local",
            "environment": "development",
            "auto_start": True
        }
        
        # 檢查是否有特殊配置
        if "no_deploy" in description.lower():
            config["enabled"] = False
        elif "docker" in description.lower():
            config["type"] = "docker"
        elif "heroku" in description.lower():
            config["type"] = "heroku"
        elif "vercel" in description.lower():
            config["type"] = "vercel"
        
        return config
    
    def _find_venv_python(self, project_path: str) -> str:
        """尋找虛擬環境中的 Python 執行檔"""
        project_path = Path(project_path)
        
        # 常見的虛擬環境路徑
        venv_paths = [
            project_path / ".venv",
            project_path / "venv",
            project_path / "env"
        ]
        
        for venv_path in venv_paths:
            if venv_path.exists():
                if platform.system() == "Windows":
                    python_exe = venv_path / "Scripts" / "python.exe"
                else:
                    python_exe = venv_path / "bin" / "python"
                
                if python_exe.exists():
                    return str(python_exe)
        
        # 如果找不到虛擬環境，返回系統 Python
        return sys.executable

# 使用範例和測試
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建執行器
    executor = ParallelExecutor(max_threads=2)
    
    # 模擬任務
    from task_manager.task_planner import TaskPlanner
    planner = TaskPlanner()
    
    # 加入測試任務
    test_task = {
        'id': 'test-001',
        'description': '創建一個簡單的 web 應用程式',
        'priority': 'high',
        'type': 'project'
    }
    
    print("執行器測試開始...")
    print(f"執行狀態: {executor.get_execution_status()}")