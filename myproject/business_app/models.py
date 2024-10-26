from django.db import models


# Create your models here.
class Product(models.Model):
    _meta = None
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("customer", "Покупатель"),
            ("salesman", "Продавец"),
        ]
