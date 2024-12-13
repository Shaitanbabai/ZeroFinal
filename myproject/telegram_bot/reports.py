import logging
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
import pytz

# Настройка логирования
logger = logging.getLogger(__name__)

# Функция для получения данных о заказах за указанный период
def fetch_order_data(start_date, end_date):
    from business_app.models import Order  # Импорт модели Order из приложения business_app
    try:
        # Логируем начало процесса получения данных о заказах
        logger.info(f"Fetching order data from {start_date} to {end_date}")
        # Фильтруем заказы по диапазону дат
        orders = Order.objects.filter(status_datetime__range=(start_date, end_date))
        data = []  # Создаем пустой список для хранения данных о заказах

        # Итерируемся по всем заказам
        for order in orders:
            # Итерируемся по всем позициям в заказе
            for item in order.items.all():
                # Добавляем данные о каждой позиции в список
                data.append({
                    'order_id': order.id,  # Идентификатор заказа
                    'product_id': item.id,  # Идентификатор продукта
                    'total_amount': order.total_amount,  # Общая сумма заказа
                    'user_id': order.user_id,  # Идентификатор пользователя
                    'status': order.status,  # Статус заказа
                    'status_datetime': order.status_datetime  # Дата и время статуса
                })

        # Логируем количество полученных позиций заказа
        logger.info(f"Fetched {len(data)} order items")
        # Возвращаем данные в виде DataFrame
        return pd.DataFrame(data)
    except Exception as e:
        # Логируем ошибку в случае исключения и повторно выбрасываем исключение
        logger.error(f"Error fetching order data: {e}")
        raise

# Функция для обработки данных о заказах
def process_order_data(df):
    try:
        # Логируем начало процесса обработки данных о заказах
        logger.info("Processing order data")
        # Группируем данные по статусу и вычисляем количество заказов и общую сумму по каждому статусу
        status_grouped = df.groupby('status').agg(
            order_count=pd.NamedAgg(column='order_id', aggfunc='size'),  # Количество заказов
            total_amount=pd.NamedAgg(column='total_amount', aggfunc='sum')  # Общая сумма
        ).reset_index()

        # Фильтруем данные по статусу "completed"
        completed_df = df[df['status'] == 'completed']
        # Вычисляем долю выручки
        revenue_share = calculate_revenue_share(completed_df)

        # Логируем завершение обработки данных
        logger.info("Order data processing completed")
        # Возвращаем сгруппированные данные и долю выручки
        return status_grouped, revenue_share
    except Exception as e:
        # Логируем ошибку в случае исключения и повторно выбрасываем исключение
        logger.error(f"Error processing order data: {e}")
        raise

# Определение функции для вычисления доли выручки
def calculate_revenue_share(df):
    from business_app.models import Product  # Импорт модели Product из приложения business_app
    try:
        # Логируем начало процесса вычисления доли выручки
        logger.info("Calculating revenue share")
        # Получаем имена продуктов на основе их ID
        product_names = {product.id: product.name for product in Product.objects.filter(id__in=df['product_id'].unique())}
        # Группируем данные по идентификаторам продуктов и суммируем выручку
        revenue_share = df.groupby('product_id')['total_amount'].sum()
        # Присваиваем именам продуктов соответствующие индексы
        revenue_share.index = revenue_share.index.map(product_names)
        # Логируем завершение расчета доли выручки
        logger.info("Revenue share calculation completed")
        # Возвращаем долю выручки
        return revenue_share
    except Exception as e:
        # Логируем ошибку в случае исключения и повторно выбрасываем исключение
        logger.error(f"Error calculating revenue share: {e}")
        raise

# Определение функции для генерации круговой диаграммы
def generate_pie_chart(revenue_share):
    try:
        # Логируем начало процесса генерации круговой диаграммы
        logger.info("Generating pie chart")
        # Создаем фигуру и ось для диаграммы
        fig, ax = plt.subplots()
        # Генерируем круговую диаграмму с процентами
        ax.pie(revenue_share, labels=revenue_share.index, autopct='%1.1f%%')
        # Устанавливаем оси равными для правильного отображения круга
        ax.axis('equal')

        buf = BytesIO()  # Создаем буфер для сохранения диаграммы
        plt.savefig(buf, format='png')  # Сохраняем диаграмму в буфер в формате PNG
        buf.seek(0)  # Перемещаем указатель на начало буфера
        plt.close(fig)  # Закрываем фигуру
        # Логируем завершение генерации диаграммы
        logger.info("Pie chart generation completed")
        # Возвращаем буфер с изображением диаграммы
        return buf
    except Exception as e:
        # Логируем ошибку в случае исключения и повторно выбрасываем исключение
        logger.error(f"Error generating pie chart: {e}")
        raise

# Определение функции для генерации отчета
def generate_report(df):
    try:
        # Проверяем, является ли DataFrame пустым
        if df.empty:
            # Логируем предупреждение о пустом DataFrame
            logger.warning("DataFrame is empty, no report to generate.")
            return "Нет данных для отчета за указанный период.", None

        # Обрабатываем данные о заказах и получаем сгруппированные данные и долю выручки
        status_grouped, revenue_share = process_order_data(df)

        text_report = "Отчет:\n"  # Инициализируем текст отчета
        # Итерируемся по строкам сгруппированных данных и добавляем информацию в текст отчета
        for _, row in status_grouped.iterrows():
            text_report += f"Статус: {row['status']}, Заказов: {row['order_count']}, Сумма: {row['total_amount']}\n"

        # Генерируем круговую диаграмму на основе доли выручки
        chart = generate_pie_chart(revenue_share)

        # Возвращаем текст отчета и изображение диаграммы
        return text_report, chart

    except KeyError as e:
        # Логируем ошибку KeyError и возвращаем сообщение об ошибке
        logger.error("KeyError encountered: %s", e)
        return "Ошибка при обработке данных: отсутствуют необходимые столбцы.", None

    except Exception as e:
        # Логируем неожиданные ошибки и возвращаем сообщение об ошибке
        logger.exception("An unexpected error occurred: %s", e)
        return "Произошла непредвиденная ошибка при генерации отчета.", None