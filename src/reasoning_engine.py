import os
from typing import List, Dict, Any, Tuple
from agents import ProblemAnalyzer, HypothesisAgent, SolutionAgent, ValidationAgent
from models import ProblemAnalysis, Hypothesis, Solution, ValidationResult
import asyncio


class ReasoningEngine:
    """Движок рассуждений, управляющий циклом агентов"""
    
    def __init__(self, api_key: str):
        self.analyzer = ProblemAnalyzer(api_key)
        self.hypothesis_agent = HypothesisAgent(api_key)
        self.solution_agent = SolutionAgent(api_key)
        self.validation_agent = ValidationAgent(api_key)
        self.max_iterations = 5
        
    async def reason(self, user_question: str, progress_callback=None) -> Tuple[List[Dict[str, Any]], Solution]:
        """
        Запускает процесс рассуждения
        
        Args:
            user_question: Вопрос пользователя
            progress_callback: Функция для отправки промежуточных результатов
            
        Returns:
            Tuple[история диалога агентов, финальное решение]
        """
        dialogue_history = []
        
        # Шаг 1: Анализ проблемы
        if progress_callback:
            await progress_callback("🔍 Анализирую проблему...")
            
        problem_analysis = self.analyzer.analyze(user_question)
        
        dialogue_history.append({
            "agent": "Аналитик",
            "message": f"Проблема: {problem_analysis.problem_statement}\nОбласть: {problem_analysis.problem_area}"
        })
        
        if progress_callback:
            await progress_callback(f"📊 Проблема определена: {problem_analysis.problem_statement} (область: {problem_analysis.problem_area})")
        
        # Цикл рассуждений
        previous_attempts = []
        iteration = 0
        final_solution = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            if progress_callback:
                await progress_callback(f"🔄 Цикл рассуждения {iteration}/{self.max_iterations}")
            
            # Шаг 2: Построение гипотезы
            hypothesis = self.hypothesis_agent.build_hypothesis(problem_analysis, previous_attempts)
            
            dialogue_history.append({
                "agent": "Генератор гипотез",
                "message": f"Гипотеза: {hypothesis.hypothesis}\nУверенность: {hypothesis.confidence:.2f}"
            })
            
            if progress_callback:
                await progress_callback(f"💡 Гипотеза {iteration}: {hypothesis.hypothesis[:100]}...")
            
            # Шаг 3: Построение решения
            solution = self.solution_agent.build_solution(problem_analysis, hypothesis)
            
            dialogue_history.append({
                "agent": "Решатель",
                "message": f"Решение: {solution.solution}\nШаги:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(solution.steps)])
            })
            
            if progress_callback:
                await progress_callback(f"🛠 Решение построено с {len(solution.steps)} шагами")
            
            # Шаг 4: Валидация решения
            validation = self.validation_agent.validate_solution(problem_analysis, solution)
            
            dialogue_history.append({
                "agent": "Валидатор",
                "message": f"Результат проверки: {'✅ Решение валидно' if validation.is_valid else '❌ Решение требует доработки'}\nОбратная связь: {validation.feedback}"
            })
            
            if validation.is_valid:
                if progress_callback:
                    await progress_callback(f"✅ Решение принято после {iteration} итераций!")
                final_solution = solution
                break
            else:
                # Добавляем попытку в историю для следующей итерации
                previous_attempts.append({
                    "hypothesis": hypothesis.hypothesis,
                    "feedback": validation.feedback,
                    "missing_aspects": validation.missing_aspects
                })
                
                if progress_callback:
                    await progress_callback(f"🔄 Решение требует доработки. Переход к следующей итерации...")
                    
                # Небольшая задержка между итерациями
                await asyncio.sleep(1)
        
        if not final_solution:
            # Если не нашли валидное решение за max_iterations, берем последнее
            final_solution = solution
            if progress_callback:
                await progress_callback(f"⚠️ Достигнут лимит итераций. Используется последнее решение.")
        
        return dialogue_history, final_solution
    
    def format_dialogue_for_telegram(self, dialogue_history: List[Dict[str, Any]]) -> str:
        """Форматирует историю диалога для отправки в Telegram"""
        formatted = "🤖 *Диалог агентов:*\n\n"
        
        for entry in dialogue_history:
            formatted += f"*{entry['agent']}:*\n{entry['message']}\n\n"
            
        return formatted 