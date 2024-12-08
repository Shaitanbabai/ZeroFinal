import logging
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from aiogram.filters import Command
from aiogram import F

from asgiref.sync import sync_to_async

from business_app.models import Order
from telegram_bot.handlers import register_handlers
from telegram_bot.keyboards import (
    get_start_keyboard,
    get_salesman_keyboard,
    get_customer_keyboard,
    get_sales_report_keyboard
)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение токена из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Включение логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщения
    handlers=[
        logging.StreamHandler()          # Логирование в терминал
    ]
)

# Инициализация бота с использованием DefaultBotProperties
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
logging.info("Bot успешно инициализирован")

# Инициализация диспетчера
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
logging.info("Dispatcher успешно инициализирован")

# Создаем и добавляем главный роутер
main_router = Router()
dp.include_router(main_router)

# Регистрация обработчиков отчетов
register_handlers(main_router)  # Регистрация роутеров из handelrs.py

# Регистрация роутеров для уведомлений
from telegram_bot.notifications import register_notifications
from telegram_bot.notifications import login as perform_login
register_notifications(main_router)  # Регистрация роутеров из notifications.py

# Экспортируем необходимые объекты
__all__ = ['bot', 'dp', 'main_router']


""" Роутеры обработки базовых команд """


# Период активности сессии в минутах
SESSION_TIMEOUT = 60

user_sessions = {}

def is_session_active(user_id):
    session = user_sessions.get(user_id)
    if not session:
        return False
    last_activity = session.get('last_activity')
    if not last_activity:
        return False
    return (timezone.now() - last_activity) < timedelta(minutes=SESSION_TIMEOUT)

def update_session_activity(user_id):
    if user_id in user_sessions:
        user_sessions[user_id]['last_activity'] = timezone.now()

@main_router.message(Command(commands=['start']))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    if not is_session_active(user_id):
        user_sessions[user_id] = {
            'role': None,
            'subscribed': False,
            'last_activity': timezone.now()
        }
        await message.answer(
            "Выберите вашу роль:",
            reply_markup=get_start_keyboard()
        )
    else:
        await message.answer("Вы уже выбрали роль в текущей сессии.")


@main_router.callback_query(F.data == 'customer')
async def customer_callback(callback_query: types.CallbackQuery):
    logging.info("Обработчик customer_callback вызван")
    user_id = callback_query.from_user.id
    if not is_session_active(user_id):
        await callback_query.answer("Ваша сессия истекла. Пожалуйста, начните заново.")
        return

    # Форматируем username
    username = callback_query.from_user.username
    if username:
        username_with_at = f"@{username}"

        # Используем sync_to_async для выполнения синхронного запроса
        order_exists = await sync_to_async(Order.objects.filter(Q(telegram_key=username) | Q(telegram_key=username_with_at)).exists)()

        if order_exists:
            user_sessions[user_id]['role'] = 'customer'
            update_session_activity(user_id)
            await callback_query.message.edit_text(
                "Отправитель указал ваше имя в заказе. "
                "Вы можете подписаться на уведомления о заказе или просто игнорировать сообщение.",
                reply_markup=get_customer_keyboard()
            )
        else:
            await callback_query.answer("Заказы с вашим именем не найдены.")
    else:
        await callback_query.answer("Ваше имя пользователя отсутствует в Telegram.")

@main_router.callback_query(F.data == 'subscribe')
async def subscribe_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if not is_session_active(user_id):
        await callback_query.answer("Ваша сессия истекла. Пожалуйста, начните заново.")
        return

    # Обновляем статус подписки
    user_sessions[user_id]['subscribed'] = True
    update_session_activity(user_id)
    await callback_query.answer("Вы подписаны на уведомления о заказе.")

@main_router.callback_query(F.data == 'salesman')
async def salesman_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if not is_session_active(user_id):
        await callback_query.answer("Ваша сессия истекла. Пожалуйста, начните заново.")
        return
    user_sessions[user_id]['role'] = 'salesman'
    update_session_activity(user_id)
    await callback_query.message.edit_text("Для выполнения действий, пожалуйста, авторизуйтесь:", reply_markup=get_salesman_keyboard())

@main_router.message(Command(commands=['login']))
async def login_command(message: types.Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)

    if session and is_session_active(user_id) and session.get('role') == 'salesman' and not session.get('subscribed'):
        success = await perform_login(message)
        if success:
            session['subscribed'] = True
            update_session_activity(user_id)
    else:
        await message.answer("Вы не можете выполнить эту команду.")


# Обработчик нажатия кнопки 'login'
@main_router.callback_query(F.data == 'login')
async def login_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if not is_session_active(user_id):
        await callback_query.answer("Ваша сессия истекла. Пожалуйста, начните заново.")
        return

    session = user_sessions.get(user_id)

    if session and session.get('role') == 'salesman' and not session.get('subscribed'):
        update_session_activity(user_id)
        await callback_query.message.edit_text(
            "Для авторизации, пожалуйста, введите команду следующим образом:\n/login email password")
    else:
        await callback_query.answer("Вы не можете выполнить эту команду.")

# @main_router.callback_query(lambda c: c.data == 'subscribe')
# async def subscribe_callback(callback_query: types.CallbackQuery):
#     user_id = callback_query.from_user.id
#     if not is_session_active(user_id):
#         await callback_query.answer("Ваша сессия истекла. Пожалуйста, начните заново.")
#         return
#     user_sessions[user_id] = {'subscribed': True}
#     await callback_query.message.edit_text("Вы успешно подписаны на уведомления.")
#
# @main_router.callback_query(F.data == 'reports')
# async def reports_callback(callback_query: types.CallbackQuery):
#     user_id = callback_query.from_user.id
#     if not is_session_active(user_id):
#         await callback_query.answer("Ваша сессия истекла. Пожалуйста, начните заново.")
#         return
#     session = user_sessions.get(user_id)
#     if session.get('role') == 'salesman' and session.get('subscribed'):
#         update_session_activity(user_id)
#         await callback_query.message.edit_text("Выберите отчет:", reply_markup=get_sales_report_keyboard())
#     else:
#         await callback_query.answer("У вас нет прав для выполнения этой команды.")

async def main():
    # await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())