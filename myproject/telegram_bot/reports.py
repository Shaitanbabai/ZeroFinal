import logging
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from business_app.models import Order, Product
from datetime import datetime, timedelta
import pytz


logger = logging.getLogger(__name__)

def fetch_order_data(start_date, end_date):
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

def generate_report(start_date, end_date):
    logger.info(f"Generating report from {start_date} to {end_date}")
    df = fetch_order_data(start_date, end_date)

    status_grouped = df.groupby('status').agg(
        order_count=pd.NamedAgg(column='order_id', aggfunc='size'),
        total_amount=pd.NamedAgg(column='total_amount', aggfunc='sum')
    ).reset_index()

    completed_df = df[df['status'] == 'completed']
    revenue_share = calculate_revenue_share(completed_df)

    text_report = f"Отчет с {start_date.date()} по {end_date.date()}:\n"
    for _, row in status_grouped.iterrows():
        text_report += f"Статус: {row['status']}, Заказов: {row['order_count']}, Сумма: {row['total_amount']}\n"

    chart = generate_pie_chart(revenue_share)

    logger.info("Report generation completed")
    return text_report, chart

def calculate_revenue_share(df):
    logger.info("Calculating revenue share")
    product_names = {product.id: product.name for product in Product.objects.filter(id__in=df['product_id'].unique())}
    revenue_share = df.groupby('product_id')['total_amount'].sum()
    revenue_share.index = revenue_share.index.map(product_names)
    logger.info("Revenue share calculation completed")
    return revenue_share

def generate_pie_chart(revenue_share):
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