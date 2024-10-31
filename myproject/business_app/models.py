from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='myproject/media/')

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("customer", "Покупатель"),
            ("salesman", "Продавец"),
        ]


class Order(models.Model):
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PAID = 'paid'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_CONFIRMED, 'Подтвержден'),
        (STATUS_PAID, 'Оплачен'),
        (STATUS_DELIVERED, 'Передан курьеру'),
        (STATUS_CANCELLED, 'Отменен'),
        (STATUS_COMPLETED, 'Завершен'),
    ]

    user:User = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    comment = models.TextField(blank=True, null=True)
    telegram_key = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    status_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.pk} by {self.user.username}"