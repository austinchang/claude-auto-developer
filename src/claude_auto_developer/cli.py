#!/usr/bin/env python3
"""
Claude Auto Developer - CLI 主介面
提供命令行操作介面
"""

import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

# 導入核心模組
from .task_manager.task_analyzer import TaskAnalyzer
from .task_manager.task_planner import TaskPlanner
from .task_manager.priority_manager import PriorityManager
from .task_manager.deadline_tracker import DeadlineTracker
from .execution_engine.parallel_executor import ParallelExecutor, ExecutionMode

console = Console()

@click.group()
@click.version_option(version="1.0.0-alpha")
def cli():
    """
    🤖 Claude Auto Developer - 智能專案開發自動化系統
    
    讓 Claude Code 在晚上也能工作的革命性開發工具
    """
    pass

@cli.command()
@click.argument('description')
@click.option('--deadline', '-d', default="1天", help='完成期限 (例如: 1天, 2小時, 1週)')
@click.option('--priority', '-p', default="medium", 
              type=click.Choice(['urgent', 'high', 'medium', 'low']),
              help='任務優先級')
@click.option('--type', '-t', default="feature",
              type=click.Choice(['feature', 'project', 'bugfix', 'enhancement']),
              help='任務類型')
@click.option('--tags', help='標籤 (用逗號分隔)')
def add(description, deadline, priority, type, tags):
    """
    新增開發任務到計畫清單
    
    範例:
    claude-auto add "為 power_meter_gui 增加 AI 預測功能" --deadline "2天" --priority "high"
    """
    console.print(f"[bold green]✅ 新增任務:[/bold green] {description}")
    
    # 分析任務
    analyzer = TaskAnalyzer()
    with console.status("[bold blue]分析任務需求..."):
        analysis = analyzer.analyze_requirement(description)
    
    # 創建任務
    planner = TaskPlanner()
    task = planner.create_task(
        description=description,
        deadline=deadline,
        priority=priority,
        task_type=type,
        tags=tags.split(',') if tags else [],
        analysis=analysis
    )
    
    # 顯示任務資訊
    display_task_info(task)
    
    console.print(f"[bold green]🎯 任務已加入計畫清單！[/bold green] ID: {task['id']}")

@cli.command()
@click.option('--filter', '-f', help='過濾條件 (priority, type, status)')
@click.option('--limit', '-l', default=20, help='顯示數量限制')
def list(filter, limit):
    """
    查看計畫清單中的所有任務
    """
    console.print("[bold blue]📋 任務計畫清單[/bold blue]")
    
    planner = TaskPlanner()
    tasks = planner.get_tasks(filter_condition=filter, limit=limit)
    
    if not tasks:
        console.print("[yellow]目前沒有任務在計畫清單中[/yellow]")
        return
    
    # 創建表格
    table = Table(title="開發任務清單")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("描述", style="white", width=40)
    table.add_column("優先級", style="red", width=10)
    table.add_column("類型", style="green", width=12)
    table.add_column("期限", style="yellow", width=15)
    table.add_column("狀態", style="blue", width=12)
    
    for task in tasks:
        status_color = {
            'pending': 'yellow',
            'in_progress': 'blue',
            'completed': 'green',
            'failed': 'red'
        }.get(task['status'], 'white')
        
        table.add_row(
            task['id'],
            task['description'][:35] + "..." if len(task['description']) > 35 else task['description'],
            task['priority'],
            task['type'],
            task['deadline'],
            f"[{status_color}]{task['status']}[/{status_color}]"
        )
    
    console.print(table)

@cli.command()
@click.option('--mode', '-m', default="auto",
              type=click.Choice(['auto', 'project', 'single', 'emergency']),
              help='執行模式')
@click.option('--max-threads', default=4, help='最大執行緒數')
def start(mode, max_threads):
    """
    啟動自動開發系統
    """
    console.print("[bold green]🚀 啟動 Claude Auto Developer...[/bold green]")
    
    planner = TaskPlanner()
    pending_tasks = planner.get_pending_tasks()
    
    if not pending_tasks:
        console.print("[yellow]沒有待執行的任務[/yellow]")
        return
    
    console.print(f"[blue]找到 {len(pending_tasks)} 個待執行任務[/blue]")
    console.print(f"[blue]執行模式: {mode}[/blue]")
    console.print(f"[blue]最大執行緒數: {max_threads}[/blue]")
    
    # 創建並啟動執行引擎
    try:
        executor = ParallelExecutor(max_threads=max_threads)
        
        # 模擬啟動過程
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task1 = progress.add_task("初始化執行引擎...", total=None)
            progress.advance(task1)
            
            task2 = progress.add_task("分析任務依賴關係...", total=None)
            progress.advance(task2)
            
            task3 = progress.add_task("分配執行緒資源...", total=None)
            progress.advance(task3)
            
            task4 = progress.add_task("啟動並行執行...", total=None)
            progress.advance(task4)
        
        # 啟動執行
        execution_mode = getattr(ExecutionMode, mode.upper())
        success = executor.start_execution(execution_mode)
        
        if success:
            console.print("[bold green]✅ 自動開發系統已啟動！[/bold green]")
            console.print("[blue]系統將在背景持續執行，您可以使用 'claude-auto status' 查看進度[/blue]")
            
            # 保存執行器引用 (簡化版，實際應該用更好的方式管理)
            import os
            executor_info = {
                "pid": os.getpid(),
                "start_time": executor.execution_stats["start_time"].isoformat() if executor.execution_stats["start_time"] else None,
                "mode": mode,
                "max_threads": max_threads
            }
            
            # 在實際環境中，這裡應該將執行器資訊保存到檔案或資料庫
            console.print(f"[dim]執行器 PID: {executor_info['pid']}[/dim]")
        else:
            console.print("[red]❌ 啟動失敗[/red]")
            
    except Exception as e:
        console.print(f"[red]啟動錯誤: {str(e)}[/red]")

@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='顯示詳細資訊')
def status(detailed):
    """
    查看系統運行狀態和任務進度
    """
    console.print("[bold blue]📊 系統狀態報告[/bold blue]")
    
    planner = TaskPlanner()
    status_info = planner.get_system_status()
    
    # 創建狀態面板
    status_text = f"""
    🔄 運行中任務: {status_info.get('running_tasks', 0)}
    ⏸️  等待中任務: {status_info.get('pending_tasks', 0)}
    ✅ 已完成任務: {status_info.get('completed_tasks', 0)}
    ❌ 失敗任務: {status_info.get('failed_tasks', 0)}
    
    💻 CPU 使用率: {status_info.get('cpu_usage', 0)}%
    🧠 記憶體使用: {status_info.get('memory_usage', 0)}%
    🗂️  活躍執行緒: {status_info.get('active_threads', 0)}
    """
    
    console.print(Panel(status_text, title="系統狀態", border_style="blue"))
    
    if detailed:
        # 顯示詳細的任務進度
        running_tasks = planner.get_running_tasks()
        if running_tasks:
            console.print("\n[bold]🔄 執行中的任務:[/bold]")
            for task in running_tasks:
                progress_bar = "█" * int(task.get('progress', 0) / 10) + "░" * (10 - int(task.get('progress', 0) / 10))
                console.print(f"  {task['id']}: {task['description'][:30]}... [{progress_bar}] {task.get('progress', 0)}%")

@cli.command()
def pause():
    """
    暫停自動開發系統
    """
    console.print("[yellow]⏸️  暫停自動開發系統...[/yellow]")
    console.print("[blue]系統已暫停，使用 'claude-auto resume' 恢復運行[/blue]")

@cli.command()
def resume():
    """
    恢復自動開發系統
    """
    console.print("[green]▶️  恢復自動開發系統...[/green]")
    console.print("[blue]系統已恢復運行[/blue]")

@cli.command()
def threads():
    """
    查看執行緒狀態
    """
    console.print("[bold blue]🧵 執行緒狀態[/bold blue]")
    
    # 模擬執行緒資訊
    thread_info = [
        {"id": "thread-1", "status": "running", "task": "生成前端組件", "progress": 75},
        {"id": "thread-2", "status": "running", "task": "創建API端點", "progress": 45},
        {"id": "thread-3", "status": "idle", "task": "等待中", "progress": 0},
        {"id": "thread-4", "status": "idle", "task": "等待中", "progress": 0},
    ]
    
    table = Table(title="執行緒狀態")
    table.add_column("執行緒ID", style="cyan")
    table.add_column("狀態", style="white")
    table.add_column("當前任務", style="green")
    table.add_column("進度", style="yellow")
    
    for thread in thread_info:
        status_color = {"running": "green", "idle": "yellow", "error": "red"}.get(thread['status'], "white")
        table.add_row(
            thread['id'],
            f"[{status_color}]{thread['status']}[/{status_color}]",
            thread['task'],
            f"{thread['progress']}%"
        )
    
    console.print(table)

def display_task_info(task):
    """顯示任務資訊"""
    info_text = f"""
    📝 描述: {task['description']}
    ⏰ 期限: {task['deadline']}
    🎯 優先級: {task['priority']}
    🏷️  類型: {task['type']}
    
    📊 複雜度評估: {task.get('complexity', 'Medium')}
    ⏱️  預估時間: {task.get('estimated_time', 'Unknown')}
    🛠️  技術棧: {', '.join(task.get('tech_stack', ['Unknown']))}
    """
    
    console.print(Panel(info_text, title=f"任務資訊 - {task['id']}", border_style="green"))

def main():
    """主程式入口"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]操作已取消[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]錯誤: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()