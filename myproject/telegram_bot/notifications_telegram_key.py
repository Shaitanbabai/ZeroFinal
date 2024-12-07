import logging
import os
import requests

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def send_telegram_message(chat_id, text, reply_markup=None):
    try:
        data = {
            "chat_id": chat_id,
            "text": text
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        logging.debug(f"Sending data to Telegram: {data}")
        res = requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json=data)
        logging.debug(f"Telegram response: {res.json()}")
        res.raise_for_status()
        logging.info(f"Message sent to {chat_id}: {text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to {chat_id}: {e}")



#
#
# def register_notifications(main_router: Router):
#     main_router.include_router(router)