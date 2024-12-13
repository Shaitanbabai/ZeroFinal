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


# Определение класса состояний для машины состояний
class ReportStates(StatesGroup):
    start_date = State()  # Состояние для выбора начальной даты
    end_date = State()    # Состояние для выбора конечной даты

# Определение класса для обработки callback данных, связанных с отчетами
class ReportCallbackData(CallbackData, prefix="report"):
    action: str  # Действие, связанное с отчетом

# Обработчик callback-запросов, начинающихся с "report_"
@report_router.callback_query(lambda c: c.data.startswith("report_"))
async def process_report_callback(callback_query: CallbackQuery, state: FSMContext):
    try:
        # Получаем данные из callback-запроса
        callback_data = callback_query.data
        start_date = None  # Начальная дата отчета (по умолчанию None)
        end_date = datetime.datetime.now()  # Конечная дата отчета (текущая дата и время)

        # Определяем начальную дату в зависимости от выбранного действия
        if callback_data == "report_today":
            # Если отчет за сегодня, устанавливаем начало дня
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif callback_data == "report_week":
            # Если отчет за неделю, вычитаем 7 дней от текущей даты
            start_date = end_date - datetime.timedelta(days=7)
        elif callback_data == "report_month":
            # Если отчет за месяц, вычитаем 30 дней от текущей даты
            start_date = end_date - datetime.timedelta(days=30)
        elif callback_data == "report_custom":
            # Если пользователь выбрал пользовательский диапазон, запрашиваем начальную дату
            await callback_query.message.answer(
                "Выберите начальную дату:",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            await state.set_state(ReportStates.start_date)  # Устанавливаем состояние выбора начальной даты
            return

        # Если начальная дата определена
        if start_date:
            # Логируем информацию о диапазоне дат
            logger.info(f"Fetching data from {start_date} to {end_date}")
            # Асинхронно получаем данные заказов за указанный период
            df = await sync_to_async(fetch_order_data)(start_date, end_date)
            if df.empty:
                # Если данных нет, отправляем сообщение пользователю
                await callback_query.message.answer("Нет данных для отчета за указанный период.")
            else:
                # Генерируем текстовый отчет и диаграмму
                text_report, chart = await generate_report(df)
                # Отправляем текстовый отчет пользователю
                await callback_query.message.answer(text_report)

                if chart:
                    # Если диаграмма создана, отправляем ее как фото
                    photo = BufferedInputFile(chart.getvalue(), filename='pie_chart.png')
                    await callback_query.message.answer_photo(photo=photo)


    except Exception as e:
        # Логируем и отправляем сообщение об ошибке в случае исключения
        logger.exception("An unexpected error occurred: %s", e)
        await callback_query.message.answer("Произошла ошибка при обработке запроса отчета.")

    finally:
        # Отправляем ответ на callback-запрос
        await callback_query.answer()


@report_router.callback_query(SimpleCalendarCallback.filter())
async def process_start_date(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    try:
        # Получение текущего состояния
        current_state = await state.get_state()

        if current_state == ReportStates.start_date:
            # Обработка выбора начальной даты
            selected, selected_date = await SimpleCalendar().process_selection(callback_query, callback_data)
            if selected:
                # Обновление данных состояния с выбранной датой
                await state.update_data(start_date=selected_date)
                # Запрос выбора конечной даты
                await callback_query.message.answer("Выберите конечную дату:",
                                                    reply_markup=await SimpleCalendar().start_calendar())
                # Установка состояния для выбора конечной даты
                await state.set_state(ReportStates.end_date)
            await callback_query.answer()

    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка при обработке начальной даты: {e}")
        await callback_query.message.answer("Произошла ошибка при обработке начальной даты. Попробуйте снова.")

@report_router.callback_query(SimpleCalendarCallback.filter())
async def process_end_date(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    try:
        # Получение текущего состояния
        current_state = await state.get_state()

        if current_state == ReportStates.end_date:
            # Обработка выбора конечной даты
            selected, selected_date = await SimpleCalendar().process_selection(callback_query, callback_data)
            if selected:
                # Получение данных из состояния
                data = await state.get_data()
                start_date = data.get("start_date")
                end_date = selected_date

                # Проверка на корректность выбранных дат
                if end_date < start_date:
                    await callback_query.message.answer("Конечная дата не может быть раньше начальной. Попробуйте снова.")
                    await callback_query.answer()
                    return

                # Очистка состояния
                await state.clear()

                # Генерация и отправка отчета
                text_report, chart = await generate_report(start_date, end_date)
                await callback_query.message.answer(text_report)

                # Отправка графика, если он есть
                if chart:
                    photo = BufferedInputFile(chart.getvalue(), filename='pie_chart.png')
                    await callback_query.message.answer_photo(photo=photo)

            await callback_query.answer()
    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка при обработке конечной даты: {e}")
        await callback_query.message.answer("Произошла ошибка при обработке конечной даты. Попробуйте снова.")


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