#!/bin/bash

# Claude Auto Developer 安裝腳本
# 自動安裝依賴和設置全局指令

set -e

echo "🤖 Claude Auto Developer 安裝腳本"
echo "=================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_status() {
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

# 獲取腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

show_status "專案根目錄: $PROJECT_ROOT"

# 檢查 Python 版本
check_python() {
    show_status "檢查 Python 環境..."
    
    if ! command -v python3 &> /dev/null; then
        show_error "Python 3 未安裝，請先安裝 Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    show_success "Python 版本: $PYTHON_VERSION"
    
    # 檢查版本是否符合要求
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        show_success "Python 版本符合要求 (>= 3.8)"
    else
        show_error "Python 版本過舊，需要 3.8 或更新版本"
        exit 1
    fi
}

# 創建虛擬環境
create_venv() {
    show_status "創建虛擬環境..."
    
    if [ -d "$PROJECT_ROOT/venv" ]; then
        show_warning "虛擬環境已存在，跳過創建"
    else
        python3 -m venv "$PROJECT_ROOT/venv"
        show_success "虛擬環境創建完成"
    fi
}

# 安裝依賴
install_dependencies() {
    show_status "安裝 Python 依賴..."
    
    # 激活虛擬環境
    source "$PROJECT_ROOT/venv/bin/activate"
    
    # 升級 pip
    python -m pip install --upgrade pip
    
    # 安裝依賴
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
        show_success "依賴安裝完成"
    else
        show_warning "requirements.txt 不存在，跳過依賴安裝"
    fi
}

# 創建全局指令
create_global_command() {
    show_status "設置全局指令..."
    
    # 創建 claude-auto 指令腳本
    GLOBAL_SCRIPT="/usr/local/bin/claude-auto"
    
    # 檢查是否有 sudo 權限
    if ! sudo -n true 2>/dev/null; then
        show_warning "需要 sudo 權限來創建全局指令"
        echo "請輸入密碼以繼續："
    fi
    
    # 創建全局指令腳本
    sudo tee "$GLOBAL_SCRIPT" > /dev/null << EOF
#!/bin/bash

# Claude Auto Developer 全局指令
# 自動激活虛擬環境並執行主程式

PROJECT_ROOT="$PROJECT_ROOT"

# 檢查專案是否存在
if [ ! -d "\$PROJECT_ROOT" ]; then
    echo "錯誤: Claude Auto Developer 專案目錄不存在: \$PROJECT_ROOT"
    exit 1
fi

# 激活虛擬環境
if [ -f "\$PROJECT_ROOT/venv/bin/activate" ]; then
    source "\$PROJECT_ROOT/venv/bin/activate"
fi

# 執行主程式
cd "\$PROJECT_ROOT"
python main.py "\$@"
EOF

    # 設置執行權限
    sudo chmod +x "$GLOBAL_SCRIPT"
    
    show_success "全局指令創建完成: $GLOBAL_SCRIPT"
}

# 創建桌面快捷方式（可選）
create_desktop_shortcut() {
    show_status "創建桌面快捷方式..."
    
    DESKTOP_FILE="$HOME/Desktop/claude-auto-developer.desktop"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Claude Auto Developer
Comment=智能專案開發自動化系統
Exec=gnome-terminal -- claude-auto
Icon=applications-development
Terminal=true
Categories=Development;
EOF
    
    chmod +x "$DESKTOP_FILE"
    show_success "桌面快捷方式創建完成"
}

# 測試安裝
test_installation() {
    show_status "測試安裝..."
    
    if command -v claude-auto &> /dev/null; then
        show_status "測試 claude-auto 指令..."
        claude-auto --version
        show_success "安裝測試通過！"
    else
        show_error "claude-auto 指令不可用，安裝可能失敗"
        return 1
    fi
}

# 顯示使用說明
show_usage() {
    echo ""
    echo "🎉 Claude Auto Developer 安裝完成！"
    echo ""
    echo "📖 基本使用方法："
    echo "  claude-auto add \"任務描述\" --deadline \"時間\" --priority \"優先級\""
    echo "  claude-auto list"
    echo "  claude-auto start"
    echo "  claude-auto status"
    echo ""
    echo "💡 範例："
    echo "  claude-auto add \"為網站添加用戶評論功能\" --deadline \"2天\" --priority \"high\""
    echo ""
    echo "📚 完整文檔: $PROJECT_ROOT/README.md"
    echo ""
}

# 主安裝流程
main() {
    show_status "開始安裝 Claude Auto Developer..."
    echo ""
    
    # 執行安裝步驟
    check_python
    create_venv
    install_dependencies
    create_global_command
    
    # 可選步驟
    if [ "$1" != "--no-desktop" ]; then
        create_desktop_shortcut
    fi
    
    # 測試安裝
    if test_installation; then
        show_usage
    else
        show_error "安裝測試失敗，請檢查上述錯誤訊息"
        exit 1
    fi
}

# 解安裝功能
uninstall() {
    show_status "解除安裝 Claude Auto Developer..."
    
    # 移除全局指令
    if [ -f "/usr/local/bin/claude-auto" ]; then
        sudo rm "/usr/local/bin/claude-auto"
        show_success "全局指令已移除"
    fi
    
    # 移除桌面快捷方式
    if [ -f "$HOME/Desktop/claude-auto-developer.desktop" ]; then
        rm "$HOME/Desktop/claude-auto-developer.desktop"
        show_success "桌面快捷方式已移除"
    fi
    
    # 移除虛擬環境
    if [ -d "$PROJECT_ROOT/venv" ]; then
        rm -rf "$PROJECT_ROOT/venv"
        show_success "虛擬環境已移除"
    fi
    
    show_success "解除安裝完成"
}

# 處理命令列參數
case "$1" in
    "uninstall")
        uninstall
        ;;
    *)
        main "$@"
        ;;
esac