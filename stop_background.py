#!/usr/bin/env python3
"""
Claude Auto Developer - 背景服務停止器
"""

import os
import sys
import signal
from pathlib import Path

def stop_background_service():
    """停止背景服務"""
    current_dir = Path(__file__).parent
    pid_file = current_dir / "claude_auto_dev.pid"
    
    if not pid_file.exists():
        print("❌ 沒有找到運行中的 Claude Auto Developer 服務")
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        print(f"🔍 找到運行中的服務 (PID: {pid})")
        
        # 嘗試溫和停止
        print("🛑 正在停止服務...")
        os.kill(pid, signal.SIGTERM)
        
        # 等待一下
        import time
        time.sleep(2)
        
        # 檢查是否仍在運行
        try:
            os.kill(pid, 0)
            # 如果還在運行，強制停止
            print("⚠️ 服務未響應，強制停止...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        except OSError:
            # 進程已經停止
            pass
        
        # 清理 PID 文件
        if pid_file.exists():
            pid_file.unlink()
        
        print("✅ Claude Auto Developer 背景服務已停止")
        return True
        
    except (OSError, ValueError) as e:
        print(f"❌ 停止服務失敗: {e}")
        # 清理無效的 PID 文件
        if pid_file.exists():
            pid_file.unlink()
        return False

def show_status():
    """顯示服務狀態"""
    current_dir = Path(__file__).parent
    pid_file = current_dir / "claude_auto_dev.pid"
    
    if not pid_file.exists():
        print("📊 狀態: ❌ 未運行")
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 檢查進程是否存在
        os.kill(pid, 0)
        print(f"📊 狀態: ✅ 運行中 (PID: {pid})")
        
        # 檢查日誌文件
        log_dir = current_dir / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("claude_auto_dev_*.log"))
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                print(f"📄 日誌文件: {latest_log}")
        
        print(f"📝 任務文件: /home/tengjung_chang/TASKS.md")
        print(f"🌐 GitHub: https://github.com/austinchang/claude-auto-developer-tasks")
        
        return True
        
    except (OSError, ValueError):
        print("📊 狀態: ❌ 未運行 (PID 文件無效)")
        # 清理無效的 PID 文件
        pid_file.unlink()
        return False

if __name__ == "__main__":
    print("🤖 Claude Auto Developer - 服務管理")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        success = stop_background_service()
        if not success:
            print("\n💡 提示:")
            print("   查看狀態: python stop_background.py status")
            print("   啟動服務: python run_background.py")
            sys.exit(1)