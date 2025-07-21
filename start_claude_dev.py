#!/usr/bin/env python3
"""
Claude Auto Developer - 一鍵啟動腳本
快速啟動完整的自主開發系統
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加 src 目錄到 Python 路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from claude_auto_developer.autonomous_engine.night_developer import NightDeveloper, NightConfig
from claude_auto_developer.file_interface.github_sync import GitHubTaskSync
from datetime import time

async def main():
    print("🤖 Claude Auto Developer - 智能自主開發系統")
    print("=" * 50)
    
    # 檢查 TASKS.md 文件
    tasks_file = Path("/home/tengjung_chang/TASKS.md")
    if not tasks_file.exists():
        print("📝 創建示例 TASKS.md 文件...")
        create_example_tasks_file(tasks_file)
    
    # 設定夜間開發配置
    print("⚙️ 初始化配置...")
    config = NightConfig(
        night_start_time=time(22, 0),        # 晚上 10 點開始夜間工作
        night_end_time=time(6, 0),           # 早上 6 點結束
        max_cpu_usage=0.8,                   # 最大 CPU 使用率 80%
        max_memory_usage=0.7,                # 最大記憶體使用率 70%
        github_sync_enabled=check_github_config(),  # 檢查是否有 GitHub 配置
        sync_interval=300,                   # 5分鐘同步一次
        auto_commit_enabled=True,            # 啟用自動提交
        max_concurrent_tasks=2               # 最大並行任務數
    )
    
    # 創建並啟動夜間開發引擎
    print("🚀 啟動夜間開發引擎...")
    night_dev = NightDeveloper(config)
    
    try:
        await night_dev.start()
        
        print("\n🌟 Claude Auto Developer 已成功啟動！")
        print("=" * 50)
        print("📋 任務管理:")
        print(f"   • 本地任務文件: {tasks_file}")
        if config.github_sync_enabled:
            print("   • GitHub 同步: ✅ 已啟用")
        else:
            print("   • GitHub 同步: ❌ 未配置（可選）")
        
        print("\n🌙 自動開發模式:")
        print("   • 夜間工作時間: 22:00 - 06:00")
        print("   • 智能資源管理: 已啟用")
        print("   • 用戶活動檢測: 已啟用")
        
        print("\n📝 使用方法:")
        print(f"   1. 編輯 {tasks_file} 添加開發任務")
        print("   2. 使用標準格式: - [ ] **任務名稱** | 截止日期: XXX | 技術: XXX | 描述: XXX")
        print("   3. 系統會自動檢測並執行新任務")
        
        if config.github_sync_enabled:
            print("   4. 也可以在 GitHub 上編輯 TASKS.md，會自動同步")
        
        print("\n⚡ 控制指令:")
        print("   • Ctrl+C: 停止系統")
        print("   • 系統會在背景持續運行並監控任務")
        
        print("\n" + "=" * 50)
        print("🔄 系統運行狀態:")
        
        # 主運行循環
        while True:
            await asyncio.sleep(60)  # 每分鐘顯示一次狀態
            
            try:
                status = night_dev.get_status()
                current_mode = status.get('working_mode', 'unknown')
                task_counts = status.get('schedule_status', {}).get('task_counts', {})
                
                running_tasks = task_counts.get('running', 0)
                pending_tasks = task_counts.get('scheduled', 0)
                completed_tasks = task_counts.get('completed', 0)
                
                # 顯示當前狀態
                mode_icon = {
                    'normal': '☀️',
                    'night': '🌙',
                    'stealth': '🤫',
                    'aggressive': '⚡'
                }.get(current_mode, '❓')
                
                print(f"[{get_current_time()}] {mode_icon} 模式: {current_mode} | "
                      f"執行中: {running_tasks} | 等待: {pending_tasks} | 已完成: {completed_tasks}")
                
            except Exception as e:
                print(f"[{get_current_time()}] ⚠️ 狀態檢查錯誤: {str(e)}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信號...")
        print("💾 保存狀態並清理資源...")
        
    except Exception as e:
        print(f"\n❌ 系統錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🔄 停止夜間開發引擎...")
        night_dev.stop()
        print("✅ 系統已安全停止")
        
        # 顯示最終統計
        try:
            final_status = night_dev.get_status()
            stats = final_status.get('stats', {})
            print(f"\n📊 運行統計:")
            print(f"   • 完成任務: {stats.get('tasks_completed_night', 0)} 個")
            print(f"   • 失敗任務: {stats.get('tasks_failed_night', 0)} 個")
            print(f"   • 自動提交: {stats.get('auto_commits', 0)} 次")
            if config.github_sync_enabled:
                print(f"   • GitHub 同步: {stats.get('github_syncs', 0)} 次")
        except:
            pass
        
        print("\n👋 感謝使用 Claude Auto Developer！")

def create_example_tasks_file(file_path: Path):
    """創建示例任務文件"""
    example_content = """# 🤖 Claude Auto Developer - 開發任務清單

> 此文件是您與 Claude Auto Developer 的溝通介面  
> 編輯此文件來新增、修改或檢查開發任務的進度  
> 系統會自動監控文件變化並開始執行任務  

---

## 🔥 緊急項目 (24小時內)

- [ ] **示例緊急任務** | 截止日期: 明天下午 | 技術: Python | 描述: 這是一個示例任務，你可以修改或刪除它 | 時間: 1小時

## ⭐ 高優先級 (本週內)

- [ ] **示例高優先級任務** | 截止日期: 週五 | 技術: React + Node.js | 描述: 創建一個簡單的 Web 應用程式 | 時間: 1天

## 📅 一般項目 (兩週內)

- [ ] **示例一般任務** | 截止日期: 下週 | 技術: Python + FastAPI | 描述: 開發 REST API 後端服務 | 時間: 2天

## 🔖 低優先級 (一個月內)

- [ ] **示例低優先級任務** | 截止日期: 月底 | 技術: Docker | 描述: 容器化現有應用程式 | 時間: 半天

---

## 📊 任務狀態統計

- 🔥 緊急: 1 個
- ⭐ 高優先級: 1 個  
- 📅 一般: 1 個
- 🔖 低優先級: 1 個

**總計: 4 個待執行任務**

---

## 📝 使用說明

### 任務格式
```markdown
- [ ] **任務標題** | 截止日期: XXX | 技術: XXX | 描述: XXX | 時間: XXX
```

### 狀態標記
- `- [ ]` 待執行
- `- [~]` 執行中  
- `- [x]` 已完成
- `- [!]` 失敗

### 優先級標記
- 🔥 緊急 (24小時內)
- ⭐ 高優先級 (本週內)
- 📅 一般 (兩週內)
- 🔖 低優先級 (一個月內)

### 截止日期格式
- `明天`, `後天`, `今天`
- `週一`, `週二`, `下週三`
- `2天後`, `1週後`
- `12月25日`, `2024-12-25`

---

*最後更新: 2025-07-21*  
*系統狀態: 🟢 正常運行*  
*下次檢查: 每5分鐘*
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(example_content)
    
    print(f"✅ 已創建示例任務文件: {file_path}")

def check_github_config() -> bool:
    """檢查是否配置了 GitHub 同步"""
    required_vars = ['GITHUB_TOKEN', 'GITHUB_REPO_OWNER', 'GITHUB_REPO_NAME']
    return all(os.getenv(var) for var in required_vars)

def get_current_time() -> str:
    """獲取當前時間字符串"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

if __name__ == "__main__":
    print("🎯 檢查 Python 環境...")
    
    # 檢查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    # 檢查依賴
    try:
        import psutil
        import aiohttp
        import watchdog
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("請執行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 環境檢查通過")
    
    # 檢查是否配置了 GitHub（可選）
    if check_github_config():
        print("✅ GitHub 同步已配置")
    else:
        print("ℹ️ GitHub 同步未配置（可選功能）")
        print("   如需啟用，請設定環境變數: GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME")
    
    print("\n🚀 啟動 Claude Auto Developer...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程式已終止")
    except Exception as e:
        print(f"\n💥 啟動失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)