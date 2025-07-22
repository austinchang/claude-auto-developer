#!/usr/bin/env python3
"""
Deployment Manager - 自動部署管理器
支援多種部署方式：本地、Docker、雲端服務等
"""

import os
import sys
import json
import shutil
import tempfile
import logging
import subprocess
import platform
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """部署配置"""
    deployment_type: str  # local, docker, heroku, vercel, aws_lambda
    environment: str  # development, staging, production
    auto_start: bool = True
    health_check_url: Optional[str] = None
    environment_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}

@dataclass
class DeploymentResult:
    """部署結果"""
    success: bool
    deployment_type: str
    deployment_url: Optional[str] = None
    container_id: Optional[str] = None
    process_id: Optional[int] = None
    logs: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []

class DeploymentManager:
    """自動部署管理器 - 支援多種部署環境"""
    
    def __init__(self, project_path: str, python_executable: str = None):
        """
        初始化部署管理器
        
        Args:
            project_path: 專案路徑
            python_executable: Python 執行檔路徑
        """
        self.project_path = Path(project_path)
        self.python_executable = python_executable or sys.executable
        
        # 平台檢測
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        
        # 部署策略
        self.deployment_strategies = {
            "local": self._deploy_local,
            "docker": self._deploy_docker,
            "heroku": self._deploy_heroku,
            "vercel": self._deploy_vercel,
            "aws_lambda": self._deploy_aws_lambda,
            "netlify": self._deploy_netlify
        }
        
        logger.info(f"DeploymentManager 初始化 - 專案: {project_path}")
    
    def auto_deploy(self, config: Optional[DeploymentConfig] = None) -> DeploymentResult:
        """
        自動部署專案
        
        Args:
            config: 部署配置，如果為 None 則自動檢測
            
        Returns:
            部署結果
        """
        if config is None:
            config = self._auto_detect_deployment_config()
        
        logger.info(f"開始自動部署 - 類型: {config.deployment_type}")
        
        # 驗證部署前置條件
        if not self._validate_deployment_prerequisites(config):
            return DeploymentResult(
                success=False,
                deployment_type=config.deployment_type,
                error="部署前置條件檢查失敗"
            )
        
        # 生成部署檔案
        self._generate_deployment_files(config)
        
        # 執行部署
        if config.deployment_type in self.deployment_strategies:
            return self.deployment_strategies[config.deployment_type](config)
        else:
            return DeploymentResult(
                success=False,
                deployment_type=config.deployment_type,
                error=f"不支援的部署類型: {config.deployment_type}"
            )
    
    def _auto_detect_deployment_config(self) -> DeploymentConfig:
        """自動檢測部署配置"""
        # 檢查專案特徵來決定部署方式
        
        # 檢查是否是 Web 應用
        if self._is_web_application():
            # 檢查是否有 Docker 相關檔案
            if (self.project_path / "Dockerfile").exists():
                deployment_type = "docker"
            # 檢查是否適合 Vercel (前端專案)
            elif self._is_frontend_project():
                deployment_type = "vercel"
            # 檢查是否適合 Heroku
            elif self._is_suitable_for_heroku():
                deployment_type = "heroku"
            else:
                deployment_type = "local"
        else:
            # 非 Web 應用，預設本地部署
            deployment_type = "local"
        
        return DeploymentConfig(
            deployment_type=deployment_type,
            environment="development",
            auto_start=True,
            health_check_url=self._detect_health_check_url()
        )
    
    def _is_web_application(self) -> bool:
        """檢查是否是 Web 應用程式"""
        # 檢查常見的 Web 框架
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                requirements = f.read().lower()
                web_frameworks = [
                    "flask", "django", "fastapi", "tornado", 
                    "bottle", "pyramid", "cherrypy", "web.py"
                ]
                if any(framework in requirements for framework in web_frameworks):
                    return True
        
        # 檢查常見的入口檔案
        web_files = ["app.py", "main.py", "server.py", "wsgi.py", "asgi.py"]
        for file_name in web_files:
            file_path = self.project_path / file_name
            if file_path.exists():
                with open(file_path) as f:
                    content = f.read().lower()
                    if any(term in content for term in ["flask", "django", "fastapi", "app.run", "uvicorn"]):
                        return True
        
        return False
    
    def _is_frontend_project(self) -> bool:
        """檢查是否是前端專案"""
        # 檢查 Node.js 相關檔案
        frontend_indicators = [
            "package.json", "index.html", "src/index.js", 
            "src/App.js", "public/index.html"
        ]
        
        return any((self.project_path / indicator).exists() for indicator in frontend_indicators)
    
    def _is_suitable_for_heroku(self) -> bool:
        """檢查是否適合 Heroku 部署"""
        # Heroku 適合的特徵
        if (self.project_path / "Procfile").exists():
            return True
        
        # 檢查是否是 Python Web 應用
        if self._is_web_application() and (self.project_path / "requirements.txt").exists():
            return True
        
        return False
    
    def _detect_health_check_url(self) -> Optional[str]:
        """檢測健康檢查 URL"""
        # 掃描程式碼尋找可能的端點
        common_endpoints = [
            "http://localhost:8000/health",
            "http://localhost:5000/health", 
            "http://localhost:3000/health",
            "http://localhost:8000/",
            "http://localhost:5000/",
            "http://localhost:3000/"
        ]
        
        # 檢查程式碼中是否定義了特定端點
        for py_file in self.project_path.rglob("*.py"):
            try:
                with open(py_file) as f:
                    content = f.read()
                    if "/health" in content or "@app.route" in content:
                        # 找到可能的健康檢查端點
                        if "5000" in content:
                            return "http://localhost:5000/health"
                        elif "3000" in content:
                            return "http://localhost:3000/health"
                        else:
                            return "http://localhost:8000/health"
            except Exception:
                continue
        
        return "http://localhost:8000/health"
    
    def _validate_deployment_prerequisites(self, config: DeploymentConfig) -> bool:
        """驗證部署前置條件"""
        logger.info("檢查部署前置條件")
        
        # 基本檢查
        if not self.project_path.exists():
            logger.error("專案路徑不存在")
            return False
        
        # 根據部署類型檢查特定條件
        if config.deployment_type == "docker":
            return self._check_docker_prerequisites()
        elif config.deployment_type == "heroku":
            return self._check_heroku_prerequisites()
        elif config.deployment_type == "vercel":
            return self._check_vercel_prerequisites()
        elif config.deployment_type == "aws_lambda":
            return self._check_aws_prerequisites()
        
        return True
    
    def _check_docker_prerequisites(self) -> bool:
        """檢查 Docker 前置條件"""
        try:
            # 檢查 Docker 是否安裝
            result = subprocess.run(["docker", "--version"], capture_output=True)
            if result.returncode != 0:
                logger.error("Docker 未安裝")
                return False
            
            # 檢查 Docker 服務是否運行
            result = subprocess.run(["docker", "info"], capture_output=True)
            if result.returncode != 0:
                logger.error("Docker 服務未運行")
                return False
            
            return True
        except FileNotFoundError:
            logger.error("Docker 命令未找到")
            return False
    
    def _check_heroku_prerequisites(self) -> bool:
        """檢查 Heroku 前置條件"""
        try:
            # 檢查 Heroku CLI
            result = subprocess.run(["heroku", "--version"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("Heroku CLI 未安裝，將生成部署指南")
            return True  # 不強制要求，可以生成指南
    
    def _check_vercel_prerequisites(self) -> bool:
        """檢查 Vercel 前置條件"""
        try:
            # 檢查 Vercel CLI
            result = subprocess.run(["vercel", "--version"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("Vercel CLI 未安裝，將生成部署指南")
            return True
    
    def _check_aws_prerequisites(self) -> bool:
        """檢查 AWS 前置條件"""
        try:
            # 檢查 AWS CLI
            result = subprocess.run(["aws", "--version"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("AWS CLI 未安裝，將生成部署指南")
            return True
    
    def _generate_deployment_files(self, config: DeploymentConfig):
        """生成部署檔案"""
        logger.info("生成部署配置檔案")
        
        if config.deployment_type == "docker":
            self._generate_dockerfile(config)
            self._generate_docker_compose(config)
        elif config.deployment_type == "heroku":
            self._generate_procfile(config)
            self._generate_heroku_config(config)
        elif config.deployment_type == "vercel":
            self._generate_vercel_config(config)
        elif config.deployment_type == "aws_lambda":
            self._generate_lambda_config(config)
        
        # 通用檔案
        self._generate_deployment_script(config)
        self._generate_env_file(config)
    
    def _generate_dockerfile(self, config: DeploymentConfig):
        """生成 Dockerfile"""
        dockerfile_content = f'''# 由 Claude Auto Developer 自動生成
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 設置環境變數
ENV PYTHONPATH=/app
ENV ENVIRONMENT={config.environment}

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f {config.health_check_url or "http://localhost:8000/health"} || exit 1

# 啟動命令
CMD ["python", "main.py"]
'''
        
        with open(self.project_path / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
    
    def _generate_docker_compose(self, config: DeploymentConfig):
        """生成 docker-compose.yml"""
        compose_content = f'''# 由 Claude Auto Developer 自動生成
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT={config.environment}
    volumes:
      - .:/app
    restart: unless-stopped
    
    # 如果需要資料庫
    # depends_on:
    #   - db
  
  # db:
  #   image: postgres:13
  #   environment:
  #     POSTGRES_DB: myapp
  #     POSTGRES_USER: user
  #     POSTGRES_PASSWORD: password
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
'''
        
        with open(self.project_path / "docker-compose.yml", "w") as f:
            f.write(compose_content)
    
    def _generate_procfile(self, config: DeploymentConfig):
        """生成 Heroku Procfile"""
        # 檢測應用類型
        if (self.project_path / "main.py").exists():
            cmd = "python main.py"
        elif (self.project_path / "app.py").exists():
            cmd = "python app.py"
        else:
            cmd = "python main.py"
        
        procfile_content = f"web: {cmd}\n"
        
        with open(self.project_path / "Procfile", "w") as f:
            f.write(procfile_content)
    
    def _generate_heroku_config(self, config: DeploymentConfig):
        """生成 Heroku 配置"""
        # runtime.txt
        with open(self.project_path / "runtime.txt", "w") as f:
            f.write("python-3.9.16\n")
        
        # app.json
        app_json = {
            "name": self.project_path.name,
            "description": f"由 Claude Auto Developer 自動生成的應用",
            "repository": "https://github.com/your-username/your-repo",
            "keywords": ["python", "claude-auto-developer"],
            "env": {
                "ENVIRONMENT": {
                    "description": "Environment type",
                    "value": config.environment
                }
            },
            "formation": {
                "web": {
                    "quantity": 1
                }
            },
            "addons": [],
            "buildpacks": [
                {
                    "url": "heroku/python"
                }
            ]
        }
        
        with open(self.project_path / "app.json", "w") as f:
            json.dump(app_json, f, indent=2)
    
    def _generate_vercel_config(self, config: DeploymentConfig):
        """生成 Vercel 配置"""
        vercel_config = {
            "version": 2,
            "builds": [
                {
                    "src": "*.py",
                    "use": "@vercel/python"
                }
            ],
            "routes": [
                {
                    "src": "/(.*)",
                    "dest": "/main.py"
                }
            ]
        }
        
        with open(self.project_path / "vercel.json", "w") as f:
            json.dump(vercel_config, f, indent=2)
    
    def _generate_lambda_config(self, config: DeploymentConfig):
        """生成 AWS Lambda 配置"""
        # serverless.yml
        serverless_config = f'''# 由 Claude Auto Developer 自動生成
service: {self.project_path.name}

provider:
  name: aws
  runtime: python3.9
  stage: {config.environment}
  region: us-east-1

functions:
  main:
    handler: main.handler
    events:
      - http:
          path: /{{proxy+}}
          method: ANY
      - http:
          path: /
          method: ANY

plugins:
  - serverless-python-requirements
'''
        
        with open(self.project_path / "serverless.yml", "w") as f:
            f.write(serverless_config)
    
    def _generate_deployment_script(self, config: DeploymentConfig):
        """生成部署腳本"""
        if self.is_windows:
            script_ext = ".bat"
            script_content = f'''@echo off
echo 🚀 部署 {self.project_path.name} ({config.deployment_type})
echo ===============================================

'''
        else:
            script_ext = ".sh"
            script_content = f'''#!/bin/bash
echo "🚀 部署 {self.project_path.name} ({config.deployment_type})"
echo "==============================================="

'''
        
        # 根據部署類型添加特定命令
        if config.deployment_type == "docker":
            if self.is_windows:
                script_content += '''
echo 📦 構建 Docker 映像...
docker build -t %CD%:latest .

echo 🚀 啟動容器...
docker run -d -p 8000:8000 --name myapp %CD%:latest

echo ✅ 部署完成! 訪問 http://localhost:8000
'''
            else:
                script_content += '''
echo "📦 構建 Docker 映像..."
docker build -t $(basename "$PWD"):latest .

echo "🚀 啟動容器..."
docker run -d -p 8000:8000 --name myapp $(basename "$PWD"):latest

echo "✅ 部署完成! 訪問 http://localhost:8000"
'''
        elif config.deployment_type == "heroku":
            script_content += '''
echo "📦 Heroku 部署..."
heroku create
git add .
git commit -m "Deploy to Heroku"
git push heroku main

echo "✅ 部署完成!"
'''
        
        script_path = self.project_path / f"deploy{script_ext}"
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # 設置執行權限 (Unix)
        if not self.is_windows:
            os.chmod(script_path, 0o755)
    
    def _generate_env_file(self, config: DeploymentConfig):
        """生成環境變數檔案"""
        env_content = f'''# 由 Claude Auto Developer 自動生成
ENVIRONMENT={config.environment}
'''
        
        # 添加配置中的環境變數
        for key, value in config.environment_vars.items():
            env_content += f"{key}={value}\n"
        
        with open(self.project_path / ".env", "w") as f:
            f.write(env_content)
    
    def _deploy_local(self, config: DeploymentConfig) -> DeploymentResult:
        """本地部署"""
        logger.info("執行本地部署")
        
        result = DeploymentResult(
            success=False,
            deployment_type="local"
        )
        
        try:
            # 尋找入口檔案
            entry_files = ["main.py", "app.py", "server.py", "run.py"]
            entry_file = None
            
            for file_name in entry_files:
                if (self.project_path / file_name).exists():
                    entry_file = file_name
                    break
            
            if not entry_file:
                result.error = "未找到入口檔案"
                return result
            
            if config.auto_start:
                # 啟動應用 (背景執行)
                cmd = [self.python_executable, entry_file]
                
                if self.is_windows:
                    process = subprocess.Popen(
                        cmd,
                        cwd=self.project_path,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    process = subprocess.Popen(
                        cmd,
                        cwd=self.project_path,
                        start_new_session=True
                    )
                
                result.process_id = process.pid
                result.deployment_url = config.health_check_url or "http://localhost:8000"
            
            result.success = True
            result.logs.append("✅ 本地部署完成")
            
        except Exception as e:
            result.error = str(e)
            result.logs.append(f"❌ 本地部署失敗: {e}")
        
        return result
    
    def _deploy_docker(self, config: DeploymentConfig) -> DeploymentResult:
        """Docker 部署"""
        logger.info("執行 Docker 部署")
        
        result = DeploymentResult(
            success=False,
            deployment_type="docker"
        )
        
        try:
            image_name = f"{self.project_path.name.lower()}:latest"
            
            # 構建映像
            build_cmd = ["docker", "build", "-t", image_name, "."]
            build_result = subprocess.run(
                build_cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                result.error = f"Docker 構建失敗: {build_result.stderr}"
                return result
            
            result.logs.append("✅ Docker 映像構建成功")
            
            if config.auto_start:
                # 啟動容器
                run_cmd = [
                    "docker", "run", "-d",
                    "-p", "8000:8000",
                    "--name", f"{self.project_path.name.lower()}_container",
                    image_name
                ]
                
                run_result = subprocess.run(run_cmd, capture_output=True, text=True)
                
                if run_result.returncode == 0:
                    result.container_id = run_result.stdout.strip()
                    result.deployment_url = "http://localhost:8000"
                    result.logs.append("✅ Docker 容器啟動成功")
                else:
                    result.logs.append(f"⚠️ 容器啟動失敗: {run_result.stderr}")
            
            result.success = True
            
        except Exception as e:
            result.error = str(e)
            result.logs.append(f"❌ Docker 部署失敗: {e}")
        
        return result
    
    def _deploy_heroku(self, config: DeploymentConfig) -> DeploymentResult:
        """Heroku 部署"""
        logger.info("執行 Heroku 部署")
        
        result = DeploymentResult(
            success=False,
            deployment_type="heroku"
        )
        
        # 生成部署指南
        guide_content = '''# Heroku 部署指南

## 前置要求
1. 安裝 Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. 登入 Heroku: `heroku login`

## 部署步驟
1. 創建 Heroku 應用: `heroku create your-app-name`
2. 提交程式碼: `git add . && git commit -m "Deploy to Heroku"`
3. 部署: `git push heroku main`
4. 開啟應用: `heroku open`

## 設置環境變數
```bash
heroku config:set ENVIRONMENT=production
```

## 查看日誌
```bash
heroku logs --tail
```
'''
        
        guide_path = self.project_path / "HEROKU_DEPLOY_GUIDE.md"
        with open(guide_path, "w") as f:
            f.write(guide_content)
        
        result.success = True
        result.logs.append("✅ Heroku 部署檔案和指南已生成")
        result.logs.append(f"📖 請參考: {guide_path}")
        
        return result
    
    def _deploy_vercel(self, config: DeploymentConfig) -> DeploymentResult:
        """Vercel 部署"""
        logger.info("執行 Vercel 部署")
        
        result = DeploymentResult(
            success=False,
            deployment_type="vercel"
        )
        
        # 生成部署指南
        guide_content = '''# Vercel 部署指南

## 前置要求
1. 安裝 Vercel CLI: `npm i -g vercel`
2. 登入 Vercel: `vercel login`

## 部署步驟
1. 在專案目錄執行: `vercel`
2. 按照提示設置專案
3. 部署: `vercel --prod`

## 或透過 GitHub
1. 將專案推送到 GitHub
2. 在 Vercel Dashboard 連接 GitHub 倉庫
3. 自動部署設置完成

## 環境變數設置
在 Vercel Dashboard 的 Settings > Environment Variables 中設置
'''
        
        guide_path = self.project_path / "VERCEL_DEPLOY_GUIDE.md"
        with open(guide_path, "w") as f:
            f.write(guide_content)
        
        result.success = True
        result.logs.append("✅ Vercel 部署檔案和指南已生成")
        result.logs.append(f"📖 請參考: {guide_path}")
        
        return result
    
    def _deploy_aws_lambda(self, config: DeploymentConfig) -> DeploymentResult:
        """AWS Lambda 部署"""
        logger.info("執行 AWS Lambda 部署")
        
        result = DeploymentResult(
            success=False,
            deployment_type="aws_lambda"
        )
        
        # 生成部署指南
        guide_content = '''# AWS Lambda 部署指南

## 前置要求
1. 安裝 AWS CLI: https://aws.amazon.com/cli/
2. 配置 AWS 憑證: `aws configure`
3. 安裝 Serverless Framework: `npm install -g serverless`

## 部署步驟
1. 安裝插件: `npm install --save-dev serverless-python-requirements`
2. 部署: `serverless deploy`
3. 查看狀態: `serverless info`

## 本地測試
```bash
serverless invoke local --function main
```

## 查看日誌
```bash
serverless logs -f main --tail
```

## 移除部署
```bash
serverless remove
```
'''
        
        guide_path = self.project_path / "AWS_LAMBDA_DEPLOY_GUIDE.md"
        with open(guide_path, "w") as f:
            f.write(guide_content)
        
        result.success = True
        result.logs.append("✅ AWS Lambda 部署檔案和指南已生成")
        result.logs.append(f"📖 請參考: {guide_path}")
        
        return result
    
    def _deploy_netlify(self, config: DeploymentConfig) -> DeploymentResult:
        """Netlify 部署"""
        logger.info("執行 Netlify 部署")
        
        result = DeploymentResult(
            success=False,
            deployment_type="netlify"
        )
        
        # 生成 netlify.toml
        netlify_config = '''# 由 Claude Auto Developer 自動生成
[build]
  publish = "dist"
  command = "python build.py"

[build.environment]
  PYTHON_VERSION = "3.9"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
'''
        
        with open(self.project_path / "netlify.toml", "w") as f:
            f.write(netlify_config)
        
        result.success = True
        result.logs.append("✅ Netlify 配置檔案已生成")
        
        return result
    
    def generate_deployment_report(self, result: DeploymentResult) -> Path:
        """生成部署報告"""
        report_content = f"""# 部署報告

## 部署摘要
- **部署類型**: {result.deployment_type}
- **部署狀態**: {'✅ 成功' if result.success else '❌ 失敗'}
- **部署時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        if result.deployment_url:
            report_content += f"- **應用 URL**: {result.deployment_url}\n"
        
        if result.container_id:
            report_content += f"- **容器 ID**: {result.container_id}\n"
        
        if result.process_id:
            report_content += f"- **進程 ID**: {result.process_id}\n"
        
        if result.error:
            report_content += f"\n## ❌ 錯誤資訊\n{result.error}\n"
        
        if result.logs:
            report_content += "\n## 📋 部署日誌\n```\n"
            report_content += "\n".join(result.logs)
            report_content += "\n```\n"
        
        report_content += f"\n---\n*由 Claude Auto Developer 部署管理器生成*\n"
        
        report_path = self.project_path / "DEPLOYMENT_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_path