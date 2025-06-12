"""
Быстрый старт - простой пример использования системы рассуждений
"""

import asyncio
import os
from dotenv import load_dotenv
from reasoning_engine import ReasoningEngine

# Загрузка переменных окружения
load_dotenv()


async def quick_demo():
    """Быстрая демонстрация работы системы"""
    
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    
    if not MISTRAL_API_KEY:
        print("❌ Ошибка: MISTRAL_API_KEY не найден!")
        print("Создайте файл .env и добавьте туда:")
        print("MISTRAL_API_KEY=your_key_here")
        return
    
    print("🚀 Демонстрация системы рассуждений с ИИ агентами")
    print("=" * 50)
    
    # Запрос проблемы у пользователя
    question = input("\n❓ Введите вашу проблему или вопрос: ")
    
    if not question.strip():
        question = "Как улучшить концентрацию при работе из дома?"
        print(f"Используем пример: {question}")
    
    print("\n⏳ Запускаем процесс рассуждения...\n")
    
    # Создаем движок
    engine = ReasoningEngine(MISTRAL_API_KEY)
    
    # Простой вывод прогресса
    async def show_progress(msg: str):
        print(f"  → {msg}")
    
    try:
        # Запускаем рассуждение
        dialogue, solution = await engine.reason(question, show_progress)
        
        # Выводим результат
        print("\n" + "="*50)
        print("✅ РЕШЕНИЕ НАЙДЕНО!")
        print("="*50)
        print(f"\n📝 {solution.solution}")
        print("\n📋 Шаги реализации:")
        for i, step in enumerate(solution.steps, 1):
            print(f"   {i}. {step}")
        
        # Спрашиваем, хочет ли пользователь увидеть полный диалог
        show_dialogue = input("\n\nПоказать полный диалог агентов? (y/n): ")
        if show_dialogue.lower() == 'y':
            print("\n" + "="*50)
            print("ДИАЛОГ АГЕНТОВ")
            print("="*50)
            for entry in dialogue:
                print(f"\n🤖 {entry['agent']}:")
                print(f"   {entry['message']}")
                
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        print("Проверьте ваш MISTRAL_API_KEY и подключение к интернету")


if __name__ == "__main__":
    print("\n🔧 Quick Start - Система рассуждений с ИИ")
    asyncio.run(quick_demo()) 