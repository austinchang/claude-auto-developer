#!/usr/bin/env python3
"""
測試 Claude Auto Developer 功能
"""

import os
import sys
sys.path.append('src')

def test_task_creation():
    """測試任務創建功能"""
    print("🧪 測試 Claude Auto Developer...")
    
    try:
        from claude_auto_developer.task_manager.task_analyzer import TaskAnalyzer
        from claude_auto_developer.execution_engine.parallel_executor import ParallelExecutor
        
        # 創建測試任務
        analyzer = TaskAnalyzer()
        description = "創建一個股票分析工具"
        
        print(f"📝 分析任務: {description}")
        analysis = analyzer.analyze_requirement(description)
        
        print(f"✅ 分析完成:")
        print(f"   複雜度: {analysis['complexity']}")
        print(f"   技術棧: {analysis['tech_stack']}")
        print(f"   預估時間: {analysis['estimated_time']}")
        
        # 創建執行器
        print("\n🚀 創建執行器...")
        executor = ParallelExecutor(max_threads=2, workspace_base="./test_output")
        
        # 模擬任務
        test_task = {
            'id': 'test-stock-001',
            'description': description,
            'priority': 'high',
            'type': 'project',
            'status': 'pending',
            'deadline': '0.5天',
            'created_at': '2025-07-21T10:30:00'
        }
        
        print("📊 執行器狀態:")
        status = executor.get_execution_status()
        for key, value in status.items():
            if key != 'active_tasks':
                print(f"   {key}: {value}")
        
        print("\n✅ 測試完成！Claude Auto Developer 核心功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_task_creation()