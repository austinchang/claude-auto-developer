# 🤖 Claude Auto Developer - 智能專案開發自動化系統

**讓 Claude Code 在晚上也能工作的革命性開發工具**

## 🎯 系統概述

Claude Auto Developer 是一個能透過單一指令管理開發任務，並自動執行多執行緒並行開發的智能系統。使用者只需要用簡單的指令描述需求，系統就會自動完成從需求分析到程式碼實作的完整開發流程。

## ✨ 核心特色

- **🎯 單指令操作** - 一行命令即可新增開發任務
- **🧠 智能計畫清單** - 自動記錄和管理所有開發需求
- **⚡ 多執行緒並行** - 同時開發多個功能或專案
- **⏰ 時間約束開發** - 在指定時間內完成開發任務
- **🤖 全自動化流程** - 從需求分析到部署上線
- **🌙 夜間自主開發** - 24/7 背景開發，睡覺時也在工作
- **🌐 GitHub 遠端協作** - 任何地方編輯 TASKS.md，自動同步執行
- **🔧 智能資源管理** - 動態調整資源使用，不干擾正常工作

## 🚀 快速開始

### 安裝
```bash
# 克隆專案
git clone https://github.com/austinchang/claude-auto-developer.git
cd claude-auto-developer

# 安裝依賴
pip install -r requirements.txt

# 安裝全局指令
python setup.py install
```

### 基本使用
```bash
# 新增開發任務
claude-auto add "為 power_meter_gui 增加 AI 預測功能" --deadline "2天" --priority "high"

# 快速開發模式（跳過計畫清單）
claude-auto quick "創建電商網站" --priority high --mode project

# 查看計畫清單
claude-auto list

# 啟動自動開發
claude-auto start

# 檢查進度
claude-auto status
```

### 🌐 GitHub 遠端任務管理

**設定 GitHub 同步（推薦方式）:**

1. **創建 GitHub 倉庫用於任務管理:**
```bash
# 在 GitHub 上創建一個新倉庫，例如: your-tasks
# 然後設定環境變數
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO_OWNER="your_username"
export GITHUB_REPO_NAME="your-tasks"
export GITHUB_TASKS_FILE="TASKS.md"
```

2. **編輯遠端任務文件:**
   - 在 GitHub 倉庫中創建或編輯 `TASKS.md` 文件
   - 使用標準的任務格式（見下方示例）
   - 系統會每 5 分鐘自動同步並執行新任務

3. **任務文件格式示例:**
```markdown
# 🤖 開發任務清單

## 🔥 緊急項目 (24小時內)
- [ ] **修復支付 Bug** | 截止日期: 明天 | 技術: Python + FastAPI | 描述: 修復第三方支付介面問題

## ⭐ 高優先級 (本週內)  
- [ ] **AI 聊天功能** | 截止日期: 週五 | 技術: OpenAI + React | 描述: 整合 GPT-4 聊天機器人
```

4. **本地 TASKS.md 位置:**
   - 本地文件位置: `/home/tengjung_chang/TASKS.md`
   - 可以直接編輯本地文件，也會自動同步到 GitHub

### 🌙 夜間自主開發

**24/7 背景開發設定:**

```bash
# 啟動夜間開發引擎
python -m claude_auto_developer.autonomous_engine.night_developer

# 或在 Python 中使用
from claude_auto_developer.autonomous_engine.night_developer import NightDeveloper, NightConfig
from datetime import time

config = NightConfig(
    night_start_time=time(22, 0),    # 晚上 10 點開始工作
    night_end_time=time(6, 0),       # 早上 6 點結束
    max_cpu_usage=0.8,               # 最大 CPU 使用率 80%
    github_sync_enabled=True         # 啟用 GitHub 同步
)

night_dev = NightDeveloper(config)
await night_dev.start()
```

**夜間開發特色:**
- **用戶活動檢測**: 自動檢測用戶是否在使用電腦
- **智能資源調配**: 在夜間最大化資源使用，白天隱藏模式
- **自動任務過濾**: 只執行適合自動化的任務
- **進度自動更新**: 完成後自動更新 TASKS.md 狀態
- **GitHub 自動同步**: 定期同步遠端任務列表

## 🏗️ 系統架構

### 核心模組
```
claude-auto-developer/
├── src/
│   ├── task_manager/           # 任務管理核心
│   │   ├── task_analyzer.py   # 需求分析器
│   │   ├── task_planner.py    # 任務規劃器
│   │   ├── priority_manager.py # 優先級管理
│   │   └── deadline_tracker.py # 時間追蹤
│   ├── execution_engine/       # 執行引擎
│   │   ├── thread_manager.py   # 執行緒管理
│   │   ├── resource_allocator.py # 資源分配
│   │   ├── dependency_resolver.py # 依賴解析
│   │   └── parallel_executor.py # 並行執行器
│   ├── ai_integration/         # AI 整合
│   │   ├── code_generator.py   # 代碼生成
│   │   ├── requirement_parser.py # 需求解析
│   │   ├── tech_selector.py    # 技術選擇
│   │   └── quality_checker.py  # 品質檢查
│   └── monitoring/            # 監控系統
│       ├── progress_tracker.py # 進度追蹤
│       ├── performance_monitor.py # 效能監控
│       └── notification_system.py # 通知系統
├── config/                    # 配置目錄
├── logs/                      # 日誌目錄
├── output/                    # 生成的專案
└── tools/                     # 輔助工具
```

## 🎯 使用情境

### 情境 1：日常功能開發
```bash
# 早上上班前設定
claude-auto add "網站新增用戶評論功能" --deadline "今天下班前"
claude-auto add "修復登入頁面的響應式問題" --deadline "2小時"
claude-auto start
```

### 情境 2：大型專案開發
```bash
# 設定一週的開發計畫
claude-auto add "電商平台：商品管理系統" --deadline "3天"
claude-auto add "電商平台：購物車功能" --deadline "2天" 
claude-auto add "電商平台：支付整合" --deadline "2天"
claude-auto start --mode "project"
```

### 情境 3：緊急需求
```bash
# 緊急修復
claude-auto add "修復生產環境數據庫連線問題" --priority "urgent" --deadline "30分鐘"
# 系統會自動暫停其他任務，全力處理緊急需求
```

## 🔧 主要指令

### 基本操作
```bash
# 新增開發任務
claude-auto add "功能描述" --deadline "時間" --priority "優先級"

# 查看任務清單
claude-auto list

# 查看詳細進度
claude-auto status --detailed

# 啟動自動開發
claude-auto start

# 暫停/恢復
claude-auto pause
claude-auto resume
```

### 進階功能
```bash
# 調整任務優先級
claude-auto priority "任務ID" --level "high"

# 修改 deadline
claude-auto deadline "任務ID" --extend "2天"

# 檢查執行緒狀態
claude-auto threads

# 查看資源使用情況
claude-auto resources
```

## 🧠 智能特性

### 1. 需求智能分析
- 自動識別技術需求（前端/後端/資料庫等）
- 評估開發複雜度和時間
- 選擇最適合的技術棧
- 生成詳細的開發計畫

### 2. 多執行緒策略
- **並行開發**：同時進行前端和後端開發
- **流水線作業**：一個功能完成後自動開始下一個
- **資源優化**：根據系統負載動態調整執行緒數量
- **衝突避免**：檢測檔案和資源衝突，自動協調

### 3. 時間管理
- **智能排程**：根據 deadline 和依賴關係最佳化執行順序
- **進度預測**：基於當前進度預測完成時間
- **自動調整**：時間緊迫時簡化非核心功能
- **緊急模式**：高優先級任務可搶占所有資源

## 📊 監控與回報

### 實時監控
- 每個執行緒的開發進度
- 資源使用情況（CPU、記憶體、磁碟）
- 預估完成時間
- 品質檢查結果

### 自動通知
- 任務完成通知
- Deadline 預警
- 錯誤和異常報告
- 每日進度報告

## 🔒 安全與品質保證

- **代碼審查**：自動進行代碼品質檢查
- **測試自動化**：自動生成和執行測試
- **版本控制**：所有變更自動提交到 Git
- **備份機制**：開發過程中自動備份
- **回滾功能**：出現問題時可快速回滾

## 🔄 與 Austin Dev Config 整合

本專案已完全整合到 Austin Dev Config 生態系統：

- **sync-all 同步**：與其他專案一起自動同步
- **VS Code 工作區**：包含在統一的開發環境中
- **全局指令**：可在任何目錄使用
- **跨電腦同步**：在家裡和辦公室都能使用

## 🛠️ 技術棧

- **Python 3.8+** - 主要開發語言
- **APScheduler** - 高級排程系統
- **SQLite** - 任務狀態管理
- **Jinja2** - 模板引擎
- **Click** - CLI 介面
- **Systemd** - 系統服務整合

## 📈 版本資訊

**當前版本**: 1.0.0-alpha  
**最後更新**: 2025-07-19  
**開發者**: Claude Code Plan Mode  
**License**: MIT

---

> 💡 **革命性突破**: 現在您真的可以「睡覺時也在開發」！設定好任務，早上醒來就有新功能等著您。

## 🚀 立即開始使用

### 方法一：基本本地開發

```bash
# 1. 進入專案目錄
cd /home/tengjung_chang/austin-dev-config/claude-auto-dev

# 2. 啟動虛擬環境
source venv/bin/activate

# 3. 快速測試
python main.py quick "創建一個計算機程式" --priority high

# 4. 查看本地任務文件
cat /home/tengjung_chang/TASKS.md
```

### 方法二：完整 GitHub 同步設定

```bash
# 1. 設定 GitHub 環境變數（替換為你的資訊）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_REPO_OWNER="austinchang"  
export GITHUB_REPO_NAME="claude-auto-developer-tasks"
export GITHUB_TASKS_FILE="TASKS.md"

# 2. 測試 GitHub 同步
python -c "
from claude_auto_developer.file_interface.github_sync import GitHubTaskSync
import asyncio

async def test():
    sync = GitHubTaskSync.from_env()
    result = await sync.sync_once()
    print(f'同步結果: {result.action} - {result.message}')

asyncio.run(test())
"

# 3. 啟動夜間開發引擎
python -c "
from claude_auto_developer.autonomous_engine.night_developer import NightDeveloper
import asyncio

async def start_night_dev():
    night_dev = NightDeveloper()
    await night_dev.start()
    print('夜間開發引擎已啟動！')
    # 運行 5 分鐘測試
    await asyncio.sleep(300)
    night_dev.stop()

asyncio.run(start_night_dev())
"
```

### 方法三：一鍵完整啟動

```bash
# 創建啟動腳本
cat > start_claude_dev.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, 'src')

from claude_auto_developer.autonomous_engine.night_developer import NightDeveloper, NightConfig
from claude_auto_developer.file_interface.github_sync import GitHubTaskSync
from datetime import time

async def main():
    print("🤖 啟動 Claude Auto Developer...")
    
    # 設定夜間開發配置
    config = NightConfig(
        night_start_time=time(22, 0),
        night_end_time=time(6, 0),
        max_cpu_usage=0.8,
        github_sync_enabled=True,
        sync_interval=300  # 5分鐘同步一次
    )
    
    # 創建並啟動夜間開發引擎
    night_dev = NightDeveloper(config)
    
    print("✅ 啟動中...")
    await night_dev.start()
    
    print("🌟 Claude Auto Developer 已啟動！")
    print("📝 編輯 /home/tengjung_chang/TASKS.md 或 GitHub 上的 TASKS.md 來添加任務")
    print("🌙 系統將在夜間自動執行開發任務")
    print("⚡ 按 Ctrl+C 停止")
    
    try:
        # 保持運行
        while True:
            await asyncio.sleep(60)
            status = night_dev.get_status()
            print(f"📊 狀態: {status['working_mode']} | 任務: {status['schedule_status']['task_counts']['running']} 個執行中")
    except KeyboardInterrupt:
        print("\n🛑 停止中...")
        night_dev.stop()
        print("✅ 已停止")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# 執行
python start_claude_dev.py
```

### 📋 TASKS.md 文件示例

你的任務文件（`/home/tengjung_chang/TASKS.md` 或 GitHub 上）應該看起來像這樣：

```markdown
# 🤖 Claude Auto Developer - 開發任務清單

## 🔥 緊急項目 (24小時內)
- [ ] **修復網站登入問題** | 截止日期: 今天下午 | 技術: Python + FastAPI | 描述: 修復用戶登入介面的 session 超時問題 | 時間: 2小時

## ⭐ 高優先級 (本週內)
- [ ] **個人作品展示網站** | 截止日期: 週五 | 技術: React + TypeScript | 描述: 創建響應式個人網站，包含作品集和聯絡表單 | 時間: 2天
- [ ] **股票價格監控工具** | 截止日期: 週四 | 技術: Python + yfinance + tkinter | 描述: 開發 GUI 應用程式監控指定股票價格變化並發送通知 | 時間: 1天
- [ ] **AI 聊天機器人** | 截止日期: 週日 | 技術: OpenAI + Streamlit | 描述: 整合 GPT API 創建智能客服聊天介面 | 時間: 1.5天

## 📅 一般項目 (兩週內)
- [ ] **數據分析儀表板** | 截止日期: 下週三 | 技術: Python + Pandas + Plotly | 描述: 創建互動式數據可視化儀表板 | 時間: 3天
- [ ] **REST API 後端服務** | 截止日期: 2週後 | 技術: FastAPI + PostgreSQL + Docker | 描述: 建立完整的用戶管理 API | 時間: 1週

---
*系統會自動監控此文件並執行新增的任務*
```

### 🎯 任務格式詳細說明

**標準格式:**
```markdown
- [ ] **任務標題** | 截止日期: XXX | 技術: XXX | 描述: XXX | 時間: XXX
```

**各欄位說明:**
- `**任務標題**`: 簡潔明確的任務名稱
- `截止日期`: 支援多種格式 (明天、週五、2024-12-25 等)
- `技術`: 使用的技術棧 (Python、React、Docker 等)
- `描述`: 詳細的需求說明
- `時間`: 預估開發時間 (2小時、1天、1週 等)

**適合自動化的任務類型:**
✅ **推薦**: Web 應用、API 開發、數據處理、GUI 工具  
✅ **推薦**: 自動化腳本、爬蟲程式、簡單遊戲  
⚠️ **謹慎**: 需要設計決策、複雜業務邏輯的項目  
❌ **避免**: 需要人工確認、測試、部署的任務

**範例任務模板:**

```markdown
## ⭐ 高優先級範例

# 簡單工具開發
- [ ] **密碼生成器** | 截止日期: 明天 | 技術: Python + tkinter | 描述: 創建 GUI 密碼生成工具，支援自定義長度和字符集 | 時間: 2小時

# Web 應用開發  
- [ ] **待辦事項應用** | 截止日期: 週末 | 技術: React + Node.js + MongoDB | 描述: 完整的 CRUD 待辦事項管理系統 | 時間: 1天

# 數據處理
- [ ] **CSV 數據分析器** | 截止日期: 週三 | 技術: Python + Pandas + Matplotlib | 描述: 自動分析 CSV 檔案並生成統計圖表 | 時間: 4小時

# API 開發
- [ ] **天氣 API 服務** | 截止日期: 週五 | 技術: FastAPI + requests | 描述: 整合第三方天氣 API 並提供統一介面 | 時間: 3小時
```

**🎉 現在你可以開始使用了！編輯任務文件，然後看著 Claude 自動為你開發程式！**

## 🤝 參與貢獻

歡迎提交 Issue 和 Pull Request！

- **GitHub Issues**: [問題回報](https://github.com/austinchang/claude-auto-developer/issues)
- **Email**: austin680909@gmail.com
- **專案主頁**: https://github.com/austinchang/claude-auto-developer