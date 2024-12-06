import logging
import os
from pathlib import Path
import requests

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group

from aiogram import Router, types
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from aiogram.filters import Command

from asgiref.sync import sync_to_async

from business_app.models import Order, User, Product, OrderItem
from telegram_bot.models import TelegramUser
from telegram_bot.bot import bot, dp  # Импортируем инициализированные объекты

from telegram_bot.keyboards import get_customer_keyboard


API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

logging.basicConfig(level=logging.INFO)

# Используем уже инициализированные объекты bot и dp
router = Router()


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

""" Роутеры для информирования продавца """

STATUS_CHOICES = {
    'pending': 'В ожидании',
    'confirmed': 'Подтвержден',
    'delivery': 'Доставка'
}


@router.message(Command("login"))
async def login(message: types.Message):
    logging.info(f"Received login command from {message.from_user.username}")

    try:
        _, email, password = message.text.split()
    except ValueError:
        await message.reply("Используйте формат: /login email password")
        return

    try:
        user = await sync_to_async(authenticate)(email=email, password=password)

        if user is not None:
            logging.info(f"User {email} authenticated successfully")
            is_salesman = await sync_to_async(
                lambda: Group.objects.get(name='salesman').user_set.filter(id=user.id).exists())()

            if is_salesman:
                await sync_to_async(TelegramUser.objects.update_or_create)(
                    username=f"@{message.from_user.username}",
                    defaults={'is_authenticated': True, 'chat_id': message.chat.id}
                )
                auth_result = ("Вы успешно авторизовались, коллега. "

                               "Если Вы всё еще видите свое сообщение с логином и паролем - "
                               "удалите самостоятельно иначе вас заберет Пятниццо!"
                               "\n\nА теперь посмотрим на фронт работ и отчеты об успехах.")
                # Отправляем сообщение только для продавцов
                await message.reply(auth_result)
                await send_current_orders(message.chat.id)
                # Удаляем сообщение пользователя
                try:
                    await message.delete()
                except Exception as e:
                    logging.error(f"Failed to delete message: {e}")
                return  # Завершаем выполнение функции, чтобы не отправлять следующее сообщение
            else:
                auth_result = ("Вы не являетесь работником магазина. "
                               "Вы можете выбрать команду /subscribe для отслеживания заказов "
                               "или авторизоваться на веб-сайте магазина.")
        else:
            auth_result = "Неправильный логин или пароль. Вы точно работник магазина? Если нет, сделайте заказ на сайте"

    except Exception as e:
        logging.error(f"Error during login: {e}")
        auth_result = "Произошла ошибка во время авторизации. Пожалуйста, попробуйте позже."

    # Отправляем сообщение для всех остальных случаев
    await message.reply(auth_result + "\nНо если Вы хотите нас хакнуть, то мы не только букеты, но и венки умеем")

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")


async def send_current_orders(chat_id):
    logging.info(f"Функция send_current_orders вызвана с chat_id: {chat_id}")

    try:
        current_orders = await sync_to_async(
            lambda: list(
                Order.objects.filter(
                    status__in=[
                        Order.STATUS_PENDING,
                        Order.STATUS_CONFIRMED,
                        Order.STATUS_DELIVERY
                    ]
                ).prefetch_related('orderitem_set__product')
            )
        )()

        logging.info("Запрос к базе данных выполнен")

        if current_orders:
            logging.info("Текущие заказы найдены")

            def process_orders():
                messages = []
                items_with_images = []

                for order in current_orders:
                    order_items = order.orderitem_set.all()
                    items_str = ', '.join(
                        [f"{item.product.name} - {item.quantity} шт." for item in order_items]
                    )
                    message = (f"Заказ ID: {order.id}\n"
                               f"Статус: {STATUS_CHOICES.get(order.status, order.status)}\n"
                               f"Адрес: {order.address}\n"
                               f"Сумма: {order.total_amount}\n"
                               f"Телефон: {order.phone}\n"
                               f"Комментарий: {order.comment or 'Нет'}\n"
                               f"Дата статуса: {order.status_datetime}\n"
                               f"Товары: {items_str}")
                    messages.append(message)

                    for item in order_items:
                        items_with_images.append((order.id, item.product.image.path))

                return messages, items_with_images

            order_messages, items_with_images = await sync_to_async(process_orders)()

            for message in order_messages:
                await bot.send_message(chat_id, message, parse_mode=ParseMode.HTML)

            for order_id, image_path in items_with_images:
                full_image_path = Path(settings.MEDIA_ROOT) / image_path
                photo = FSInputFile(full_image_path)
                await bot.send_photo(chat_id=chat_id, photo=photo, caption=f"Изображение для заказа ID: {order_id}")

        else:
            logging.info("Нет текущих заказов")
            await bot.send_message(chat_id, "Нет текущих заказов.")

        logging.info("Сообщение отправлено")
    except Exception as e:
        logging.error(f"Ошибка при выполнении send_current_orders: {e}")


""" Роутер для подписки на уведомления """


@router.message(Command("subscribe"))
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


""" Роутеры для рассылки уведомлений """


# @receiver(post_save, sender=Order)
# def notify_salesman_of_order_change(_sender, instance, created, **_kwargs):
#     """Информирует продавцов о создании или изменении заказа."""
#     message = f"Новый заказ создан: {instance.id}. Детали: {instance.details}" if created else f"Статус заказа {instance.id} изменился на {instance.status}."
#
#     try:
#         salesmen = TelegramUser.objects.filter(is_authenticated=True)
#         for salesman in salesmen:
#             async_to_sync(send_telegram_message)(salesman.chat_id, message)
#     except Exception as e:
#         logging.error(f"Error notifying salesmen: {e}")


def send_telegram_message(chat_id, text, reply_markup=None):
    try:
        data = {
            "chat_id": chat_id,
            "text": text
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        res = requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json=data)
        print(f"{res.json()=}")
        res.raise_for_status()
        logging.info(f"Message sent to {chat_id}: {text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to {chat_id}: {e}")

@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    telegram_username = instance.telegram_key
    logging.debug(f"Telegram username: {telegram_username}")
    if telegram_username:
        try:
            user = TelegramUser.objects.filter(username=telegram_username).first()
            logging.debug(f"User found: {user}")
            if user:
                logging.debug(f"Order created: {created}, Order status: {instance.status}")
                if created:
                    message = "Ваш заказ создан. Подпишитесь для отслеживания статуса."
                    reply_markup = get_customer_keyboard()
                else:
                    if instance.status == "completed":
                        message = f"Ваш заказ с ID {instance.id} завершен."
                    else:
                        message = f"Статус вашего заказа с ID {instance.id} изменился на {instance.status}."
                    reply_markup = None

                send_telegram_message(user.chat_id, message, reply_markup)
            else:
                logging.warning(f"No Telegram user found for username {telegram_username}")
        except Exception as e:
            logging.error(f"Error notifying user {telegram_username}: {e}")


def register_notifications(main_router: Router):
    main_router.include_router(router)
