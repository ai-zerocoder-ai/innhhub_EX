import telebot
from config import TELEGRAM_BOT_TOKEN
import requests
import xml.etree.ElementTree as ET

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Ответ на команды /start и /help"""
    bot.reply_to(message, "Добро пожаловать! Используйте команды:\n"
                          "/rate — получить курсы валют (USD, CNY, EUR) и биткойна.")

@bot.message_handler(commands=['rate'])
def send_all_rates(message):
    """Ответ на команду /rate"""
    response = "Курсы валют и биткойна:\n"

    # Получаем курсы валют
    rates = get_exchange_rates()
    if rates:
        for code, data in rates.items():
            response += f"{data['name']} ({code}): {data['nominal']} = {data['value']} руб.\n"
    else:
        response += "Не удалось получить курсы валют.\n"

    # Получаем курс биткойна
    bitcoin_rate = get_bitcoin_rate()
    if bitcoin_rate:
        response += f"\nКурс биткойна: 1 BTC = {bitcoin_rate} руб."
    else:
        response += "\nНе удалось получить курс биткойна."

    # Отправляем результат
    bot.reply_to(message, response)

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
