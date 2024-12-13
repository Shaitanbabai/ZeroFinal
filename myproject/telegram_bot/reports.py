import logging
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
import pytz

# Настройка логирования
logger = logging.getLogger(__name__)

def fetch_order_data(start_date, end_date):
    from business_app.models import Order
    try:
        logger.info(f"Fetching order data from {start_date} to {end_date}")
        orders = Order.objects.filter(status_datetime__range=(start_date, end_date))
        data = []

        for order in orders:
            for item in order.items.all():
                data.append({
                    'order_id': order.id,
                    'product_id': item.id,
                    'total_amount': order.total_amount,
                    'user_id': order.user_id,
                    'status': order.status,
                    'status_datetime': order.status_datetime
                })

        logger.info(f"Fetched {len(data)} order items")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error fetching order data: {e}")
        raise

def process_order_data(df):
    try:
        logger.info("Processing order data")
        status_grouped = df.groupby('status').agg(
            order_count=pd.NamedAgg(column='order_id', aggfunc='size'),
            total_amount=pd.NamedAgg(column='total_amount', aggfunc='sum')
        ).reset_index()

        completed_df = df[df['status'] == 'completed']
        revenue_share = calculate_revenue_share(completed_df)

        logger.info("Order data processing completed")
        return status_grouped, revenue_share
    except Exception as e:
        logger.error(f"Error processing order data: {e}")
        raise

def calculate_revenue_share(df):
    from business_app.models import Product
    try:
        logger.info("Calculating revenue share")
        product_names = {product.id: product.name for product in Product.objects.filter(id__in=df['product_id'].unique())}
        revenue_share = df.groupby('product_id')['total_amount'].sum()
        revenue_share.index = revenue_share.index.map(product_names)
        logger.info("Revenue share calculation completed")
        return revenue_share
    except Exception as e:
        logger.error(f"Error calculating revenue share: {e}")
        raise

def generate_pie_chart(revenue_share):
    try:
        logger.info("Generating pie chart")
        fig, ax = plt.subplots()
        ax.pie(revenue_share, labels=revenue_share.index, autopct='%1.1f%%')
        ax.axis('equal')

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        logger.info("Pie chart generation completed")
        return buf
    except Exception as e:
        logger.error(f"Error generating pie chart: {e}")
        raise

def generate_report(df):
    try:
        logger.info("Generating report")
        status_grouped, revenue_share = process_order_data(df)

        text_report = "Отчет:\n"
        for _, row in status_grouped.iterrows():
            text_report += f"Статус: {row['status']}, Заказов: {row['order_count']}, Сумма: {row['total_amount']}\n"

        chart = generate_pie_chart(revenue_share)

        logger.info("Report generation completed")
        return text_report, chart
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise