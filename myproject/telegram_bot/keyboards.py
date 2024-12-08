from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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



def get_sales_report_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Отчет за сегодня", callback_data="report_today"),
            InlineKeyboardButton(text="Отчет за 7 дней", callback_data="report_week")
        ],
        [
            InlineKeyboardButton(text="Отчет за месяц", callback_data="report_month"),
            InlineKeyboardButton(text="Настраиваемый отчет", callback_data="report_custom")
        ]
    ])
    return keyboard

# def get_reports_keyboard():
#     """
#     Возвращает клавиатуру для выбора отчетов по продажам.
#     """
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     today_report_button = InlineKeyboardButton(text="Отчет за сегодня", callback_data="report_today")
#     week_report_button = InlineKeyboardButton(text="Отчет за 7 дней", callback_data="report_week")
#     month_report_button = InlineKeyboardButton(text="Отчет за месяц", callback_data="report_month")
#     keyboard.add(today_report_button, week_report_button, month_report_button)
#     return keyboard