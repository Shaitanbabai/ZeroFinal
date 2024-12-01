from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_customer_keyboard():
    """
    Возвращает клавиатуру для покупателя с кнопкой подписки на уведомления.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    subscribe_button = InlineKeyboardButton(text="Подписаться на уведомления о движении заказа", callback_data="subscribe")
    keyboard.add(subscribe_button)
    return keyboard

def get_salesman_start_keyboard():
    """
    Возвращает клавиатуру для неавторизованного продавца с командой /start.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    start_button = InlineKeyboardButton(text="Начать", callback_data="start")
    keyboard.add(start_button)
    return keyboard

def get_salesman_authorized_keyboard():
    """
    Возвращает клавиатуру для авторизованного продавца с командами /logout, /reports, /help.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    logout_button = InlineKeyboardButton(text="Выйти", callback_data="logout")
    reports_button = InlineKeyboardButton(text="Отчеты", callback_data="reports")
    help_button = InlineKeyboardButton(text="Помощь", callback_data="help")
    keyboard.add(logout_button, reports_button, help_button)
    return keyboard

def get_reports_keyboard():
    """
    Возвращает клавиатуру для выбора отчетов по продажам.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    today_report_button = InlineKeyboardButton(text="Отчет за сегодня", callback_data="report_today")
    week_report_button = InlineKeyboardButton(text="Отчет за 7 дней", callback_data="report_week")
    month_report_button = InlineKeyboardButton(text="Отчет за месяц", callback_data="report_month")
    keyboard.add(today_report_button, week_report_button, month_report_button)
    return keyboard