from pydantic import BaseModel
from typing import List, Optional

class ProblemAnalysis(BaseModel):
    """Структурированный анализ проблемы"""
    problem_statement: str
    problem_area: str
    
    
class Hypothesis(BaseModel):
    """Гипотеза решения проблемы"""
    hypothesis: str
    confidence: float  # От 0 до 1
    

class Solution(BaseModel):
    """Решение проблемы"""
    solution: str
    steps: List[str]
    
    
class ValidationResult(BaseModel):
    """Результат проверки решения"""
    is_valid: bool
    confidence: float
    feedback: str
    missing_aspects: Optional[List[str]] = None 