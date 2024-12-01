import logging
import asyncio
import os

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group

from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import BotCommand

from myproject.business_app.models import Order
from .models import TelegramUser

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('TELEGRAM_API_TOKEN'), parse_mode='HTML')
dp = Dispatcher()
router = Router()
dp.include_router(router)

class SimpleLoggingMiddleware:
    """
    Простая middleware-функция для логирования событий.
    """
    async def __call__(self, handler, event, data):
        """
        Логирование событий.
        Args:
            handler: Обработчик события.
            event: Событие, которое необходимо обработать.
            data: Дополнительные данные события.
        """
        logging.info(f"Handling event: {event}")
        return await handler(event, data)

# Установка middleware для логгирования сообщений
dp.message.middleware(SimpleLoggingMiddleware())

async def send_telegram_message(chat_id, message):
    """Отправляет сообщение в Telegram пользователю.

        Args:
            chat_id (int): Уникальный идентификатор чата.
            message (str): Сообщение для отправки.
        """
    await bot.send_message(chat_id=chat_id, text=message)


""" Информер для пользователей о статусе конкретного заказа. """


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):  # noqa: F841
    """Отправляет уведомления в Telegram о создании или изменении статуса заказа.

        Args:
            sender: Отправитель сигнала.
            instance (Order): Экземпляр заказа.
            created (bool): Булевый флаг, указывающий, было ли создано новое значение.
        """
    telegram_username = instance.telegram_key
    if telegram_username:
        if created:
            message = f"Ваш заказ создан. Подпишитесь для отслеживания статуса."
        else:
            message = f"Статус вашего заказа изменился на {instance.status}."

        user = TelegramUser.objects.filter(username=telegram_username).first()
        if user:
            asyncio.run(send_telegram_message(user.chat_id, message))

@router.message(commands=['subscribe'])
async def subscribe(message: types.Message):
    """Обрабатывает команду /subscribe для подписки пользователя на уведомления.

        Args:
            message (types.Message): Сообщение от пользователя.
        """
    chat_id = message.chat.id
    telegram_username = f"@{message.from_user.username}"

    # Проверяем, есть ли заказы с таким telegram_key
    orders = Order.objects.filter(telegram_key=telegram_username)
    if orders.exists():
        # Создаем или обновляем запись в базе данных для пользователя Telegram
        TelegramUser.objects.update_or_create(
            username=telegram_username,
            defaults={'chat_id': chat_id}
        )
        await message.reply("Вы подписались на уведомления о статусах ваших заказов.")
    else:
        await message.reply("Не найден заказ, связанный с вашим именем пользователя.")


""" Информер для продавцов о создании и изменении заказов. """


@router.message(commands=['login'])
async def login(message: types.Message):
    # Пример команды: /login username password
    try:
        _, username, password = message.text.split()
    except ValueError:
        await message.reply("Используйте формат: /login username password")
        return

    user = authenticate(username=username, password=password)

    if user is not None:
        if Group.objects.get(name='salesman') in user.groups.all():
            TelegramUser.objects.update_or_create(
                username=f"@{message.from_user.username}",
                defaults={'is_authenticated': True, 'chat_id': message.chat.id}
            )
            await message.reply("Вы успешно авторизовались как salesman.")
        else:
            await message.reply("У вас нет доступа к функционалу salesman.")
    else:
        await message.reply("Неправильный логин или пароль.")


@receiver(post_save, sender=Order)
def notify_salesman_of_order_change(sender, instance, created, **kwargs):
    message = f"Новый заказ создан: {instance.id}. Детали: {instance.details}" if created else f"Статус заказа {instance.id} изменился на {instance.status}."

    # Получаем всех авторизованных пользователей salesman
    salesmen = TelegramUser.objects.filter(is_authenticated=True)

    for salesman in salesmen:
        asyncio.run(send_telegram_message(salesman.chat_id, message))


""" Базовые команды бота и управление командами. """


@router.message(commands=['start'])
async def start(message: types.Message):
    """Обработка команды /start."""
    welcome_text = (
        "Добро пожаловать в бот-информатор магазина FlowerLover! Вот список доступных команд:\n"
        "/start - Начать использование бота\n"
        "/help - Показать меню команд\n"
        "/login - Авторизация (только для продавцов)\n"
        "/subscribe - Подписаться на уведомления по заказу"
    )
    await message.reply(welcome_text)

@router.message(commands=['help'])
async def help_command(message: types.Message):
    """Обработка команды /help."""
    help_text = (
        "Список доступных команд:\n"
        "/start - Начать использование бота\n"
        "/help - Показать меню команд\n"
        "/login - Авторизация (только для продавцов)\n"
        "/subscribe - Подписаться на уведомления по заказу"
    )
    await message.reply(help_text)


async def set_commands(telegram_bot: Bot):
    """Устанавливает доступные команды для бота в Telegram.

    Args:
        telegram_bot (Bot): Экземпляр бота.
    """
    commands = [
        BotCommand(command="/start", description="Начать использование бота"),
        BotCommand(command="/help", description="Показать меню команд"),
        BotCommand(command="/login", description="Авторизация (формат: /login username password)"),
        BotCommand(command="/subscribe", description="Подписаться на уведомления по заказу"),
    ]
    await telegram_bot.set_my_commands(commands)


async def main():
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
