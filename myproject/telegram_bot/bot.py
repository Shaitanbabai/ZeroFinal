import logging
import os

from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv
from handlers import register_handlers

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение токена из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Включение логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создаем и добавляем главный роутер
main_router = Router()
dp.include_router(main_router)

# Регистрация обработчиков
register_handlers(main_router)

# Экспортируем необходимые объекты
__all__ = ['bot', 'dp', 'main_router']


# Обработка команды /start
@main_router.message(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = (
        "Добро пожаловать в бот-информатор магазина FlowerLover! Вот список доступных команд:\n"
        "/start - Начать использование бота\n"
        "/help - Показать меню команд\n"
        "/login - Авторизация (только для продавцов)\n"
        "/subscribe - Подписаться на уведомления по заказу"
    )
    await message.reply(welcome_text)

# Обработка команды /help
@main_router.message(commands=['help'])
async def send_help(message: types.Message):
    help_text = (
        "Список доступных команд:\n"
        "/start - Начать использование бота\n"
        "/help - Показать меню команд\n"
        "/login - Авторизация (только для продавцов)\n"
        "/subscribe - Подписаться на уведомления по заказу"
    )
    await message.reply(help_text)

async def set_commands(telegram_bot: Bot):
    """Устанавливает доступные команды для бота в Telegram."""
    commands = [
        BotCommand(command="/start", description="Начать использование бота"),
        BotCommand(command="/help", description="Показать меню команд"),
        BotCommand(command="/login", description="Авторизация (формат: /login username password)"),
        BotCommand(command="/subscribe", description="Подписаться на уведомления по заказу"),
        BotCommand(command="/reports", description="Запрос отчетов по продажам"),
    ]

    await telegram_bot.set_my_commands(commands)

async def main():
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())