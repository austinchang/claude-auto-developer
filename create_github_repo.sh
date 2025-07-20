#!/bin/bash

# GitHub 倉庫創建輔助腳本
# 處理 SSL 憑證問題的替代方案

echo "🚀 GitHub 倉庫創建輔助腳本"
echo "================================"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

show_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

show_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

show_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

PROJECT_NAME="claude-auto-developer"
GITHUB_USER="austinchang"
REPO_URL="https://github.com/${GITHUB_USER}/${PROJECT_NAME}.git"

show_info "專案名稱: $PROJECT_NAME"
show_info "GitHub 使用者: $GITHUB_USER"
show_info "倉庫 URL: $REPO_URL"

# 方法 1: 嘗試使用 GitHub CLI（忽略 SSL）
try_gh_cli() {
    show_info "嘗試使用 GitHub CLI 創建倉庫..."
    
    # 暫時忽略 SSL 驗證
    export GIT_SSL_NO_VERIFY=true
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    
    if gh repo create "${GITHUB_USER}/${PROJECT_NAME}" --public --source=. --remote=origin --push 2>/dev/null; then
        show_success "GitHub 倉庫創建成功！"
        return 0
    else
        show_warning "GitHub CLI 創建失敗"
        return 1
    fi
}

# 方法 2: 使用 curl 直接調用 GitHub API
try_api_create() {
    show_info "嘗試使用 GitHub API 創建倉庫..."
    
    # 檢查是否有 GitHub token
    if [ -z "$GITHUB_TOKEN" ]; then
        show_error "需要 GITHUB_TOKEN 環境變數"
        echo "請設定您的 GitHub Personal Access Token:"
        echo "export GITHUB_TOKEN=your_token_here"
        return 1
    fi
    
    # 創建倉庫的 JSON 資料
    local json_data='{
        "name": "'"$PROJECT_NAME"'",
        "description": "智能專案開發自動化系統 - 讓 Claude Code 在晚上也能工作",
        "homepage": "",
        "private": false,
        "has_issues": true,
        "has_projects": true,
        "has_wiki": true
    }'
    
    # 使用 curl 創建倉庫（忽略 SSL）
    local response=$(curl -k -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "$json_data" \
        "https://api.github.com/user/repos")
    
    if echo "$response" | grep -q '"clone_url"'; then
        show_success "GitHub 倉庫創建成功！"
        return 0
    else
        show_error "API 創建失敗"
        echo "回應: $response"
        return 1
    fi
}

# 方法 3: 手動指導
manual_guide() {
    show_info "提供手動創建指導..."
    
    echo ""
    echo "📋 手動創建 GitHub 倉庫步驟："
    echo "================================"
    echo ""
    echo "1. 🌐 前往 GitHub 網站:"
    echo "   https://github.com/new"
    echo ""
    echo "2. 📝 填寫倉庫資訊:"
    echo "   - Repository name: claude-auto-developer"
    echo "   - Description: 智能專案開發自動化系統 - 讓 Claude Code 在晚上也能工作"
    echo "   - Public repository (勾選)"
    echo "   - 不要初始化 README, .gitignore 或 license"
    echo ""
    echo "3. 🔗 創建後，使用以下指令連接:"
    echo "   git remote add origin $REPO_URL"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "4. ✅ 推送成功後，倉庫網址為:"
    echo "   https://github.com/${GITHUB_USER}/${PROJECT_NAME}"
    echo ""
}

# 設定 Git 遠程倉庫
setup_remote() {
    show_info "設定 Git 遠程倉庫..."
    
    # 檢查是否已有 origin
    if git remote get-url origin &>/dev/null; then
        show_warning "遠程倉庫 origin 已存在"
        git remote set-url origin "$REPO_URL"
        show_info "已更新遠程倉庫 URL"
    else
        git remote add origin "$REPO_URL"
        show_success "已添加遠程倉庫"
    fi
}

# 推送代碼
push_code() {
    show_info "推送代碼到 GitHub..."
    
    # 忽略 SSL 驗證進行推送
    GIT_SSL_NO_VERIFY=true git push -u origin main
    
    if [ $? -eq 0 ]; then
        show_success "代碼推送成功！"
        echo ""
        echo "🎉 倉庫網址: https://github.com/${GITHUB_USER}/${PROJECT_NAME}"
        return 0
    else
        show_error "推送失敗，可能需要手動創建倉庫"
        return 1
    fi
}

# 主函數
main() {
    cd "$(dirname "$0")"
    
    show_info "開始創建 GitHub 倉庫..."
    echo ""
    
    # 嘗試不同方法
    if try_gh_cli; then
        show_success "使用 GitHub CLI 創建成功"
    elif try_api_create; then
        show_success "使用 API 創建成功"
        setup_remote
        push_code
    else
        show_warning "自動創建失敗，提供手動指導"
        manual_guide
        
        echo ""
        read -p "已手動創建倉庫？(y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            setup_remote
            push_code
        else
            show_info "請按照上述步驟手動創建倉庫"
        fi
    fi
}

# 執行主函數
main "$@"