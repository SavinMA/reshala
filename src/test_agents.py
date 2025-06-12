"""
Тестовый скрипт для проверки работы агентов без Telegram
"""

import asyncio
import os
from dotenv import load_dotenv
from reasoning_engine import ReasoningEngine

# Загрузка переменных окружения
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    raise ValueError("Пожалуйста, установите MISTRAL_API_KEY в файле .env")


async def test_reasoning():
    """Тестирует работу движка рассуждений"""
    
    # Создаем движок
    engine = ReasoningEngine(MISTRAL_API_KEY)
    
    # Тестовые вопросы
    test_questions = [
        "Как улучшить производительность Python кода?",
        "Как начать вести здоровый образ жизни?",
        "Как организовать эффективную работу удаленной команды?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"Тест {i}: {question}")
        print('='*60)
        
        # Функция для вывода прогресса
        async def print_progress(message: str):
            print(f">>> {message}")
        
        try:
            # Запускаем рассуждение
            dialogue_history, solution = await engine.reason(
                question,
                progress_callback=print_progress
            )
            
            # Выводим диалог
            print("\n--- ДИАЛОГ АГЕНТОВ ---")
            for entry in dialogue_history:
                print(f"\n[{entry['agent']}]:")
                print(entry['message'])
                print("-" * 40)
            
            # Выводим финальное решение
            print("\n--- ФИНАЛЬНОЕ РЕШЕНИЕ ---")
            print(f"Решение: {solution.solution}")
            print("\nШаги:")
            for j, step in enumerate(solution.steps, 1):
                print(f"{j}. {step}")
                
        except Exception as e:
            print(f"Ошибка: {str(e)}")
        
        # Пауза между тестами
        if i < len(test_questions):
            print("\nНажмите Enter для следующего теста...")
            input()


if __name__ == "__main__":
    print("Запуск тестирования агентов...")
    asyncio.run(test_reasoning()) 