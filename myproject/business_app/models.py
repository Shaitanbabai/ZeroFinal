import logging

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from telegram_bot.keyboards import get_customer_keyboard
from telegram_bot.models import TelegramUser
# from telegram_bot.notifications import send_telegram_message

from django.utils import timezone

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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


class Order(models.Model):
    DoesNotExist = None
    objects = None
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DELIVERY = 'delivery'
    STATUS_CANCELED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_DELIVERY, 'Delivery'),
        (STATUS_CANCELED, 'Canceled'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField(Product, through=OrderItem, related_name='orders')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    phone = models.CharField(max_length=12)
    address = models.TextField(max_length=120)
    comment = models.TextField(max_length=120, blank=True, null=True)
    telegram_key = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    status_datetime = models.DateTimeField(auto_now_add=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def change_status(self, new_status):
#         self.status = new_status
#         self.status_datetime = timezone.now()
#         self.save()
#         OrderStatusHistory.objects.create(order=self, status=new_status, status_datetime=self.status_datetime)
#
# class OrderStatusHistory(models.Model):
#     order = models.ForeignKey('Order', related_name='status_history', on_delete=models.CASCADE)
#     status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
#     status_datetime = models.DateTimeField(default=timezone.now)
#
#     def __str__(self):
#         return f"{self.order.id} - {self.status} at {self.status_datetime}"


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


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    # вложенные импорты не вызовут ошибку цикрулярного импорта,
    # так как код внутри функций не читается интерпретатором
    # при изначальном выполнении модуля
    from telegram_bot.models import TelegramUser
    print("Signal received")
    logging.debug("Signal received")
    telegram_username = instance.telegram_key
    logging.debug(f"Searching for Telegram user with username: {telegram_username}")
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



