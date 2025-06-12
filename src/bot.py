import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatAction
from reasoning_engine import ReasoningEngine
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение токенов из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not TELEGRAM_BOT_TOKEN or not MISTRAL_API_KEY:
    raise ValueError("Пожалуйста, установите TELEGRAM_BOT_TOKEN и MISTRAL_API_KEY в файле .env")

# Создание движка рассуждений
reasoning_engine = ReasoningEngine(MISTRAL_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    welcome_message = """👋 Привет! Я бот-решатель проблем с ИИ рассуждением.

🤖 Как я работаю:
1. Вы описываете проблему
2. Я анализирую её и определяю область
3. Мои агенты начинают рассуждать:
   - Аналитик определяет суть проблемы
   - Генератор гипотез предлагает подход
   - Решатель создает конкретное решение
   - Валидатор проверяет его качество
4. Процесс повторяется до нахождения хорошего решения

📝 Просто отправьте мне вашу проблему или вопрос!"""
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """📚 Доступные команды:

/start - Начать работу с ботом
/help - Показать эту справку
/status - Проверить статус бота

💡 Примеры вопросов:
- "Как улучшить производительность Python кода?"
- "Как начать здоровый образ жизни?"
- "Как организовать эффективную работу команды?"

Просто отправьте ваш вопрос, и я начну процесс рассуждения!"""
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /status"""
    status_text = "✅ Бот работает нормально!\n🤖 Все системы активны."
    await update.message.reply_text(status_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_question = update.message.text
    chat_id = update.message.chat_id
    
    # Отправляем индикатор набора текста
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Начальное сообщение
    start_message = await update.message.reply_text("🚀 Начинаю процесс рассуждения...")
    
    try:
        # Функция для отправки промежуточных обновлений
        async def send_progress(message: str):
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            # Продолжаем показывать индикатор набора
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Запускаем процесс рассуждения
        dialogue_history, solution = await reasoning_engine.reason(
            user_question,
            progress_callback=send_progress
        )
        
        # Отправляем полный диалог агентов
        dialogue_text = reasoning_engine.format_dialogue_for_telegram(dialogue_history)
        
        # Разбиваем на части, если сообщение слишком длинное
        MAX_MESSAGE_LENGTH = 4000
        if len(dialogue_text) > MAX_MESSAGE_LENGTH:
            # Отправляем по частям
            for i in range(0, len(dialogue_text), MAX_MESSAGE_LENGTH):
                part = dialogue_text[i:i + MAX_MESSAGE_LENGTH]
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=dialogue_text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Отправляем финальное решение
        final_message = f"""
🎯 *ФИНАЛЬНОЕ РЕШЕНИЕ:*

*Решение:* {solution.solution}

*Шаги реализации:*
"""
        for i, step in enumerate(solution.steps, 1):
            final_message += f"\n{i}. {step}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=final_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Удаляем начальное сообщение
        await start_message.delete()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        error_message = f"❌ Произошла ошибка при обработке вашего запроса: {str(e)}"
        await context.bot.send_message(
            chat_id=chat_id,
            text=error_message
        )
        await start_message.delete()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )


def main() -> None:
    """Основная функция запуска бота"""
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Регистрация обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Бот запускается...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main() 