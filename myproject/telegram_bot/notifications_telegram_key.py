import logging
import os
import requests

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def send_telegram_message(chat_id: int | str, text: str, reply_markup: dict | None = None) -> requests.Response:
    data = {"chat_id": chat_id, "text": text}  # Используем chat_id в данных, отправляемых в Telegram API
    if reply_markup:
        data["reply_markup"] = reply_markup
    logging.debug(f"Sending data to Telegram: {data}")
    res = requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json=data)
    print(f"{res.content=}")
    return res

# def register_notifications(main_router: Router):
#     main_router.include_router(router)