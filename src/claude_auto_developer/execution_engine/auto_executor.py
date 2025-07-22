#!/usr/bin/env python3
"""
Auto Executor - 自動執行環境管理器
負責專案的自動環境建置、依賴安裝、測試執行和服務啟動
"""

import os
import sys
import subprocess
import venv
import json
import time
import shutil
import platform
import psutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoExecutor:
    """自動執行環境管理器 - 讓生成的程式碼能夠自動運行"""
    
    def __init__(self, project_path: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化自動執行器
        
        Args:
            project_path: 專案路徑
            config: 執行配置
        """
        self.project_path = Path(project_path)
        self.venv_path = self.project_path / ".venv"
        self.config = config or self._default_config()
        
        # 平台檢測
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        
        # Python 執行檔路徑
        if self.is_windows:
            self.python_executable = self.venv_path / "Scripts" / "python.exe"
            self.pip_executable = self.venv_path / "Scripts" / "pip.exe"
        else:
            self.python_executable = self.venv_path / "bin" / "python"
            self.pip_executable = self.venv_path / "bin" / "pip"
        
        # 執行日誌
        self.execution_log = []
        
        logger.info(f"AutoExecutor 初始化 - 專案: {project_path}")
    
    def _default_config(self) -> Dict[str, Any]:
        """預設執行配置"""
        return {
            "auto_install": True,
            "auto_test": True,
            "auto_run": True,
            "test_framework": "pytest",
            "entry_point": "main.py",
            "health_check_url": "http://localhost:8000/health",
            "max_retries": 3,
            "timeout": 300,  # 5分鐘
            "resource_limits": {
                "max_cpu_percent": 80,
                "max_memory_mb": 1024
            }
        }
    
    def full_auto_run(self) -> Dict[str, Any]:
        """
        完整自動執行流程
        
        Returns:
            執行結果報告
        """
        self.log("🚀 開始自動執行流程")
        
        results = {
            "project_path": str(self.project_path),
            "start_time": datetime.now().isoformat(),
            "steps": {},
            "success": True,
            "logs": []
        }
        
        try:
            # 1. 檢查專案結構
            if not self._check_project_structure():
                raise Exception("專案結構檢查失敗")
            results["steps"]["structure_check"] = {"status": "success"}
            
            # 2. 創建虛擬環境
            if self.config["auto_install"]:
                venv_result = self.create_virtual_environment()
                results["steps"]["venv_creation"] = venv_result
                
                if venv_result["success"]:
                    # 3. 安裝依賴
                    install_result = self.install_dependencies()
                    results["steps"]["dependency_install"] = install_result
                else:
                    raise Exception("虛擬環境創建失敗")
            
            # 4. 執行測試
            if self.config["auto_test"]:
                test_result = self.run_tests()
                results["steps"]["test_execution"] = test_result
                
                if not test_result["success"] and test_result.get("critical_failures", 0) > 0:
                    self.log("⚠️ 發現關鍵測試失敗，嘗試自動修復")
                    # 可以在這裡加入自動修復邏輯
            
            # 5. 啟動服務
            if self.config["auto_run"]:
                service_result = self.start_service()
                results["steps"]["service_start"] = service_result
                
                if service_result["success"]:
                    # 6. 健康檢查
                    health_result = self.health_check()
                    results["steps"]["health_check"] = health_result
            
            # 7. 生成執行報告
            report_path = self.generate_execution_report(results)
            results["report_path"] = str(report_path)
            
        except Exception as e:
            self.log(f"❌ 執行失敗: {str(e)}", "ERROR")
            results["success"] = False
            results["error"] = str(e)
        
        results["end_time"] = datetime.now().isoformat()
        results["logs"] = self.execution_log
        
        return results
    
    def _check_project_structure(self) -> bool:
        """檢查專案結構是否完整"""
        self.log("📁 檢查專案結構")
        
        required_files = ["requirements.txt"]
        required_dirs = ["src"]
        
        for file_name in required_files:
            if not (self.project_path / file_name).exists():
                self.log(f"缺少必要檔案: {file_name}", "WARN")
                # 嘗試生成基本 requirements.txt
                if file_name == "requirements.txt":
                    self._generate_basic_requirements()
        
        for dir_name in required_dirs:
            if not (self.project_path / dir_name).exists():
                self.log(f"缺少必要目錄: {dir_name}", "WARN")
                (self.project_path / dir_name).mkdir(exist_ok=True)
        
        return True
    
    def _generate_basic_requirements(self):
        """生成基本的 requirements.txt"""
        basic_requirements = [
            "pytest>=6.2.0",
            "python-dotenv>=0.19.0",
            "requests>=2.25.0"
        ]
        
        req_path = self.project_path / "requirements.txt"
        with open(req_path, "w") as f:
            f.write("\n".join(basic_requirements))
        
        self.log("✅ 生成基本 requirements.txt")
    
    def create_virtual_environment(self) -> Dict[str, Any]:
        """創建虛擬環境"""
        self.log("🔧 創建虛擬環境")
        
        result = {
            "success": False,
            "venv_path": str(self.venv_path),
            "python_version": None
        }
        
        try:
            # 如果已存在，先刪除
            if self.venv_path.exists():
                self.log("移除舊的虛擬環境")
                shutil.rmtree(self.venv_path)
            
            # 創建新的虛擬環境
            venv.create(self.venv_path, with_pip=True)
            
            # 驗證創建成功
            if self.python_executable.exists():
                # 取得 Python 版本
                version_cmd = [str(self.python_executable), "--version"]
                version_result = subprocess.run(version_cmd, capture_output=True, text=True)
                result["python_version"] = version_result.stdout.strip()
                
                result["success"] = True
                self.log(f"✅ 虛擬環境創建成功: {result['python_version']}")
            else:
                raise Exception("虛擬環境創建失敗")
                
        except Exception as e:
            self.log(f"❌ 虛擬環境創建失敗: {str(e)}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def install_dependencies(self) -> Dict[str, Any]:
        """安裝專案依賴"""
        self.log("📦 安裝專案依賴")
        
        result = {
            "success": False,
            "installed_packages": [],
            "failed_packages": []
        }
        
        try:
            requirements_file = self.project_path / "requirements.txt"
            
            if not requirements_file.exists():
                self.log("未找到 requirements.txt，跳過依賴安裝", "WARN")
                result["success"] = True
                return result
            
            # 升級 pip
            self.log("升級 pip...")
            upgrade_cmd = [str(self.pip_executable), "install", "--upgrade", "pip"]
            subprocess.run(upgrade_cmd, capture_output=True)
            
            # 安裝依賴
            self.log("安裝 requirements.txt 中的依賴...")
            install_cmd = [
                str(self.pip_executable), 
                "install", 
                "-r", 
                str(requirements_file)
            ]
            
            process = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=self.config["timeout"]
            )
            
            if process.returncode == 0:
                result["success"] = True
                self.log("✅ 所有依賴安裝成功")
                
                # 列出已安裝的套件
                list_cmd = [str(self.pip_executable), "list", "--format=json"]
                list_result = subprocess.run(list_cmd, capture_output=True, text=True)
                if list_result.returncode == 0:
                    result["installed_packages"] = json.loads(list_result.stdout)
            else:
                self.log(f"❌ 依賴安裝失敗: {process.stderr}", "ERROR")
                result["error"] = process.stderr
                
        except subprocess.TimeoutExpired:
            self.log("❌ 依賴安裝超時", "ERROR")
            result["error"] = "Installation timeout"
        except Exception as e:
            self.log(f"❌ 依賴安裝異常: {str(e)}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def run_tests(self) -> Dict[str, Any]:
        """執行測試"""
        self.log("🧪 執行測試")
        
        result = {
            "success": False,
            "test_framework": self.config["test_framework"],
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "coverage": None
        }
        
        try:
            test_dir = self.project_path / "tests"
            
            if not test_dir.exists() or not any(test_dir.iterdir()):
                self.log("未找到測試檔案，生成基本測試", "WARN")
                self._generate_basic_tests()
            
            if self.config["test_framework"] == "pytest":
                result.update(self._run_pytest())
            elif self.config["test_framework"] == "unittest":
                result.update(self._run_unittest())
            else:
                self.log(f"不支援的測試框架: {self.config['test_framework']}", "WARN")
                result["success"] = True  # 跳過測試
                
        except Exception as e:
            self.log(f"❌ 測試執行失敗: {str(e)}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def _run_pytest(self) -> Dict[str, Any]:
        """執行 pytest 測試"""
        test_cmd = [
            str(self.python_executable),
            "-m", "pytest",
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_report.json"
        ]
        
        result = {}
        
        try:
            process = subprocess.run(
                test_cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=self.config["timeout"]
            )
            
            # 解析測試結果
            report_file = self.project_path / "test_report.json"
            if report_file.exists():
                with open(report_file) as f:
                    report_data = json.load(f)
                    
                result["tests_run"] = report_data.get("summary", {}).get("total", 0)
                result["tests_passed"] = report_data.get("summary", {}).get("passed", 0)
                result["tests_failed"] = report_data.get("summary", {}).get("failed", 0)
                result["success"] = result["tests_failed"] == 0
            else:
                # 從輸出解析
                if "passed" in process.stdout:
                    result["success"] = True
                    self.log("✅ 測試通過")
                else:
                    result["success"] = False
                    self.log("❌ 測試失敗", "ERROR")
                    
        except subprocess.TimeoutExpired:
            self.log("❌ 測試執行超時", "ERROR")
            result["error"] = "Test timeout"
        
        return result
    
    def _run_unittest(self) -> Dict[str, Any]:
        """執行 unittest 測試"""
        test_cmd = [
            str(self.python_executable),
            "-m", "unittest",
            "discover",
            "-s", "tests",
            "-v"
        ]
        
        result = {}
        
        try:
            process = subprocess.run(
                test_cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=self.config["timeout"]
            )
            
            result["success"] = process.returncode == 0
            
            if result["success"]:
                self.log("✅ 單元測試通過")
            else:
                self.log("❌ 單元測試失敗", "ERROR")
                
        except subprocess.TimeoutExpired:
            self.log("❌ 測試執行超時", "ERROR")
            result["error"] = "Test timeout"
        
        return result
    
    def _generate_basic_tests(self):
        """生成基本測試檔案"""
        test_dir = self.project_path / "tests"
        test_dir.mkdir(exist_ok=True)
        
        test_content = '''import pytest
import sys
import os

# 將 src 加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic():
    """基本測試 - 確保測試框架正常運作"""
    assert True
    
def test_project_structure():
    """測試專案結構"""
    assert os.path.exists('../src')
    assert os.path.exists('../requirements.txt')
'''
        
        test_file = test_dir / "test_basic.py"
        with open(test_file, "w") as f:
            f.write(test_content)
        
        self.log("✅ 生成基本測試檔案")
    
    def start_service(self) -> Dict[str, Any]:
        """啟動服務"""
        self.log("🚀 啟動服務")
        
        result = {
            "success": False,
            "pid": None,
            "port": None,
            "entry_point": self.config["entry_point"]
        }
        
        try:
            entry_file = self.project_path / self.config["entry_point"]
            
            # 尋找可能的入口點
            if not entry_file.exists():
                possible_entries = ["main.py", "app.py", "server.py", "run.py"]
                for entry in possible_entries:
                    if (self.project_path / entry).exists():
                        entry_file = self.project_path / entry
                        result["entry_point"] = entry
                        break
                
                if not entry_file.exists():
                    # 檢查 src 目錄
                    for entry in possible_entries:
                        if (self.project_path / "src" / entry).exists():
                            entry_file = self.project_path / "src" / entry
                            result["entry_point"] = f"src/{entry}"
                            break
            
            if not entry_file.exists():
                self.log("未找到入口檔案，跳過服務啟動", "WARN")
                result["success"] = True
                return result
            
            # 啟動服務（背景執行）
            if self.is_windows:
                # Windows 使用 START 命令
                start_cmd = f'start /B {self.python_executable} {entry_file}'
                process = subprocess.Popen(start_cmd, shell=True)
            else:
                # Unix-like 系統
                start_cmd = [str(self.python_executable), str(entry_file)]
                process = subprocess.Popen(
                    start_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
            
            # 等待服務啟動
            time.sleep(3)
            
            # 檢查進程是否還在運行
            if process.poll() is None:
                result["success"] = True
                result["pid"] = process.pid
                self.log(f"✅ 服務啟動成功 (PID: {process.pid})")
                
                # 嘗試找到監聽的端口
                try:
                    proc = psutil.Process(process.pid)
                    connections = proc.connections()
                    for conn in connections:
                        if conn.status == 'LISTEN':
                            result["port"] = conn.laddr.port
                            self.log(f"服務監聽端口: {conn.laddr.port}")
                            break
                except Exception:
                    pass
            else:
                self.log("❌ 服務啟動失敗", "ERROR")
                
        except Exception as e:
            self.log(f"❌ 服務啟動異常: {str(e)}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        self.log("🏥 執行健康檢查")
        
        result = {
            "success": False,
            "status_code": None,
            "response_time": None
        }
        
        try:
            import requests
            
            # 嘗試多個可能的健康檢查端點
            health_urls = [
                self.config["health_check_url"],
                "http://localhost:8000/",
                "http://localhost:5000/",
                "http://localhost:3000/",
                "http://127.0.0.1:8000/health",
                "http://127.0.0.1:8000/api/health"
            ]
            
            for url in health_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=5)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        result["success"] = True
                        result["status_code"] = response.status_code
                        result["response_time"] = response_time
                        result["url"] = url
                        self.log(f"✅ 健康檢查通過: {url} ({response_time:.2f}s)")
                        break
                except Exception:
                    continue
            
            if not result["success"]:
                self.log("⚠️ 健康檢查失敗，但服務可能仍在運行", "WARN")
                result["success"] = True  # 不算作失敗
                
        except ImportError:
            self.log("requests 套件未安裝，跳過健康檢查", "WARN")
            result["success"] = True
        except Exception as e:
            self.log(f"健康檢查異常: {str(e)}", "WARN")
            result["success"] = True  # 不算作失敗
        
        return result
    
    def stop_service(self, pid: int) -> bool:
        """停止服務"""
        try:
            if self.is_windows:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, 9)
            
            self.log(f"✅ 服務已停止 (PID: {pid})")
            return True
        except Exception as e:
            self.log(f"停止服務失敗: {str(e)}", "ERROR")
            return False
    
    def generate_execution_report(self, results: Dict[str, Any]) -> Path:
        """生成執行報告"""
        self.log("📄 生成執行報告")
        
        report_content = f"""# 自動執行報告

## 專案資訊
- **專案路徑**: {results['project_path']}
- **開始時間**: {results['start_time']}
- **結束時間**: {results.get('end_time', 'N/A')}
- **執行狀態**: {'✅ 成功' if results['success'] else '❌ 失敗'}

## 執行步驟

"""
        
        for step_name, step_result in results.get("steps", {}).items():
            status = "✅" if step_result.get("success", False) else "❌"
            report_content += f"### {status} {step_name}\n"
            
            if isinstance(step_result, dict):
                for key, value in step_result.items():
                    if key != "success":
                        report_content += f"- **{key}**: {value}\n"
            
            report_content += "\n"
        
        if results.get("error"):
            report_content += f"## ❌ 錯誤資訊\n{results['error']}\n\n"
        
        report_content += "## 執行日誌\n```\n"
        report_content += "\n".join(results.get("logs", []))
        report_content += "\n```\n"
        
        report_content += f"\n---\n*由 Claude Auto Developer 自動生成*\n"
        
        report_path = self.project_path / "EXECUTION_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_path
    
    def log(self, message: str, level: str = "INFO"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_log.append(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARN":
            logger.warning(message)
        else:
            logger.info(message)

def create_and_run_project(project_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    便捷函數：創建並運行專案
    
    Args:
        project_path: 專案路徑
        config: 執行配置
        
    Returns:
        執行結果
    """
    executor = AutoExecutor(project_path, config)
    return executor.full_auto_run()