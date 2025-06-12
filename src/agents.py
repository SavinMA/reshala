import os
from mistralai import Mistral
from models import ProblemAnalysis, Hypothesis, Solution, ValidationResult
import json
from typing import List, Dict, Any
import time
import httpx

class BaseAgent:
    """Базовый класс для всех агентов"""
    def __init__(self, api_key: str, model: str = "mistral-large-latest", max_retries: int = 3):
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        
    def _create_message(self, role: str, content: str) -> dict:
        return {"role": role, "content": content}

    def _safe_chat_complete(self, messages: List[Dict[str, Any]], response_format: Dict[str, str], current_model: str) -> Any:
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.complete(
                    model=current_model,
                    messages=messages,
                    response_format=response_format
                )
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    print(f"Rate limit hit with model {current_model}. Retrying with mistral-small-latest...")
                    current_model = "mistral-small-latest" # Switch to a different model
                    time.sleep(2 ** attempt) # Exponential backoff
                else:
                    raise # Re-raise other API errors
            except Exception as e:
                if "capacity exceeded" in str(e):
                    print(f"Rate limit hit with model {current_model}. Retrying with mistral-small-latest...")
                    current_model = "mistral-small-latest" # Switch to a different model
                    time.sleep(2 ** attempt) # Exponential backoff
                else:
                    raise # Re-raise other API errors
        raise Exception("Max retries exceeded for API call.")


class ProblemAnalyzer(BaseAgent):
    """Агент для анализа проблемы и определения области"""
    
    def analyze(self, user_question: str) -> ProblemAnalysis:
        """Анализирует вопрос пользователя и возвращает структурированный результат"""
        
        system_prompt = """Ты - эксперт по анализу проблем. Твоя задача - проанализировать вопрос пользователя и:
1. Четко сформулировать проблему
2. Определить область проблемы

Отвечай в формате JSON:
{
    "problem_statement": "четкая формулировка проблемы",
    "problem_area": "одна из областей"
}"""
        
        messages = [
            self._create_message("system", system_prompt),
            self._create_message("user", user_question)
        ]
        
        response = self._safe_chat_complete(
            messages=messages,
            response_format={"type": "json_object"},
            current_model=self.model
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return ProblemAnalysis(**result)


class HypothesisAgent(BaseAgent):
    """Агент для построения гипотез"""
    
    def build_hypothesis(self, problem: ProblemAnalysis, previous_attempts: List[Dict[str, Any]] = None) -> Hypothesis:
        """Строит гипотезу решения проблемы"""
        
        context = f"Проблема: {problem.problem_statement}\nОбласть: {problem.problem_area}"
        
        if previous_attempts:
            context += "\n\nПредыдущие попытки:\n"
            for attempt in previous_attempts:
                context += f"- Гипотеза: {attempt['hypothesis']}\n"
                context += f"  Обратная связь: {attempt['feedback']}\n"
        
        system_prompt = f"""Ты - эксперт по построению гипотез в области {problem.problem_area}. 
Твоя задача - предложить гипотезу решения проблемы.
Если есть предыдущие попытки, то учитывай их и придумай новую гипотезу.
Предлагай самую простую гипотезу для решения проблемы.

Отвечай в формате JSON:
{{
    "hypothesis": "детальное описание гипотезы решения",
    "confidence": 0.8 (значение от 0 до 1 - уверенность в гипотезе)
}}"""
        
        messages = [
            self._create_message("system", system_prompt),
            self._create_message("user", context)
        ]
        
        response = self._safe_chat_complete(
            messages=messages,
            response_format={"type": "json_object"},
            current_model=self.model
        )
        
        result = json.loads(response.choices[0].message.content)
        return Hypothesis(**result)


class SolutionAgent(BaseAgent):
    """Агент для построения решений"""
    
    def build_solution(self, problem: ProblemAnalysis, hypothesis: Hypothesis) -> Solution:
        """Строит конкретное решение на основе гипотезы"""
        
        context = f"""Проблема: {problem.problem_statement}
Область: {problem.problem_area}
Гипотеза: {hypothesis.hypothesis}"""
        
        system_prompt = f"""Ты - эксперт по решению проблем в области {problem.problem_area}.
Твоя задача - построить конкретное решение на основе предложенной гипотезы.

Отвечай в формате JSON:
{{
    "solution": "описание решения",
    "steps": ["шаг 1", "шаг 2", "шаг 3", ...]
}}"""
        
        messages = [
            self._create_message("system", system_prompt),
            self._create_message("user", context)
        ]
        
        response = self._safe_chat_complete(
            messages=messages,
            response_format={"type": "json_object"},
            current_model=self.model
        )
        
        result = json.loads(response.choices[0].message.content)
        return Solution(**result)


class ValidationAgent(BaseAgent):
    """Агент для проверки решений"""
    
    def __init__(self, api_key: str, model: str = "mistral-large-latest", max_retries: int = 3):
        super().__init__(api_key, model, max_retries)

    def validate_solution(self, problem: ProblemAnalysis, solution: Solution) -> ValidationResult:
        """Проверяет, решает ли предложенное решение проблему"""
        
        context = f"""Проблема: {problem.problem_statement}
Область: {problem.problem_area}
Предложенное решение: {solution.solution}
Шаги: {', '.join(solution.steps)}"""
        
        system_prompt = f"""Ты - критический эксперт в области {problem.problem_area}.
Твоя задача - проверить, действительно ли предложенное решение решает проблему.
Будь критичен, но справедлив.

Отвечай в формате JSON:
{{
    "confidence": 0.55, (Результат сходимости решения в процентах)
    "feedback": "детальная обратная связь",
    "missing_aspects": ["аспект 1", "аспект 2"] или null
}}"""
        
        messages = [
            self._create_message("system", system_prompt),
            self._create_message("user", context)
        ]
        
        response = self._safe_chat_complete(
            messages=messages,
            response_format={"type": "json_object"},
            current_model=self.model
        )
        
        result = json.loads(response.choices[0].message.content)
        return ValidationResult(**result) 