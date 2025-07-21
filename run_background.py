#!/usr/bin/env python3
"""
Claude Auto Developer - 背景服務啟動器
真正的背景執行，不占用終端機
"""

import asyncio
import sys
import os
import signal
import logging
from pathlib import Path
from datetime import datetime, time

# 添加 src 目錄到 Python 路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from claude_auto_developer.autonomous_engine.night_developer import NightDeveloper, NightConfig

# 設置日誌
log_dir = current_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"claude_auto_dev_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()  # 也輸出到控制台（啟動時）
    ]
)

logger = logging.getLogger(__name__)

class BackgroundService:
    """背景服務管理器"""
    
    def __init__(self):
        self.night_dev = None
        self.running = False
        
        # 設置信號處理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """處理停止信號"""
        logger.info(f"接收到停止信號 {signum}")
        self.stop()
        sys.exit(0)
    
    def check_github_config(self) -> bool:
        """檢查是否配置了 GitHub 同步"""
        required_vars = ['GITHUB_TOKEN', 'GITHUB_REPO_OWNER', 'GITHUB_REPO_NAME']
        
        # 首先檢查環境變數
        env_configured = all(os.getenv(var) for var in required_vars)
        
        # 如果環境變數沒有，檢查 .env 文件
        if not env_configured:
            env_file = current_dir / '.env'
            if env_file.exists():
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' in line and not line.strip().startswith('#'):
                                key, value = line.strip().split('=', 1)
                                if key.strip() in required_vars and value.strip():
                                    os.environ[key.strip()] = value.strip()
                    
                    # 再次檢查
                    env_configured = all(os.getenv(var) for var in required_vars)
                except Exception as e:
                    logger.warning(f"讀取 .env 文件失敗: {e}")
        
        return env_configured
    
    def create_tasks_file_if_needed(self):
        """如果需要的話創建 TASKS.md 文件"""
        tasks_file = Path("/home/tengjung_chang/TASKS.md")
        if not tasks_file.exists():
            logger.info("創建示例 TASKS.md 文件...")
            
            example_content = """# 🤖 Claude Auto Developer - 開發任務清單

> 此文件是您與 Claude Auto Developer 的溝通介面  
> 編輯此文件來新增、修改或檢查開發任務的進度  
> 系統會自動監控文件變化並開始執行任務  
> 🌐 GitHub 同步: https://github.com/austinchang/claude-auto-developer-tasks

---

## 🔥 緊急項目 (24小時內)

## ⭐ 高優先級 (本週內)

## 📅 一般項目 (兩週內)

## 🔖 低優先級 (一個月內)

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

---

*最後更新: """ + datetime.now().strftime('%Y-%m-%d') + """*  
*系統狀態: 🟢 正常運行*  
*自動同步: ✅ 已啟用 (每5分鐘)*
"""
            
            with open(tasks_file, 'w', encoding='utf-8') as f:
                f.write(example_content)
            
            logger.info(f"已創建示例任務文件: {tasks_file}")
    
    async def start(self):
        """啟動背景服務"""
        logger.info("🤖 Claude Auto Developer 背景服務啟動中...")
        
        # 檢查並創建必要文件
        self.create_tasks_file_if_needed()
        
        # 配置系統
        github_enabled = self.check_github_config()
        logger.info(f"GitHub 同步: {'✅ 已啟用' if github_enabled else '❌ 未配置'}")
        
        config = NightConfig(
            night_start_time=time(22, 0),        # 晚上 10 點開始夜間工作
            night_end_time=time(6, 0),           # 早上 6 點結束
            max_cpu_usage=0.8,                   # 最大 CPU 使用率 80%
            max_memory_usage=0.7,                # 最大記憶體使用率 70%
            github_sync_enabled=github_enabled,  # GitHub 同步
            sync_interval=300,                   # 5分鐘同步一次
            auto_commit_enabled=True,            # 啟用自動提交
            max_concurrent_tasks=2               # 最大並行任務數
        )
        
        # 創建並啟動夜間開發引擎
        self.night_dev = NightDeveloper(config)
        
        # 添加回調
        self.night_dev.add_callback('mode_change', self.on_mode_change)
        self.night_dev.add_callback('task_complete', self.on_task_complete)
        
        await self.night_dev.start()
        self.running = True
        
        logger.info("🌟 Claude Auto Developer 背景服務已啟動！")
        logger.info("📝 編輯 /home/tengjung_chang/TASKS.md 或 GitHub 上的 TASKS.md 來添加任務")
        logger.info("🌙 系統將在夜間自動執行開發任務")
        logger.info(f"📄 日誌文件: {log_file}")
        
        # 進入主循環
        try:
            await self.main_loop()
        except asyncio.CancelledError:
            logger.info("服務被取消")
        except Exception as e:
            logger.error(f"服務運行錯誤: {e}", exc_info=True)
        finally:
            self.stop()
    
    async def main_loop(self):
        """主運行循環"""
        last_status_time = datetime.now()
        
        while self.running:
            try:
                # 每小時記錄一次狀態
                now = datetime.now()
                if (now - last_status_time).total_seconds() > 3600:  # 1小時
                    status = self.night_dev.get_status()
                    mode = status.get('working_mode', 'unknown')
                    tasks = status.get('schedule_status', {}).get('task_counts', {})
                    
                    logger.info(f"📊 系統狀態: {mode} | "
                              f"執行中: {tasks.get('running', 0)} | "
                              f"等待: {tasks.get('scheduled', 0)} | "
                              f"已完成: {tasks.get('completed', 0)}")
                    
                    last_status_time = now
                
                # 等待下一個檢查週期
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                logger.error(f"主循環錯誤: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    def stop(self):
        """停止服務"""
        if not self.running:
            return
            
        logger.info("🛑 停止 Claude Auto Developer 背景服務...")
        self.running = False
        
        if self.night_dev:
            self.night_dev.stop()
        
        logger.info("✅ 背景服務已停止")
    
    def on_mode_change(self, old_mode, new_mode):
        """工作模式變更回調"""
        logger.info(f"🔄 工作模式變更: {old_mode.value} -> {new_mode.value}")
    
    def on_task_complete(self, task, success):
        """任務完成回調"""
        status = "✅ 完成" if success else "❌ 失敗"
        logger.info(f"📋 任務{status}: {task.original_task.title}")

def create_pid_file():
    """創建 PID 文件"""
    pid_file = current_dir / "claude_auto_dev.pid"
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    return pid_file

def remove_pid_file():
    """移除 PID 文件"""
    pid_file = current_dir / "claude_auto_dev.pid"
    if pid_file.exists():
        pid_file.unlink()

def is_already_running():
    """檢查是否已經有實例在運行"""
    pid_file = current_dir / "claude_auto_dev.pid"
    if not pid_file.exists():
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 檢查進程是否存在
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        # PID 文件存在但進程不存在，清理文件
        pid_file.unlink()
        return False

async def main():
    """主函數"""
    print("🔍 檢查運行狀態...")
    
    if is_already_running():
        print("❌ Claude Auto Developer 已經在背景運行中")
        print("   如需停止，請執行: python stop_background.py")
        sys.exit(1)
    
    print("✅ 可以啟動")
    
    # 創建 PID 文件
    pid_file = create_pid_file()
    
    try:
        service = BackgroundService()
        await service.start()
    except KeyboardInterrupt:
        logger.info("收到中斷信號")
    except Exception as e:
        logger.error(f"啟動失敗: {e}", exc_info=True)
    finally:
        remove_pid_file()

if __name__ == "__main__":
    print("🚀 Claude Auto Developer - 背景服務模式")
    print("=" * 50)
    
    # 檢查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    # 檢查依賴
    try:
        import aiohttp
        import psutil
        import watchdog
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("請執行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 環境檢查通過")
    print("🔄 啟動背景服務...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 服務已停止")
    except Exception as e:
        print(f"\n💥 啟動失敗: {e}")
        sys.exit(1)