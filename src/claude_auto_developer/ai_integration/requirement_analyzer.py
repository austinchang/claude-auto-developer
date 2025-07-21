#!/usr/bin/env python3
"""
Requirement Analyzer - 深度需求分析器
能夠從模糊的自然語言描述中提取精確的技術需求和架構建議
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum

from .model_manager import ModelManager, ModelType, model_manager

logger = logging.getLogger(__name__)

class RequirementType(Enum):
    """需求類型枚舉"""
    FUNCTIONAL = "functional"          # 功能性需求
    NON_FUNCTIONAL = "non_functional"  # 非功能性需求
    TECHNICAL = "technical"            # 技術需求
    BUSINESS = "business"              # 業務需求
    SECURITY = "security"              # 安全需求
    PERFORMANCE = "performance"        # 性能需求
    INTEGRATION = "integration"        # 整合需求
    COMPLIANCE = "compliance"          # 合規需求

class Priority(Enum):
    """需求優先級"""
    CRITICAL = "critical"    # 關鍵需求
    HIGH = "high"           # 高優先級
    MEDIUM = "medium"       # 中優先級
    LOW = "low"            # 低優先級
    NICE_TO_HAVE = "nice_to_have"  # 可選需求

@dataclass
class Requirement:
    """單個需求定義"""
    id: str
    type: RequirementType
    priority: Priority
    title: str
    description: str
    acceptance_criteria: List[str]
    technical_notes: List[str]
    dependencies: List[str]
    estimated_effort: str  # 估算工作量 (hours/days)
    risk_level: str       # 風險等級 (low/medium/high)
    
    def __post_init__(self):
        if not self.acceptance_criteria:
            self.acceptance_criteria = []
        if not self.technical_notes:
            self.technical_notes = []
        if not self.dependencies:
            self.dependencies = []

@dataclass
class TechnicalStack:
    """技術棧建議"""
    backend_language: str
    backend_framework: str
    frontend_language: Optional[str]
    frontend_framework: Optional[str]
    database: str
    cache: Optional[str]
    message_queue: Optional[str]
    deployment: List[str]
    monitoring: List[str]
    testing_frameworks: List[str]
    
    def __post_init__(self):
        if not self.deployment:
            self.deployment = []
        if not self.monitoring:
            self.monitoring = []
        if not self.testing_frameworks:
            self.testing_frameworks = []

@dataclass
class ArchitecturePattern:
    """架構模式建議"""
    pattern_name: str
    description: str
    pros: List[str]
    cons: List[str]
    use_cases: List[str]
    implementation_complexity: str
    
    def __post_init__(self):
        if not self.pros:
            self.pros = []
        if not self.cons:
            self.cons = []
        if not self.use_cases:
            self.use_cases = []

@dataclass
class RequirementAnalysisResult:
    """需求分析完整結果"""
    original_description: str
    analysis_id: str
    requirements: List[Requirement]
    technical_stack: TechnicalStack
    architecture_patterns: List[ArchitecturePattern]
    project_scope: Dict[str, Any]
    estimated_timeline: Dict[str, str]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    next_steps: List[str]
    confidence_score: float
    analysis_timestamp: str

class RequirementAnalyzer:
    """深度需求分析器"""
    
    def __init__(self, model_manager: ModelManager = None):
        self.model_manager = model_manager or model_manager
        
        # 領域知識庫
        self.domain_knowledge = self._load_domain_knowledge()
        self.tech_stack_templates = self._load_tech_stack_templates()
        self.architecture_patterns = self._load_architecture_patterns()
        
        # 分析歷史和學習數據
        self.analysis_history: List[Dict[str, Any]] = []
        self.pattern_frequency: Dict[str, int] = {}
        
        logger.info("RequirementAnalyzer 初始化完成")
    
    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """載入領域知識庫"""
        return {
            "web_applications": {
                "keywords": ["網站", "web", "前端", "後端", "API", "界面", "用戶", "登入", "註冊"],
                "typical_features": ["用戶認證", "資料管理", "搜尋功能", "檔案上傳", "通知系統"],
                "security_requirements": ["HTTPS", "輸入驗證", "CSRF 防護", "XSS 防護", "SQL 注入防護"],
                "performance_requirements": ["響應時間 < 2s", "並發用戶支援", "資料庫優化"]
            },
            "mobile_applications": {
                "keywords": ["手機", "移動", "app", "ios", "android", "響應式"],
                "typical_features": ["離線支援", "推送通知", "位置服務", "相機整合", "社交分享"],
                "security_requirements": ["資料加密", "生物識別", "安全存儲", "網路安全"],
                "performance_requirements": ["快速啟動", "低電量消耗", "流暢動畫"]
            },
            "data_analytics": {
                "keywords": ["數據", "分析", "報表", "統計", "機器學習", "AI", "預測"],
                "typical_features": ["資料收集", "資料清理", "視覺化", "報表生成", "預測模型"],
                "security_requirements": ["資料隱私", "存取控制", "審計日誌", "資料匿名化"],
                "performance_requirements": ["大數據處理", "即時分析", "分散式計算"]
            },
            "e_commerce": {
                "keywords": ["電商", "購物", "商品", "訂單", "支付", "庫存", "物流"],
                "typical_features": ["商品目錄", "購物車", "支付處理", "訂單管理", "庫存管理"],
                "security_requirements": ["PCI DSS 合規", "支付安全", "個資保護", "交易安全"],
                "performance_requirements": ["高可用性", "負載均衡", "快速搜尋", "CDN 加速"]
            },
            "iot_systems": {
                "keywords": ["物聯網", "iot", "感測器", "設備", "監控", "自動化", "遠程"],
                "typical_features": ["設備管理", "資料收集", "即時監控", "自動化控制", "報警系統"],
                "security_requirements": ["設備認證", "資料加密", "安全通信", "固件安全"],
                "performance_requirements": ["低延遲", "高可靠性", "邊緣計算", "資料壓縮"]
            }
        }
    
    def _load_tech_stack_templates(self) -> Dict[str, TechnicalStack]:
        """載入技術棧模板"""
        return {
            "modern_web_python": TechnicalStack(
                backend_language="Python",
                backend_framework="FastAPI",
                frontend_language="TypeScript",
                frontend_framework="React",
                database="PostgreSQL",
                cache="Redis",
                message_queue="Celery",
                deployment=["Docker", "Kubernetes"],
                monitoring=["Prometheus", "Grafana"],
                testing_frameworks=["pytest", "Jest"]
            ),
            "enterprise_java": TechnicalStack(
                backend_language="Java",
                backend_framework="Spring Boot",
                frontend_language="TypeScript",
                frontend_framework="Angular",
                database="PostgreSQL",
                cache="Redis",
                message_queue="RabbitMQ",
                deployment=["Docker", "Kubernetes"],
                monitoring=["Micrometer", "Grafana"],
                testing_frameworks=["JUnit", "Mockito"]
            ),
            "nodejs_microservices": TechnicalStack(
                backend_language="TypeScript",
                backend_framework="NestJS",
                frontend_language="TypeScript",
                frontend_framework="Next.js",
                database="MongoDB",
                cache="Redis",
                message_queue="Apache Kafka",
                deployment=["Docker", "AWS ECS"],
                monitoring=["DataDog", "New Relic"],
                testing_frameworks=["Jest", "Cypress"]
            ),
            "serverless_stack": TechnicalStack(
                backend_language="Python",
                backend_framework="AWS Lambda",
                frontend_language="TypeScript",
                frontend_framework="React",
                database="DynamoDB",
                cache="ElastiCache",
                message_queue="AWS SQS",
                deployment=["AWS SAM", "CloudFormation"],
                monitoring=["CloudWatch", "X-Ray"],
                testing_frameworks=["pytest", "Jest"]
            )
        }
    
    def _load_architecture_patterns(self) -> Dict[str, ArchitecturePattern]:
        """載入架構模式"""
        return {
            "monolithic": ArchitecturePattern(
                pattern_name="Monolithic Architecture",
                description="單體架構，所有功能在一個部署單元中",
                pros=["簡單部署", "容易測試", "開發快速"],
                cons=["擴展困難", "技術債務", "單點故障"],
                use_cases=["小型應用", "MVP 產品", "團隊規模小"],
                implementation_complexity="Low"
            ),
            "microservices": ArchitecturePattern(
                pattern_name="Microservices Architecture",
                description="微服務架構，功能分解為獨立的服務",
                pros=["獨立部署", "技術多樣性", "容錯性好"],
                cons=["複雜性高", "網路延遲", "資料一致性"],
                use_cases=["大型應用", "多團隊開發", "高擴展需求"],
                implementation_complexity="High"
            ),
            "serverless": ArchitecturePattern(
                pattern_name="Serverless Architecture",
                description="無伺服器架構，使用雲端函數服務",
                pros=["自動擴展", "按需付費", "無基礎設施管理"],
                cons=["供應商鎖定", "冷啟動延遲", "監控困難"],
                use_cases=["事件驅動應用", "輕量級 API", "不規則負載"],
                implementation_complexity="Medium"
            ),
            "event_driven": ArchitecturePattern(
                pattern_name="Event-Driven Architecture",
                description="事件驅動架構，組件透過事件通信",
                pros=["鬆散耦合", "高擴展性", "即時處理"],
                cons=["複雜性高", "事件順序", "除錯困難"],
                use_cases=["即時系統", "大數據處理", "IoT 應用"],
                implementation_complexity="High"
            )
        }
    
    async def analyze_requirements(self, description: str) -> RequirementAnalysisResult:
        """深度分析需求描述"""
        analysis_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"開始需求分析: {analysis_id}")
            
            # 1. 識別領域和項目類型
            domain_analysis = await self._identify_domain(description)
            
            # 2. 提取功能性需求
            functional_requirements = await self._extract_functional_requirements(description, domain_analysis)
            
            # 3. 推斷非功能性需求
            non_functional_requirements = await self._infer_non_functional_requirements(description, domain_analysis)
            
            # 4. 分析技術需求
            technical_requirements = await self._analyze_technical_requirements(description, domain_analysis)
            
            # 5. 合併所有需求
            all_requirements = functional_requirements + non_functional_requirements + technical_requirements
            
            # 6. 推薦技術棧
            tech_stack = await self._recommend_tech_stack(description, domain_analysis, all_requirements)
            
            # 7. 推薦架構模式
            architecture_patterns = await self._recommend_architecture_patterns(description, all_requirements)
            
            # 8. 評估項目範圍
            project_scope = await self._assess_project_scope(description, all_requirements)
            
            # 9. 估算時間線
            timeline = await self._estimate_timeline(all_requirements, project_scope)
            
            # 10. 風險評估
            risk_assessment = await self._assess_risks(description, all_requirements, tech_stack)
            
            # 11. 生成建議和下一步
            recommendations = await self._generate_recommendations(all_requirements, tech_stack, risk_assessment)
            next_steps = await self._generate_next_steps(all_requirements, project_scope)
            
            # 12. 計算信心分數
            confidence_score = self._calculate_confidence_score(description, all_requirements)
            
            result = RequirementAnalysisResult(
                original_description=description,
                analysis_id=analysis_id,
                requirements=all_requirements,
                technical_stack=tech_stack,
                architecture_patterns=architecture_patterns,
                project_scope=project_scope,
                estimated_timeline=timeline,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                next_steps=next_steps,
                confidence_score=confidence_score,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            # 記錄分析歷史
            self._record_analysis_history(description, result)
            
            logger.info(f"需求分析完成: {analysis_id}, 信心分數: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"需求分析失敗: {str(e)}")
            raise
    
    async def _identify_domain(self, description: str) -> Dict[str, Any]:
        """識別應用領域"""
        
        system_message = """你是一個業務分析專家。請分析用戶描述並識別應用領域。

回應格式要求（JSON）：
{
  "primary_domain": "主要領域（如 web_applications, mobile_applications, data_analytics 等）",
  "secondary_domains": ["次要領域1", "次要領域2"],
  "application_type": "應用類型（如 web_app, mobile_app, api, cli, library 等）",
  "target_users": ["目標用戶群體1", "目標用戶群體2"],
  "business_model": "商業模式描述",
  "key_features_identified": ["識別到的關鍵功能1", "關鍵功能2"],
  "complexity_indicators": ["複雜度指標1", "複雜度指標2"],
  "industry_context": "行業背景"
}"""
        
        prompt = f"""
請分析以下專案描述並識別其應用領域：

描述: {description}

請考慮：
1. 主要應用領域和類型
2. 目標用戶群體
3. 商業模式和行業背景
4. 關鍵功能特徵
5. 複雜度指標
6. 技術挑戰

可能的領域包括：
- web_applications: 網頁應用
- mobile_applications: 移動應用
- data_analytics: 數據分析
- e_commerce: 電子商務
- iot_systems: 物聯網系統
- enterprise_software: 企業軟體
- gaming: 遊戲應用
- fintech: 金融科技
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.REQUIREMENT_ANALYSIS,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            max_tokens=1500
        )
        
        try:
            domain_analysis = json.loads(result['content'])
            logger.info(f"識別領域: {domain_analysis['primary_domain']}")
            return domain_analysis
        except json.JSONDecodeError:
            logger.warning("領域識別回應不是 JSON 格式，使用預設分析")
            return {
                "primary_domain": "web_applications",
                "secondary_domains": [],
                "application_type": "web_app",
                "target_users": ["general_users"],
                "business_model": "未指定",
                "key_features_identified": [],
                "complexity_indicators": ["medium"],
                "industry_context": "通用"
            }
    
    async def _extract_functional_requirements(
        self, 
        description: str, 
        domain_analysis: Dict[str, Any]
    ) -> List[Requirement]:
        """提取功能性需求"""
        
        system_message = """你是一個需求工程師。請從用戶描述中提取詳細的功能性需求。

每個需求需要包含：
1. 清晰的標題
2. 詳細描述
3. 可測試的驗收標準
4. 技術考量
5. 優先級評估

回應格式要求（JSON 陣列）：
[
  {
    "title": "需求標題",
    "description": "詳細描述",
    "acceptance_criteria": ["驗收標準1", "驗收標準2"],
    "technical_notes": ["技術考量1", "技術考量2"],
    "priority": "critical/high/medium/low/nice_to_have",
    "estimated_effort": "2 days",
    "dependencies": ["依賴項1", "依賴項2"],
    "risk_level": "low/medium/high"
  }
]"""
        
        prompt = f"""
請從以下描述中提取功能性需求：

描述: {description}
應用領域: {domain_analysis['primary_domain']}
應用類型: {domain_analysis['application_type']}
關鍵功能: {', '.join(domain_analysis.get('key_features_identified', []))}

請識別：
1. 核心功能需求
2. 用戶管理需求
3. 資料管理需求
4. 業務邏輯需求
5. 整合需求
6. 報表和分析需求

每個需求都要：
- 從用戶角度描述
- 包含明確的驗收標準
- 評估實作難度和風險
- 識別依賴關係
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.REQUIREMENT_ANALYSIS,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            max_tokens=3000
        )
        
        try:
            requirements_data = json.loads(result['content'])
            requirements = []
            
            for i, req_data in enumerate(requirements_data):
                req = Requirement(
                    id=f"FR_{i+1:03d}",
                    type=RequirementType.FUNCTIONAL,
                    priority=Priority(req_data.get('priority', 'medium')),
                    title=req_data['title'],
                    description=req_data['description'],
                    acceptance_criteria=req_data.get('acceptance_criteria', []),
                    technical_notes=req_data.get('technical_notes', []),
                    dependencies=req_data.get('dependencies', []),
                    estimated_effort=req_data.get('estimated_effort', '1 day'),
                    risk_level=req_data.get('risk_level', 'medium')
                )
                requirements.append(req)
            
            logger.info(f"提取功能性需求: {len(requirements)} 個")
            return requirements
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"功能需求提取失敗，使用預設需求: {str(e)}")
            return self._get_default_functional_requirements()
    
    async def _infer_non_functional_requirements(
        self, 
        description: str, 
        domain_analysis: Dict[str, Any]
    ) -> List[Requirement]:
        """推斷非功能性需求"""
        
        domain = domain_analysis['primary_domain']
        domain_knowledge = self.domain_knowledge.get(domain, {})
        
        # 基於領域知識推斷非功能性需求
        inferred_requirements = []
        req_id = 1
        
        # 性能需求
        performance_reqs = domain_knowledge.get('performance_requirements', [])
        for perf_req in performance_reqs:
            req = Requirement(
                id=f"NFR_{req_id:03d}",
                type=RequirementType.PERFORMANCE,
                priority=Priority.HIGH,
                title=f"性能需求: {perf_req}",
                description=f"系統需要滿足 {perf_req} 的性能要求",
                acceptance_criteria=[f"系統測試通過 {perf_req} 標準"],
                technical_notes=["需要進行性能測試", "可能需要快取和優化"],
                dependencies=["系統架構設計"],
                estimated_effort="3 days",
                risk_level="medium"
            )
            inferred_requirements.append(req)
            req_id += 1
        
        # 安全需求
        security_reqs = domain_knowledge.get('security_requirements', [])
        for sec_req in security_reqs:
            req = Requirement(
                id=f"NFR_{req_id:03d}",
                type=RequirementType.SECURITY,
                priority=Priority.CRITICAL,
                title=f"安全需求: {sec_req}",
                description=f"系統必須實作 {sec_req} 安全措施",
                acceptance_criteria=[f"通過 {sec_req} 安全檢查"],
                technical_notes=["需要安全專家審核", "定期安全測試"],
                dependencies=["認證系統設計"],
                estimated_effort="2 days",
                risk_level="high"
            )
            inferred_requirements.append(req)
            req_id += 1
        
        # 可用性需求
        req = Requirement(
            id=f"NFR_{req_id:03d}",
            type=RequirementType.NON_FUNCTIONAL,
            priority=Priority.HIGH,
            title="可用性需求: 99.9% 正常運行時間",
            description="系統需要維持高可用性，年度正常運行時間至少 99.9%",
            acceptance_criteria=["監控顯示 99.9% 正常運行時間", "故障恢復時間 < 5 分鐘"],
            technical_notes=["需要負載均衡", "需要故障轉移機制", "需要健康檢查"],
            dependencies=["基礎設施設計"],
            estimated_effort="5 days",
            risk_level="medium"
        )
        inferred_requirements.append(req)
        
        logger.info(f"推斷非功能性需求: {len(inferred_requirements)} 個")
        return inferred_requirements
    
    async def _analyze_technical_requirements(
        self, 
        description: str, 
        domain_analysis: Dict[str, Any]
    ) -> List[Requirement]:
        """分析技術需求"""
        
        system_message = """你是一個技術架構師。請分析技術需求和約束條件。

回應格式要求（JSON 陣列）：
[
  {
    "title": "技術需求標題",
    "description": "詳細技術描述",
    "acceptance_criteria": ["技術驗收標準1", "技術驗收標準2"],
    "technical_notes": ["實作考量1", "實作考量2"],
    "priority": "critical/high/medium/low",
    "estimated_effort": "3 days",
    "dependencies": ["相關依賴1", "相關依賴2"],
    "risk_level": "low/medium/high"
  }
]"""
        
        prompt = f"""
請分析以下項目的技術需求：

描述: {description}
應用領域: {domain_analysis['primary_domain']}
複雜度指標: {', '.join(domain_analysis.get('complexity_indicators', []))}

請識別：
1. 技術棧選擇需求
2. 整合需求（第三方 API、服務等）
3. 資料存儲需求
4. 部署和基礎設施需求
5. 監控和日誌需求
6. 備份和災難恢復需求
7. 擴展性需求
8. 合規性需求

每個技術需求應該：
- 明確技術選擇的理由
- 包含實作驗證方式
- 評估技術風險
- 識別關鍵依賴
"""
        
        result = await self.model_manager.execute_task(
            task_type=ModelType.REQUIREMENT_ANALYSIS,
            prompt=prompt,
            system_message=system_message,
            priority="quality",
            max_tokens=2500
        )
        
        try:
            requirements_data = json.loads(result['content'])
            requirements = []
            
            for i, req_data in enumerate(requirements_data):
                req = Requirement(
                    id=f"TR_{i+1:03d}",
                    type=RequirementType.TECHNICAL,
                    priority=Priority(req_data.get('priority', 'medium')),
                    title=req_data['title'],
                    description=req_data['description'],
                    acceptance_criteria=req_data.get('acceptance_criteria', []),
                    technical_notes=req_data.get('technical_notes', []),
                    dependencies=req_data.get('dependencies', []),
                    estimated_effort=req_data.get('estimated_effort', '2 days'),
                    risk_level=req_data.get('risk_level', 'medium')
                )
                requirements.append(req)
            
            logger.info(f"分析技術需求: {len(requirements)} 個")
            return requirements
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"技術需求分析失敗，使用預設需求: {str(e)}")
            return self._get_default_technical_requirements()
    
    async def _recommend_tech_stack(
        self, 
        description: str, 
        domain_analysis: Dict[str, Any],
        requirements: List[Requirement]
    ) -> TechnicalStack:
        """推薦技術棧"""
        
        # 基於領域和需求複雜度選擇合適的技術棧模板
        domain = domain_analysis['primary_domain']
        complexity_indicators = domain_analysis.get('complexity_indicators', ['medium'])
        
        # 分析需求中的技術偏好
        high_performance_needed = any(
            'performance' in req.description.lower() or req.type == RequirementType.PERFORMANCE
            for req in requirements
        )
        
        security_critical = any(
            req.type == RequirementType.SECURITY and req.priority in [Priority.CRITICAL, Priority.HIGH]
            for req in requirements
        )
        
        scalability_needed = any(
            'scale' in req.description.lower() or 'concurrent' in req.description.lower()
            for req in requirements
        )
        
        # 選擇技術棧模板
        if 'enterprise' in complexity_indicators and security_critical:
            template_key = "enterprise_java"
        elif scalability_needed and 'microservices' in description.lower():
            template_key = "nodejs_microservices"
        elif 'serverless' in description.lower() or 'lambda' in description.lower():
            template_key = "serverless_stack"
        else:
            template_key = "modern_web_python"
        
        tech_stack = self.tech_stack_templates[template_key]
        
        logger.info(f"推薦技術棧模板: {template_key}")
        return tech_stack
    
    async def _recommend_architecture_patterns(
        self, 
        description: str,
        requirements: List[Requirement]
    ) -> List[ArchitecturePattern]:
        """推薦架構模式"""
        
        recommended_patterns = []
        
        # 分析需求特徵
        high_scalability = any(
            'scale' in req.description.lower() for req in requirements
        )
        
        real_time_processing = any(
            'real time' in req.description.lower() or 'instant' in req.description.lower()
            for req in requirements
        )
        
        complex_business_logic = len([
            req for req in requirements 
            if req.type == RequirementType.FUNCTIONAL and req.priority in [Priority.CRITICAL, Priority.HIGH]
        ]) > 10
        
        event_driven_features = any(
            'notification' in req.description.lower() or 'event' in req.description.lower()
            for req in requirements
        )
        
        # 基於特徵推薦架構模式
        if high_scalability and complex_business_logic:
            recommended_patterns.append(self.architecture_patterns['microservices'])
        
        if real_time_processing or event_driven_features:
            recommended_patterns.append(self.architecture_patterns['event_driven'])
        
        if 'serverless' in description.lower():
            recommended_patterns.append(self.architecture_patterns['serverless'])
        
        # 如果沒有特殊需求，推薦單體架構
        if not recommended_patterns:
            recommended_patterns.append(self.architecture_patterns['monolithic'])
        
        logger.info(f"推薦架構模式: {[p.pattern_name for p in recommended_patterns]}")
        return recommended_patterns
    
    async def _assess_project_scope(
        self, 
        description: str,
        requirements: List[Requirement]
    ) -> Dict[str, Any]:
        """評估項目範圍"""
        
        total_requirements = len(requirements)
        critical_requirements = len([req for req in requirements if req.priority == Priority.CRITICAL])
        high_requirements = len([req for req in requirements if req.priority == Priority.HIGH])
        
        # 計算功能點
        functional_points = len([req for req in requirements if req.type == RequirementType.FUNCTIONAL])
        integration_points = len([req for req in requirements if req.type == RequirementType.INTEGRATION])
        
        # 評估複雜度
        if total_requirements > 30 or critical_requirements > 10:
            complexity = "high"
        elif total_requirements > 15 or critical_requirements > 5:
            complexity = "medium"
        else:
            complexity = "low"
        
        # 評估項目規模
        if functional_points > 20:
            size = "large"
        elif functional_points > 10:
            size = "medium"
        else:
            size = "small"
        
        return {
            "total_requirements": total_requirements,
            "critical_requirements": critical_requirements,
            "high_priority_requirements": high_requirements,
            "functional_points": functional_points,
            "integration_points": integration_points,
            "estimated_complexity": complexity,
            "estimated_size": size,
            "team_size_recommendation": self._recommend_team_size(complexity, size),
            "phases": self._suggest_development_phases(requirements)
        }
    
    async def _estimate_timeline(
        self, 
        requirements: List[Requirement],
        project_scope: Dict[str, Any]
    ) -> Dict[str, str]:
        """估算開發時間線"""
        
        # 計算總工作量（天）
        total_effort_days = 0
        for req in requirements:
            effort_str = req.estimated_effort
            if 'day' in effort_str:
                days = int(re.findall(r'\d+', effort_str)[0])
                total_effort_days += days
            elif 'hour' in effort_str:
                hours = int(re.findall(r'\d+', effort_str)[0])
                total_effort_days += hours / 8
        
        # 考慮風險緩衝（30%）
        buffered_effort = total_effort_days * 1.3
        
        # 基於團隊規模調整
        team_size = project_scope['team_size_recommendation']
        if team_size > 1:
            parallel_efficiency = 0.8  # 多人協作效率折扣
            calendar_days = (buffered_effort / team_size) * parallel_efficiency
        else:
            calendar_days = buffered_effort
        
        # 轉換為周和月
        weeks = calendar_days / 5  # 工作日
        months = weeks / 4
        
        return {
            "estimated_effort_days": f"{total_effort_days:.1f} 天",
            "with_buffer_days": f"{buffered_effort:.1f} 天",
            "calendar_weeks": f"{weeks:.1f} 週",
            "calendar_months": f"{months:.1f} 個月",
            "team_size": f"{team_size} 人",
            "start_to_mvp": f"{weeks * 0.6:.1f} 週（MVP）",
            "start_to_production": f"{weeks:.1f} 週（生產版本）"
        }
    
    async def _assess_risks(
        self, 
        description: str,
        requirements: List[Requirement],
        tech_stack: TechnicalStack
    ) -> Dict[str, Any]:
        """評估項目風險"""
        
        risks = {
            "technical_risks": [],
            "business_risks": [],
            "timeline_risks": [],
            "resource_risks": [],
            "overall_risk_level": "medium"
        }
        
        # 技術風險
        high_risk_requirements = [req for req in requirements if req.risk_level == "high"]
        if high_risk_requirements:
            risks["technical_risks"].append(f"有 {len(high_risk_requirements)} 個高風險技術需求")
        
        # 複雜度風險
        complex_integrations = [req for req in requirements if req.type == RequirementType.INTEGRATION]
        if len(complex_integrations) > 5:
            risks["technical_risks"].append("複雜整合需求可能導致開發延遲")
        
        # 時間線風險
        critical_requirements = [req for req in requirements if req.priority == Priority.CRITICAL]
        if len(critical_requirements) > 10:
            risks["timeline_risks"].append("關鍵需求過多，可能影響交付時間")
        
        # 資源風險
        if len(requirements) > 25:
            risks["resource_risks"].append("需求範圍龐大，可能需要更多開發資源")
        
        # 計算整體風險等級
        total_risk_factors = (
            len(risks["technical_risks"]) + 
            len(risks["business_risks"]) + 
            len(risks["timeline_risks"]) + 
            len(risks["resource_risks"])
        )
        
        if total_risk_factors > 6:
            risks["overall_risk_level"] = "high"
        elif total_risk_factors > 3:
            risks["overall_risk_level"] = "medium"
        else:
            risks["overall_risk_level"] = "low"
        
        return risks
    
    async def _generate_recommendations(
        self, 
        requirements: List[Requirement],
        tech_stack: TechnicalStack,
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """生成建議"""
        
        recommendations = []
        
        # 基於風險級別的建議
        if risk_assessment["overall_risk_level"] == "high":
            recommendations.append("建議採用敏捷開發方法，分階段交付以降低風險")
            recommendations.append("考慮建立 POC（概念驗證）來驗證技術可行性")
        
        # 基於需求數量的建議
        if len(requirements) > 20:
            recommendations.append("建議將需求分為核心功能和增強功能，優先開發核心功能")
        
        # 基於技術棧的建議
        if tech_stack.backend_framework in ["FastAPI", "NestJS"]:
            recommendations.append("選用的框架支援快速原型開發，建議先實作 MVP")
        
        # 基於安全需求的建議
        security_requirements = [req for req in requirements if req.type == RequirementType.SECURITY]
        if security_requirements:
            recommendations.append("建議在開發早期就整合安全最佳實踐")
            recommendations.append("考慮進行定期安全審計和滲透測試")
        
        return recommendations
    
    async def _generate_next_steps(
        self, 
        requirements: List[Requirement],
        project_scope: Dict[str, Any]
    ) -> List[str]:
        """生成下一步行動項目"""
        
        next_steps = [
            "與利害關係人確認需求優先級",
            "進行技術可行性評估",
            "準備詳細的項目計畫和時間表",
            "設置開發環境和 CI/CD 流程",
            "開始 MVP 開發"
        ]
        
        # 基於項目複雜度調整
        if project_scope["estimated_complexity"] == "high":
            next_steps.insert(1, "建立技術原型驗證關鍵架構決策")
            next_steps.insert(-1, "準備風險緩解計畫")
        
        return next_steps
    
    def _calculate_confidence_score(
        self, 
        description: str, 
        requirements: List[Requirement]
    ) -> float:
        """計算分析信心分數"""
        
        score = 0.5  # 基礎分數
        
        # 基於描述詳細程度
        if len(description) > 100:
            score += 0.1
        if len(description) > 300:
            score += 0.1
        
        # 基於提取的需求數量
        if len(requirements) > 5:
            score += 0.1
        if len(requirements) > 15:
            score += 0.1
        
        # 基於需求詳細程度
        detailed_requirements = [
            req for req in requirements 
            if len(req.acceptance_criteria) > 1 and len(req.technical_notes) > 0
        ]
        if len(detailed_requirements) > len(requirements) * 0.5:
            score += 0.1
        
        # 基於優先級分布
        priority_distribution = {}
        for req in requirements:
            priority_distribution[req.priority] = priority_distribution.get(req.priority, 0) + 1
        
        if len(priority_distribution) > 2:  # 有多種優先級
            score += 0.1
        
        return min(score, 1.0)
    
    def _record_analysis_history(
        self, 
        description: str, 
        result: RequirementAnalysisResult
    ):
        """記錄分析歷史"""
        
        record = {
            "description": description,
            "analysis_id": result.analysis_id,
            "requirement_count": len(result.requirements),
            "confidence_score": result.confidence_score,
            "tech_stack": result.technical_stack.backend_framework,
            "timestamp": result.analysis_timestamp
        }
        
        self.analysis_history.append(record)
        
        # 更新模式頻率
        for pattern in result.architecture_patterns:
            pattern_name = pattern.pattern_name
            self.pattern_frequency[pattern_name] = self.pattern_frequency.get(pattern_name, 0) + 1
        
        # 保持歷史記錄在合理範圍內
        if len(self.analysis_history) > 500:
            self.analysis_history = self.analysis_history[-250:]
    
    def _recommend_team_size(self, complexity: str, size: str) -> int:
        """推薦團隊規模"""
        
        if complexity == "high" and size == "large":
            return 6
        elif complexity == "high" or size == "large":
            return 4
        elif complexity == "medium" or size == "medium":
            return 3
        else:
            return 2
    
    def _suggest_development_phases(self, requirements: List[Requirement]) -> List[str]:
        """建議開發階段"""
        
        phases = []
        
        # MVP 階段
        critical_reqs = [req for req in requirements if req.priority == Priority.CRITICAL]
        if critical_reqs:
            phases.append(f"階段 1 - MVP: {len(critical_reqs)} 個關鍵功能")
        
        # 核心功能階段
        high_reqs = [req for req in requirements if req.priority == Priority.HIGH]
        if high_reqs:
            phases.append(f"階段 2 - 核心功能: {len(high_reqs)} 個高優先級功能")
        
        # 增強功能階段
        medium_reqs = [req for req in requirements if req.priority == Priority.MEDIUM]
        if medium_reqs:
            phases.append(f"階段 3 - 增強功能: {len(medium_reqs)} 個中優先級功能")
        
        # 可選功能階段
        optional_reqs = [req for req in requirements if req.priority in [Priority.LOW, Priority.NICE_TO_HAVE]]
        if optional_reqs:
            phases.append(f"階段 4 - 可選功能: {len(optional_reqs)} 個可選功能")
        
        return phases
    
    def _get_default_functional_requirements(self) -> List[Requirement]:
        """獲取預設功能需求"""
        return [
            Requirement(
                id="FR_001",
                type=RequirementType.FUNCTIONAL,
                priority=Priority.CRITICAL,
                title="用戶註冊功能",
                description="用戶可以通過郵箱註冊新帳戶",
                acceptance_criteria=["用戶可以輸入郵箱和密碼", "系統驗證郵箱格式", "註冊成功後發送確認郵件"],
                technical_notes=["需要郵箱驗證", "密碼加密存儲"],
                dependencies=["用戶數據庫設計"],
                estimated_effort="2 days",
                risk_level="low"
            )
        ]
    
    def _get_default_technical_requirements(self) -> List[Requirement]:
        """獲取預設技術需求"""
        return [
            Requirement(
                id="TR_001",
                type=RequirementType.TECHNICAL,
                priority=Priority.HIGH,
                title="資料庫設計",
                description="設計和實作應用資料庫schema",
                acceptance_criteria=["資料庫正規化", "建立適當索引", "資料庫遷移腳本"],
                technical_notes=["使用 PostgreSQL", "設置連接池"],
                dependencies=["需求分析完成"],
                estimated_effort="3 days",
                risk_level="medium"
            )
        ]

# 使用範例
async def main():
    """測試需求分析器"""
    
    analyzer = RequirementAnalyzer()
    
    description = """
    我想創建一個電商網站，用戶可以瀏覽商品、加入購物車、結帳付款。
    需要支援多種支付方式，包括信用卡和數位錢包。
    還需要有後台管理系統，讓商家可以管理商品和訂單。
    系統需要支援高並發訪問，預期同時有上千用戶在線。
    """
    
    result = await analyzer.analyze_requirements(description)
    
    print(f"分析 ID: {result.analysis_id}")
    print(f"信心分數: {result.confidence_score:.2f}")
    print(f"需求總數: {len(result.requirements)}")
    print(f"推薦技術棧: {result.technical_stack.backend_framework}")
    print(f"推薦架構: {[p.pattern_name for p in result.architecture_patterns]}")
    print(f"預估時間: {result.estimated_timeline['calendar_months']}")
    
    print("\n功能需求:")
    for req in result.requirements:
        if req.type == RequirementType.FUNCTIONAL:
            print(f"- {req.title} ({req.priority.value})")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())