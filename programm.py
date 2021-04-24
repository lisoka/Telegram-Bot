import telebot
from telebot import types
import requests
import config
import random
import sqlite3

TOKEN = config.token
API_KEY = config.api
bot = telebot.TeleBot(TOKEN)

value = ''
flag = True


class Database:
    def __init__(self, user_name):
        global flag
        self.user_name = user_name
        self.con = sqlite3.connect('users.db')
        self.cur = self.con.cursor()
        if flag is True:
            print(9)
            self.write()
            flag = False

    def read(self):
        result = self.cur.execute(f'''SELECT favorites FROM users WHERE user_name = ?''', (self.user_name,)).fetchall()
        for elem in result:
            return elem[0]

    def write_1(self, link):
        if str(self.read()) is not None:
            text = str(self.read()) + f'\n{link}' + '\n'
        else:
            text = link + '\n'
        self.cur.execute(f"UPDATE users SET favorites = ? WHERE user_name = ?", (text, self.user_name,))
        self.con.commit()

    def write(self):
        try:
            self.cur.execute('INSERT INTO users(user_name, favorites) VALUES(?, ?)', (self.user_name, ''))
            self.con.commit()
        except:
            pass

    def close(self):
        self.con.close()


@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if 'спасибо' in message.text.lower():
        bot.send_message(message.from_user.id, "Всегда пожалуйста!")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, config.text_2)
    elif message.text == "/best":
        try:
            result = Database(message.from_user.username).read()
            bot.send_message(message.from_user.id, result)
        except:
            bot.send_message(message.from_user.id, config.text_4)
    elif message.text == "/start":
        bot.send_message(message.from_user.id, config.text_1)
    else:
        try:
            start(message)
        except:
            bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


def start(message):
    global value
    value = '%20'.join(message.text.split())
    get_result(message, value)


def get_result(message, value):
    response = requests.get(f"https://api.edamam.com/search?q={value}&app_id={config.id}&app_key={config.api}")
    result = response.json()
    number = random.randint(0, len(result['hits']) - 1)
    link = result['hits'][number]['recipe']['shareAs']
    label = result['hits'][number]['recipe']['label']
    image = result['hits'][number]['recipe']['image']
    ing = result['hits'][number]['recipe']['ingredientLines']
    bot.send_message(message.from_user.id, link)
    bot.send_message(message.from_user.id, label)
    bot.send_message(message.from_user.id, image)
    bot.send_message(message.from_user.id, ', '.join(ing))

    bot.send_message(message.from_user.id, 'Приятного аппетита!')

    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
    keyboard.add(key_no)
    question = 'Добавить блюдо в понравившиеся?'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_worker(call):
        if call.data == "yes":
            bot.send_message(call.message.chat.id, config.text_3)
            Database(message.from_user.username).write_1(link)

        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Печально. Попробуйте еще раз.')


bot.polling(none_stop=True, interval=0)
