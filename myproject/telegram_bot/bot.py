import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from dotenv import load_dotenv


# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение токена из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Включение логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Обработка команды /start
@dp.message(commands=['start'])
async def send_welcome(message: Message):
    await message.reply("Добро пожаловать! Я ваш помощник в интернет-магазине.")


# Обработка команды /help
@dp.message(commands=['help'])
async def send_help(message: Message):
    await message.reply("Список доступных команд:\n/start - Начать работу с ботом\n/help - Получить помощь")


# Основной запуск бота
async def main():
    # Здесь можно подключать middleware и другие настройки
    # Например, логирование или базы данных

    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())