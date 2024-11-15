from django.db import models
from django.contrib.auth.models import User

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
        (STATUS_CANCELED, 'Cancelled'),
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
