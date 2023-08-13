import sqlite3
import telebot
from telebot import types

API_TOKEN = 'TOKEN'
bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')
con = sqlite3.connect('main.db', check_same_thread=False)
admins_id = [1142412436]
last_date = ''
now_fb = False

@bot.message_handler(commands=['start', 'help', 'menu'])
def send_welcome(message):
    cur = con.cursor()
    cur.execute(f'SELECT name FROM users WHERE tg_id = {message.from_user.id}')
    if len(cur.fetchall()) == 0:
        bot.send_message(message.from_user.id, "Начата регистрация, введи своё имя")
        bot.register_next_step_handler(message, reg_enter_name)
    else:
        cur.execute(f'SELECT queue FROM users WHERE tg_id = {message.from_user.id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if cur.fetchall()[0][0] == 0:
            btn1 = types.KeyboardButton("Записаться")
            markup.add(btn1)
            bot.send_message(message.from_user.id, "\u274C Ты <b>не записан</b> в очередь\nЗаписаться можно прямо сейчас",
                             reply_markup=markup)
        else:
            btn1 = types.KeyboardButton("Удалить запись")
            markup.add(btn1)
            bot.send_message(message.from_user.id,
                             "\u2705 Ты <b>записан</b> в очередь\nУдалить запись можно прямо сейчас",
                             reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Записаться")
def start_sign_up(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Да, записать")
    btn2 = types.KeyboardButton("Нет, вернуться")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "Подтверждаешь?", reply_markup=markup)
    bot.register_next_step_handler(message, confirm_sign_up)


def confirm_sign_up(message):
    refresh_queue()
    cur = con.cursor()
    cur.execute(f'SELECT MAX(queue) FROM users')
    cur_queue = cur.fetchall()[0][0] + 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if message.text == "Да, записать":
        cur.execute(f'UPDATE users SET queue = {cur_queue} WHERE tg_id = {message.from_user.id}')
        con.commit()
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id,
                         f"\u2705 Успех! Сейчас твой номер - <b>{cur_queue}</b>\nНапиши /menu для возврата",
                         reply_markup=markup)
    else:
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id, f"Отменено\nНапиши /menu для возврата", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Удалить запись")
def start_delete_sign_up(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Да, удалить запись")
    btn2 = types.KeyboardButton("Нет, вернуться")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "Подтверждаешь?", reply_markup=markup)
    bot.register_next_step_handler(message, confirm_delete_sign_up)


def confirm_delete_sign_up(message):
    cur = con.cursor()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if message.text == "Да, удалить запись":
        cur.execute(f'UPDATE users SET queue = 0 WHERE tg_id = {message.from_user.id}')
        con.commit()
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id, f"\u274C Успех!\nНапиши /menu для возврата", reply_markup=markup)
    else:
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id, f"Отменено\nНапиши /menu для возврата", reply_markup=markup)


def reg_enter_name(message):
    cur = con.cursor()
    cur.execute(f'SELECT id FROM users WHERE name = "{message.text}"')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if len(cur.fetchall()) == 0:
        bot.send_message(message.from_user.id, "Извини, это имя неправильное, попробуй другое")
        bot.register_next_step_handler(message, reg_enter_name)
    else:
        cur.execute(f'SELECT tg_id FROM users WHERE name = "{message.text}";')
        if cur.fetchall()[0][0] == 0:
            cur.execute(f'UPDATE users SET tg_id = {message.from_user.id} WHERE name = "{message.text}"')
            con.commit()
            btn1 = types.KeyboardButton("/menu")
            markup.add(btn1)
            bot.send_message(message.from_user.id, f"Добро пожаловать! Регистрация завершена\nНапиши /menu для возврата", reply_markup=markup)
        else:
            bot.send_message(message.from_user.id, "Извини, это имя уже кем-то используется, попробуй другое")
            bot.register_next_step_handler(message, reg_enter_name)


def refresh_queue():
    cur = con.cursor()
    cur.execute('SELECT tg_id FROM users WHERE queue <> 0 GROUP BY queue;')
    a = []
    for i in cur.fetchall():
        a.append(i[0])
    k = 1
    for i in a:
        cur.execute(f'UPDATE users SET queue = {k} WHERE tg_id = {i};')
        k += 1
    con.commit()


def make_queue_list():
    cur = con.cursor()
    a = []
    cur.execute('SELECT tg_id, name FROM users WHERE queue <> 0 GROUP BY queue;')
    k = 1
    for i in cur.fetchall():
        a.append([k, i[0], i[1]])
        k += 1
    return a


@bot.message_handler(commands=['adm'])
def admin_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if message.from_user.id in admins_id:
        btn1 = types.KeyboardButton("Все записанные")
        btn2 = types.KeyboardButton("Разослать список")
        btn3 = types.KeyboardButton("Начать опрос")
        btn7 = types.KeyboardButton("/menu")
        btn4 = types.KeyboardButton("Изменить статусы")
        btn5 = types.KeyboardButton("Остановить опрос")
        btn6 = types.KeyboardButton("Общее сообщение")
        btn8 = types.KeyboardButton("Добавить пользователя")
        btn9 = types.KeyboardButton("Set time")
        markup.add(btn1, btn3, btn4, btn2, btn5, btn8, btn7, btn6)
        bot.send_message(message.from_user.id, "Добро пожаловать в админ-панель!\nВыбери раздел", reply_markup=markup)
    else:
        bot.send_message(message.from_user.id, "К сожалению, у тебя нет доступа к админ-панели")


@bot.message_handler(func=lambda message: message.text == "Все записанные" and message.from_user.id in admins_id)
def see_queue_list(message):
    s = 'Это все записанные в очередь:\n'
    for i in make_queue_list():
        s += f'\n{str(i[0])}. {i[2]}'
    bot.send_message(message.from_user.id, s)


@bot.message_handler(func=lambda message: message.text == "Разослать список" and message.from_user.id in admins_id)
def send_queue_list(message):
    a = make_queue_list()
    for j in a:
        s = "Очередь на занятие:\n<i>Ты выделен жирным шрифтом</i>\n"
        for i in a:
            if i[1] == j[1]:
                s += f'<b>\n{str(i[0])}. {i[2]}</b>'
            else:
                s += f'\n{str(i[0])}. {i[2]}'
        if j[1] != 0:
            bot.send_message(j[1], s)


@bot.message_handler(func=lambda message: message.text == "Добавить пользователя" and message.from_user.id in admins_id)
def add_new_user_1(message):
    bot.send_message(message.from_user.id, "Напиши имя нового пользователя (для отмены напиши 'cancel')")
    bot.register_next_step_handler(message, add_new_user_2)


def add_new_user_2(message):
    cur = con.cursor()
    if message.text != 'cancel':
        cur.execute(f'INSERT INTO users (name) VALUES ("{message.text}");')
        con.commit()
        bot.send_message(message.from_user.id, f"Пользователь '{message.text}' добавлен. Напиши /adm для возврата")
    else:
        bot.send_message(message.from_user.id, f"Отменено. Напиши /adm для возврата")


@bot.message_handler(func=lambda message: message.text == "Изменить статусы" and message.from_user.id in admins_id)
def edit_user_status_1(message):
    bot.send_message(message.from_user.id, "Напиши имя пользователя, статус которого нужно поменять (для отмены напиши 'cancel')")
    bot.register_next_step_handler(message, edit_user_status_2)


def edit_user_status_2(message):
    cur = con.cursor()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if message.text != 'cancel':
        cur.execute(f'SELECT id FROM users WHERE name = "{message.text}";')
        if cur.fetchall() is not None:
            cur.execute(f'UPDATE users SET editing = 1 WHERE name = "{message.text}";')
            con.commit()
            cur.execute(f'SELECT queue FROM users WHERE name = "{message.text}"')
            t = cur.fetchall()[0][0]
            if t == 0:
                btn1 = types.KeyboardButton("Да, записать")
                btn2 = types.KeyboardButton("Нет, вернуться")
                markup.add(btn1, btn2)
                bot.send_message(message.from_user.id, "Пользователь не записан, ты хочешь записать его?",
                                 reply_markup=markup)
                bot.register_next_step_handler(message, edit_user_status_3)
            else:
                btn1 = types.KeyboardButton("Да, удалить запись")
                btn2 = types.KeyboardButton("Нет, вернуться")
                markup.add(btn1, btn2)
                bot.send_message(message.from_user.id,
                                 f"Пользователь записан и имеет номер - {str(t)}. Ты хочешь удалить его запись?",
                                 reply_markup=markup)
                bot.register_next_step_handler(message, edit_user_status_3)
        else:
            bot.send_message(message.from_user.id,
                             "Неправильное имя, попробуй другое или напиши 'cancel' для отмены")
            bot.register_next_step_handler(message, edit_user_status_1)
    else:
        bot.send_message(message.from_user.id, f"Отменено. Напиши /adm для возврата")


def edit_user_status_3(message):
    cur = con.cursor()
    if message.text == 'Да, удалить запись':
        cur.execute('SELECT tg_id FROM users WHERE editing = 1')
        bot.send_message(cur.fetchall()[0][0], "\u26A0 Твоя запись была удалена администратором")
        cur.execute('UPDATE users SET queue = 0 WHERE editing = 1;')
        cur.execute('UPDATE users SET editing = 0 WHERE editing = 1;')
        bot.send_message(message.from_user.id, f"Успех. Напиши /adm для возврата")
    elif message.text == 'Да, записать':
        cur.execute(f'SELECT MAX(queue) FROM users')
        cur_queue = cur.fetchall()[0][0] + 1
        cur.execute(f'UPDATE users SET queue = {cur_queue} WHERE editing = 1')
        cur.execute('UPDATE users SET editing = 0 WHERE editing = 1;')
        bot.send_message(message.from_user.id, f"Успех. Теперь пользователь имеет номер - {cur_queue}. Напиши /adm для возврата")
        cur.execute('SELECT tg_id FROM users WHERE editing = 1')
        bot.send_message(cur.fetchall()[0][0], f"\u26A0 Ты был записан в очередь администратором. Сейчас твой номер - {cur_queue}")
    else:
        cur.execute('UPDATE users SET editing = 0 WHERE editing = 1;')
        bot.send_message(message.from_user.id, f"Отменено. Напиши /adm для возврата")
    con.commit()


@bot.message_handler(func=lambda message: message.text == "Общее сообщение" and message.from_user.id in admins_id)
def message_to_all_1(message):
    bot.send_message(message.from_user.id, "Напиши сообщение для всех пользователей (для отмены напиши 'cancel')")
    bot.register_next_step_handler(message, message_to_all_2)


def message_to_all_2(message):
    cur = con.cursor()
    if message.text != 'cancel':
        cur.execute(f'SELECT tg_id FROM users WHERE tg_id <> 0;')
        for i in cur.fetchall():
            bot.send_message(i[0], f'Сообщение от администратра:\n\n{message.text}')
        bot.send_message(message.from_user.id, 
                         f"Успех. Все пользователи получили сообщение: '{message.text}'.\nНапиши /adm для возврата")
    else:
        bot.send_message(message.from_user.id, f"Отменено. Напиши /adm для возврата")


@bot.message_handler(func=lambda message: message.text == "Начать опрос" and message.from_user.id in admins_id)
def start_collect_feedback_1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Да, начать")
    btn2 = types.KeyboardButton("Нет, вернуться")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "Ты хочешь начать опрос?", reply_markup=markup)
    bot.register_next_step_handler(message, start_collect_feedback_2)


def start_collect_feedback_2(message):
    if message.text == 'Да, начать':
        bot.send_message(message.from_user.id, f"Напиши дату последнего занятия")
        bot.register_next_step_handler(message, start_collect_feedback_3)
    else:
        bot.send_message(message.from_user.id, f"Отменено. Напиши /adm для возврата")


def start_collect_feedback_3(message):
    global last_date, now_fb
    if not now_fb:
        cur = con.cursor()
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Да, я выступил на занятии", callback_data='fb_yes')
        btn2 = types.InlineKeyboardButton("Нет, я НЕ выступил на занятии", callback_data='fb_no')
        markup.add(btn1, btn2)
        last_date = message.text
        cur.execute('SELECT tg_id FROM users WHERE queue <> 0;')
        for i in cur.fetchall():
            bot.send_message(i[0], f"Ты выступал на занятии {last_date}?", reply_markup=markup)
            cur.execute(f'UPDATE users SET feedback = 1 WHERE tg_id = {i[0]};')
        bot.send_message(message.from_user.id, f"Успех. Все записанные пользователи получили опрос'\nНапиши /adm для возврата")
        now_fb = True
        con.commit()
    else:
        bot.send_message(message.from_user.id, f"Опрос уже начат!\n<b>Опрос по занятию в {last_date}</b>\nНапиши /adm для возврата")


@bot.message_handler(func=lambda message: message.text == "Остановить опрос" and message.from_user.id in admins_id)
def stop_collect_feedback_1(message):
    cur = con.cursor()
    cur.execute('SELECT tg_id, name, feedback FROM users WHERE (feedback = 2) OR (feedback = 3) OR (feedback = 1);')
    s = 'Текущие результаты опроса:\n'
    for i in cur.fetchall():
        if i[2] == 2:
            s += f'\n{i[1]} \u2705'
        elif i[2] == 3:
            s += f'\n{i[1]} \u274C'
        elif i[2] == 1:
            s += f'\n{i[1]} \u2753'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Да, остановить")
    btn2 = types.KeyboardButton("Нет, вернуться")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, f"{s}\n\nТы хочешь остановить опрос и удалить из очереди всех неответивших?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, stop_collect_feedback_2)

def stop_collect_feedback_2(message):
    if message.text == "Да, остановить":
        cur = con.cursor()
        cur.execute('SELECT tg_id FROM users WHERE feedback = 1;')
        for i in cur.fetchall():
            bot.send_message(i[0], "\u26A0 Ты был удалён из очереди из-за того, что не принял участие в опросе")
        cur.execute('UPDATE users SET queue = 0 WHERE feedback = 1;')
        cur.execute('UPDATE users SET feedback = 2 WHERE feedback = 1;')
        con.commit()
        bot.send_message(message.from_user.id, "Успех. Начинается процедура завершения опроса")
        auto_stop_collecting()
    else:
        bot.send_message(message.from_user.id, f"Отменено. Напиши /adm для возврата")


def auto_stop_collecting():
    global now_fb
    if now_fb:
        cur = con.cursor()
        cur.execute('SELECT tg_id FROM users WHERE feedback = 1')
        if len(cur.fetchall()) == 0:
            cur.execute('SELECT tg_id, name, feedback FROM users WHERE (feedback = 2) OR (feedback = 3);')
            s = 'Опрос завершён\nВот его результаты:\n'
            for i in cur.fetchall():
                if i[2] == 2:
                    s += f'\n{i[1]} \u2705'
                elif i[2] == 3:
                    s += f'\n{i[1]} \u274C'
            for i in admins_id:
                bot.send_message(i, s)
            cur.execute('UPDATE users SET feedback = 0 WHERE (feedback = 2) OR (feedback = 3);')
            con.commit()
            now_fb = False



@bot.callback_query_handler(func= lambda call: call.data == 'fb_yes' or call.data == 'fb_no')
def callbacks(call):
    global last_date, now_fb
    if now_fb:
        cur = con.cursor()
        if call.data == 'fb_no':
            bot.edit_message_text(f"Ты выступал на занятии {last_date}?\n\n\u274C Ты выбрал 'нет'. Место в очереди остается за тобой",
                                  chat_id=call.message.chat.id, message_id=call.message.message_id)
            cur.execute(f'UPDATE users SET feedback = 3 WHERE tg_id = {call.message.chat.id};')
            refresh_queue()
        elif call.data == 'fb_yes':
            bot.edit_message_text(
                f"Ты выступал на занятии {last_date}?\n\n\u2705 Ты выбрал 'да'. Для следующего выступления необходимо заново встать в очередь",
                chat_id=call.message.chat.id, message_id=call.message.message_id)
            cur.execute(f'UPDATE users SET feedback = 2 WHERE tg_id = {call.message.chat.id};')
            cur.execute(f'UPDATE users SET queue = 0 WHERE tg_id = {call.message.chat.id};')
        con.commit()
        auto_stop_collecting()
    else:
        bot.edit_message_text(
            f"Ты выступал на занятии {last_date}?\n\n\u26A0 Опрос завершён, ответы больше не принимаются!",
            chat_id=call.message.chat.id, message_id=call.message.message_id)

bot.polling(none_stop=True, interval=2)
