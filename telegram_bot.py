import os
import requests
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь .env")

if not API_URL:
    raise ValueError("API_URL не найден. Проверь .env")

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

        data = response.json()
        bot_reply = data.get(
            "response",
            "Сервер не вернул корректный ответ"
        )

    except requests.exceptions.Timeout:
        bot_reply = "Сервер долго отвечает, попробуйте позже"

    except requests.exceptions.ConnectionError:
        bot_reply = "Сервер недоступен"

    except requests.exceptions.HTTPError:
        bot_reply = "Ошибка обработки запроса на сервере"

    except requests.exceptions.RequestException:
        bot_reply = "Произошла ошибка при обращении к серверу"

    bot.send_message(message.chat.id, bot_reply)


print("Telegram-бот запущен")
bot.infinity_polling(skip_pending=True)
