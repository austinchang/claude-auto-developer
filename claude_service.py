#!/usr/bin/env python3
"""
Claude Auto Developer - 服務控制器
一個腳本控制所有操作
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd_args):
    """執行命令"""
    try:
        result = subprocess.run(cmd_args, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False

def show_help():
    """顯示幫助"""
    print("""
🤖 Claude Auto Developer - 服務控制器

用法:
  python claude_service.py <command>

命令:
  start     - 啟動背景服務
  stop      - 停止背景服務  
  status    - 查看服務狀態
  restart   - 重新啟動服務
  logs      - 查看最新日誌
  edit      - 編輯任務文件

範例:
  python claude_service.py start    # 啟動背景服務
  python claude_service.py status   # 查看狀態
  python claude_service.py logs     # 查看日誌
""")

def start_service():
    """啟動服務"""
    print("🚀 啟動 Claude Auto Developer 背景服務...")
    
    # 檢查是否已經運行
    if run_command([sys.executable, "stop_background.py", "status"]):
        print("⚠️ 服務已經在運行中")
        return True
    
    # 啟動背景服務
    try:
        # 使用 nohup 在背景運行
        subprocess.Popen([
            "nohup", sys.executable, "run_background.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待一下讓服務啟動
        import time
        time.sleep(3)
        
        # 檢查是否成功啟動
        if run_command([sys.executable, "stop_background.py", "status"]):
            print("✅ 背景服務啟動成功！")
            print("💡 使用 'python claude_service.py status' 查看狀態")
            print("💡 使用 'python claude_service.py logs' 查看日誌")
            return True
        else:
            print("❌ 背景服務啟動失敗")
            return False
            
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        return False

def stop_service():
    """停止服務"""
    print("🛑 停止 Claude Auto Developer 背景服務...")
    return run_command([sys.executable, "stop_background.py"])

def show_status():
    """顯示狀態"""
    return run_command([sys.executable, "stop_background.py", "status"])

def restart_service():
    """重新啟動服務"""
    print("🔄 重新啟動 Claude Auto Developer...")
    stop_service()
    import time
    time.sleep(2)
    return start_service()

def show_logs():
    """顯示日誌"""
    log_dir = Path(__file__).parent / "logs"
    if not log_dir.exists():
        print("❌ 日誌目錄不存在")
        return False
    
    log_files = list(log_dir.glob("claude_auto_dev_*.log"))
    if not log_files:
        print("❌ 沒有找到日誌文件")
        return False
    
    # 獲取最新的日誌文件
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 顯示最新日誌: {latest_log}")
    print("=" * 50)
    
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 顯示最後 50 行
            for line in lines[-50:]:
                print(line.rstrip())
    except Exception as e:
        print(f"❌ 讀取日誌失敗: {e}")
        return False
    
    return True

def edit_tasks():
    """編輯任務文件"""
    tasks_file = Path("/home/tengjung_chang/TASKS.md")
    
    if not tasks_file.exists():
        print("❌ 任務文件不存在")
        print("💡 請先啟動服務以創建任務文件")
        return False
    
    # 嘗試使用不同的編輯器
    editors = ['code', 'nano', 'vim', 'vi']
    
    for editor in editors:
        try:
            subprocess.run([editor, str(tasks_file)], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print(f"❌ 無法找到編輯器，請手動編輯: {tasks_file}")
    print(f"🌐 或在 GitHub 上編輯: https://github.com/austinchang/claude-auto-developer-tasks")
    return False

def main():
    """主函數"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    # 切換到腳本目錄
    os.chdir(Path(__file__).parent)
    
    if command == "start":
        start_service()
    elif command == "stop":
        stop_service()
    elif command == "status":
        show_status()
    elif command == "restart":
        restart_service()
    elif command == "logs":
        show_logs()
    elif command == "edit":
        edit_tasks()
    elif command in ["help", "-h", "--help"]:
        show_help()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()

if __name__ == "__main__":
    main()