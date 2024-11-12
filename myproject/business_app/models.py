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


class Order(models.Model):
    """
    Модель заказа.
    Связана с моделями пользователя, продукта, комплексного заказа (OrderItem).
    Определяет параметры заказа, статус заказа и дату создания.
    """

    # objects = None
    objects = None
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_CONFIRMED, 'Подтвержден'),
        (STATUS_DELIVERED, 'Передан курьеру'),
        (STATUS_CANCELED, 'Отменен'),
        (STATUS_COMPLETED, 'Завершен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')  # type: User
    items = models.ManyToManyField('Product', through='OrderItem', related_name='orders')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    comment = models.TextField(blank=True, null=True)
    telegram_key = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    status_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.pk} by {self.user.username}"

    def update_total_amount(self):
        """Обновляет общую сумму заказа, суммируя стоимость всех элементов."""
        self.total_amount = sum(
            item.quantity * item.product.price  # Убедитесь, что у вас есть доступ к product и его цене
            for item in OrderItem.objects.filter(order=self)
        )
        self.save()


class OrderItem(models.Model):
    """
    Модель для связи продукта и заказа.
    В заказе может быть несколько продуктов и несколько единиц продукта в заказе.
    Связывание происходит через внешние ключи.
    """
    objects = None
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')  # type: Order
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='order_items')  # type: Product
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ {self.price} each"

    def save(self, *args, **kwargs):
        """Переопределяем метод save для автоматического обновления общей суммы заказа."""
        super().save(*args, **kwargs)
        self.order.update_total_amount()
