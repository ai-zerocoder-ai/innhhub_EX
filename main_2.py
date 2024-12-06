import telebot
from config import TELEGRAM_BOT_TOKEN, CHAT_ID
import requests
import xml.etree.ElementTree as ET
import schedule
import time
from threading import Thread
from datetime import datetime
import pytz

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ID группы Telegram, в которую бот будет отправлять сообщения
GROUP_CHAT_ID = CHAT_ID

def get_exchange_rates():
    """Получение курсов валют от ЦБ РФ"""
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    response = requests.get(url)
    if response.status_code == 200:
        tree = ET.fromstring(response.content)
        rates = {}
        for currency in tree.findall('Valute'):
            char_code = currency.find('CharCode').text
            value = currency.find('Value').text
            name = currency.find('Name').text
            nominal = currency.find('Nominal').text
            if char_code in ['USD', 'CNY', 'EUR']:
                rates[char_code] = {
                    'name': name,
                    'nominal': int(nominal),
                    'value': float(value.replace(',', '.'))
                }
        return rates
    else:
        return None

def get_bitcoin_rate():
    """Получение курса биткойна через CoinGecko"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "rub"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('bitcoin', {}).get('rub', None)
    else:
        return None

def generate_rate_message():
    """Генерация сообщения с курсами валют и биткойна"""
    response = "Курсы валют и биткойна:\n"

    # Курсы валют
    rates = get_exchange_rates()
    if rates:
        for code, data in rates.items():
            response += f"{data['name']} ({code}): {data['nominal']} = {data['value']} руб.\n"
    else:
        response += "Не удалось получить курсы валют.\n"

    # Курс биткойна
    bitcoin_rate = get_bitcoin_rate()
    if bitcoin_rate:
        response += f"\nКурс биткойна: 1 BTC = {bitcoin_rate} руб."
    else:
        response += "\nНе удалось получить курс биткойна."

    return response

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Ответ на команды /start и /help"""
    bot.reply_to(message, "Добро пожаловать! Используйте команды:\n"
                          "/rate — получить курсы валют (USD, CNY, EUR) и биткойна.")

@bot.message_handler(commands=['rate'])
def send_all_rates(message):
    """Ответ на команду /rate"""
    response = generate_rate_message()
    bot.reply_to(message, response)

def send_daily_rates():
    """Ежедневная отправка курсов в группу Telegram"""
    response = generate_rate_message()
    bot.send_message(GROUP_CHAT_ID, response)

def schedule_daily_task():
    """Планирование ежедневной задачи"""
    # Устанавливаем московское время
    moscow_timezone = pytz.timezone("Europe/Moscow")

    # Планируем задачу на 9:00 утра по Москве
    schedule.every().day.at("09:00").do(send_daily_rates)

    while True:
        # Учет текущего времени с учетом временной зоны
        now = datetime.now(moscow_timezone)
        schedule.run_pending()
        time.sleep(1)

# Запуск планировщика в отдельном потоке
def start_scheduler():
    scheduler_thread = Thread(target=schedule_daily_task)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Запуск бота
if __name__ == "__main__":
    start_scheduler()
    bot.polling(none_stop=True)
