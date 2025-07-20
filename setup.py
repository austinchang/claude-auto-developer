#!/usr/bin/env python3
"""
Claude Auto Developer - 智能專案開發自動化系統
安裝腳本
"""

from setuptools import setup, find_packages
import os

# 讀取 README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 讀取 requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="claude-auto-developer",
    version="1.0.0-alpha",
    author="Austin Chang",
    author_email="austin680909@gmail.com",
    description="智能專案開發自動化系統 - 讓 Claude Code 在晚上也能工作",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/austinchang/claude-auto-developer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "claude-auto=claude_auto_developer.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "claude_auto_developer": [
            "config/task_templates/*",
            "config/schedules/*",
            "config/workflows/*",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/austinchang/claude-auto-developer/issues",
        "Source": "https://github.com/austinchang/claude-auto-developer",
        "Documentation": "https://github.com/austinchang/claude-auto-developer/blob/main/README.md",
    },
)