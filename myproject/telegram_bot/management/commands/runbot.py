from django.core.management.base import BaseCommand, CommandError
import asyncio
from telegram_bot.bot import main

class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **kwargs):
        self.stdout.write('Запуск Telegram бота...')
        try:
            asyncio.run(main())
        except Exception as e:
            raise CommandError(f'Ошибка при запуске бота: {e}')