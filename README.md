# 🤖 Claude Auto Developer - 智能自主開發系統

**真正的 24/7 自動化開發工具 - 讓 AI 在你睡覺時也能開發程式！**

[![GitHub](https://img.shields.io/badge/GitHub-claude--auto--developer-blue?logo=github)](https://github.com/austinchang/claude-auto-developer)
[![Tasks](https://img.shields.io/badge/GitHub-任務管理-green?logo=github)](https://github.com/austinchang/claude-auto-developer-tasks)
[![Status](https://img.shields.io/badge/Status-生產就緒-success)]()

---

## 🎯 系統概述

Claude Auto Developer 是一個革命性的 AI 自動化開發系統，能夠：

- 📝 **智能任務解析** - 自動理解你的開發需求
- 🔄 **自動同步檢測** - 監控 GitHub 和本地任務變化  
- 🌙 **24/7 夜間開發** - 真正的背景服務，睡覺時也在工作
- 🧠 **多 AI 模型整合** - Claude + GPT-4 + Gemini 協同開發
- ⚡ **智能資源管理** - 根據用戶活動調整資源使用
- 🚀 **全自動化流程** - 從需求分析到程式碼部署

---

## ✨ 核心特色

### 🔥 **真正的自主開發**
- **智能任務解析**: 自動分析需求，選擇最佳技術棧
- **24/7 背景執行**: 不占用終端機，真正的背景服務
- **用戶活動檢測**: 白天隱藏模式，夜間全力開發
- **自動狀態同步**: 完成狀態自動更新到 GitHub

### 🌐 **GitHub 遠端協作**
- **雙向同步**: 本地 ↔ GitHub 自動同步
- **任何地方編輯**: 在 GitHub 上編輯任務，5分鐘內自動執行
- **自動提交**: 完成的專案自動 Git commit 和推送
- **進度追蹤**: 即時更新任務執行狀態

### 🧠 **多 AI 整合**
- **Claude 3.5 Sonnet**: 主要開發和程式碼生成
- **GPT-4**: 複雜邏輯分析和架構設計
- **Gemini Pro**: 品質檢查和程式碼優化
- **智能模型選擇**: 根據任務類型自動選擇最佳 AI

### 🤖 **全自動執行** (新功能)
- **自動環境建置**: 創建虛擬環境、安裝依賴
- **自動測試執行**: 發現並執行測試、自動修復簡單錯誤
- **自動部署**: 支援 Docker、Heroku、Vercel 等多種部署方式
- **實時監控**: 健康檢查、性能監控、日誌記錄

---

## 🚀 快速開始

### 📦 環境準備

**1. 進入專案目錄**
```bash
cd /home/tengjung_chang/austin-dev-config/claude-auto-dev
```

**2. 啟動虛擬環境**
```bash
source venv/bin/activate
```

**3. 安裝依賴 (如需要)**
```bash
pip install -r requirements.txt
```

### ⚡ 一鍵啟動 (推薦)

**快捷命令設置** (已自動配置):
```bash
claude-status      # 查看服務狀態
claude-start       # 啟動背景服務
claude-stop        # 停止服務
claude-logs        # 查看即時日誌
claude-edit        # 編輯任務文件
claude-dir         # 進入專案目錄
```

**立即啟動**:
```bash
claude-start       # 啟動背景服務
claude-status      # 確認運行狀態
```

### 📝 三種任務編輯方式

**方式1: GitHub 遠端編輯 (推薦)**
```bash
# 訪問 GitHub 任務管理頁面
https://github.com/austinchang/claude-auto-developer-tasks/blob/main/TASKS.md
```

**方式2: 本地快速編輯**
```bash
claude-edit        # 使用預設編輯器
# 或直接編輯
nano /home/tengjung_chang/TASKS.md
```

**方式3: 專案目錄操作**
```bash
cd /home/tengjung_chang/austin-dev-config/claude-auto-dev
python claude_service.py start
python claude_service.py status
```

---

## 📋 任務格式標準

### 基本格式
```markdown
- [ ] **任務標題** | 截止日期: XXX | 技術: XXX | 描述: XXX | 時間: XXX
```

### 優先級分類
```markdown
## 🔥 緊急項目 (24小時內)
- [ ] **修復支付 Bug** | 截止日期: 今天下午 | 技術: Python + FastAPI | 描述: 修復第三方支付介面連接失敗問題 | 時間: 3小時

## ⭐ 高優先級 (本週內)  
- [ ] **個人作品集網站** | 截止日期: 週五 | 技術: React + TypeScript + Tailwind | 描述: 創建響應式個人網站，包含專案展示、技能介紹、聯絡表單 | 時間: 2天

## 📅 一般項目 (兩週內)
- [ ] **資料分析儀表板** | 截止日期: 下週三 | 技術: Python + Streamlit + Plotly | 描述: 創建互動式數據可視化工具，支援 CSV 上傳和圖表生成 | 時間: 3天

## 🔖 低優先級 (一個月內)
- [ ] **移動端原型** | 截止日期: 月底 | 技術: React Native + Expo | 描述: 開發跨平台移動應用 MVP 版本 | 時間: 1週
```

---

## 🤖 自動執行功能

### ⚡ 執行流程
Claude Auto Developer 現在支援完整的自動執行流程：

1. **📝 程式碼生成** - 智能生成專案代碼
2. **🔧 環境建置** - 自動創建虛擬環境、安裝依賴
3. **🧪 自動測試** - 執行測試、自動修復錯誤
4. **🚀 自動部署** - 支援多種部署方式
5. **🏥 健康監控** - 服務狀態檢查、性能監控

### 📋 執行參數配置
在任務描述中可以添加執行參數：

```markdown
- [ ] **Web API 服務** | 截止: 今天 | 技術: FastAPI | 描述: 創建 REST API 服務 docker | 時間: 2小時
```

**支援的參數：**
- `docker` - 使用 Docker 部署
- `heroku` - 部署到 Heroku
- `vercel` - 部署到 Vercel
- `no_auto_run` - 禁用自動執行
- `no_test` - 跳過測試階段
- `unittest` - 使用 unittest 測試框架

### 🔧 自動執行組件

#### AutoExecutor - 環境管理器
- ✅ 自動創建虛擬環境
- ✅ 智能安裝依賴套件
- ✅ 啟動專案服務
- ✅ 健康狀態檢查

#### TestRunner - 測試執行器
- ✅ 自動發現測試檔案
- ✅ 支援多種測試框架 (pytest, unittest, nose)
- ✅ 自動修復簡單錯誤
- ✅ 生成測試報告

#### DeploymentManager - 部署管理器
- ✅ Docker 容器化部署
- ✅ Heroku 雲端部署
- ✅ Vercel 前端部署
- ✅ AWS Lambda 無伺服器部署
- ✅ 本地服務部署

### 📊 執行報告
每次自動執行完成後會生成詳細報告：
- `EXECUTION_REPORT.md` - 環境建置報告
- `TEST_REPORT.md` - 測試執行報告
- `DEPLOYMENT_REPORT.md` - 部署狀態報告

---

## 🛠️ 服務管理

### 📊 狀態監控
```bash
# 查看服務狀態
claude-status

# 查看即時日誌 (最後50行)
claude-logs

# 查看詳細日誌文件
tail -f logs/claude_auto_dev_$(date +%Y%m%d).log
```

### 🔄 服務控制
```bash
# 啟動背景服務
claude-start

# 停止服務
claude-stop

# 重新啟動
python claude_service.py restart

# 查看幫助
python claude_service.py help
```

### 🔧 進階操作
```bash
# 進入專案目錄
claude-dir

# 手動啟動 (前台模式)
python start_claude_dev.py

# 直接背景啟動
python run_background.py &

# 檢查進程
ps aux | grep claude
```

---

## 🌙 自動化工作模式

### 🌓 **夜間模式** (22:00 - 06:00)
- **資源使用**: 最大化 (CPU 80%, 記憶體 70%)
- **並行任務**: 最多 2 個同時執行
- **執行策略**: 處理所有優先級任務
- **自動提交**: Git commit 和推送到 GitHub

### ☀️ **白天模式** (06:00 - 22:00)
- **用戶活躍時**: 隱藏模式 (CPU < 30%)
- **用戶空閒時**: 積極模式 (CPU < 80%)  
- **智能檢測**: 避免干擾正常工作
- **動態調整**: 根據系統負載自動調整

### 🔄 **自動同步機制**
- **GitHub 檢查**: 每 5 分鐘檢查遠端變化
- **本地監控**: 即時監控文件變化
- **差異分析**: 自動識別新增、修改的任務
- **狀態更新**: 完成後自動同步回 GitHub

---

## 🎯 適合自動化的任務類型

### ✅ **強烈推薦**
- **Web 應用開發**: React, Vue, Angular 前端專案
- **API 後端服務**: FastAPI, Express, Django REST API
- **數據處理工具**: Python Pandas, 數據分析腳本
- **自動化腳本**: 檔案處理, 系統管理, 爬蟲程式
- **小型工具**: CLI 工具, GUI 應用, 實用程式

### ⚠️ **需要詳細描述**
- **複雜業務邏輯**: 需要明確的需求和流程描述
- **第三方整合**: 提供 API 文檔和認證資訊
- **資料庫設計**: 明確的資料結構和關聯需求

### ❌ **不適合自動化**
- **需要人工決策**: 設計評審, 需求確認
- **需要測試驗證**: 生產環境部署, 用戶驗收測試
- **需要外部協調**: 與他人協作或需要確認的任務

---

## 🏗️ 系統架構

### 核心模組
```
claude-auto-developer/
├── src/claude_auto_developer/
│   ├── ai_integration/           # AI 模型整合
│   │   ├── model_manager.py      # 多模型管理
│   │   ├── code_generator_v2.py  # 智能程式碼生成
│   │   ├── quality_assessor.py   # 品質評估
│   │   └── architecture_designer.py # 架構設計
│   ├── autonomous_engine/        # 自主引擎
│   │   ├── night_developer.py    # 夜間開發引擎
│   │   ├── schedule_manager.py   # 智能排程管理
│   │   └── resource_optimizer.py # 資源優化器
│   ├── file_interface/           # 檔案介面
│   │   ├── task_file_parser.py   # 任務解析器
│   │   ├── github_sync.py        # GitHub 同步
│   │   ├── file_monitor.py       # 檔案監控
│   │   └── progress_updater.py   # 進度更新
│   └── task_manager/             # 任務管理
├── claude_service.py             # 🎯 統一服務控制器
├── run_background.py             # 背景服務啟動器
├── stop_background.py            # 服務停止器
├── start_claude_dev.py           # 前台啟動器
├── logs/                         # 日誌目錄
└── output/                       # 生成專案目錄
```

### 🔧 服務控制腳本
- **`claude_service.py`**: 統一服務控制 (推薦使用)
- **`run_background.py`**: 真正的背景服務
- **`start_claude_dev.py`**: 前台顯示模式
- **快捷命令**: `claude-*` 全局可用

---

## 🌐 GitHub 整合

### 📊 任務管理儲存庫
- **GitHub URL**: https://github.com/austinchang/claude-auto-developer-tasks
- **主要文件**: [TASKS.md](https://github.com/austinchang/claude-auto-developer-tasks/blob/main/TASKS.md)
- **編輯連結**: [直接編輯](https://github.com/austinchang/claude-auto-developer-tasks/edit/main/TASKS.md)

### 🔄 同步配置
```bash
# 環境變數 (已配置在 .env 文件中)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO_OWNER=austinchang
GITHUB_REPO_NAME=claude-auto-developer-tasks
GITHUB_TASKS_FILE=TASKS.md
```

### 📝 工作流程
1. **編輯任務**: 在 GitHub 或本地編輯 TASKS.md
2. **自動檢測**: 5分鐘內檢測到變化
3. **解析任務**: 自動分析新增或修改的任務
4. **排程執行**: 根據優先級和截止時間排程
5. **生成程式碼**: AI 自動開發並測試
6. **狀態更新**: 完成狀態同步回 GitHub
7. **自動提交**: 專案推送到對應儲存庫

---

## 📊 監控與日誌

### 📄 日誌系統
```bash
# 查看即時日誌
claude-logs

# 日誌文件位置
ls logs/claude_auto_dev_*.log

# 監控特定日誌
tail -f logs/claude_auto_dev_$(date +%Y%m%d).log
```

### 🔍 狀態檢查
```bash
# 完整狀態檢查
claude-status

# 檢查進程
ps aux | grep claude

# 檢查 PID 文件
cat claude_auto_dev.pid
```

### 📈 效能監控
- **CPU 使用率**: 自動監控和調整
- **記憶體使用**: 動態資源分配
- **任務完成率**: 統計成功/失敗比例
- **夜間工作時間**: 記錄自動開發時數

---

## 🚨 故障排除

### 常見問題

**1. 服務無法啟動**
```bash
# 檢查 Python 環境
claude-dir && source venv/bin/activate
python --version

# 重新安裝依賴
pip install -r requirements.txt

# 清理 PID 文件
rm -f claude_auto_dev.pid
```

**2. GitHub 同步失敗**
```bash
# 檢查網路連接
curl -I https://api.github.com

# 檢查環境變數
cat .env | grep GITHUB

# 測試 GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

**3. 任務無法執行**
```bash
# 檢查任務格式
claude-edit

# 查看詳細錯誤
claude-logs

# 重新啟動服務
python claude_service.py restart
```

**4. 權限問題**
```bash
# 設置腳本權限
chmod +x *.py

# 檢查文件權限
ls -la /home/tengjung_chang/TASKS.md
```

---

## 💡 最佳實踐

### 撰寫高質量任務
1. **明確的功能描述**: 具體說明要實現什麼
2. **技術棧選擇**: 指定使用的程式語言和框架
3. **詳細需求**: 包含功能細節和預期行為
4. **合理時間估計**: 提供現實的開發時間

### 系統使用技巧
1. **優先級管理**: 合理分配任務優先級
2. **定期檢查**: 監控系統運行狀況
3. **任務分解**: 將複雜任務拆分成小任務
4. **日誌監控**: 定期查看執行日誌

### 效能優化
1. **夜間模式**: 充分利用夜間時間開發
2. **資源管理**: 避免在工作時間干擾
3. **任務排程**: 合理安排任務執行順序
4. **自動化**: 盡量使用自動化功能

---

## 🔗 相關連結

### 📁 **本地路徑**
- **專案目錄**: `/home/tengjung_chang/austin-dev-config/claude-auto-dev`
- **任務文件**: `/home/tengjung_chang/TASKS.md`
- **日誌目錄**: `logs/claude_auto_dev_*.log`
- **配置文件**: `.env`

### 🌐 **GitHub 連結**
- **任務管理**: https://github.com/austinchang/claude-auto-developer-tasks
- **主專案**: https://github.com/austinchang/claude-auto-developer
- **編輯任務**: https://github.com/austinchang/claude-auto-developer-tasks/edit/main/TASKS.md
- **問題回報**: https://github.com/austinchang/claude-auto-developer/issues

### 📚 **文檔**
- **使用指南**: [USAGE_GUIDE.md](./USAGE_GUIDE.md)
- **快速參考**: 本 README
- **API 文檔**: 程式碼註釋中

---

## 🎉 立即開始

### 🚀 **3 步驟開始使用**

**步驟 1: 檢查服務狀態**
```bash
claude-status
```

**步驟 2: 添加你的第一個任務**
- 訪問: https://github.com/austinchang/claude-auto-developer-tasks/edit/main/TASKS.md
- 或執行: `claude-edit`

**步驟 3: 等待自動執行**
- 監控日誌: `claude-logs`
- 查看進度: 任務狀態會自動更新

### 📋 **任務範例**
```markdown
## ⭐ 高優先級 (本週內)

- [ ] **我的第一個自動化專案** | 截止日期: 明天 | 技術: Python + FastAPI | 描述: 創建一個簡單的 TODO API，支援增刪改查功能，包含 SQLite 資料庫和 RESTful 介面 | 時間: 4小時
```

### 🎯 **期待結果**
- ✅ 自動分析需求
- ✅ 選擇合適技術棧
- ✅ 生成完整專案結構
- ✅ 實作所有功能
- ✅ 自動測試和除錯
- ✅ Git 提交和推送

**🌟 享受真正的 24/7 自動化開發體驗！**

---

## 🤝 參與貢獻

### 問題回報
- **GitHub Issues**: [回報問題](https://github.com/austinchang/claude-auto-developer/issues)
- **Email**: austin680909@gmail.com

### 功能請求
歡迎提交新功能建議和改進意見！

---

## 📈 版本資訊

**當前版本**: 2.0.0 - 完整背景服務版  
**最後更新**: 2025-07-21  
**開發者**: Claude Code Plan Mode  
**License**: MIT

### 🆕 **v2.0.0 新功能**
- ✅ 真正的背景服務運行
- ✅ 統一的服務控制介面
- ✅ 全局快捷命令支援
- ✅ 完整的日誌系統
- ✅ GitHub 雙向同步
- ✅ 智能工作模式切換

---

**💫 現在，AI 真的可以在你睡覺時幫你開發程式了！**

🚀 **立即開始**: `claude-start`  
📊 **查看狀態**: `claude-status`  
📝 **編輯任務**: https://github.com/austinchang/claude-auto-developer-tasks