from django.db import models


class TelegramUser(models.Model):
    id = models.IntegerField(unique=True, primary_key=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    is_authenticated = models.BooleanField(default=False)

    # Добавьте дополнительные поля, если необходимо

    def __str__(self):
        return f"{self.username} ({self.id})"
