import logging

def setup_logging(log_file='app.log', level=logging.INFO):
    """Настройка логирования с поддержкой вывода в файл и консоль."""
    # Создание логгера
    logger = logging.getLogger()
    logger.setLevel(level)

    # Форматирование
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Обработчик для файла
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_logger(name):
    return logging.getLogger(name)

def log_event(message):
    """Логирование события."""
    logger = get_logger(__name__)
    logger.info(message)

def log_error(message):
    """Логирование ошибки."""
    logger = get_logger(__name__)
    logger.error(message)

# Настроим логирование при импорте модуля
setup_logging(log_file='errors.log', level=logging.DEBUG)  # Указываем файл для логов ошибок и уровень

