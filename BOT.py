
import telebot
from telebot import types
from googletrans import Translator
import random
import os
import speech_recognition as sr
from pydub import AudioSegment

TOKEN = '8499454857:AAFyeW8FWeIV27Vrw9S9o6i0z6PrHKc0k84'
bot = telebot.TeleBot(TOKEN)
translator = Translator()

user_state = {}

popular_langs = {
    'ru': 'Русский 🇷🇺',
    'en': 'Английский 🇬🇧',
    'ky': 'Кыргызский 🇰🇬',
    'tr': 'Турецкий 🇹🇷',
    'fr': 'Французский 🇫🇷',
    'de': 'Немецкий 🇩🇪',
    'zh-cn': 'Китайский 🇨🇳',
    'ar': 'Арабский 🇸🇦'
}


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = {'from': None, 'to': None}

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔤 Переводчик", callback_data="go_translate"),
        types.InlineKeyboardButton("🎮 Игра: Камень/Ножницы/Бумага", callback_data="go_game")
    )

    bot.send_message(user_id,
    "👋 Привет! Я могу переводить текст (включая голосовые) и играть в 'Камень, ножницы, бумага'.\n\nВыбери действие:",
    reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['go_translate', 'go_game'])
def handle_menu_callback(call):
    if call.data == 'go_translate':
        choose_from_lang(call.message)
    elif call.data == 'go_game':
        rock_paper_scissors(call.message)


@bot.message_handler(commands=['translate'])
def choose_from_lang(message):
    user_id = message.chat.id
    user_state[user_id] = {'from': None, 'to': None}
    show_language_keyboard(user_id, mode='from')


def show_language_keyboard(user_id, mode):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for code, name in popular_langs.items():
        markup.add(types.KeyboardButton(f"{name} | {code}"))

    if mode == 'from':
        bot.send_message(user_id, "🌐 С какого языка перевести?", reply_markup=markup)
    else:
        bot.send_message(user_id, "➡️ На какой язык перевести?", reply_markup=markup)


@bot.message_handler(func=lambda m: " | " in m.text)
def handle_lang_choice(message):
    user_id = message.chat.id
    lang_code = message.text.split(" | ")[1]

    if not user_state.get(user_id):
        user_state[user_id] = {}

    if not user_state[user_id].get('from'):
        user_state[user_id]['from'] = lang_code
        show_language_keyboard(user_id, mode='to')
    elif not user_state[user_id].get('to'):
        user_state[user_id]['to'] = lang_code
        bot.send_message(user_id, "✍️ Теперь отправьте текст или голосовое сообщение для перевода:")


@bot.message_handler(
    func=lambda m: user_state.get(m.chat.id) and user_state[m.chat.id].get('from') and user_state[m.chat.id].get('to'))
def translate_text(message):
    user_id = message.chat.id
    src = user_state[user_id]['from']
    dest = user_state[user_id]['to']
    text = message.text.strip()

    try:
        translated = translator.translate(text, src=src, dest=dest)
        bot.send_message(user_id, f"📤 Перевод:\n\n{translated.text}")
    except Exception as e:
        print(e)
        bot.send_message(user_id, "❌ Ошибка при переводе.")

    user_state.pop(user_id, None)



@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.chat.id

    if not user_state.get(user_id) or not user_state[user_id].get('from') or not user_state[user_id].get('to'):
        bot.send_message(user_id, "❗ Сначала выберите языки с помощью команды /translate.")
        return

    try:
        file_info = bot.get_file(message.voice.file_id)
        file = bot.download_file(file_info.file_path)

        with open("voice.ogg", 'wb') as f:
            f.write(file)

        sound = AudioSegment.from_ogg("voice.ogg")
        sound.export("voice.wav", format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile("voice.wav") as source:
            audio_data = recognizer.record(source)
            lang_code = user_state[user_id]['from']

            text = recognizer.recognize_google(audio_data, language=lang_code)
            bot.send_message(user_id, f"🔊 Распознанный текст:\n{text}")

            translated = translator.translate(text, src=lang_code, dest=user_state[user_id]['to'])
            bot.send_message(user_id, f"📤 Перевод:\n{translated.text}")

    except sr.UnknownValueError:
        bot.send_message(user_id, "❌ Не удалось распознать речь.")
    except Exception as e:
        print(e)
        bot.send_message(user_id, "❌ Ошибка при обработке голосового сообщения.")
    finally:
        try:
            os.remove("voice.ogg")
            os.remove("voice.wav")
        except:
            pass

    user_state.pop(user_id, None)


@bot.message_handler(commands=['game'])
def rock_paper_scissors(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add('🪨 Камень', '✂️ Ножницы', '📄 Бумага')
    bot.send_message(message.chat.id, "Выбери: камень, ножницы или бумага", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in ['🪨 Камень', '✂️ Ножницы', '📄 Бумага'])
def handle_rps(message):
    user_choice = message.text
    options = ['🪨 Камень', '✂️ Ножницы', '📄 Бумага']
    bot_choice = random.choice(options)

    result = get_rps_result(user_choice, bot_choice)
    response = f"Ты выбрал: {user_choice}\nБот выбрал: {bot_choice}\n\n{result}"
    bot.send_message(message.chat.id, response)


def get_rps_result(user, bot):
    if user == bot:
        return "🔁 Ничья!"
    elif (user == '🪨 Камень' and bot == '✂️ Ножницы') or \
            (user == '✂️ Ножницы' and bot == '📄 Бумага') or \
            (user == '📄 Бумага' and bot == '🪨 Камень'):
        return "🎉 Ты победил!"
    else:
        return "😢 Ты проиграл."



bot.polling(none_stop=True)
