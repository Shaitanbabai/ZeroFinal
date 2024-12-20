import logging
import os

from django.db import models
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from django_lifecycle import LifecycleModel, hook, AFTER_CREATE, AFTER_UPDATE

from telegram_bot.keyboards import get_customer_keyboard
from telegram_bot.models import TelegramUser
from telegram_bot.keyboards import convert_to_dict
from telegram_bot.notifications_telegram_key import send_telegram_message


API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщения
    handlers=[
        logging.StreamHandler()          # Логирование в терминал
    ]
)

# Create your models here.
class Product(models.Model):
    """
    Модель продукта. Связана с моделью пользователя. Передает параметры карточки продукта.
    """
    DoesNotExist = None
    objects = None
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='myproject/media/', default='no_photo.jpg')
    is_active = models.BooleanField(default=True)  # Поле для статуса активности

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("customer", "Покупатель"),
            ("salesman", "Продавец"),
        ]


class OrderItem(models.Model):
    objects = None
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Order(LifecycleModel):
    objects = None
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DELIVERY = 'delivery'
    STATUS_CANCELED = 'canceled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_DELIVERY, 'Delivery'),
        (STATUS_CANCELED, 'Canceled'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField('Product', through='OrderItem', related_name='orders')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    phone = models.CharField(max_length=12)
    address = models.TextField(max_length=120)
    comment = models.TextField(max_length=120, blank=True, null=True)
    telegram_key = models.CharField(max_length=100, blank=True, null=True)
    telegram_id = models.CharField(max_length=50, blank=True, null=True)
    telegram_user = models.ForeignKey('telegram_bot.TelegramUser', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    status_datetime = models.DateTimeField(auto_now_add=True)

    @hook(AFTER_CREATE)
    def notify_creation(self, telegram_user=None):
        from telegram_bot.models import TelegramUser
        logging.debug(f"Attempting to notify user for Order ID: {self.id}")

        if self.status == 'confirmed':
            telegram_username = self.telegram_key
            if telegram_username:
                user = TelegramUser.objects.filter(username=telegram_username).first()
                if user:
                    logging.debug(f"Found Telegram user {user.username}")
                    message = f"Для вас есть заказ с ID {self.id} в статусе confirmed."
                    reply_markup = get_customer_keyboard()
                    reply_markup_dict = convert_to_dict(reply_markup)
                    send_telegram_message(chat_id=user.id, text=message, reply_markup=reply_markup_dict)
                else:
                    logging.warning(f"No Telegram user found for username {telegram_username}")
            else:
                logging.warning("Telegram username is not set for this order.")
        else:
            logging.debug("Order is not in 'confirmed' status, skipping notification.")

    @hook(AFTER_UPDATE, when='status', has_changed=True)
    def notify_status_change(self):
        from telegram_bot.models import TelegramUser
        logging.debug(f"Attempting to notify user for status change of Order ID: {self.id}")

        user = TelegramUser.objects.filter(username=self.telegram_key).first()
        if user:
            logging.debug(f"Found Telegram user {user.username}")
            message = f"Статус вашего заказа с ID {self.id} изменился на {self.status}."
            reply_markup = get_customer_keyboard()
            reply_markup_dict = convert_to_dict(reply_markup)
            send_telegram_message(chat_id=user.id, text=message, reply_markup=reply_markup_dict)
        else:
            logging.warning(f"No Telegram user found for username {self.telegram_key}")


class Review(models.Model):
    objects = None
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.IntegerField()
    content = models.TextField(max_length=240)
    rating = models.IntegerField()
    pub_date = models.DateTimeField(auto_now_add=True)
    # Один заказ --> Один отзыв --> Один ответ
    reply = models.OneToOneField('Reply', null=True, blank=True, on_delete=models.SET_NULL, related_name='review')

    def __str__(self):
        return f"Review by {self.user.username} for order {self.order_id}"

class Reply(models.Model):
    # review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')  # >1 ответа на отзыв
    content = models.TextField(max_length=240)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.review = None

    def __str__(self):
        return f"Reply to review {self.review.id}"


# @receiver(post_save, sender=Order)
# def notify_order_status_change(sender, instance, created, **kwargs):
#     logging.debug(f"Signal for Order: created={created}, instance={instance}")
#     from telegram_bot.models import TelegramUser
#
#     telegram_username = instance.telegram_key
#     logging.debug(f"Searching for Telegram user with username: {telegram_username}")
#
#     if telegram_username:
#         try:
#             user = TelegramUser.objects.filter(username=telegram_username).first()
#             logging.debug(f"User found: {user}")
#
#             if user:
#                 if created:
#                     # Если заказ создан, отправляем сообщение о создании
#                     message = f"Ваш заказ с ID {instance.id} создан и подтвержден."
#                     reply_markup = get_customer_keyboard()
#                 else:
#                     # Если заказ обновлен, проверяем статус
#                     if instance.status == "completed":
#                         message = f"Ваш заказ с ID {instance.id} завершен."
#                     else:
#                         message = f"Статус вашего заказа с ID {instance.id} изменился на {instance.status}."
#                     reply_markup = None
#
#                 send_telegram_message(user_id=user.id, text=message, reply_markup=reply_markup)
#             else:
#                 logging.warning(f"No Telegram user found for username {telegram_username}")
#         except Exception as e:
#             logging.error(f"Error notifying user {telegram_username}: {e}")



