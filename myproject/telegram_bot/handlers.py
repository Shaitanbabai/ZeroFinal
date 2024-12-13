import logging
import datetime
from datetime import timedelta
from io import BytesIO
from aiogram import types, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import BufferedInputFile
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from asgiref.sync import sync_to_async
from telegram_bot.reports import generate_report as generate_report_sync
from telegram_bot.reports import fetch_order_data, calculate_revenue_share, generate_pie_chart
from telegram_bot.keyboards import get_sales_report_inline_keyboard

# Настройка логирования
logger = logging.getLogger(__name__)

# Обернем синхронную функцию в асинхронную
generate_report = sync_to_async(generate_report_sync, thread_sensitive=True)

# Создание роутера для обработки сообщений и событий
report_router = Router()


class ReportStates(StatesGroup):
    start_date = State()
    end_date = State()

class ReportCallbackData(CallbackData, prefix="report"):
    action: str


@report_router.callback_query(lambda c: c.data.startswith("report_"))
async def process_report_callback(callback_query: CallbackQuery, state: FSMContext):
    logging.info("Обработка callback data: %s", callback_query.data)
    try:
        callback_data = callback_query.data
        start_date = None
        end_date = datetime.datetime.now()

        if callback_data == "report_today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif callback_data == "report_week":
            start_date = end_date - timedelta(days=7)
        elif callback_data == "report_month":
            start_date = end_date - timedelta(days=30)
        elif callback_data == "report_custom":
            await callback_query.message.answer(
                "Выберите начальную дату:",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            await state.set_state(ReportStates.start_date)
            return

        if start_date:
            df = await sync_to_async(fetch_order_data)(start_date, end_date)
            text_report, chart = await generate_report(df)
            await callback_query.message.answer(text_report)

            if chart:
                # Создайте объект BufferedInputFile, передавая поток и имя файла
                photo = BufferedInputFile(chart.getvalue(), filename='pie_chart.png')
                await callback_query.message.answer_photo(photo=photo)

        await callback_query.answer()
    except TelegramAPIError as e:
        logging.error("Ошибка Telegram API: %s", e)
        await callback_query.message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")
    except Exception as e:
        logging.exception("Неизвестная ошибка: %s", e)
        await callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@report_router.callback_query(SimpleCalendarCallback.filter())
async def process_calendar_selection(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    logging.info("Обработка выбора календаря.")
    try:
        selected, selected_date = await SimpleCalendar().process_selection(callback_query, callback_data)
        current_state = await state.get_state()

        if not selected:
            await callback_query.answer()
            return

        if current_state == ReportStates.start_date:
            await state.update_data(start_date=selected_date)
            await callback_query.message.answer(
                "Выберите конечную дату:",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            await state.set_state(ReportStates.end_date)
        elif current_state == ReportStates.end_date:
            data = await state.get_data()
            start_date = data.get("start_date")
            end_date = selected_date

            if end_date < start_date:
                await callback_query.message.answer("Конечная дата не может быть раньше начальной. Попробуйте снова.")
                await callback_query.answer()
                return

            await state.clear()

            text_report, chart = await generate_report(start_date, end_date)
            await callback_query.message.answer(text_report)

            if chart:
                photo = BufferedInputFile(chart.getvalue(), filename='pie_chart.png')
                await callback_query.message.answer_photo(photo=photo)

        await callback_query.answer()
    except TelegramAPIError as e:
        logging.error("Ошибка Telegram API: %s", e)
        await callback_query.message.answer("Произошла ошибка при обработке выбора даты. Попробуйте позже.")
    except Exception as e:
        logging.exception("Неизвестная ошибка: %s", e)
        await callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@report_router.message(Command("show_reports"))  # команда вызова отчетов
async def show_reports(message: types.Message):
    logging.info("Команда /show_reports получена от пользователя: %s", message.from_user.id)
    try:
        keyboard = get_sales_report_inline_keyboard()
        await message.answer("Выберите отчет:", reply_markup=keyboard)
    except Exception as e:
        logging.exception("Ошибка при отображении отчетов: %s", e)
        await message.answer("Произошла ошибка при отображении отчетов. Попробуйте позже.")


def register_handlers(main_router: Router):
    main_router.include_router(report_router)