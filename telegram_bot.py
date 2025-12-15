import os
import requests
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверьте файл .env")

API_URL = os.getenv("API_URL", "http://web:8000/api/message")

bot = TeleBot(BOT_TOKEN)


@bot.message_handler(content_types=["text"])
def handle_message(message):
    user_text = message.text

    try:
        response = requests.post(
            API_URL,
            json={"message": user_text},
            timeout=5
        )
        response.raise_for_status()

        bot_reply = response.json().get(
            "response",
            "Не удалось получить ответ от сервера"
        )

    except requests.exceptions.RequestException:
        bot_reply = "Сервер временно недоступен"

    bot.send_message(message.chat.id, bot_reply)


print("Telegram-бот запущен")
bot.infinity_polling(skip_pending=True)