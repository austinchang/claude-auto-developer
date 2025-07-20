#!/usr/bin/env python3
"""
Claude Auto Developer - 主程式入口
智能專案開發自動化系統
"""

import sys
import os
import argparse
from pathlib import Path

# 添加 src 目錄到 Python 路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from claude_auto_developer.cli import main

if __name__ == "__main__":
    main()