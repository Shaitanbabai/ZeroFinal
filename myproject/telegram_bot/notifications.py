import logging
import asyncio

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group

from aiogram import Router, types

from business_app.models import Order
from models import TelegramUser
from telegram_bot.bot import bot, dp  # Импортируем инициализированные объекты

logging.basicConfig(level=logging.INFO)

# Используем уже инициализированные объекты bot и dp
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


""" Роутеры для информирования клиента """
@router.message(commands=['subscribe'])
async def subscribe(message: types.Message):
    """Обрабатывает команду /subscribe для подписки пользователя на уведомления."""
    chat_id = message.chat.id
    telegram_username = f"@{message.from_user.username}"

    try:
        orders = Order.objects.filter(telegram_key=telegram_username)
        if orders.exists():
            TelegramUser.objects.update_or_create(
                username=telegram_username,
                defaults={'chat_id': chat_id}
            )
            await message.reply("Вы подписались на уведомления о статусах ваших заказов.")
        else:
            await message.reply("Не найден заказ, связанный с вашим именем пользователя.")
    except Exception as e:
        logging.error(f"Error subscribing user {telegram_username}: {e}")
        await message.reply("Произошла ошибка при подписке.")


@receiver(post_save, sender=Order)
def notify_salesman_of_order_change(_sender, instance, created, **_kwargs):
    """Информирует продавцов о создании или изменении заказа."""
    message = f"Новый заказ создан: {instance.id}. Детали: {instance.details}" if created else f"Статус заказа {instance.id} изменился на {instance.status}."

    try:
        salesmen = TelegramUser.objects.filter(is_authenticated=True)
        for salesman in salesmen:
            asyncio.run(send_telegram_message(salesman.chat_id, message))
    except Exception as e:
        logging.error(f"Error notifying salesmen: {e}")


""" Роутеры для информирования продавца """


@router.message(commands=['login'])
async def login(message: types.Message):
    """Обрабатывает команду /login для авторизации пользователя."""
    try:
        _, username, password = message.text.split()
    except ValueError:
        await message.reply("Используйте формат: /login username password")
        return

    try:
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
    except Exception as e:
        logging.error(f"Error during login: {e}")
        await message.reply("Произошла ошибка во время авторизации.")


async def send_telegram_message(chat_id, message):
    """Отправляет сообщение в Telegram пользователю."""
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")


@receiver(post_save, sender=Order)
def notify_order_status_change(_sender, instance, created, **_kwargs):
    """Отправляет уведомления в Telegram о создании или изменении статуса заказа."""
    telegram_username = instance.telegram_key
    if telegram_username:
        message = "Ваш заказ создан. Подпишитесь для отслеживания статуса." if created else f"Статус вашего заказа изменился на {instance.status}."

        try:
            user = TelegramUser.objects.filter(username=telegram_username).first()
            if user:
                asyncio.run(send_telegram_message(user.chat_id, message))
        except Exception as e:
            logging.error(f"Error notifying user {telegram_username}: {e}")
