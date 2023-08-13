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
        bot.send_message(message.from_user.id, "Start registration, enter your name")
        bot.register_next_step_handler(message, reg_enter_name)
    else:
        cur.execute(f'SELECT queue FROM users WHERE tg_id = {message.from_user.id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if cur.fetchall()[0][0] == 0:
            btn1 = types.KeyboardButton("Sign up")
            markup.add(btn1)
            bot.send_message(message.from_user.id, "\u274C You <b>don't</b> sign up to the queue\nYou can do it now",
                             reply_markup=markup)
        else:
            btn1 = types.KeyboardButton("Delete sign up")
            markup.add(btn1)
            bot.send_message(message.from_user.id,
                             "\u2705 You <b>are sign up</b> to the queue\nYou can delete this sign up now",
                             reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Sign up")
def start_sign_up(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Yes, sign up")
    btn2 = types.KeyboardButton("No, go back")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "Are you sure?", reply_markup=markup)
    bot.register_next_step_handler(message, confirm_sign_up)


def confirm_sign_up(message):
    refresh_queue()
    cur = con.cursor()
    cur.execute(f'SELECT MAX(queue) FROM users')
    cur_queue = cur.fetchall()[0][0] + 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if message.text == "Yes, sign up":
        cur.execute(f'UPDATE users SET queue = {cur_queue} WHERE tg_id = {message.from_user.id}')
        con.commit()
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id,
                         f"\u2705 Done! Now you have number - <b>{cur_queue}</b>\nUse /menu to return",
                         reply_markup=markup)
    else:
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id, f"Canceled\nUse /menu to return", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Delete sign up")
def start_delete_sign_up(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Yes, delete sign up")
    btn2 = types.KeyboardButton("No, go back")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "Are you sure?", reply_markup=markup)
    bot.register_next_step_handler(message, confirm_delete_sign_up)


def confirm_delete_sign_up(message):
    cur = con.cursor()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if message.text == "Yes, delete sign up":
        cur.execute(f'UPDATE users SET queue = 0 WHERE tg_id = {message.from_user.id}')
        con.commit()
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id, f"\u274C Done!\nUse /menu to return", reply_markup=markup)
    else:
        btn1 = types.KeyboardButton("/menu")
        markup.add(btn1)
        bot.send_message(message.from_user.id, f"Canceled\nUse /menu to return", reply_markup=markup)


def reg_enter_name(message):
    cur = con.cursor()
    cur.execute(f'SELECT id FROM users WHERE name = "{message.text}"')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if len(cur.fetchall()) == 0:
        bot.send_message(message.from_user.id, "Sorry, try another name")
        bot.register_next_step_handler(message, reg_enter_name)
    else:
        cur.execute(f'SELECT tg_id FROM users WHERE name = "{message.text}";')
        if cur.fetchall()[0][0] == 0:
            cur.execute(f'UPDATE users SET tg_id = {message.from_user.id} WHERE name = "{message.text}"')
            con.commit()
            btn1 = types.KeyboardButton("/menu")
            markup.add(btn1)
            bot.send_message(message.from_user.id, f"Welcome! Registration done\nUse /menu to return", reply_markup=markup)
        else:
            bot.send_message(message.from_user.id, "Sorry, this name is already used, try another")
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
        btn1 = types.KeyboardButton("See queue list")
        btn2 = types.KeyboardButton("Send queue list")
        btn3 = types.KeyboardButton("Start collecting feedbacks")
        btn7 = types.KeyboardButton("/menu")
        btn4 = types.KeyboardButton("Edit user status")
        btn5 = types.KeyboardButton("Stop collecting feedbacks")
        btn6 = types.KeyboardButton("Make message to all users")
        btn8 = types.KeyboardButton("Add new user")
        btn9 = types.KeyboardButton("Set time")
        markup.add(btn1, btn3, btn4, btn2, btn5, btn8, btn7, btn6)
        bot.send_message(message.from_user.id, "Welcome to admin menu\nChoose one option", reply_markup=markup)
    else:
        bot.send_message(message.from_user.id, "You don't have access to admin menu")


@bot.message_handler(func=lambda message: message.text == "See queue list" and message.from_user.id in admins_id)
def see_queue_list(message):
    s = 'Here is all users in queue:\n'
    for i in make_queue_list():
        s += f'\n{str(i[0])}. {i[2]}'
    bot.send_message(message.from_user.id, s)


@bot.message_handler(func=lambda message: message.text == "Send queue list" and message.from_user.id in admins_id)
def send_queue_list(message):
    a = make_queue_list()
    for j in a:
        s = "Here is today queue:\n<i>You are highlighted in bold</i>\n"
        for i in a:
            if i[1] == j[1]:
                s += f'<b>\n{str(i[0])}. {i[2]}</b>'
            else:
                s += f'\n{str(i[0])}. {i[2]}'
        if j[1] != 0:
            bot.send_message(j[1], s)


@bot.message_handler(func=lambda message: message.text == "Add new user" and message.from_user.id in admins_id)
def add_new_user_1(message):
    bot.send_message(message.from_user.id, "Enter name to new user (to cancel write 'cancel')")
    bot.register_next_step_handler(message, add_new_user_2)


def add_new_user_2(message):
    cur = con.cursor()
    if message.text != 'cancel':
        cur.execute(f'INSERT INTO users (name) VALUES ("{message.text}");')
        con.commit()
        bot.send_message(message.from_user.id, f"User '{message.text}' was added. Use /adm to return")
    else:
        bot.send_message(message.from_user.id, f"Canceled. Use /adm to return")


@bot.message_handler(func=lambda message: message.text == "Edit user status" and message.from_user.id in admins_id)
def edit_user_status_1(message):
    bot.send_message(message.from_user.id, "Enter name to change user's status (to cancel write 'cancel')")
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
                btn1 = types.KeyboardButton("Yes, make sign up")
                btn2 = types.KeyboardButton("No, go back")
                markup.add(btn1, btn2)
                bot.send_message(message.from_user.id, "User don't have sign up. Do you want to make sign up?",
                                 reply_markup=markup)
                bot.register_next_step_handler(message, edit_user_status_3)
            else:
                btn1 = types.KeyboardButton("Yes, delete sign up")
                btn2 = types.KeyboardButton("No, go back")
                markup.add(btn1, btn2)
                bot.send_message(message.from_user.id,
                                 f"User have sign up and he have number - {str(t)}. Do you want to delete sign up?",
                                 reply_markup=markup)
                bot.register_next_step_handler(message, edit_user_status_3)
        else:
            bot.send_message(message.from_user.id,
                             "Incorrect name, try another name or write 'cancel' to cancel the operation")
            bot.register_next_step_handler(message, edit_user_status_1)
    else:
        bot.send_message(message.from_user.id, f"Canceled. Use /adm to return")


def edit_user_status_3(message):
    cur = con.cursor()
    if message.text == 'Yes, delete sign up':
        cur.execute('UPDATE users SET queue = 0 WHERE editing = 1;')
        cur.execute('UPDATE users SET editing = 0 WHERE editing = 1;')
        bot.send_message(message.from_user.id, f"Done. Use /adm to return")
    elif message.text == 'Yes, make sign up':
        cur.execute(f'SELECT MAX(queue) FROM users')
        cur_queue = cur.fetchall()[0][0] + 1
        cur.execute(f'UPDATE users SET queue = {cur_queue} WHERE editing = 1')
        cur.execute('UPDATE users SET editing = 0 WHERE editing = 1;')
        bot.send_message(message.from_user.id, f"Done. Now user have number - {cur_queue}. Use /adm to return")
    else:
        cur.execute('UPDATE users SET editing = 0 WHERE editing = 1;')
        bot.send_message(message.from_user.id, f"Canceled. Use /adm to return")
    con.commit()


@bot.message_handler(func=lambda message: message.text == "Make message to all users" and message.from_user.id in admins_id)
def message_to_all_1(message):
    bot.send_message(message.from_user.id, "Enter message for all users (to cancel write 'cancel')")
    bot.register_next_step_handler(message, message_to_all_2)


def message_to_all_2(message):
    cur = con.cursor()
    if message.text != 'cancel':
        cur.execute(f'SELECT tg_id FROM users WHERE tg_id <> 0;')
        for i in cur.fetchall():
            bot.send_message(i[0], f'Message from admin:\n\n{message.text}')
        bot.send_message(message.from_user.id, f"Done. All users get message: '{message.text}'.\nUse /adm to return")
    else:
        bot.send_message(message.from_user.id, f"Canceled. Use /adm to return")


@bot.message_handler(func=lambda message: message.text == "Start collecting feedbacks" and message.from_user.id in admins_id)
def start_collect_feedback_1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Yes, start it")
    btn2 = types.KeyboardButton("No, go back")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "Do you want to start collecting feedbacks?", reply_markup=markup)
    bot.register_next_step_handler(message, start_collect_feedback_2)


def start_collect_feedback_2(message):
    if message.text == 'Yes, start it':
        bot.send_message(message.from_user.id, f"Write data (and time) of last class")
        bot.register_next_step_handler(message, start_collect_feedback_3)
    else:
        bot.send_message(message.from_user.id, f"Canceled. Use /adm to return")


def start_collect_feedback_3(message):
    global last_date, now_fb
    if not now_fb:
        cur = con.cursor()
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Yes, I used my turn", callback_data='fb_yes')
        btn2 = types.InlineKeyboardButton("No, I don't use my turn", callback_data='fb_no')
        markup.add(btn1, btn2)
        last_date = message.text
        cur.execute('SELECT tg_id FROM users WHERE queue <> 0;')
        for i in cur.fetchall():
            bot.send_message(i[0], f"Are you used your turn in class {last_date}?", reply_markup=markup)
            cur.execute(f'UPDATE users SET feedback = 1 WHERE tg_id = {i[0]};')
        bot.send_message(message.from_user.id, f"Done. All users who was signed up get message'.\nUse /adm to return")
        now_fb = True
        con.commit()
    else:
        bot.send_message(message.from_user.id, f"Collecting is already run!\n<b>Date: {last_date}</b>\nUse /adm to return")


@bot.message_handler(func=lambda message: message.text == "Stop collecting feedbacks" and message.from_user.id in admins_id)
def stop_collect_feedback_1(message):
    cur = con.cursor()
    cur.execute('SELECT tg_id, name, feedback FROM users WHERE (feedback = 2) OR (feedback = 3) OR (feedback = 1);')
    s = 'Now there are this results of feedback:\n'
    for i in cur.fetchall():
        if i[2] == 2:
            s += f'\n{i[1]} \u2705'
        elif i[2] == 3:
            s += f'\n{i[1]} \u274C'
        elif i[2] == 1:
            s += f'\n{i[1]} \u2753'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Yes, stop it")
    btn2 = types.KeyboardButton("No, go back")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, f"{s}\n\nDo you want to stop collecting feedbacks and delete \u2753?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, stop_collect_feedback_2)

def stop_collect_feedback_2(message):
    if message.text == "Yes, stop it":
        cur = con.cursor()
        cur.execute('SELECT tg_id FROM users WHERE feedback = 1;')
        for i in cur.fetchall():
            bot.send_message(i[0], "\u26A0 You was deleted from queue because you don't take part in feedback")
        cur.execute('UPDATE users SET queue = 0 WHERE feedback = 1;')
        cur.execute('UPDATE users SET feedback = 2 WHERE feedback = 1;')
        con.commit()
        bot.send_message(message.from_user.id, "Done. Now will start stop collecting procedure")
        auto_stop_collecting()
    else:
        bot.send_message(message.from_user.id, f"Canceled. Use /adm to return")


def auto_stop_collecting():
    global now_fb
    if now_fb:
        cur = con.cursor()
        cur.execute('SELECT tg_id FROM users WHERE feedback = 1')
        if len(cur.fetchall()) == 0:
            cur.execute('SELECT tg_id, name, feedback FROM users WHERE (feedback = 2) OR (feedback = 3);')
            s = 'Collecting feedbacks was stopped\nHere is the result:\n'
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
            bot.edit_message_text(f"Are you used your turn in class {last_date}?\n\n\u274C You choose 'No' and saved your turn in the queue",
                                  chat_id=call.message.chat.id, message_id=call.message.message_id)
            cur.execute(f'UPDATE users SET feedback = 3 WHERE tg_id = {call.message.chat.id};')
            refresh_queue()
        elif call.data == 'fb_yes':
            bot.edit_message_text(
                f"Are you used your turn in class {last_date}?\n\n\u2705 You choose 'Yes' and was deleted from the queue",
                chat_id=call.message.chat.id, message_id=call.message.message_id)
            cur.execute(f'UPDATE users SET feedback = 2 WHERE tg_id = {call.message.chat.id};')
            cur.execute(f'UPDATE users SET queue = 0 WHERE tg_id = {call.message.chat.id};')
        con.commit()
        auto_stop_collecting()
    else:
        bot.edit_message_text(
            f"Are you used your turn in class {last_date}?\n\n\u26A0 The time is out!",
            chat_id=call.message.chat.id, message_id=call.message.message_id)

bot.polling(none_stop=True, interval=2)
