from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def convert_to_dict(inline_keyboard_markup):
    """ Конвертация aiogram InlineKeyboardMarkup в словарь, совместимый с Telegram API. """
    return {
        "inline_keyboard": [
            [{"text": button.text, "callback_data": button.callback_data} for button in row]
            for row in inline_keyboard_markup.inline_keyboard
        ]
    }

def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Я - работник", callback_data="salesman"),
            InlineKeyboardButton(text="Я - покупатель", callback_data="customer")
        ]
    ])
    return keyboard

def get_customer_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подписаться на уведомления о движении заказа", callback_data="subscribe")
        ]
    ])
    return keyboard

def get_salesman_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Авторизоваться", callback_data="login")
        ]
    ])
    return keyboard


def get_sales_report_reply_keyboard():
    # Создаем список списков с кнопками
    buttons = [
        [KeyboardButton("Отчет за сегодня")],
        [KeyboardButton("Отчет за 7 дней")],
        [KeyboardButton("Отчет за месяц")],
        [KeyboardButton("Настраиваемый отчет")]
    ]

    # Создаем клавиатуру с кнопками
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

# def get_reports_keyboard():
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     today_report_button = InlineKeyboardButton(text="Отчет за сегодня", callback_data="report_today")
#     week_report_button = InlineKeyboardButton(text="Отчет за 7 дней", callback_data="report_week")
#     month_report_button = InlineKeyboardButton(text="Отчет за месяц", callback_data="report_month")
#     keyboard.add(today_report_button, week_report_button, month_report_button)
#     return keyboard