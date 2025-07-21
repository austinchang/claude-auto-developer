#!/usr/bin/env python3
"""
Code Generator V2 - 進階代碼生成器
使用多模型 AI 協作生成高品質、生產級代碼
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import tempfile
import subprocess

from .model_manager import ModelManager, ModelType, model_manager

logger = logging.getLogger(__name__)

@dataclass
class CodeGenerationTask:
    """代碼生成任務定義"""
    task_id: str
    description: str
    project_type: str  # web_app, api, cli, library, etc.
    target_language: str
    framework: Optional[str] = None
    additional_requirements: List[str] = None
    complexity: str = "medium"  # simple, medium, complex, enterprise
    quality_level: str = "production"  # prototype, development, production, enterprise
    
    def __post_init__(self):
        if self.additional_requirements is None:
            self.additional_requirements = []

@dataclass 
class GeneratedCode:
    """生成代碼結果"""
    file_path: str
    content: str
    language: str
    file_type: str  # source, test, config, doc
    description: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class CodeGenerationResult:
    """代碼生成完整結果"""
    task_id: str
    success: bool
    generated_files: List[GeneratedCode]
    project_structure: Dict[str, Any]
    dependencies: Dict[str, List[str]]  # 按語言分組的依賴
    setup_instructions: List[str]
    testing_instructions: List[str]
    deployment_instructions: List[str]
    quality_score: float
    generation_time: float
    models_used: List[str]
    error_message: Optional[str] = None

class CodeGeneratorV2:
    """進階代碼生成器 V2"""
    
    def __init__(self, model_manager: ModelManager = None):
        self.model_manager = model_manager or model_manager
        
        # 代碼模板和模式
        self.templates = self._load_templates()
        self.patterns = self._load_patterns()
        
        # 生成歷史和學習數據
        self.generation_history: List[Dict[str, Any]] = []
        self.quality_feedback: Dict[str, float] = {}
        
        logger.info("CodeGeneratorV2 初始化完成")
    
    def _load_templates(self) -> Dict[str, Any]:
        """載入代碼模板"""
        return {
            "python": {
                "web_app": {
                    "framework_templates": {
                        "fastapi": self._get_fastapi_template(),
                        "flask": self._get_flask_template(),
                        "django": self._get_django_template()
                    }
                },
                "api": {
                    "rest_api": self._get_rest_api_template(),
                    "graphql_api": self._get_graphql_template()
                },
                "cli": {
                    "click": self._get_click_template(),
                    "argparse": self._get_argparse_template()
                }
            },
            "javascript": {
                "web_app": {
                    "react": self._get_react_template(),
                    "vue": self._get_vue_template(),
                    "angular": self._get_angular_template()
                },
                "node_api": {
                    "express": self._get_express_template(),
                    "nestjs": self._get_nestjs_template()
                }
            },
            "typescript": {
                "web_app": {
                    "react": self._get_react_ts_template(),
                    "next": self._get_nextjs_template()
                }
            }
        }
    
    def _load_patterns(self) -> Dict[str, Any]:
        """載入代碼模式和最佳實踐"""
        return {
            "architecture_patterns": {
                "mvc": "Model-View-Controller pattern",
                "mvvm": "Model-View-ViewModel pattern", 
                "clean_architecture": "Clean Architecture principles",
                "microservices": "Microservices architecture",
                "event_driven": "Event-driven architecture"
            },
            "design_patterns": {
                "singleton": "Singleton pattern implementation",
                "factory": "Factory pattern for object creation",
                "observer": "Observer pattern for event handling",
                "strategy": "Strategy pattern for algorithms",
                "dependency_injection": "Dependency injection pattern"
            },
            "security_patterns": {
                "authentication": "JWT/OAuth authentication",
                "authorization": "Role-based access control",
                "input_validation": "Input validation and sanitization",
                "sql_injection_prevention": "SQL injection prevention",
                "xss_prevention": "XSS attack prevention"
            }
        }
    
    async def generate_project(self, task: CodeGenerationTask) -> CodeGenerationResult:
        """生成完整專案"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"開始生成專案: {task.description}")
            
            # 1. 分析需求和設計架構
            architecture = await self._analyze_and_design_architecture(task)
            
            # 2. 生成專案結構
            project_structure = await self._generate_project_structure(task, architecture)
            
            # 3. 生成核心代碼文件
            core_files = await self._generate_core_files(task, architecture, project_structure)
            
            # 4. 生成測試文件
            test_files = await self._generate_test_files(task, core_files)
            
            # 5. 生成配置文件
            config_files = await self._generate_config_files(task, architecture)
            
            # 6. 生成文檔
            doc_files = await self._generate_documentation(task, core_files)
            
            # 7. 生成部署文件
            deployment_files = await self._generate_deployment_files(task, architecture)
            
            # 8. 整合所有生成的文件
            all_files = core_files + test_files + config_files + doc_files + deployment_files
            
            # 9. 生成依賴和指令
            dependencies = await self._generate_dependencies(task, all_files)
            setup_instructions = await self._generate_setup_instructions(task, dependencies)
            testing_instructions = await self._generate_testing_instructions(task)
            deployment_instructions = await self._generate_deployment_instructions(task)
            
            # 10. 評估代碼品質
            quality_score = await self._assess_code_quality(all_files)
            
            end_time = asyncio.get_event_loop().time()
            generation_time = end_time - start_time
            
            result = CodeGenerationResult(
                task_id=task.task_id,
                success=True,
                generated_files=all_files,
                project_structure=project_structure,
                dependencies=dependencies,
                setup_instructions=setup_instructions,
                testing_instructions=testing_instructions,
                deployment_instructions=deployment_instructions,
                quality_score=quality_score,
                generation_time=generation_time,
                models_used=self._get_models_used()
            )
            
            # 記錄生成歷史
            self._record_generation_history(task, result)
            
            logger.info(f"專案生成完成，耗時 {generation_time:.2f}s，品質評分 {quality_score:.2f}")
            
            return result
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            generation_time = end_time - start_time
            
            logger.error(f"專案生成失敗: {str(e)}")
            
            return CodeGenerationResult(
                task_id=task.task_id,
                success=False,
                generated_files=[],
                project_structure={},
                dependencies={},
                setup_instructions=[],
                testing_instructions=[],
                deployment_instructions=[],
                quality_score=0.0,
                generation_time=generation_time,
                models_used=self._get_models_used(),
                error_message=str(e)
            )
    
    async def _analyze_and_design_architecture(self, task: CodeGenerationTask) -> Dict[str, Any]:
        """分析需求並設計系統架構"""
        
        system_message = """你是一個資深的軟體架構師。請分析用戶需求並設計合適的系統架構。
        
回應格式要求（JSON）：
{
  "architecture_type": "架構類型（如 MVC, microservices, layered）",
  "components": ["組件1", "組件2", "組件3"],
  "data_flow": "數據流向描述",
  "technology_stack": {
    "backend": ["技術1", "技術2"],
    "frontend": ["技術1", "技術2"],
    "database": ["技術1"],
    "deployment": ["技術1", "技術2"]
  },
  "security_considerations": ["安全考量1", "安全考量2"],
  "scalability_strategy": "擴展策略描述",
  "estimated_complexity": "simple/medium/complex/enterprise"
}"""
        
        prompt = f"""
請為以下專案設計系統架構：

專案描述: {task.description}
專案類型: {task.project_type}
目標語言: {task.target_language}
指定框架: {task.framework or "自動選擇"}
複雜度: {task.complexity}
品質要求: {task.quality_level}
額外需求: {', '.join(task.additional_requirements)}

請考慮：
1. 最佳的架構模式
2. 合適的技術棧
3. 擴展性和維護性
4. 安全性考量
5. 性能優化策略
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.ARCHITECTURE_DESIGN,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            max_tokens=2000
        )
        
        try:
            architecture = json.loads(result['content'])
            logger.info(f"架構設計完成: {architecture['architecture_type']}")
            return architecture
        except json.JSONDecodeError:
            # 如果回應不是 JSON，嘗試解析文字
            logger.warning("架構設計回應不是 JSON 格式，使用預設架構")
            return self._get_default_architecture(task)
    
    async def _generate_project_structure(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成專案目錄結構"""
        
        if task.target_language == "python":
            if task.project_type == "web_app":
                return {
                    "app/": {
                        "__init__.py": "初始化文件",
                        "main.py": "應用入口",
                        "api/": {
                            "__init__.py": "",
                            "routes/": {
                                "__init__.py": "",
                                "auth.py": "認證路由",
                                "users.py": "用戶路由"
                            },
                            "models/": {
                                "__init__.py": "",
                                "user.py": "用戶模型",
                                "database.py": "數據庫配置"
                            },
                            "services/": {
                                "__init__.py": "",
                                "auth_service.py": "認證服務",
                                "user_service.py": "用戶服務"
                            }
                        },
                        "core/": {
                            "__init__.py": "",
                            "config.py": "配置管理",
                            "security.py": "安全設置",
                            "middleware.py": "中間件"
                        }
                    },
                    "tests/": {
                        "__init__.py": "",
                        "test_api/": {
                            "__init__.py": "",
                            "test_auth.py": "認證測試",
                            "test_users.py": "用戶測試"
                        },
                        "test_services/": {
                            "__init__.py": "",
                            "test_auth_service.py": "認證服務測試"
                        }
                    },
                    "requirements.txt": "依賴清單",
                    "requirements-dev.txt": "開發依賴",
                    "Dockerfile": "Docker 配置",
                    "docker-compose.yml": "Docker Compose",
                    ".env.example": "環境變數範例",
                    "README.md": "專案說明",
                    ".gitignore": "Git 忽略文件"
                }
        
        # 其他語言的結構...
        return {}
    
    async def _generate_core_files(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any],
        project_structure: Dict[str, Any]
    ) -> List[GeneratedCode]:
        """生成核心代碼文件"""
        
        generated_files = []
        
        if task.target_language == "python" and task.project_type == "web_app":
            # 生成主應用文件
            main_py = await self._generate_python_main_file(task, architecture)
            generated_files.append(main_py)
            
            # 生成 API 路由
            auth_routes = await self._generate_auth_routes(task, architecture)
            generated_files.append(auth_routes)
            
            # 生成數據模型
            user_model = await self._generate_user_model(task, architecture)
            generated_files.append(user_model)
            
            # 生成服務層
            auth_service = await self._generate_auth_service(task, architecture)
            generated_files.append(auth_service)
        
        return generated_files
    
    async def _generate_python_main_file(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成 Python 主應用文件"""
        
        framework = task.framework or "fastapi"
        
        system_message = f"""你是一個專業的 {framework} 開發者。請生成一個高品質的主應用文件。

代碼要求：
1. 遵循 PEP 8 代碼風格
2. 包含完整的型別註解
3. 包含適當的錯誤處理
4. 包含安全性配置
5. 包含 CORS 和中間件設置
6. 代碼要有詳細註釋
7. 生產環境就緒"""
        
        prompt = f"""
請為 {framework} 應用生成主入口文件 (main.py)：

專案描述: {task.description}
架構類型: {architecture.get('architecture_type', 'MVC')}
技術棧: {architecture.get('technology_stack', {})}
品質要求: {task.quality_level}

需要包含：
1. 應用初始化
2. 路由註冊
3. 中間件配置
4. 錯誤處理
5. 安全設置
6. 健康檢查端點
7. 文檔配置

請生成完整、生產就緒的代碼。
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.CODE_GENERATION,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            required_languages=["python"],
            max_tokens=3000
        )
        
        return GeneratedCode(
            file_path="app/main.py",
            content=result['content'],
            language="python",
            file_type="source",
            description="主應用入口文件",
            dependencies=["fastapi", "uvicorn", "python-dotenv"]
        )
    
    async def _generate_auth_routes(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成認證路由"""
        
        system_message = """你是一個專業的 API 開發者。請生成安全、完整的認證路由。

代碼要求：
1. JWT 令牌認證
2. 密碼哈希處理
3. 輸入驗證
4. 錯誤處理
5. 速率限制
6. 完整的型別註解
7. 安全最佳實踐"""
        
        prompt = f"""
請生成認證路由文件 (api/routes/auth.py)：

專案描述: {task.description}
安全考量: {', '.join(architecture.get('security_considerations', []))}

需要包含的端點：
1. POST /auth/register - 用戶註冊
2. POST /auth/login - 用戶登入
3. POST /auth/refresh - 刷新令牌
4. POST /auth/logout - 用戶登出
5. GET /auth/me - 獲取當前用戶資訊

每個端點都需要：
- 完整的輸入驗證
- 適當的錯誤處理
- 安全性考量
- 詳細的文檔字符串
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.CODE_GENERATION,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            required_languages=["python"],
            max_tokens=3000
        )
        
        return GeneratedCode(
            file_path="app/api/routes/auth.py",
            content=result['content'],
            language="python",
            file_type="source",
            description="認證路由處理",
            dependencies=["fastapi", "pydantic", "passlib", "python-jose"]
        )
    
    async def _generate_user_model(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成用戶數據模型"""
        
        system_message = """你是一個數據庫專家。請生成完整的用戶數據模型。

代碼要求：
1. 使用 SQLAlchemy ORM
2. 包含 Pydantic 模型
3. 數據驗證
4. 關聯關係
5. 索引優化
6. 完整型別註解"""
        
        prompt = f"""
請生成用戶模型文件 (api/models/user.py)：

專案描述: {task.description}
數據庫: {architecture.get('technology_stack', {}).get('database', ['SQLite'])[0]}

需要包含：
1. User SQLAlchemy 模型
2. UserCreate Pydantic 模型（註冊用）
3. UserResponse Pydantic 模型（回應用）
4. UserUpdate Pydantic 模型（更新用）
5. 適當的驗證器
6. 數據庫索引
7. 關聯關係（如果需要）

字段包括：
- id (主鍵)
- email (唯一)
- username (唯一)
- hashed_password
- is_active
- created_at
- updated_at
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.CODE_GENERATION,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            required_languages=["python"],
            max_tokens=2500
        )
        
        return GeneratedCode(
            file_path="app/api/models/user.py",
            content=result['content'],
            language="python",
            file_type="source",
            description="用戶數據模型",
            dependencies=["sqlalchemy", "pydantic", "email-validator"]
        )
    
    async def _generate_auth_service(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成認證服務"""
        
        system_message = """你是一個後端服務專家。請生成完整的認證服務層。

代碼要求：
1. 業務邏輯封裝
2. 密碼安全處理
3. JWT 令牌管理
4. 錯誤處理
5. 異步支援
6. 完整型別註解"""
        
        prompt = f"""
請生成認證服務文件 (api/services/auth_service.py)：

專案描述: {task.description}

需要包含的方法：
1. register_user() - 用戶註冊
2. authenticate_user() - 用戶認證
3. create_access_token() - 創建訪問令牌
4. verify_token() - 驗證令牌
5. get_current_user() - 獲取當前用戶
6. hash_password() - 密碼哈希
7. verify_password() - 密碼驗證

安全要求：
- bcrypt 密碼哈希
- JWT 令牌與過期時間
- 安全隨機 secret key
- 輸入清理和驗證
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.CODE_GENERATION,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            required_languages=["python"],
            max_tokens=3000
        )
        
        return GeneratedCode(
            file_path="app/api/services/auth_service.py",
            content=result['content'],
            language="python",
            file_type="source",
            description="認證業務邏輯服務",
            dependencies=["passlib", "python-jose", "bcrypt"]
        )
    
    async def _generate_test_files(
        self, 
        task: CodeGenerationTask, 
        core_files: List[GeneratedCode]
    ) -> List[GeneratedCode]:
        """生成測試文件"""
        
        test_files = []
        
        for core_file in core_files:
            if core_file.file_type == "source":
                test_file = await self._generate_test_for_file(task, core_file)
                test_files.append(test_file)
        
        return test_files
    
    async def _generate_test_for_file(
        self, 
        task: CodeGenerationTask, 
        source_file: GeneratedCode
    ) -> GeneratedCode:
        """為特定文件生成測試"""
        
        system_message = """你是一個測試專家。請生成全面的單元測試和集成測試。

測試要求：
1. 使用 pytest 框架
2. 100% 代碼覆蓋率目標
3. 正面和負面測試案例
4. Mock 外部依賴
5. 異步測試支援
6. 清晰的測試文檔"""
        
        prompt = f"""
請為以下代碼文件生成全面的測試：

文件路徑: {source_file.file_path}
文件描述: {source_file.description}

代碼內容:
```{source_file.language}
{source_file.content[:2000]}...
```

需要測試：
1. 所有公開方法
2. 邊界條件
3. 錯誤情況
4. 異常處理
5. 安全性驗證

請生成完整的 pytest 測試文件。
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.TESTING,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            required_languages=["python"],
            max_tokens=2500
        )
        
        test_path = source_file.file_path.replace("app/", "tests/test_")
        if not test_path.startswith("test_"):
            test_path = f"test_{os.path.basename(test_path)}"
        
        return GeneratedCode(
            file_path=f"tests/{test_path}",
            content=result['content'],
            language="python",
            file_type="test",
            description=f"測試文件: {source_file.description}",
            dependencies=["pytest", "pytest-asyncio", "httpx", "pytest-mock"]
        )
    
    async def _generate_config_files(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> List[GeneratedCode]:
        """生成配置文件"""
        
        config_files = []
        
        # requirements.txt
        requirements = await self._generate_requirements_file(task, architecture)
        config_files.append(requirements)
        
        # .env.example
        env_example = await self._generate_env_example(task, architecture)
        config_files.append(env_example)
        
        # Dockerfile
        dockerfile = await self._generate_dockerfile(task, architecture)
        config_files.append(dockerfile)
        
        return config_files
    
    async def _generate_requirements_file(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成 requirements.txt"""
        
        base_deps = {
            "web_app": [
                "fastapi>=0.68.0",
                "uvicorn[standard]>=0.15.0",
                "python-dotenv>=0.19.0",
                "pydantic>=1.8.0",
                "sqlalchemy>=1.4.0",
                "alembic>=1.7.0",
                "passlib[bcrypt]>=1.7.4",
                "python-jose[cryptography]>=3.3.0",
                "python-multipart>=0.0.5"
            ]
        }
        
        deps = base_deps.get(task.project_type, [])
        
        # 根據數據庫添加依賴
        db_type = architecture.get('technology_stack', {}).get('database', ['sqlite'])[0].lower()
        if 'postgresql' in db_type:
            deps.append("psycopg2-binary>=2.9.0")
        elif 'mysql' in db_type:
            deps.append("PyMySQL>=1.0.0")
        
        content = "\n".join(sorted(deps))
        
        return GeneratedCode(
            file_path="requirements.txt",
            content=content,
            language="text",
            file_type="config",
            description="Python 依賴清單"
        )
    
    async def _generate_env_example(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成環境變數範例文件"""
        
        env_vars = [
            "# 應用配置",
            "APP_NAME=Claude Auto Generated App",
            "APP_VERSION=1.0.0",
            "DEBUG=False",
            "ENVIRONMENT=development",
            "",
            "# 安全配置", 
            "SECRET_KEY=your-secret-key-here-change-in-production",
            "ACCESS_TOKEN_EXPIRE_MINUTES=30",
            "",
            "# 數據庫配置",
            "DATABASE_URL=sqlite:///./app.db",
            "",
            "# CORS 配置",
            "ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080",
            "",
            "# 日誌配置",
            "LOG_LEVEL=INFO"
        ]
        
        content = "\n".join(env_vars)
        
        return GeneratedCode(
            file_path=".env.example",
            content=content,
            language="text",
            file_type="config",
            description="環境變數配置範例"
        )
    
    async def _generate_dockerfile(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成 Dockerfile"""
        
        dockerfile_content = f"""# {task.description} - Docker 配置
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY app/ ./app/

# 創建非 root 用戶
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]"""
        
        return GeneratedCode(
            file_path="Dockerfile",
            content=dockerfile_content,
            language="dockerfile",
            file_type="config",
            description="Docker 容器配置"
        )
    
    async def _generate_documentation(
        self, 
        task: CodeGenerationTask, 
        core_files: List[GeneratedCode]
    ) -> List[GeneratedCode]:
        """生成文檔"""
        
        doc_files = []
        
        # README.md
        readme = await self._generate_readme(task, core_files)
        doc_files.append(readme)
        
        return doc_files
    
    async def _generate_readme(
        self, 
        task: CodeGenerationTask, 
        core_files: List[GeneratedCode]
    ) -> GeneratedCode:
        """生成 README.md"""
        
        system_message = """你是一個技術文檔專家。請生成清晰、全面的 README 文檔。

文檔要求：
1. 清晰的專案描述
2. 完整的安裝指南
3. 使用範例
4. API 文檔連結
5. 貢獻指南
6. 許可證資訊"""
        
        prompt = f"""
請為以下專案生成專業的 README.md：

專案描述: {task.description}
專案類型: {task.project_type}
技術棧: {task.target_language}

生成的文件包括：
{', '.join([f.description for f in core_files])}

README 需要包含：
1. 專案簡介
2. 功能特色
3. 技術棧
4. 安裝指南
5. 使用說明
6. API 文檔
7. 開發指南
8. 部署說明
9. 貢獻指南
10. 許可證

請使用 Markdown 格式，包含適當的徽章和圖表。
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.DOCUMENTATION,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            max_tokens=3000
        )
        
        return GeneratedCode(
            file_path="README.md",
            content=result['content'],
            language="markdown",
            file_type="doc",
            description="專案說明文檔"
        )
    
    async def _generate_deployment_files(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> List[GeneratedCode]:
        """生成部署文件"""
        
        deployment_files = []
        
        # docker-compose.yml
        docker_compose = await self._generate_docker_compose(task, architecture)
        deployment_files.append(docker_compose)
        
        return deployment_files
    
    async def _generate_docker_compose(
        self, 
        task: CodeGenerationTask, 
        architecture: Dict[str, Any]
    ) -> GeneratedCode:
        """生成 docker-compose.yml"""
        
        compose_content = f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    depends_on:
      - db
    volumes:
      - ./app:/app/app
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:"""
        
        return GeneratedCode(
            file_path="docker-compose.yml",
            content=compose_content,
            language="yaml",
            file_type="config",
            description="Docker Compose 配置"
        )
    
    async def _generate_dependencies(
        self, 
        task: CodeGenerationTask, 
        all_files: List[GeneratedCode]
    ) -> Dict[str, List[str]]:
        """整理所有依賴"""
        
        deps = {"python": set()}
        
        for file in all_files:
            if file.dependencies:
                deps["python"].update(file.dependencies)
        
        return {"python": sorted(list(deps["python"]))}
    
    async def _generate_setup_instructions(
        self, 
        task: CodeGenerationTask, 
        dependencies: Dict[str, List[str]]
    ) -> List[str]:
        """生成安裝指令"""
        
        instructions = [
            "1. 克隆專案: git clone <repository-url>",
            "2. 進入目錄: cd <project-directory>", 
            "3. 創建虛擬環境: python -m venv venv",
            "4. 啟動虛擬環境: source venv/bin/activate (Linux/Mac) 或 venv\\Scripts\\activate (Windows)",
            "5. 安裝依賴: pip install -r requirements.txt",
            "6. 複製環境變數: cp .env.example .env",
            "7. 修改環境變數: 編輯 .env 文件",
            "8. 運行應用: uvicorn app.main:app --reload"
        ]
        
        return instructions
    
    async def _generate_testing_instructions(self, task: CodeGenerationTask) -> List[str]:
        """生成測試指令"""
        
        return [
            "1. 安裝測試依賴: pip install pytest pytest-asyncio httpx",
            "2. 運行所有測試: pytest",
            "3. 運行測試並查看覆蓋率: pytest --cov=app",
            "4. 運行特定測試: pytest tests/test_specific.py",
            "5. 查看詳細輸出: pytest -v"
        ]
    
    async def _generate_deployment_instructions(self, task: CodeGenerationTask) -> List[str]:
        """生成部署指令"""
        
        return [
            "1. 使用 Docker: docker build -t app-name .",
            "2. 運行容器: docker run -p 8000:8000 app-name",
            "3. 使用 Docker Compose: docker-compose up -d",
            "4. 生產部署: 設置反向代理 (Nginx) 和 SSL 證書",
            "5. 監控: 設置日誌收集和監控系統"
        ]
    
    async def _assess_code_quality(self, all_files: List[GeneratedCode]) -> float:
        """評估代碼品質"""
        
        # 這裡可以實作更複雜的品質評估
        # 暫時基於文件數量和內容長度給出評分
        
        total_score = 0.0
        file_count = len(all_files)
        
        if file_count == 0:
            return 0.0
        
        for file in all_files:
            score = 0.0
            
            # 基於內容長度評分
            content_length = len(file.content)
            if content_length > 1000:
                score += 0.3
            elif content_length > 500:
                score += 0.2
            else:
                score += 0.1
            
            # 基於文件類型評分
            if file.file_type == "source":
                score += 0.4
            elif file.file_type == "test":
                score += 0.3
            elif file.file_type == "config":
                score += 0.2
            else:
                score += 0.1
            
            # 基於語言特定評分
            if file.language == "python" and "def " in file.content:
                score += 0.2
            
            total_score += min(score, 1.0)
        
        return min(total_score / file_count, 1.0)
    
    def _get_models_used(self) -> List[str]:
        """獲取使用的模型列表"""
        # 這裡應該追蹤實際使用的模型
        return ["claude-3-5-sonnet-20241022", "gpt-4-turbo-preview"]
    
    def _record_generation_history(
        self, 
        task: CodeGenerationTask, 
        result: CodeGenerationResult
    ):
        """記錄生成歷史"""
        
        record = {
            "task": asdict(task),
            "result": {
                "success": result.success,
                "file_count": len(result.generated_files),
                "quality_score": result.quality_score,
                "generation_time": result.generation_time,
                "models_used": result.models_used
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.generation_history.append(record)
        
        # 保持歷史記錄在合理範圍內
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-500:]
    
    def _get_default_architecture(self, task: CodeGenerationTask) -> Dict[str, Any]:
        """獲取預設架構"""
        return {
            "architecture_type": "MVC",
            "components": ["API Layer", "Service Layer", "Data Layer"],
            "data_flow": "Client -> API -> Service -> Database",
            "technology_stack": {
                "backend": [task.target_language, task.framework or "fastapi"],
                "database": ["SQLite"],
                "deployment": ["Docker"]
            },
            "security_considerations": ["JWT Authentication", "Input Validation"],
            "scalability_strategy": "Horizontal scaling with load balancer",
            "estimated_complexity": task.complexity
        }
    
    # 模板方法 (簡化版本)
    def _get_fastapi_template(self) -> str:
        return "FastAPI application template"
    
    def _get_flask_template(self) -> str:
        return "Flask application template"
    
    def _get_django_template(self) -> str:
        return "Django application template"
    
    def _get_rest_api_template(self) -> str:
        return "REST API template"
    
    def _get_graphql_template(self) -> str:
        return "GraphQL API template"
    
    def _get_click_template(self) -> str:
        return "Click CLI template"
    
    def _get_argparse_template(self) -> str:
        return "Argparse CLI template"
    
    def _get_react_template(self) -> str:
        return "React application template"
    
    def _get_vue_template(self) -> str:
        return "Vue application template"
    
    def _get_angular_template(self) -> str:
        return "Angular application template"
    
    def _get_express_template(self) -> str:
        return "Express.js template"
    
    def _get_nestjs_template(self) -> str:
        return "NestJS template"
    
    def _get_react_ts_template(self) -> str:
        return "React TypeScript template"
    
    def _get_nextjs_template(self) -> str:
        return "Next.js template"

# 使用範例
async def main():
    """測試代碼生成器"""
    
    generator = CodeGeneratorV2()
    
    task = CodeGenerationTask(
        task_id="test-001",
        description="創建一個用戶管理 API，支援註冊、登入和用戶資料管理",
        project_type="web_app",
        target_language="python",
        framework="fastapi",
        additional_requirements=["JWT 認證", "PostgreSQL 數據庫", "Docker 部署"],
        complexity="medium",
        quality_level="production"
    )
    
    result = await generator.generate_project(task)
    
    if result.success:
        print(f"專案生成成功！")
        print(f"生成文件數: {len(result.generated_files)}")
        print(f"品質評分: {result.quality_score:.2f}")
        print(f"生成時間: {result.generation_time:.2f}s")
        
        for file in result.generated_files:
            print(f"- {file.file_path}: {file.description}")
    else:
        print(f"專案生成失敗: {result.error_message}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())