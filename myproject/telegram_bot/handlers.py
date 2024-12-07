import logging
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from telegram_bot.reports import generate_report

# Настройка логирования
logger = logging.getLogger(__name__)

# Создание роутера для обработки сообщений и событий
report_router = Router()


""" Роутреы обработки отчетов о продажах """

class ReportStates(StatesGroup):
    """Класс состояний для выбора периода отчета."""
    start_date = State()
    end_date = State()

@report_router.callback_query(F.data == 'report_date_range')
async def report_date_range_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Обрабатывает начало выбора диапазона дат для отчета.

    Args:
        callback_query (types.CallbackQuery): Объект callback запроса.
        state (FSMContext): Контекст конечного автомата состояний.
    """
    try:
        await callback_query.message.answer(
            "Выберите начальную дату:",
            reply_markup=await SimpleCalendar().start_calendar()
        )
        await state.set_state(ReportStates.start_date)
        logger.info("Начало выбора даты для отчета")
    except Exception as e:
        logger.error(f"Ошибка в report_date_range_handler: {e}")
        await callback_query.message.answer("Произошла ошибка при выборе начальной даты. Попробуйте снова.")


@report_router.callback_query(SimpleCalendarCallback.filter())
async def process_start_date(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    current_state = await state.get_state()

    if current_state == ReportStates.start_date:
        """Обрабатывает выбор начальной даты."""
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
        """Обрабатывает выбор конечной даты и генерацию отчета."""
        try:
            selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
            if selected:
                data = await state.get_data()
                start_date = data['start_date']
                end_date = date
                await state.clear()

                # Генерация отчета
                text_report, chart = generate_report(start_date, end_date)

                # Отправка текстового отчета пользователю
                await callback_query.message.answer(text_report)

                # Отправка диаграммы пользователю
                await callback_query.message.answer_photo(photo=chart)

        except Exception as e:
            logger.error(f"Ошибка в process_end_date: {e}")
            await callback_query.message.answer("Произошла ошибка при выборе конечной даты. Попробуйте снова.")


# Функция для регистрации всех обработчиков
def register_handlers(main_router: Router):
    main_router.include_router(report_router)