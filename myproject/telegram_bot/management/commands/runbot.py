import logging
import asyncio
from django.core.management.base import BaseCommand, CommandError
from telegram_bot.bot import main

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Установите нужный уровень логирования

# Создаем обработчик для вывода логов в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Создаем форматтер и добавляем его в обработчик
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(console_handler)

class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **kwargs):
        logger.info('Запуск Telegram бота...')
        try:
            asyncio.run(main())
        except Exception as e:
            logger.error('Ошибка при запуске бота: %s', e, exc_info=True)
            raise CommandError(f'Ошибка при запуске бота: {e}')