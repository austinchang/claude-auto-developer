#!/usr/bin/env python3
"""
Model Manager - 多模型 AI 管理器
負責管理和協調多個 AI 模型，智能選擇最適合的模型執行任務
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
import httpx
import openai
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """AI 模型類型枚舉"""
    CODE_GENERATION = "code_generation"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"

class ModelProvider(Enum):
    """AI 模型提供商枚舉"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    LOCAL = "local"

@dataclass
class ModelCapability:
    """模型能力定義"""
    model_type: ModelType
    quality_score: float  # 0.0-1.0
    speed_score: float    # 0.0-1.0
    cost_score: float     # 0.0-1.0 (higher = cheaper)
    context_length: int
    supported_languages: List[str]
    
class AIModel:
    """AI 模型封裝類"""
    
    def __init__(
        self,
        name: str,
        provider: ModelProvider,
        api_key: Optional[str] = None,
        capabilities: List[ModelCapability] = None,
        rate_limit: int = 60,  # requests per minute
        cost_per_1k_tokens: float = 0.0
    ):
        self.name = name
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.value.upper()}_API_KEY")
        self.capabilities = capabilities or []
        self.rate_limit = rate_limit
        self.cost_per_1k_tokens = cost_per_1k_tokens
        
        # 使用統計
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_request_time = None
        self.recent_requests = []  # 最近請求的時間戳
        
        # 初始化客戶端
        self._init_client()
    
    def _init_client(self):
        """初始化 AI 客戶端"""
        try:
            if self.provider == ModelProvider.ANTHROPIC:
                self.client = Anthropic(api_key=self.api_key)
            elif self.provider == ModelProvider.OPENAI:
                self.client = openai.OpenAI(api_key=self.api_key)
            elif self.provider == ModelProvider.GOOGLE:
                # Google AI 客戶端初始化
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
            else:
                self.client = None
                
            logger.info(f"已初始化 {self.provider.value} 模型: {self.name}")
            
        except Exception as e:
            logger.error(f"初始化 {self.provider.value} 客戶端失敗: {str(e)}")
            self.client = None
    
    def can_handle(self, task_type: ModelType) -> bool:
        """檢查模型是否能處理指定任務類型"""
        return any(cap.model_type == task_type for cap in self.capabilities)
    
    def get_capability_score(self, task_type: ModelType) -> float:
        """獲取模型對指定任務的能力評分"""
        for cap in self.capabilities:
            if cap.model_type == task_type:
                # 綜合評分：品質 50%、速度 30%、成本 20%
                return cap.quality_score * 0.5 + cap.speed_score * 0.3 + cap.cost_score * 0.2
        return 0.0
    
    def is_rate_limited(self) -> bool:
        """檢查是否受到速率限制"""
        current_time = time.time()
        # 移除一分鐘前的請求記錄
        self.recent_requests = [
            req_time for req_time in self.recent_requests 
            if current_time - req_time < 60
        ]
        return len(self.recent_requests) >= self.rate_limit
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """生成 AI 回應"""
        if self.is_rate_limited():
            raise Exception(f"模型 {self.name} 已達速率限制")
        
        try:
            start_time = time.time()
            
            # 記錄請求時間
            self.recent_requests.append(start_time)
            self.total_requests += 1
            
            response = None
            tokens_used = 0
            
            if self.provider == ModelProvider.ANTHROPIC:
                response = await self._call_anthropic(
                    prompt, system_message, max_tokens, temperature, **kwargs
                )
            elif self.provider == ModelProvider.OPENAI:
                response = await self._call_openai(
                    prompt, system_message, max_tokens, temperature, **kwargs
                )
            elif self.provider == ModelProvider.GOOGLE:
                response = await self._call_google(
                    prompt, system_message, max_tokens, temperature, **kwargs
                )
            
            end_time = time.time()
            
            # 更新統計資訊
            tokens_used = response.get('tokens_used', 0)
            self.total_tokens += tokens_used
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            self.total_cost += cost
            self.last_request_time = datetime.now()
            
            result = {
                'content': response.get('content', ''),
                'model': self.name,
                'tokens_used': tokens_used,
                'cost': cost,
                'response_time': end_time - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"模型 {self.name} 回應完成，使用 {tokens_used} tokens，耗時 {result['response_time']:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"模型 {self.name} 生成回應失敗: {str(e)}")
            raise
    
    async def _call_anthropic(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """調用 Anthropic Claude 模型"""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.messages.create(
                model=self.name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            
            return {
                'content': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens
            }
            
        except Exception as e:
            logger.error(f"Anthropic API 調用失敗: {str(e)}")
            raise
    
    async def _call_openai(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """調用 OpenAI GPT 模型"""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"OpenAI API 調用失敗: {str(e)}")
            raise
    
    async def _call_google(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """調用 Google Gemini 模型"""
        try:
            model = self.client.GenerativeModel(self.name)
            
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
            
            response = model.generate_content(
                full_prompt,
                generation_config={
                    'max_output_tokens': max_tokens,
                    'temperature': temperature
                }
            )
            
            return {
                'content': response.text,
                'tokens_used': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
            
        except Exception as e:
            logger.error(f"Google AI API 調用失敗: {str(e)}")
            raise

class ModelManager:
    """多模型 AI 管理器"""
    
    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.performance_stats: Dict[str, Dict[str, float]] = {}
        
        # 初始化預設模型
        self._init_default_models()
    
    def _init_default_models(self):
        """初始化預設的 AI 模型"""
        
        # Claude 3.5 Sonnet - 優秀的代碼生成和分析
        claude_capabilities = [
            ModelCapability(
                ModelType.CODE_GENERATION, 0.95, 0.85, 0.70, 200000,
                ["python", "javascript", "typescript", "java", "go", "rust", "cpp"]
            ),
            ModelCapability(
                ModelType.REQUIREMENT_ANALYSIS, 0.90, 0.90, 0.70, 200000,
                ["natural_language"]
            ),
            ModelCapability(
                ModelType.ARCHITECTURE_DESIGN, 0.90, 0.85, 0.70, 200000,
                ["system_design"]
            ),
            ModelCapability(
                ModelType.CODE_REVIEW, 0.85, 0.90, 0.70, 200000,
                ["python", "javascript", "typescript", "java"]
            )
        ]
        
        self.add_model(AIModel(
            name="claude-3-5-sonnet-20241022",
            provider=ModelProvider.ANTHROPIC,
            capabilities=claude_capabilities,
            rate_limit=50,
            cost_per_1k_tokens=0.003
        ))
        
        # GPT-4 - 優秀的邏輯推理和複雜任務
        gpt4_capabilities = [
            ModelCapability(
                ModelType.CODE_GENERATION, 0.90, 0.75, 0.50, 128000,
                ["python", "javascript", "typescript", "java", "cpp"]
            ),
            ModelCapability(
                ModelType.ARCHITECTURE_DESIGN, 0.95, 0.80, 0.50, 128000,
                ["system_design"]
            ),
            ModelCapability(
                ModelType.DEBUGGING, 0.90, 0.80, 0.50, 128000,
                ["python", "javascript", "java"]
            )
        ]
        
        self.add_model(AIModel(
            name="gpt-4-turbo-preview",
            provider=ModelProvider.OPENAI,
            capabilities=gpt4_capabilities,
            rate_limit=40,
            cost_per_1k_tokens=0.01
        ))
        
        # Gemini Pro - 快速且成本效益高
        gemini_capabilities = [
            ModelCapability(
                ModelType.CODE_GENERATION, 0.80, 0.95, 0.90, 32000,
                ["python", "javascript", "java"]
            ),
            ModelCapability(
                ModelType.DOCUMENTATION, 0.85, 0.95, 0.90, 32000,
                ["markdown", "natural_language"]
            ),
            ModelCapability(
                ModelType.TESTING, 0.80, 0.90, 0.90, 32000,
                ["python", "javascript"]
            )
        ]
        
        self.add_model(AIModel(
            name="gemini-pro",
            provider=ModelProvider.GOOGLE,
            capabilities=gemini_capabilities,
            rate_limit=60,
            cost_per_1k_tokens=0.0005
        ))
    
    def add_model(self, model: AIModel):
        """添加新模型"""
        self.models[model.name] = model
        logger.info(f"已添加模型: {model.name} ({model.provider.value})")
    
    def get_best_model(
        self,
        task_type: ModelType,
        priority: str = "balanced",  # balanced, quality, speed, cost
        required_languages: List[str] = None
    ) -> Optional[AIModel]:
        """選擇最適合的模型"""
        
        available_models = []
        
        for model in self.models.values():
            if not model.can_handle(task_type):
                continue
            
            if model.is_rate_limited():
                continue
            
            # 檢查語言支援
            if required_languages:
                supported = any(
                    lang in cap.supported_languages
                    for cap in model.capabilities
                    if cap.model_type == task_type
                )
                if not supported:
                    continue
            
            score = model.get_capability_score(task_type)
            
            # 根據優先級調整評分
            if priority == "quality":
                for cap in model.capabilities:
                    if cap.model_type == task_type:
                        score = cap.quality_score
                        break
            elif priority == "speed":
                for cap in model.capabilities:
                    if cap.model_type == task_type:
                        score = cap.speed_score
                        break
            elif priority == "cost":
                for cap in model.capabilities:
                    if cap.model_type == task_type:
                        score = cap.cost_score
                        break
            
            available_models.append((model, score))
        
        if not available_models:
            logger.warning(f"沒有可用的模型處理任務類型: {task_type}")
            return None
        
        # 選擇評分最高的模型
        best_model = max(available_models, key=lambda x: x[1])[0]
        
        logger.info(f"為任務 {task_type} 選擇模型: {best_model.name}")
        return best_model
    
    async def execute_task(
        self,
        task_type: ModelType,
        prompt: str,
        system_message: Optional[str] = None,
        priority: str = "balanced",
        required_languages: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """執行 AI 任務"""
        
        start_time = time.time()
        
        # 選擇最佳模型
        model = self.get_best_model(task_type, priority, required_languages)
        if not model:
            raise Exception(f"沒有可用的模型處理任務: {task_type}")
        
        try:
            # 執行任務
            result = await model.generate_response(
                prompt=prompt,
                system_message=system_message,
                **kwargs
            )
            
            # 記錄任務歷史
            task_record = {
                'task_type': task_type.value,
                'model_used': model.name,
                'prompt_length': len(prompt),
                'response_length': len(result['content']),
                'tokens_used': result['tokens_used'],
                'cost': result['cost'],
                'response_time': result['response_time'],
                'timestamp': result['timestamp'],
                'success': True
            }
            
            self.task_history.append(task_record)
            self._update_performance_stats(model.name, task_record)
            
            return result
            
        except Exception as e:
            # 記錄失敗
            task_record = {
                'task_type': task_type.value,
                'model_used': model.name,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            
            self.task_history.append(task_record)
            logger.error(f"任務執行失敗: {str(e)}")
            raise
    
    def _update_performance_stats(self, model_name: str, task_record: Dict[str, Any]):
        """更新模型性能統計"""
        if model_name not in self.performance_stats:
            self.performance_stats[model_name] = {
                'total_tasks': 0,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'total_cost': 0.0,
                'avg_tokens': 0.0
            }
        
        stats = self.performance_stats[model_name]
        stats['total_tasks'] += 1
        
        if task_record['success']:
            # 更新成功率
            successful_tasks = sum(
                1 for record in self.task_history
                if record.get('model_used') == model_name and record.get('success', False)
            )
            stats['success_rate'] = successful_tasks / stats['total_tasks']
            
            # 更新平均回應時間
            total_time = sum(
                record.get('response_time', 0) for record in self.task_history
                if record.get('model_used') == model_name and record.get('success', False)
            )
            stats['avg_response_time'] = total_time / successful_tasks
            
            # 更新總成本和平均 tokens
            stats['total_cost'] += task_record.get('cost', 0)
            total_tokens = sum(
                record.get('tokens_used', 0) for record in self.task_history
                if record.get('model_used') == model_name and record.get('success', False)
            )
            stats['avg_tokens'] = total_tokens / successful_tasks
    
    def get_model_stats(self) -> Dict[str, Any]:
        """獲取模型統計資訊"""
        return {
            'models': {
                name: {
                    'total_requests': model.total_requests,
                    'total_tokens': model.total_tokens,
                    'total_cost': model.total_cost,
                    'last_request': model.last_request_time.isoformat() if model.last_request_time else None,
                    'rate_limited': model.is_rate_limited()
                }
                for name, model in self.models.items()
            },
            'performance': self.performance_stats,
            'total_tasks': len(self.task_history),
            'task_distribution': {
                task_type.value: sum(
                    1 for record in self.task_history
                    if record.get('task_type') == task_type.value
                )
                for task_type in ModelType
            }
        }
    
    def optimize_model_selection(self):
        """基於歷史數據優化模型選擇策略"""
        # 分析每個模型在不同任務類型上的表現
        task_performance = {}
        
        for record in self.task_history:
            if not record.get('success', False):
                continue
            
            task_type = record['task_type']
            model_name = record['model_used']
            
            if task_type not in task_performance:
                task_performance[task_type] = {}
            
            if model_name not in task_performance[task_type]:
                task_performance[task_type][model_name] = {
                    'count': 0,
                    'avg_time': 0,
                    'avg_cost': 0,
                    'quality_score': 0
                }
            
            perf = task_performance[task_type][model_name]
            perf['count'] += 1
            perf['avg_time'] = (perf['avg_time'] * (perf['count'] - 1) + record['response_time']) / perf['count']
            perf['avg_cost'] = (perf['avg_cost'] * (perf['count'] - 1) + record['cost']) / perf['count']
        
        # 根據性能數據更新模型能力評分
        for task_type, models_perf in task_performance.items():
            for model_name, perf in models_perf.items():
                if model_name in self.models:
                    model = self.models[model_name]
                    # 更新模型能力評分（這裡可以實作更複雜的學習演算法）
                    for cap in model.capabilities:
                        if cap.model_type.value == task_type:
                            # 簡單的適應性調整
                            if perf['avg_time'] < 5.0:  # 快速回應
                                cap.speed_score = min(1.0, cap.speed_score + 0.01)
                            if perf['avg_cost'] < 0.01:  # 低成本
                                cap.cost_score = min(1.0, cap.cost_score + 0.01)
        
        logger.info("模型選擇策略已優化")

# 全局模型管理器實例
model_manager = ModelManager()

# 使用範例
async def main():
    """測試模型管理器"""
    logger.info("測試多模型 AI 管理器...")
    
    try:
        # 測試代碼生成
        result = await model_manager.execute_task(
            task_type=ModelType.CODE_GENERATION,
            prompt="創建一個 Python 函數，計算斐波那契數列",
            system_message="你是一個專業的 Python 開發者",
            priority="quality"
        )
        
        print(f"生成的代碼:\n{result['content']}")
        print(f"使用模型: {result['model']}")
        print(f"tokens: {result['tokens_used']}, 成本: ${result['cost']:.4f}")
        
        # 獲取統計資訊
        stats = model_manager.get_model_stats()
        print(f"模型統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())