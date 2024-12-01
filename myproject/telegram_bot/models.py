from django.db import models


class TelegramUser(models.Model):
    objects = None
    chat_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    is_authenticated = models.BooleanField(default=False)

    # Добавьте дополнительные поля, если необходимо

    def __str__(self):
        return f"{self.username} ({self.chat_id})"
