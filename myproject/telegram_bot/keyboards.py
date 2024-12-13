from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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


# def get_sales_report_reply_keyboard():
#     # Создаем список списков с кнопками - для смены типа клавиатуры надо изменить импорты функций get_sales_report
#     buttons = [
#         [KeyboardButton(text="Отчет за сегодня")],
#         [KeyboardButton(text="Отчет за 7 дней")],
#         [KeyboardButton(text="Отчет за месяц")],
#         [KeyboardButton(text="Настраиваемый отчет")]
#     ]
#
#     # Создаем клавиатуру с кнопками
#     keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
#     return keyboard

def get_sales_report_inline_keyboard():
    # Создаем инлайн-кнопки с callback_data
    buttons = [
        [InlineKeyboardButton(text="Отчет за сегодня", callback_data="report_today"),
         InlineKeyboardButton(text="Отчет за 7 дней", callback_data="report_7_days")],
        [InlineKeyboardButton(text="Отчет за месяц", callback_data="report_month"),
         InlineKeyboardButton(text="Настраиваемый отчет", callback_data="custom_report")]
    ]

    # Создаем инлайн-клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard