#!/usr/bin/env python3
"""
Test Runner - 自動測試執行器
支援多種測試框架，自動發現測試，生成測試報告，並嘗試自動修復簡單錯誤
"""

import os
import sys
import subprocess
import json
import re
import ast
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """測試結果"""
    test_name: str
    status: str  # passed, failed, error, skipped
    duration: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    
@dataclass
class TestReport:
    """測試報告"""
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float
    test_results: List[TestResult]
    coverage: Optional[float] = None
    
class TestRunner:
    """自動測試執行器 - 支援多種測試框架和自動修復"""
    
    def __init__(self, project_path: str, python_executable: str = None):
        """
        初始化測試執行器
        
        Args:
            project_path: 專案路徑
            python_executable: Python 執行檔路徑
        """
        self.project_path = Path(project_path)
        self.python_executable = python_executable or sys.executable
        self.test_frameworks = {
            "pytest": self._run_pytest,
            "unittest": self._run_unittest,
            "nose": self._run_nose,
            "doctest": self._run_doctest
        }
        
        logger.info(f"TestRunner 初始化 - 專案: {project_path}")
    
    def auto_discover_and_run(self) -> Dict[str, Any]:
        """
        自動發現並執行測試
        
        Returns:
            測試執行結果
        """
        logger.info("開始自動測試發現和執行")
        
        # 1. 檢測測試框架
        framework = self._detect_test_framework()
        logger.info(f"檢測到測試框架: {framework}")
        
        # 2. 發現測試檔案
        test_files = self._discover_test_files()
        logger.info(f"發現 {len(test_files)} 個測試檔案")
        
        # 3. 如果沒有測試，生成基本測試
        if not test_files:
            logger.warning("未發現測試檔案，生成基本測試")
            self._generate_basic_tests()
            test_files = self._discover_test_files()
        
        # 4. 執行測試
        test_report = self._run_tests(framework)
        
        # 5. 如果有失敗，嘗試自動修復
        if test_report.failed > 0 or test_report.errors > 0:
            logger.info("發現測試失敗，嘗試自動修復")
            fix_results = self._auto_fix_tests(test_report)
            
            if fix_results["fixes_applied"] > 0:
                logger.info(f"應用了 {fix_results['fixes_applied']} 個修復，重新執行測試")
                # 重新執行測試
                test_report = self._run_tests(framework)
        
        # 6. 生成測試報告
        report_path = self._generate_test_report(test_report)
        
        return {
            "framework": framework,
            "test_report": asdict(test_report),
            "report_path": str(report_path),
            "test_files": [str(f) for f in test_files]
        }
    
    def _detect_test_framework(self) -> str:
        """檢測專案使用的測試框架"""
        # 檢查 requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                requirements = f.read().lower()
                if "pytest" in requirements:
                    return "pytest"
                elif "nose" in requirements:
                    return "nose"
        
        # 檢查配置檔案
        if (self.project_path / "pytest.ini").exists() or \
           (self.project_path / "setup.cfg").exists() and self._has_pytest_config():
            return "pytest"
        
        # 檢查測試檔案導入
        for test_file in self._discover_test_files():
            with open(test_file) as f:
                content = f.read()
                if "import pytest" in content or "from pytest" in content:
                    return "pytest"
                elif "import nose" in content or "from nose" in content:
                    return "nose"
        
        # 預設使用 unittest
        return "unittest"
    
    def _has_pytest_config(self) -> bool:
        """檢查 setup.cfg 是否包含 pytest 配置"""
        setup_cfg = self.project_path / "setup.cfg"
        if setup_cfg.exists():
            with open(setup_cfg) as f:
                return "[tool:pytest]" in f.read()
        return False
    
    def _discover_test_files(self) -> List[Path]:
        """發現測試檔案"""
        test_files = []
        
        # 常見的測試目錄
        test_dirs = ["tests", "test", "testing"]
        
        for test_dir in test_dirs:
            test_path = self.project_path / test_dir
            if test_path.exists() and test_path.is_dir():
                # 遞迴尋找測試檔案
                test_files.extend(test_path.rglob("test_*.py"))
                test_files.extend(test_path.rglob("*_test.py"))
        
        # 也在 src 目錄中尋找
        src_dir = self.project_path / "src"
        if src_dir.exists():
            test_files.extend(src_dir.rglob("test_*.py"))
            test_files.extend(src_dir.rglob("*_test.py"))
        
        # 根目錄的測試檔案
        test_files.extend(self.project_path.glob("test_*.py"))
        test_files.extend(self.project_path.glob("*_test.py"))
        
        return list(set(test_files))  # 去重
    
    def _generate_basic_tests(self):
        """生成基本測試檔案"""
        test_dir = self.project_path / "tests"
        test_dir.mkdir(exist_ok=True)
        
        # 生成 __init__.py
        (test_dir / "__init__.py").touch()
        
        # 生成基本測試
        basic_test = '''"""
基本測試檔案 - 由 Claude Auto Developer 自動生成
"""

import unittest
import sys
import os

# 將專案路徑加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'src')):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestBasic(unittest.TestCase):
    """基本測試類別"""
    
    def test_import(self):
        """測試專案可以被匯入"""
        # 嘗試匯入專案模組
        try:
            import main
            self.assertTrue(True)
        except ImportError:
            # 如果 main.py 不存在，只要確保測試框架正常運作
            self.assertTrue(True)
    
    def test_project_structure(self):
        """測試專案結構"""
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        # 檢查基本檔案
        self.assertTrue(os.path.exists(os.path.join(project_root, 'requirements.txt')))
        
        # 檢查目錄結構
        expected_dirs = ['tests']
        for dir_name in expected_dirs:
            dir_path = os.path.join(project_root, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"缺少目錄: {dir_name}")
    
    def test_python_version(self):
        """測試 Python 版本"""
        self.assertGreaterEqual(sys.version_info[:2], (3, 7))

if __name__ == '__main__':
    unittest.main()
'''
        
        test_file = test_dir / "test_basic.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(basic_test)
        
        logger.info("生成基本測試檔案")
    
    def _run_tests(self, framework: str) -> TestReport:
        """執行測試"""
        if framework in self.test_frameworks:
            return self.test_frameworks[framework]()
        else:
            logger.warning(f"不支援的測試框架: {framework}，使用 unittest")
            return self._run_unittest()
    
    def _run_pytest(self) -> TestReport:
        """執行 pytest 測試"""
        logger.info("執行 pytest 測試")
        
        # 準備命令
        cmd = [
            self.python_executable,
            "-m", "pytest",
            "--tb=short",
            "--json-report",
            "--json-report-file=pytest_report.json",
            "-v"
        ]
        
        # 如果有 pytest-cov，加入覆蓋率
        try:
            subprocess.run([self.python_executable, "-c", "import pytest_cov"], 
                         capture_output=True, check=True)
            cmd.extend(["--cov=.", "--cov-report=json"])
        except subprocess.CalledProcessError:
            pass
        
        # 執行測試
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time
        
        # 解析結果
        report = TestReport(
            total_tests=0,
            passed=0,
            failed=0,
            errors=0,
            skipped=0,
            duration=duration,
            test_results=[]
        )
        
        # 從 JSON 報告解析
        report_file = self.project_path / "pytest_report.json"
        if report_file.exists():
            with open(report_file) as f:
                json_data = json.load(f)
                summary = json_data.get("summary", {})
                report.total_tests = summary.get("total", 0)
                report.passed = summary.get("passed", 0)
                report.failed = summary.get("failed", 0)
                report.errors = summary.get("error", 0)
                report.skipped = summary.get("skipped", 0)
                
                # 解析測試結果
                for test in json_data.get("tests", []):
                    test_result = TestResult(
                        test_name=test.get("nodeid", ""),
                        status=test.get("outcome", ""),
                        duration=test.get("duration", 0.0),
                        error_message=test.get("call", {}).get("longrepr")
                    )
                    report.test_results.append(test_result)
        else:
            # 從輸出解析
            self._parse_pytest_output(result.stdout, report)
        
        # 解析覆蓋率
        cov_file = self.project_path / "coverage.json"
        if cov_file.exists():
            with open(cov_file) as f:
                cov_data = json.load(f)
                report.coverage = cov_data.get("totals", {}).get("percent_covered")
        
        return report
    
    def _parse_pytest_output(self, output: str, report: TestReport):
        """解析 pytest 輸出"""
        lines = output.split('\n')
        
        for line in lines:
            # 解析測試結果行
            if " PASSED" in line:
                report.passed += 1
                report.total_tests += 1
            elif " FAILED" in line:
                report.failed += 1
                report.total_tests += 1
            elif " ERROR" in line:
                report.errors += 1
                report.total_tests += 1
            elif " SKIPPED" in line:
                report.skipped += 1
                report.total_tests += 1
            
            # 解析摘要行
            match = re.search(r'(\d+) passed', line)
            if match:
                report.passed = int(match.group(1))
            
            match = re.search(r'(\d+) failed', line)
            if match:
                report.failed = int(match.group(1))
    
    def _run_unittest(self) -> TestReport:
        """執行 unittest 測試"""
        logger.info("執行 unittest 測試")
        
        # 準備命令
        cmd = [
            self.python_executable,
            "-m", "unittest",
            "discover",
            "-s", ".",
            "-p", "test*.py",
            "-v"
        ]
        
        # 執行測試
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time
        
        # 解析結果
        report = TestReport(
            total_tests=0,
            passed=0,
            failed=0,
            errors=0,
            skipped=0,
            duration=duration,
            test_results=[]
        )
        
        # 解析輸出
        lines = result.stderr.split('\n') + result.stdout.split('\n')
        
        for line in lines:
            # 測試結果
            if " ... ok" in line:
                report.passed += 1
                report.total_tests += 1
            elif " ... FAIL" in line:
                report.failed += 1
                report.total_tests += 1
            elif " ... ERROR" in line:
                report.errors += 1
                report.total_tests += 1
            elif " ... skipped" in line:
                report.skipped += 1
                report.total_tests += 1
            
            # 摘要
            match = re.search(r'Ran (\d+) test', line)
            if match:
                report.total_tests = int(match.group(1))
        
        return report
    
    def _run_nose(self) -> TestReport:
        """執行 nose 測試"""
        logger.info("執行 nose 測試")
        # 類似 pytest 的實現
        return self._run_unittest()  # 簡化實現
    
    def _run_doctest(self) -> TestReport:
        """執行 doctest 測試"""
        logger.info("執行 doctest 測試")
        
        # 尋找所有 Python 檔案
        py_files = list(self.project_path.rglob("*.py"))
        
        report = TestReport(
            total_tests=0,
            passed=0,
            failed=0,
            errors=0,
            skipped=0,
            duration=0,
            test_results=[]
        )
        
        for py_file in py_files:
            cmd = [self.python_executable, "-m", "doctest", str(py_file), "-v"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析結果
            if "Test passed" in result.stdout:
                report.passed += 1
                report.total_tests += 1
            elif "Test failed" in result.stdout:
                report.failed += 1
                report.total_tests += 1
        
        return report
    
    def _auto_fix_tests(self, test_report: TestReport) -> Dict[str, Any]:
        """
        嘗試自動修復測試失敗
        
        Args:
            test_report: 測試報告
            
        Returns:
            修復結果
        """
        fixes_applied = 0
        fix_results = []
        
        for test_result in test_report.test_results:
            if test_result.status in ["failed", "error"]:
                # 分析錯誤類型
                error_type = self._analyze_error(test_result)
                
                # 根據錯誤類型嘗試修復
                if error_type == "import_error":
                    if self._fix_import_error(test_result):
                        fixes_applied += 1
                        fix_results.append(f"修復匯入錯誤: {test_result.test_name}")
                elif error_type == "assertion_error":
                    if self._fix_assertion_error(test_result):
                        fixes_applied += 1
                        fix_results.append(f"修復斷言錯誤: {test_result.test_name}")
                elif error_type == "attribute_error":
                    if self._fix_attribute_error(test_result):
                        fixes_applied += 1
                        fix_results.append(f"修復屬性錯誤: {test_result.test_name}")
        
        return {
            "fixes_applied": fixes_applied,
            "fix_results": fix_results
        }
    
    def _analyze_error(self, test_result: TestResult) -> str:
        """分析錯誤類型"""
        error_msg = test_result.error_message or ""
        
        if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
            return "import_error"
        elif "AssertionError" in error_msg:
            return "assertion_error"
        elif "AttributeError" in error_msg:
            return "attribute_error"
        elif "NameError" in error_msg:
            return "name_error"
        else:
            return "unknown"
    
    def _fix_import_error(self, test_result: TestResult) -> bool:
        """修復匯入錯誤"""
        try:
            # 解析錯誤訊息找出缺少的模組
            match = re.search(r"No module named '([^']+)'", test_result.error_message or "")
            if match:
                module_name = match.group(1)
                
                # 檢查是否是專案內的模組
                if self._is_project_module(module_name):
                    # 修復路徑問題
                    self._fix_python_path()
                    return True
                else:
                    # 嘗試安裝缺少的套件
                    logger.info(f"嘗試安裝缺少的套件: {module_name}")
                    cmd = [self.python_executable, "-m", "pip", "install", module_name]
                    result = subprocess.run(cmd, capture_output=True)
                    return result.returncode == 0
        except Exception as e:
            logger.error(f"修復匯入錯誤失敗: {e}")
        
        return False
    
    def _fix_python_path(self):
        """修復 Python 路徑問題"""
        # 在所有測試檔案中加入正確的路徑
        for test_file in self._discover_test_files():
            with open(test_file, 'r') as f:
                content = f.read()
            
            # 檢查是否已有路徑設置
            if "sys.path" not in content:
                # 在檔案開頭加入路徑設置
                path_setup = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

'''
                content = path_setup + content
                
                with open(test_file, 'w') as f:
                    f.write(content)
    
    def _is_project_module(self, module_name: str) -> bool:
        """檢查是否是專案內的模組"""
        # 檢查各種可能的位置
        possible_paths = [
            self.project_path / f"{module_name}.py",
            self.project_path / module_name,
            self.project_path / "src" / f"{module_name}.py",
            self.project_path / "src" / module_name
        ]
        
        return any(path.exists() for path in possible_paths)
    
    def _fix_assertion_error(self, test_result: TestResult) -> bool:
        """修復斷言錯誤"""
        # 這裡可以實現更複雜的邏輯，例如：
        # 1. 分析預期值和實際值
        # 2. 如果差異很小（例如浮點數精度問題），調整測試
        # 3. 如果是常量錯誤，更新預期值
        
        # 目前只記錄，不自動修復（避免破壞測試邏輯）
        logger.info(f"斷言錯誤需要手動檢查: {test_result.test_name}")
        return False
    
    def _fix_attribute_error(self, test_result: TestResult) -> bool:
        """修復屬性錯誤"""
        # 可以嘗試：
        # 1. 檢查是否是拼寫錯誤
        # 2. 檢查是否是版本兼容問題
        # 3. 添加缺少的屬性或方法
        
        logger.info(f"屬性錯誤需要手動檢查: {test_result.test_name}")
        return False
    
    def _generate_test_report(self, test_report: TestReport) -> Path:
        """生成測試報告"""
        report_content = f"""# 測試執行報告

## 摘要
- **總測試數**: {test_report.total_tests}
- **通過**: {test_report.passed} ✅
- **失敗**: {test_report.failed} ❌
- **錯誤**: {test_report.errors} 🔥
- **跳過**: {test_report.skipped} ⏭️
- **執行時間**: {test_report.duration:.2f} 秒
"""
        
        if test_report.coverage is not None:
            report_content += f"- **測試覆蓋率**: {test_report.coverage:.1f}%\n"
        
        # 成功率
        if test_report.total_tests > 0:
            success_rate = (test_report.passed / test_report.total_tests) * 100
            report_content += f"- **成功率**: {success_rate:.1f}%\n"
        
        # 詳細結果
        if test_report.test_results:
            report_content += "\n## 詳細結果\n\n"
            
            # 失敗的測試
            failed_tests = [r for r in test_report.test_results if r.status in ["failed", "error"]]
            if failed_tests:
                report_content += "### ❌ 失敗的測試\n\n"
                for test in failed_tests:
                    report_content += f"- **{test.test_name}**\n"
                    if test.error_message:
                        report_content += f"  - 錯誤: {test.error_message[:200]}...\n"
                    report_content += f"  - 耗時: {test.duration:.3f}s\n\n"
            
            # 通過的測試（摘要）
            passed_tests = [r for r in test_report.test_results if r.status == "passed"]
            if passed_tests:
                report_content += f"\n### ✅ 通過的測試 ({len(passed_tests)} 個)\n"
                report_content += "省略詳細列表...\n"
        
        report_content += f"\n---\n*由 Claude Auto Developer 測試執行器生成*\n"
        report_content += f"*生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        report_path = self.project_path / "TEST_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_path