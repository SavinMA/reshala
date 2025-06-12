import os
from typing import List, Dict, Any, Tuple
from agents import ProblemAnalyzer, HypothesisAgent, SolutionAgent, ValidationAgent
from models import ProblemAnalysis, Hypothesis, Solution, ValidationResult
import asyncio
import logging


class ReasoningEngine:
    """Движок рассуждений, управляющий циклом агентов"""
    
    def __init__(self, api_key: str):
        self.analyzer = ProblemAnalyzer(api_key)
        self.hypothesis_agent = HypothesisAgent(api_key)
        self.solution_agent = SolutionAgent(api_key)
        self.validation_agent = ValidationAgent(api_key)
        self.max_iterations = 5
        self.validity_threshold = float(os.getenv("VALIDITY_THRESHOLD_PERCENTAGE", "97"))/100 # Default to "97" if not set

        
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
            await progress_callback("🔍 *Анализирую проблему...*")
            
        problem_analysis = self.analyzer.analyze(user_question)
        await asyncio.sleep(1) # Задержка между запросами к агентам
        
        analysis_message = f"""*Аналитик:*
Проблема: {problem_analysis.problem_statement}
Область: {problem_analysis.problem_area}"""
        dialogue_history.append({"agent": "Аналитик", "message": analysis_message})
        if progress_callback:
            await progress_callback(analysis_message)
        
        # Цикл рассуждений
        previous_attempts = []
        iteration = 0
        final_solution = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Шаг 2: Построение гипотезы
            hypothesis = self.hypothesis_agent.build_hypothesis(problem_analysis, previous_attempts)
            await asyncio.sleep(1) # Задержка между запросами к агентам
            
            hypothesis_message = f"""*Генератор гипотез:*
Гипотеза: {hypothesis.hypothesis}
Уверенность: {hypothesis.confidence:.2f}"""
            dialogue_history.append({"agent": "Генератор гипотез", "message": hypothesis_message})
            if progress_callback:
                await progress_callback(hypothesis_message)
            
            # Шаг 3: Построение решения
            solution = self.solution_agent.build_solution(problem_analysis, hypothesis)
            await asyncio.sleep(1) # Задержка между запросами к агентам
            
            solution_message = f"""*Решатель:*
Решение: {solution.solution}
Шаги:
""" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(solution.steps)])
            dialogue_history.append({"agent": "Решатель", "message": solution_message})
            if progress_callback:
                await progress_callback(solution_message)
            
            # Шаг 4: Валидация решения
            validation = self.validation_agent.validate_solution(problem_analysis, solution)
            await asyncio.sleep(1) # Задержка между запросами к агентам
            
            isValid = validation.confidence >= self.validity_threshold

            validation_message = f"""*Валидатор:*
Валидность решения: {validation.confidence*100:.0f}%: {'✅ Решение валидно' if isValid else '❌ Решение требует доработки'}\nОбратная связь: {validation.feedback}"""
            dialogue_history.append({"agent": "Валидатор", "message": validation_message})
            if progress_callback:
                await progress_callback(validation_message)
            
            if isValid:
                if progress_callback:
                    await progress_callback(f"✅ *Решение принято после {iteration} итераций!*")
                final_solution = solution
                break
            else:
                logging.info(f"Решение не валидно (уверенность: {validation.confidence}). Настройка: {self.validity_threshold}")
                # Добавляем попытку в историю для следующей итерации
                previous_attempts.append({
                    "hypothesis": hypothesis.hypothesis,
                    "feedback": validation.feedback,
                    "missing_aspects": validation.missing_aspects
                })
                
                #if progress_callback:
                #    await progress_callback(f"🔄 *Решение требует доработки. Переход к следующей итерации...*")
                    
                # Небольшая задержка между итерациями
                await asyncio.sleep(1)
        
        if not final_solution:
            # Если не нашли валидное решение за max_iterations, берем последнее
            final_solution = solution
            if progress_callback:
                await progress_callback(f"⚠️ *Достигнут лимит итераций. Используется последнее решение.*")
        
        return dialogue_history, final_solution 