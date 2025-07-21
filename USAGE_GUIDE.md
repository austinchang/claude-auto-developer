# 🤖 Claude Auto Developer - 完整使用指南

**真正的 24/7 自動開發系統 - 現在已完全就緒！**

## 🎉 系統狀態

✅ **完全配置完成** - 所有功能已啟用  
✅ **背景服務運行中** - PID: 檢查 `python claude_service.py status`  
✅ **GitHub 同步已啟用** - 每 5 分鐘自動檢查  
✅ **本地任務監控** - 即時檔案變化檢測  

---

## 🚀 立即開始使用

### 方法 1: 一鍵控制 (推薦)
```bash
# 進入專案目錄
cd /home/tengjung_chang/austin-dev-config/claude-auto-dev

# 查看服務狀態
python claude_service.py status

# 啟動背景服務 (如果未運行)
python claude_service.py start

# 查看即時日誌
python claude_service.py logs

# 編輯任務文件
python claude_service.py edit

# 停止服務
python claude_service.py stop
```

### 方法 2: GitHub 遠端編輯
1. **訪問**: https://github.com/austinchang/claude-auto-developer-tasks/blob/main/TASKS.md
2. **點擊** ✏️ 編輯按鈕
3. **添加任務** (使用標準格式)
4. **提交變更** - 5分鐘內自動執行

### 方法 3: 本地編輯
```bash
# 直接編輯本地任務文件
nano /home/tengjung_chang/TASKS.md

# 或使用 VS Code
code /home/tengjung_chang/TASKS.md
```

---

## 📋 任務格式標準

### 基本格式
```markdown
- [ ] **任務標題** | 截止日期: XXX | 技術: XXX | 描述: XXX | 時間: XXX
```

### 實際範例
```markdown
## ⭐ 高優先級 (本週內)

- [ ] **個人作品集網站** | 截止日期: 週五 | 技術: React + TypeScript + Tailwind | 描述: 創建響應式個人作品集，包含專案展示、技能介紹、聯絡表單，支援暗黑模式切換 | 時間: 2天

- [ ] **股票監控 API** | 截止日期: 週四 | 技術: Python + FastAPI + yfinance | 描述: 開發股票價格監控 REST API，支援多股票追蹤、價格警報、歷史數據查詢 | 時間: 1天
```

---

## 🔄 自動化工作流程

### 1. 任務檢測
- **GitHub 檢查**: 每 5 分鐘自動檢查遠端變化
- **本地監控**: 即時監控 `/home/tengjung_chang/TASKS.md` 變化
- **差異分析**: 自動識別新增、修改、刪除的任務

### 2. 智能排程
- **優先級排序**: 🔥 緊急 > ⭐ 高 > 📅 一般 > 🔖 低優先級
- **截止時間**: 自動計算時間緊迫度
- **資源分配**: 根據系統負載動態調整

### 3. 自動執行
- **夜間模式**: 22:00-06:00 全力開發
- **白天模式**: 用戶活動時降低資源使用
- **智能檢測**: 自動判斷用戶是否在使用電腦

### 4. 狀態更新
- **進度追蹤**: 自動更新任務狀態 (待執行 → 執行中 → 已完成)
- **GitHub 同步**: 完成狀態自動同步回 GitHub
- **錯誤處理**: 失敗任務標記並記錄錯誤原因

---

## 🛠️ 服務管理命令

### 基本控制
```bash
# 查看幫助
python claude_service.py help

# 服務狀態檢查
python claude_service.py status

# 啟動背景服務
python claude_service.py start

# 停止服務
python claude_service.py stop

# 重新啟動
python claude_service.py restart
```

### 監控和調試
```bash
# 查看最新日誌 (最後50行)
python claude_service.py logs

# 編輯任務文件
python claude_service.py edit

# 手動檢查 PID 文件
cat claude_auto_dev.pid

# 檢查進程
ps aux | grep python
```

---

## 📊 工作模式說明

### 🌙 夜間模式 (22:00-06:00)
- **資源使用**: 最大化 (CPU 80%, 記憶體 70%)
- **並行任務**: 最多 2 個同時執行
- **優先策略**: 處理所有等級的任務
- **提交機制**: 自動 Git commit 和推送

### ☀️ 白天模式 (06:00-22:00)
- **用戶活躍時**: 隱藏模式 (CPU < 30%)
- **用戶空閒時**: 積極模式 (CPU < 80%)
- **並行任務**: 1-3 個 (根據負載調整)
- **智能檢測**: 避免干擾正常工作

---

## 🎯 適合自動化的任務類型

### ✅ **強烈推薦**
- **Web 應用**: React, Vue, Angular 前端專案
- **API 服務**: FastAPI, Express, Django REST API
- **資料處理**: Python Pandas, 數據分析工具
- **自動化腳本**: 檔案處理, 系統管理, 爬蟲
- **小型工具**: CLI 工具, GUI 應用, 實用程式

### ⚠️ **需要詳細描述**
- **複雜業務邏輯**: 需要明確的需求和邏輯描述
- **第三方整合**: 提供 API 文檔和認證資訊
- **資料庫設計**: 明確的資料結構和關聯需求

### ❌ **不適合自動化**
- **需要人工決策**: 設計評審, 需求確認
- **需要測試驗證**: 生產環境部署, 用戶驗收
- **需要外部協調**: 與他人協作的任務

---

## 🔗 重要連結

### 📁 本地路徑
- **專案目錄**: `/home/tengjung_chang/austin-dev-config/claude-auto-dev`
- **任務文件**: `/home/tengjung_chang/TASKS.md`
- **日誌目錄**: `/home/tengjung_chang/austin-dev-config/claude-auto-dev/logs/`
- **配置文件**: `/home/tengjung_chang/austin-dev-config/claude-auto-dev/.env`

### 🌐 GitHub 連結
- **任務管理儲存庫**: https://github.com/austinchang/claude-auto-developer-tasks
- **主專案**: https://github.com/austinchang/claude-auto-developer
- **編輯任務**: https://github.com/austinchang/claude-auto-developer-tasks/edit/main/TASKS.md

---

## 🚨 故障排除

### 服務無法啟動
```bash
# 檢查 Python 環境
source venv/bin/activate
python --version

# 檢查依賴
pip install -r requirements.txt

# 檢查權限
chmod +x *.py

# 清理 PID 文件
rm -f claude_auto_dev.pid
```

### GitHub 同步失敗
```bash
# 檢查環境變數
echo $GITHUB_TOKEN
echo $GITHUB_REPO_OWNER

# 重新設置 .env 文件
nano .env

# 測試 GitHub 連接
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### 任務執行失敗
```bash
# 查看詳細日誌
python claude_service.py logs

# 檢查任務格式
cat /home/tengjung_chang/TASKS.md

# 重新啟動服務
python claude_service.py restart
```

---

## 💡 最佳實踐

### 撰寫高質量任務
1. **明確的目標**: 具體描述要實現的功能
2. **技術棧選擇**: 指定使用的程式語言和框架
3. **詳細需求**: 包含功能細節和預期行為
4. **合理時間**: 提供現實的時間估計

### 任務管理技巧
1. **優先級劃分**: 合理分配任務優先級
2. **截止時間**: 設定明確的完成時間
3. **分解複雜任務**: 將大任務拆分成小任務
4. **定期檢查**: 監控任務執行進度

### 系統維護
1. **定期查看日誌**: 了解系統運行狀況
2. **清理完成任務**: 定期整理任務清單
3. **更新依賴**: 保持系統依賴最新
4. **備份配置**: 定期備份重要配置

---

## 🎉 立即體驗

**現在一切都準備就緒！**

1. **檢查服務狀態**:
   ```bash
   python claude_service.py status
   ```

2. **添加你的第一個任務**:
   - 訪問: https://github.com/austinchang/claude-auto-developer-tasks/blob/main/TASKS.md
   - 點擊編輯，添加你的任務
   - 提交變更

3. **等待自動執行**:
   - 5分鐘內系統會檢測到變化
   - 自動開始開發你的專案
   - 完成後狀態會自動更新

4. **監控進度**:
   ```bash
   python claude_service.py logs
   ```

**🚀 享受真正的 24/7 自動化開發體驗！**

---

*最後更新: 2025-07-21*  
*版本: 2.0.0 - 完整背景服務版*  
*狀態: ✅ 生產就緒*