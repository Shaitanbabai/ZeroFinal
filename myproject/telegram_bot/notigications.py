import asyncio
from django.db.models.signals import post_save
from django.dispatch import receiver
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand
from business_app.models import Order
from .utils import get_telegram_bot_token
from .models import TelegramUser

# Создаем экземпляр бота
bot = Bot(token=get_telegram_bot_token(), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


# Функция для отправки сообщения в Telegram
async def send_telegram_message(chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message)


# Обработчик сигнала для уведомления об изменении статуса заказа
@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    telegram_username = instance.telegram_key
    if telegram_username:
        if created:
            message = f"Ваш заказ {instance.id} создан. Подпишитесь для отслеживания статуса."
        else:
            message = f"Статус вашего заказа {instance.id} изменился на {instance.status}."

        user = TelegramUser.objects.filter(username=telegram_username).first()
        if user:
            asyncio.run(send_telegram_message(user.chat_id, message))


# Обработчик команды /subscribe
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    chat_id = message.chat.id
    telegram_username = message.from_user.username
    args = message.get_args().split()

    if len(args) != 2:
        await message.reply(
            "Пожалуйста, укажите имя пользователя и ID заказа после команды /subscribe. Пример: /subscribe @username 12345")
        return

    provided_telegram_username, order_id = args

    # Проверяем, что provided_telegram_username совпадает с telegram_username в заказе
    order = Order.objects.filter(order_id=order_id, telegram_key=provided_telegram_username).first()

    if order:
        if order.telegram_key == f"@{telegram_username}":
            TelegramUser.objects.update_or_create(
                username=telegram_username,
                defaults={'chat_id': chat_id}
            )
            await message.reply(f"Вы подписались на уведомления по заказу {order_id}.")
        else:
            await message.reply("Вы не имеете права подписаться на уведомления для этого заказа.")
    else:
        await message.reply("Заказ не найден или указан неверный username.")


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/subscribe", description="Подписаться на уведомления по заказу"),
    ]
    await bot.set_my_commands(commands)


async def main():
    await set_commands(bot)
    # Запуск поллинга
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
