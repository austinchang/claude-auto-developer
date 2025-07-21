#!/usr/bin/env python3
"""
Quality Assessor - 代碼品質評估器
負責評估代碼品質、性能、安全性、可維護性等多個維度
"""

import asyncio
import ast
import json
import logging
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from .model_manager import ModelManager, ModelType

logger = logging.getLogger(__name__)

class QualityDimension(Enum):
    """品質評估維度"""
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    STANDARDS_COMPLIANCE = "standards_compliance"

class SeverityLevel(Enum):
    """嚴重程度等級"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class QualityIssue:
    """品質問題定義"""
    id: str
    dimension: QualityDimension
    severity: SeverityLevel
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    suggestion: str
    impact: str
    effort_to_fix: str  # low, medium, high
    
@dataclass
class QualityMetric:
    """品質指標"""
    dimension: QualityDimension
    name: str
    value: float  # 0.0-1.0
    description: str
    target_value: float
    status: str  # excellent, good, fair, poor

@dataclass
class QualityReport:
    """品質評估報告"""
    project_path: str
    assessment_time: datetime
    overall_score: float  # 0.0-1.0
    dimension_scores: Dict[QualityDimension, float]
    metrics: List[QualityMetric]
    issues: List[QualityIssue]
    recommendations: List[str]
    improvement_plan: Dict[str, Any]
    code_statistics: Dict[str, Any]
    technology_analysis: Dict[str, Any]

class QualityAssessor:
    """代碼品質評估器"""
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        
        # 評估規則配置
        self.quality_rules = self._init_quality_rules()
        
        # 支援的文件類型
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown'
        }
        
        # 評估歷史
        self.assessment_history: List[QualityReport] = []
    
    def _init_quality_rules(self) -> Dict[str, Any]:
        """初始化品質評估規則"""
        return {
            QualityDimension.CODE_QUALITY: {
                "complexity_threshold": 10,
                "line_length_max": 120,
                "function_length_max": 50,
                "class_length_max": 300,
                "nesting_depth_max": 4,
                "duplicate_code_threshold": 0.1
            },
            QualityDimension.PERFORMANCE: {
                "loop_efficiency": True,
                "memory_usage": True,
                "algorithm_complexity": True,
                "database_queries": True
            },
            QualityDimension.SECURITY: {
                "input_validation": True,
                "sql_injection": True,
                "xss_prevention": True,
                "authentication": True,
                "authorization": True,
                "sensitive_data": True
            },
            QualityDimension.MAINTAINABILITY: {
                "naming_conventions": True,
                "code_organization": True,
                "coupling": True,
                "cohesion": True,
                "error_handling": True
            },
            QualityDimension.TESTABILITY: {
                "test_coverage": 0.8,
                "test_quality": True,
                "mockability": True,
                "dependency_injection": True
            },
            QualityDimension.DOCUMENTATION: {
                "code_comments": True,
                "api_documentation": True,
                "readme_quality": True,
                "architecture_docs": True
            }
        }
    
    async def assess_project(
        self,
        project_path: str,
        include_tests: bool = True,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """評估整個專案的品質"""
        
        logger.info(f"開始評估專案品質: {project_path}")
        
        try:
            # 1. 掃描專案文件
            project_files = self._scan_project_files(project_path, include_tests)
            
            # 2. 分析代碼統計
            code_statistics = await self._analyze_code_statistics(project_files)
            
            # 3. 技術分析
            technology_analysis = await self._analyze_technology_stack(project_files)
            
            # 4. 各維度品質評估
            dimension_scores = {}
            all_issues = []
            all_metrics = []
            
            for dimension in QualityDimension:
                logger.info(f"評估 {dimension.value} 維度...")
                
                score, issues, metrics = await self._assess_dimension(
                    dimension, project_files, code_statistics, custom_rules
                )
                
                dimension_scores[dimension] = score
                all_issues.extend(issues)
                all_metrics.extend(metrics)
            
            # 5. 計算整體評分
            overall_score = sum(dimension_scores.values()) / len(dimension_scores)
            
            # 6. 生成改進建議
            recommendations = await self._generate_recommendations(
                dimension_scores, all_issues, code_statistics
            )
            
            # 7. 制定改進計畫
            improvement_plan = await self._create_improvement_plan(
                all_issues, dimension_scores
            )
            
            # 創建品質報告
            report = QualityReport(
                project_path=project_path,
                assessment_time=datetime.now(),
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                metrics=all_metrics,
                issues=all_issues,
                recommendations=recommendations,
                improvement_plan=improvement_plan,
                code_statistics=code_statistics,
                technology_analysis=technology_analysis
            )
            
            # 記錄評估歷史
            self.assessment_history.append(report)
            
            logger.info(f"品質評估完成，整體評分: {overall_score:.2f}")
            return report
            
        except Exception as e:
            logger.error(f"品質評估失敗: {str(e)}")
            raise
    
    def _scan_project_files(self, project_path: str, include_tests: bool) -> List[Dict[str, Any]]:
        """掃描專案文件"""
        
        files = []
        project_root = Path(project_path)
        
        # 忽略的目錄
        ignore_dirs = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.env', 'dist', 'build', '.idea', '.vscode',
            'coverage', '.coverage', 'htmlcov'
        }
        
        if not include_tests:
            ignore_dirs.update({'tests', 'test', '__tests__', 'spec'})
        
        for file_path in project_root.rglob('*'):
            if file_path.is_file():
                # 檢查是否在忽略目錄中
                if any(ignored in file_path.parts for ignored in ignore_dirs):
                    continue
                
                # 檢查文件擴展名
                extension = file_path.suffix.lower()
                if extension in self.supported_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        files.append({
                            'path': str(file_path),
                            'relative_path': str(file_path.relative_to(project_root)),
                            'extension': extension,
                            'language': self.supported_extensions[extension],
                            'content': content,
                            'size': len(content),
                            'lines': len(content.splitlines())
                        })
                        
                    except (UnicodeDecodeError, PermissionError) as e:
                        logger.warning(f"無法讀取文件 {file_path}: {str(e)}")
                        continue
        
        logger.info(f"掃描到 {len(files)} 個代碼文件")
        return files
    
    async def _analyze_code_statistics(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析代碼統計資訊"""
        
        stats = {
            'total_files': len(files),
            'total_lines': sum(f['lines'] for f in files),
            'total_size': sum(f['size'] for f in files),
            'languages': {},
            'file_sizes': [],
            'complexity_distribution': {},
            'duplication_rate': 0.0
        }
        
        # 語言分布統計
        for file_info in files:
            lang = file_info['language']
            if lang not in stats['languages']:
                stats['languages'][lang] = {
                    'files': 0,
                    'lines': 0,
                    'size': 0
                }
            
            stats['languages'][lang]['files'] += 1
            stats['languages'][lang]['lines'] += file_info['lines']
            stats['languages'][lang]['size'] += file_info['size']
            
            stats['file_sizes'].append(file_info['lines'])
        
        # Python 代碼特殊分析
        python_files = [f for f in files if f['language'] == 'python']
        if python_files:
            stats['python_analysis'] = await self._analyze_python_code(python_files)
        
        # JavaScript/TypeScript 代碼分析
        js_files = [f for f in files if f['language'] in ['javascript', 'typescript']]
        if js_files:
            stats['javascript_analysis'] = await self._analyze_javascript_code(js_files)
        
        return stats
    
    async def _analyze_python_code(self, python_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析 Python 代碼"""
        
        analysis = {
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'complexity_issues': [],
            'style_issues': []
        }
        
        for file_info in python_files:
            try:
                tree = ast.parse(file_info['content'])
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        analysis['functions'] += 1
                        
                        # 檢查函數複雜度
                        complexity = self._calculate_cyclomatic_complexity(node)
                        if complexity > self.quality_rules[QualityDimension.CODE_QUALITY]['complexity_threshold']:
                            analysis['complexity_issues'].append({
                                'file': file_info['relative_path'],
                                'function': node.name,
                                'line': node.lineno,
                                'complexity': complexity
                            })
                    
                    elif isinstance(node, ast.ClassDef):
                        analysis['classes'] += 1
                    
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        analysis['imports'] += 1
                        
            except SyntaxError as e:
                logger.warning(f"Python 語法錯誤 {file_info['relative_path']}: {str(e)}")
                continue
        
        return analysis
    
    async def _analyze_javascript_code(self, js_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析 JavaScript/TypeScript 代碼"""
        
        analysis = {
            'functions': 0,
            'classes': 0,
            'modules': 0,
            'potential_issues': []
        }
        
        for file_info in js_files:
            content = file_info['content']
            
            # 簡單的正則表達式分析（實際項目中應使用專業的 JS 解析器）
            function_matches = re.findall(r'function\s+\w+|(?:\w+\s*=\s*)?(?:async\s+)?(?:\([^)]*\)\s*=>\s*|\w+\([^)]*\)\s*{)', content)
            class_matches = re.findall(r'class\s+\w+', content)
            import_matches = re.findall(r'import\s+.*?from|require\s*\(', content)
            
            analysis['functions'] += len(function_matches)
            analysis['classes'] += len(class_matches)
            analysis['modules'] += len(import_matches)
            
            # 檢查常見問題
            if 'eval(' in content:
                analysis['potential_issues'].append({
                    'file': file_info['relative_path'],
                    'issue': 'eval() usage detected',
                    'severity': 'high'
                })
            
            if 'innerHTML' in content:
                analysis['potential_issues'].append({
                    'file': file_info['relative_path'],
                    'issue': 'innerHTML usage detected (potential XSS)',
                    'severity': 'medium'
                })
        
        return analysis
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """計算循環複雜度"""
        
        complexity = 1  # 基本複雜度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    async def _analyze_technology_stack(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析技術棧"""
        
        tech_analysis = {
            'frameworks': [],
            'libraries': [],
            'databases': [],
            'build_tools': [],
            'testing_frameworks': []
        }
        
        # 檢查配置文件
        config_files = [f for f in files if f['relative_path'] in [
            'package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml',
            'go.mod', 'composer.json', 'Gemfile'
        ]]
        
        for config_file in config_files:
            content = config_file['content']
            
            if config_file['relative_path'] == 'package.json':
                tech_analysis.update(self._analyze_package_json(content))
            elif config_file['relative_path'] == 'requirements.txt':
                tech_analysis.update(self._analyze_requirements_txt(content))
        
        # 分析代碼中的導入
        for file_info in files:
            if file_info['language'] == 'python':
                imports = self._extract_python_imports(file_info['content'])
                tech_analysis['libraries'].extend(imports)
            elif file_info['language'] in ['javascript', 'typescript']:
                imports = self._extract_js_imports(file_info['content'])
                tech_analysis['libraries'].extend(imports)
        
        # 去重
        for key in tech_analysis:
            if isinstance(tech_analysis[key], list):
                tech_analysis[key] = list(set(tech_analysis[key]))
        
        return tech_analysis
    
    def _analyze_package_json(self, content: str) -> Dict[str, List[str]]:
        """分析 package.json"""
        
        result = {
            'frameworks': [],
            'libraries': [],
            'build_tools': [],
            'testing_frameworks': []
        }
        
        try:
            data = json.loads(content)
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            
            # 框架識別
            frameworks = ['react', 'vue', 'angular', 'express', 'nestjs', 'next', 'nuxt']
            for fw in frameworks:
                if any(fw in dep for dep in dependencies):
                    result['frameworks'].append(fw)
            
            # 測試框架
            test_frameworks = ['jest', 'mocha', 'jasmine', 'cypress', 'playwright']
            for tf in test_frameworks:
                if any(tf in dep for dep in dependencies):
                    result['testing_frameworks'].append(tf)
            
            # 構建工具
            build_tools = ['webpack', 'vite', 'rollup', 'parcel', 'babel']
            for bt in build_tools:
                if any(bt in dep for dep in dependencies):
                    result['build_tools'].append(bt)
                    
        except json.JSONDecodeError:
            pass
        
        return result
    
    def _analyze_requirements_txt(self, content: str) -> Dict[str, List[str]]:
        """分析 requirements.txt"""
        
        result = {
            'frameworks': [],
            'libraries': [],
            'testing_frameworks': []
        }
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip().lower()
            if line and not line.startswith('#'):
                package = line.split('==')[0].split('>=')[0].split('<=')[0]
                
                # 框架識別
                if package in ['django', 'flask', 'fastapi', 'tornado']:
                    result['frameworks'].append(package)
                
                # 測試框架
                elif package in ['pytest', 'unittest2', 'nose', 'behave']:
                    result['testing_frameworks'].append(package)
                
                else:
                    result['libraries'].append(package)
        
        return result
    
    def _extract_python_imports(self, content: str) -> List[str]:
        """提取 Python 導入"""
        
        imports = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
                        
        except SyntaxError:
            pass
        
        return imports
    
    def _extract_js_imports(self, content: str) -> List[str]:
        """提取 JavaScript 導入"""
        
        imports = []
        
        # ES6 imports
        import_matches = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        imports.extend(import_matches)
        
        # CommonJS requires
        require_matches = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
        imports.extend(require_matches)
        
        # 只保留包名（去除相對路徑）
        package_imports = [imp for imp in imports if not imp.startswith('.')]
        
        return package_imports
    
    async def _assess_dimension(
        self,
        dimension: QualityDimension,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any],
        custom_rules: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估特定維度的品質"""
        
        issues = []
        metrics = []
        
        if dimension == QualityDimension.CODE_QUALITY:
            score, dim_issues, dim_metrics = await self._assess_code_quality(files, code_stats)
        
        elif dimension == QualityDimension.PERFORMANCE:
            score, dim_issues, dim_metrics = await self._assess_performance(files, code_stats)
        
        elif dimension == QualityDimension.SECURITY:
            score, dim_issues, dim_metrics = await self._assess_security(files, code_stats)
        
        elif dimension == QualityDimension.MAINTAINABILITY:
            score, dim_issues, dim_metrics = await self._assess_maintainability(files, code_stats)
        
        elif dimension == QualityDimension.TESTABILITY:
            score, dim_issues, dim_metrics = await self._assess_testability(files, code_stats)
        
        elif dimension == QualityDimension.DOCUMENTATION:
            score, dim_issues, dim_metrics = await self._assess_documentation(files, code_stats)
        
        elif dimension == QualityDimension.ARCHITECTURE:
            score, dim_issues, dim_metrics = await self._assess_architecture(files, code_stats)
        
        elif dimension == QualityDimension.STANDARDS_COMPLIANCE:
            score, dim_issues, dim_metrics = await self._assess_standards_compliance(files, code_stats)
        
        else:
            score = 0.5
            dim_issues = []
            dim_metrics = []
        
        issues.extend(dim_issues)
        metrics.extend(dim_metrics)
        
        return score, issues, metrics
    
    async def _assess_code_quality(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估代碼品質"""
        
        issues = []
        metrics = []
        scores = []
        
        # 複雜度評估
        complexity_issues = 0
        if 'python_analysis' in code_stats:
            complexity_issues = len(code_stats['python_analysis'].get('complexity_issues', []))
        
        complexity_score = max(0, 1.0 - complexity_issues * 0.1)
        scores.append(complexity_score)
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.CODE_QUALITY,
            name="Cyclomatic Complexity",
            value=complexity_score,
            description="代碼循環複雜度評分",
            target_value=0.8,
            status="good" if complexity_score >= 0.8 else "fair" if complexity_score >= 0.6 else "poor"
        ))
        
        # 代碼長度評估
        long_files = sum(1 for f in files if f['lines'] > 500)
        file_length_score = max(0, 1.0 - long_files / len(files))
        scores.append(file_length_score)
        
        if long_files > 0:
            issues.append(QualityIssue(
                id="CQ001",
                dimension=QualityDimension.CODE_QUALITY,
                severity=SeverityLevel.MEDIUM,
                title="文件過長",
                description=f"發現 {long_files} 個文件超過 500 行",
                file_path="multiple",
                line_number=None,
                code_snippet=None,
                suggestion="考慮拆分大文件為更小的模組",
                impact="降低代碼可讀性和維護性",
                effort_to_fix="medium"
            ))
        
        # 命名規範評估
        naming_score = await self._assess_naming_conventions(files)
        scores.append(naming_score)
        
        overall_score = sum(scores) / len(scores)
        
        return overall_score, issues, metrics
    
    async def _assess_performance(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估性能"""
        
        issues = []
        metrics = []
        score = 0.7  # 預設評分
        
        # 檢查 JavaScript 性能問題
        if 'javascript_analysis' in code_stats:
            js_issues = code_stats['javascript_analysis'].get('potential_issues', [])
            perf_issues = [issue for issue in js_issues if 'performance' in issue.get('issue', '').lower()]
            
            if perf_issues:
                score -= len(perf_issues) * 0.1
                
                for issue in perf_issues:
                    issues.append(QualityIssue(
                        id="PERF001",
                        dimension=QualityDimension.PERFORMANCE,
                        severity=SeverityLevel.MEDIUM,
                        title="性能問題",
                        description=issue['issue'],
                        file_path=issue['file'],
                        line_number=None,
                        code_snippet=None,
                        suggestion="優化代碼邏輯以提升性能",
                        impact="可能影響應用程式響應速度",
                        effort_to_fix="medium"
                    ))
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.PERFORMANCE,
            name="Performance Score",
            value=max(0, score),
            description="整體性能評分",
            target_value=0.8,
            status="good" if score >= 0.8 else "fair" if score >= 0.6 else "poor"
        ))
        
        return max(0, score), issues, metrics
    
    async def _assess_security(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估安全性"""
        
        issues = []
        metrics = []
        score = 0.8  # 預設評分
        
        # 檢查常見安全問題
        for file_info in files:
            content = file_info['content'].lower()
            
            # SQL 注入風險
            if 'execute(' in content and 'format(' in content:
                issues.append(QualityIssue(
                    id="SEC001",
                    dimension=QualityDimension.SECURITY,
                    severity=SeverityLevel.HIGH,
                    title="潛在 SQL 注入風險",
                    description="使用字符串格式化構建 SQL 查詢",
                    file_path=file_info['relative_path'],
                    line_number=None,
                    code_snippet=None,
                    suggestion="使用參數化查詢或 ORM",
                    impact="可能導致數據洩露或破壞",
                    effort_to_fix="medium"
                ))
                score -= 0.2
            
            # 硬編碼密碼/密鑰
            password_patterns = [
                r'password\s*=\s*[\'"][^\'"]{3,}[\'"]',
                r'secret\s*=\s*[\'"][^\'"]{10,}[\'"]',
                r'api_key\s*=\s*[\'"][^\'"]{10,}[\'"]'
            ]
            
            for pattern in password_patterns:
                if re.search(pattern, content):
                    issues.append(QualityIssue(
                        id="SEC002",
                        dimension=QualityDimension.SECURITY,
                        severity=SeverityLevel.CRITICAL,
                        title="硬編碼敏感資訊",
                        description="在代碼中發現硬編碼的密碼或密鑰",
                        file_path=file_info['relative_path'],
                        line_number=None,
                        code_snippet=None,
                        suggestion="使用環境變數或配置文件存儲敏感資訊",
                        impact="敏感資訊可能被洩露",
                        effort_to_fix="low"
                    ))
                    score -= 0.3
        
        # JavaScript 特殊安全檢查
        if 'javascript_analysis' in code_stats:
            js_issues = code_stats['javascript_analysis'].get('potential_issues', [])
            security_issues = [issue for issue in js_issues if issue.get('severity') in ['high', 'critical']]
            
            for issue in security_issues:
                issues.append(QualityIssue(
                    id="SEC003",
                    dimension=QualityDimension.SECURITY,
                    severity=SeverityLevel.HIGH if issue['severity'] == 'high' else SeverityLevel.CRITICAL,
                    title="JavaScript 安全問題",
                    description=issue['issue'],
                    file_path=issue['file'],
                    line_number=None,
                    code_snippet=None,
                    suggestion="修復安全漏洞",
                    impact="可能導致 XSS 或其他安全問題",
                    effort_to_fix="medium"
                ))
                score -= 0.15
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.SECURITY,
            name="Security Score",
            value=max(0, score),
            description="整體安全評分",
            target_value=0.9,
            status="excellent" if score >= 0.9 else "good" if score >= 0.7 else "poor"
        ))
        
        return max(0, score), issues, metrics
    
    async def _assess_maintainability(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估可維護性"""
        
        issues = []
        metrics = []
        scores = []
        
        # 文件組織評估
        directory_structure_score = self._assess_directory_structure(files)
        scores.append(directory_structure_score)
        
        # 代碼重複評估
        duplication_score = 1.0 - code_stats.get('duplication_rate', 0.0)
        scores.append(duplication_score)
        
        # 函數長度評估
        if 'python_analysis' in code_stats:
            python_analysis = code_stats['python_analysis']
            # 這裡應該檢查函數長度，暫時使用簡化邏輯
            function_length_score = 0.8  # 預設值
            scores.append(function_length_score)
        
        overall_score = sum(scores) / len(scores)
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.MAINTAINABILITY,
            name="Maintainability Index",
            value=overall_score,
            description="可維護性指數",
            target_value=0.75,
            status="good" if overall_score >= 0.75 else "fair" if overall_score >= 0.5 else "poor"
        ))
        
        return overall_score, issues, metrics
    
    async def _assess_testability(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估可測試性"""
        
        issues = []
        metrics = []
        
        # 測試文件比例
        test_files = [f for f in files if self._is_test_file(f['relative_path'])]
        test_ratio = len(test_files) / len(files) if files else 0
        
        # 測試覆蓋率估算（基於測試文件比例）
        estimated_coverage = min(test_ratio * 2, 1.0)  # 簡化估算
        
        if estimated_coverage < 0.5:
            issues.append(QualityIssue(
                id="TEST001",
                dimension=QualityDimension.TESTABILITY,
                severity=SeverityLevel.MEDIUM,
                title="測試覆蓋率不足",
                description=f"估計測試覆蓋率只有 {estimated_coverage*100:.1f}%",
                file_path="project",
                line_number=None,
                code_snippet=None,
                suggestion="增加單元測試和整合測試",
                impact="降低代碼品質保證",
                effort_to_fix="high"
            ))
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.TESTABILITY,
            name="Test Coverage",
            value=estimated_coverage,
            description="估計測試覆蓋率",
            target_value=0.8,
            status="good" if estimated_coverage >= 0.8 else "fair" if estimated_coverage >= 0.5 else "poor"
        ))
        
        return estimated_coverage, issues, metrics
    
    async def _assess_documentation(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估文檔品質"""
        
        issues = []
        metrics = []
        scores = []
        
        # README 文件檢查
        readme_files = [f for f in files if f['relative_path'].lower().startswith('readme')]
        readme_score = 1.0 if readme_files else 0.0
        scores.append(readme_score)
        
        if not readme_files:
            issues.append(QualityIssue(
                id="DOC001",
                dimension=QualityDimension.DOCUMENTATION,
                severity=SeverityLevel.MEDIUM,
                title="缺少 README 文件",
                description="專案根目錄缺少 README 文件",
                file_path="project_root",
                line_number=None,
                code_snippet=None,
                suggestion="創建詳細的 README.md 文件",
                impact="降低專案可理解性",
                effort_to_fix="low"
            ))
        
        # 代碼註釋評估
        comment_ratio = self._calculate_comment_ratio(files)
        comment_score = min(comment_ratio * 5, 1.0)  # 20% 註釋率得滿分
        scores.append(comment_score)
        
        if comment_ratio < 0.1:
            issues.append(QualityIssue(
                id="DOC002",
                dimension=QualityDimension.DOCUMENTATION,
                severity=SeverityLevel.LOW,
                title="代碼註釋不足",
                description=f"代碼註釋比例只有 {comment_ratio*100:.1f}%",
                file_path="multiple",
                line_number=None,
                code_snippet=None,
                suggestion="增加有意義的代碼註釋",
                impact="降低代碼可讀性",
                effort_to_fix="medium"
            ))
        
        overall_score = sum(scores) / len(scores)
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.DOCUMENTATION,
            name="Documentation Score",
            value=overall_score,
            description="文檔品質評分",
            target_value=0.7,
            status="good" if overall_score >= 0.7 else "fair" if overall_score >= 0.4 else "poor"
        ))
        
        return overall_score, issues, metrics
    
    async def _assess_architecture(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估架構品質"""
        
        issues = []
        metrics = []
        
        # 目錄結構評估
        structure_score = self._assess_directory_structure(files)
        
        # 模組化程度評估
        modularity_score = self._assess_modularity(files, code_stats)
        
        overall_score = (structure_score + modularity_score) / 2
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.ARCHITECTURE,
            name="Architecture Score",
            value=overall_score,
            description="架構品質評分",
            target_value=0.75,
            status="good" if overall_score >= 0.75 else "fair" if overall_score >= 0.5 else "poor"
        ))
        
        return overall_score, issues, metrics
    
    async def _assess_standards_compliance(
        self,
        files: List[Dict[str, Any]],
        code_stats: Dict[str, Any]
    ) -> Tuple[float, List[QualityIssue], List[QualityMetric]]:
        """評估標準合規性"""
        
        issues = []
        metrics = []
        score = 0.8  # 預設評分
        
        # 檢查編碼標準
        for file_info in files:
            if file_info['language'] == 'python':
                # 檢查 PEP 8 相關標準
                lines = file_info['content'].split('\n')
                for i, line in enumerate(lines):
                    if len(line) > 120:  # 行長度檢查
                        issues.append(QualityIssue(
                            id="STD001",
                            dimension=QualityDimension.STANDARDS_COMPLIANCE,
                            severity=SeverityLevel.LOW,
                            title="行長度超出標準",
                            description="代碼行長度超過 120 字符",
                            file_path=file_info['relative_path'],
                            line_number=i + 1,
                            code_snippet=line[:100] + "..." if len(line) > 100 else line,
                            suggestion="縮短代碼行或適當換行",
                            impact="降低代碼可讀性",
                            effort_to_fix="low"
                        ))
                        score -= 0.01
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.STANDARDS_COMPLIANCE,
            name="Standards Compliance",
            value=max(0, score),
            description="編碼標準合規性",
            target_value=0.9,
            status="excellent" if score >= 0.9 else "good" if score >= 0.7 else "fair"
        ))
        
        return max(0, score), issues, metrics
    
    def _is_test_file(self, file_path: str) -> bool:
        """判斷是否為測試文件"""
        
        test_indicators = [
            'test_', '_test.', 'test.', '.test.',
            'spec_', '_spec.', 'spec.', '.spec.',
            '/tests/', '/test/', '/__tests__/',
            '.test.', '.spec.'
        ]
        
        return any(indicator in file_path.lower() for indicator in test_indicators)
    
    def _calculate_comment_ratio(self, files: List[Dict[str, Any]]) -> float:
        """計算註釋比例"""
        
        total_lines = 0
        comment_lines = 0
        
        for file_info in files:
            lines = file_info['content'].split('\n')
            total_lines += len(lines)
            
            for line in lines:
                stripped_line = line.strip()
                
                # Python 註釋
                if file_info['language'] == 'python' and stripped_line.startswith('#'):
                    comment_lines += 1
                
                # JavaScript/TypeScript 註釋
                elif file_info['language'] in ['javascript', 'typescript']:
                    if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                        comment_lines += 1
                
                # Java 註釋
                elif file_info['language'] == 'java':
                    if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                        comment_lines += 1
        
        return comment_lines / total_lines if total_lines > 0 else 0.0
    
    def _assess_directory_structure(self, files: List[Dict[str, Any]]) -> float:
        """評估目錄結構"""
        
        # 檢查是否有良好的目錄結構
        directories = set()
        for file_info in files:
            parts = Path(file_info['relative_path']).parts
            if len(parts) > 1:
                directories.add(parts[0])
        
        # 良好的目錄結構指標
        good_dirs = {'src', 'lib', 'app', 'components', 'utils', 'services', 'models', 'views', 'controllers'}
        structure_score = len(good_dirs.intersection(directories)) / len(good_dirs)
        
        return min(structure_score * 2, 1.0)  # 有一半好目錄就得滿分
    
    def _assess_modularity(self, files: List[Dict[str, Any]], code_stats: Dict[str, Any]) -> float:
        """評估模組化程度"""
        
        # 基於文件數量和平均大小評估模組化
        if not files:
            return 0.0
        
        avg_file_size = sum(f['lines'] for f in files) / len(files)
        
        # 理想的文件大小是 100-300 行
        if 100 <= avg_file_size <= 300:
            size_score = 1.0
        elif avg_file_size < 100:
            size_score = avg_file_size / 100
        else:
            size_score = max(0, 1.0 - (avg_file_size - 300) / 700)
        
        return size_score
    
    async def _assess_naming_conventions(self, files: List[Dict[str, Any]]) -> float:
        """評估命名規範"""
        
        score = 0.8  # 預設評分
        
        # 檢查 Python 命名規範
        python_files = [f for f in files if f['language'] == 'python']
        
        for file_info in python_files:
            try:
                tree = ast.parse(file_info['content'])
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 檢查函數命名（應該是 snake_case）
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                            score -= 0.01
                    
                    elif isinstance(node, ast.ClassDef):
                        # 檢查類命名（應該是 PascalCase）
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            score -= 0.01
                            
            except SyntaxError:
                continue
        
        return max(0, score)
    
    async def _generate_recommendations(
        self,
        dimension_scores: Dict[QualityDimension, float],
        issues: List[QualityIssue],
        code_stats: Dict[str, Any]
    ) -> List[str]:
        """生成改進建議"""
        
        recommendations = []
        
        # 基於評分生成建議
        for dimension, score in dimension_scores.items():
            if score < 0.6:
                if dimension == QualityDimension.CODE_QUALITY:
                    recommendations.append("建議重構複雜的函數和類，降低循環複雜度")
                elif dimension == QualityDimension.SECURITY:
                    recommendations.append("立即修復安全漏洞，加強輸入驗證和數據保護")
                elif dimension == QualityDimension.TESTABILITY:
                    recommendations.append("增加單元測試和整合測試，提升測試覆蓋率")
                elif dimension == QualityDimension.DOCUMENTATION:
                    recommendations.append("補充代碼註釋和專案文檔")
        
        # 基於嚴重問題生成建議
        critical_issues = [issue for issue in issues if issue.severity == SeverityLevel.CRITICAL]
        if critical_issues:
            recommendations.append(f"優先處理 {len(critical_issues)} 個嚴重問題")
        
        # 基於技術棧生成建議
        if 'languages' in code_stats:
            languages = list(code_stats['languages'].keys())
            if 'python' in languages:
                recommendations.append("考慮使用 Black 和 isort 自動格式化 Python 代碼")
            if 'javascript' in languages or 'typescript' in languages:
                recommendations.append("考慮使用 ESLint 和 Prettier 改善 JavaScript 代碼品質")
        
        # 通用建議
        recommendations.extend([
            "建立代碼審查流程，確保代碼品質",
            "設置 CI/CD 流水線，自動執行品質檢查",
            "定期進行代碼重構，保持代碼的健康度"
        ])
        
        return recommendations
    
    async def _create_improvement_plan(
        self,
        issues: List[QualityIssue],
        dimension_scores: Dict[QualityDimension, float]
    ) -> Dict[str, Any]:
        """制定改進計畫"""
        
        # 按嚴重程度排序問題
        critical_issues = [issue for issue in issues if issue.severity == SeverityLevel.CRITICAL]
        high_issues = [issue for issue in issues if issue.severity == SeverityLevel.HIGH]
        medium_issues = [issue for issue in issues if issue.severity == SeverityLevel.MEDIUM]
        
        plan = {
            "immediate_actions": [
                {
                    "priority": "critical",
                    "issues": len(critical_issues),
                    "estimated_effort": "high",
                    "description": "修復所有嚴重安全問題和阻塞性問題"
                }
            ],
            "short_term_goals": [
                {
                    "priority": "high",
                    "issues": len(high_issues),
                    "estimated_effort": "medium",
                    "description": "處理高優先級問題，改善核心品質指標"
                }
            ],
            "long_term_goals": [
                {
                    "priority": "medium",
                    "issues": len(medium_issues),
                    "estimated_effort": "low",
                    "description": "持續改進，優化代碼品質和可維護性"
                }
            ],
            "success_metrics": {
                "target_overall_score": 0.85,
                "critical_issues_resolved": "100%",
                "high_issues_resolved": "80%",
                "test_coverage_target": "80%"
            }
        }
        
        return plan
    
    def get_assessment_history(self) -> List[Dict[str, Any]]:
        """獲取評估歷史"""
        return [asdict(report) for report in self.assessment_history]
    
    def export_report(self, report: QualityReport, format: str = "json") -> str:
        """匯出報告"""
        
        if format == "json":
            return json.dumps(asdict(report), indent=2, ensure_ascii=False, default=str)
        
        elif format == "html":
            return self._generate_html_report(report)
        
        else:
            raise ValueError(f"不支援的格式: {format}")
    
    def _generate_html_report(self, report: QualityReport) -> str:
        """生成 HTML 報告"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>代碼品質評估報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; }}
                .dimension {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .issue {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }}
                .critical {{ border-left-color: #d32f2f; }}
                .high {{ border-left-color: #f57c00; }}
                .medium {{ border-left-color: #fbc02d; }}
                .low {{ border-left-color: #388e3c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>代碼品質評估報告</h1>
                <p>專案: {report.project_path}</p>
                <p>評估時間: {report.assessment_time}</p>
                <div class="score">整體評分: {report.overall_score:.2f}/1.0</div>
            </div>
            
            <h2>維度評分</h2>
        """
        
        for dimension, score in report.dimension_scores.items():
            html += f"""
            <div class="dimension">
                <strong>{dimension.value}</strong>: {score:.2f}/1.0
            </div>
            """
        
        html += "<h2>發現的問題</h2>"
        
        for issue in report.issues:
            severity_class = issue.severity.value
            html += f"""
            <div class="issue {severity_class}">
                <h4>{issue.title} ({issue.severity.value.upper()})</h4>
                <p><strong>文件:</strong> {issue.file_path}</p>
                <p><strong>描述:</strong> {issue.description}</p>
                <p><strong>建議:</strong> {issue.suggestion}</p>
            </div>
            """
        
        html += "</body></html>"
        
        return html

# 使用範例
async def main():
    """測試品質評估器"""
    logger.info("測試代碼品質評估器...")
    
    assessor = QualityAssessor()
    
    try:
        # 測試品質評估
        report = await assessor.assess_project(
            project_path="/home/tengjung_chang/austin-dev-config/claude-auto-dev",
            include_tests=True
        )
        
        print(f"整體評分: {report.overall_score:.2f}")
        print(f"發現問題: {len(report.issues)} 個")
        print(f"關鍵指標: {len(report.metrics)} 個")
        
        # 維度評分
        for dimension, score in report.dimension_scores.items():
            print(f"{dimension.value}: {score:.2f}")
        
        # 嚴重問題統計
        severity_count = {}
        for issue in report.issues:
            severity_count[issue.severity.value] = severity_count.get(issue.severity.value, 0) + 1
        
        print(f"問題分佈: {severity_count}")
        
    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())