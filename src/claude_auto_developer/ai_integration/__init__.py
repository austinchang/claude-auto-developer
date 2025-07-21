"""
AI Integration Module - AI 整合模組
提供多模型 AI 整合、智能代碼生成和需求分析能力
"""

from .model_manager import ModelManager, ModelType, AIModel
from .code_generator_v2 import CodeGeneratorV2
from .requirement_analyzer import RequirementAnalyzer
from .architecture_designer import ArchitectureDesigner
from .quality_assessor import QualityAssessor

__all__ = [
    'ModelManager',
    'ModelType', 
    'AIModel',
    'CodeGeneratorV2',
    'RequirementAnalyzer',
    'ArchitectureDesigner',
    'QualityAssessor'
]

__version__ = "2.0.0"