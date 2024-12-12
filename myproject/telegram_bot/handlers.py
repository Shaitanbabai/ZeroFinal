import logging
import datetime
from datetime import timedelta
from aiogram import types, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from telegram_bot.reports import generate_report
from telegram_bot.keyboards import get_sales_report_reply_keyboard

# Настройка логирования
logger = logging.getLogger(__name__)

# Создание роутера для обработки сообщений и событий
report_router = Router()


class ReportStates(StatesGroup):
    start_date = State()
    end_date = State()

class ReportCallbackData(CallbackData, prefix="report"):
    action: str

@report_router.callback_query(lambda c: c.data.startswith("report_"))
async def process_report_callback(callback_query: types.CallbackQuery, state: FSMContext):
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
        logger.info("Начало выбора даты для отчета")
        return

    if start_date:
        text_report, chart = generate_report(start_date, end_date)
        await callback_query.message.answer(text_report)
        await callback_query.message.answer_photo(photo=chart)

    await callback_query.answer()

@report_router.callback_query(SimpleCalendarCallback.filter())
async def process_start_date(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    current_state = await state.get_state()

    if current_state == ReportStates.start_date:
        try:
            selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
            if selected:
                await state.update_data(start_date=date)
                await callback_query.message.answer(
                    "Выберите конечную дату:",
                    reply_markup=await SimpleCalendar().start_calendar()
                )
                await state.set_state(ReportStates.end_date)
                logger.info(f"Начальная дата выбрана: {date}")
        except Exception as e:
            logger.error(f"Ошибка в process_start_date: {e}")
            await callback_query.message.answer("Произошла ошибка при выборе начальной даты. Попробуйте снова.")

@report_router.callback_query(SimpleCalendarCallback.filter())
async def process_end_date(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    current_state = await state.get_state()

    if current_state == ReportStates.end_date:
        try:
            selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
            if selected:
                data = await state.get_data()
                start_date = data['start_date']
                end_date = date
                await state.clear()

                text_report, chart = generate_report(start_date, end_date)

                await callback_query.message.answer(text_report)
                await callback_query.message.answer_photo(photo=chart)

        except Exception as e:
            logger.error(f"Ошибка в process_end_date: {e}")
            await callback_query.message.answer("Произошла ошибка при выборе конечной даты. Попробуйте снова.")


@report_router.message(Command("show_reports"))  # команда вызова отчетов
async def show_reports(message: types.Message):
    logging.info("Команда /show_reports получена")
    keyboard = get_sales_report_reply_keyboard()
    await message.answer("Выберите отчет:", reply_markup=keyboard)

def register_handlers(main_router: Router):
    main_router.include_router(report_router)