import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Токен бота из .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
