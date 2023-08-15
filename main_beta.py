import sqlite3
import telebot
from telebot import types

API_TOKEN = '6561744201:AAFlX7bqKzRCLIQglCDCh5S80PQjCArBqXc'
bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')
con = sqlite3.connect('main_beta.db', check_same_thread=False)
admins_id = [1142412436]
classes = ['queue_opd', 'queue_prog']
classes_names = ['💾 ОПД', '💻 Прога']
fb_list = ['opd_fb', 'prog_fb']
class_dates = ['12.08.23', '15.08.23']


@bot.message_handler(commands=['start', 'help', 'menu'])
def send_welcome(message):
    cur = con.cursor()
    cur.execute(f'SELECT * FROM users WHERE tg_id = {message.from_user.id};')
    if len(cur.fetchall()) == 0:
        bot.send_message(message.from_user.id, "Ты еще не зарегистрирован(а), введи своё имя чтобы начать")
        bot.register_next_step_handler(message, new_reg)
    else:
        cur.execute(f'SELECT last_message FROM users WHERE tg_id = {message.from_user.id};')
        temp = cur.fetchall()[0][0]
        if temp is not None:
            bot.delete_message(message.from_user.id, temp)
        markup, st = get_queues_list_text(message.from_user.id)
        lst_msg = bot.send_message(message.from_user.id, st, reply_markup=markup).message_id
        cur.execute(f'UPDATE users SET last_message = {lst_msg} WHERE tg_id = {message.from_user.id};')
        con.commit()
        if fb_alert(message.from_user.id):
            bot.send_message(message.from_user.id, "❗️Сейчас открыты опросы, в которых ты еще не поучаствовал(а)!")
        markup_1 = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup_1.add(types.KeyboardButton("Полные списки"), types.KeyboardButton("Открытые опросы"))
        bot.send_message(message.from_user.id, "Ты можешь выбрать другие разделы:", reply_markup=markup_1)


@bot.message_handler(func=lambda message: message.text == '/adm' and message.from_user.id in admins_id)
def send_admin(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("🏁 Старт опроса"), types.KeyboardButton("⛔ Остановка опроса"),
               types.KeyboardButton("✏️ Изменить статус"))
    bot.send_message(message.from_user.id, "Добро пожалось в меню админа!", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "✏️ Изменить статус" and message.from_user.id in admins_id)
def change_status_1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for i in classes_names:
        markup.add(types.KeyboardButton(i))
    markup.add(types.KeyboardButton("⬅️ Вернуться в меню"))
    bot.send_message(message.from_user.id, "По какому предмету изменить статус пользователя?", reply_markup=markup)
    bot.register_next_step_handler(message, change_status_2)


def change_status_2(message):
    if message.text == "⬅️ Вернуться в меню":
        send_admin(message)
    else:
        num = classes_names.index(message.text)
        bot.send_message(message.from_user.id, f"Введи имя пользователя, статус которого надо поменять "
                                               f"в очереди на {classes_names[num]}")
        bot.register_next_step_handler(message, change_status_3, num)


def change_status_3(message, num):
    cur = con.cursor()
    cur.execute(f'SELECT {classes[num]} FROM users WHERE name = "{message.text}";')
    temp = cur.fetchall()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if len(temp) == 0:
        bot.send_message(message.from_user.id, f"Такого пользователя не существует")
        send_admin(message)
    elif temp[0][0] == 0:
        markup.add(types.KeyboardButton("Да, поставить"), types.KeyboardButton("Нет"))
        bot.send_message(message.from_user.id,
                         f"Пользователь НЕ находится в очереди на {classes_names[num]}, поставить?",
                         reply_markup=markup)
        bot.register_next_step_handler(message, change_status_4, num, message.text)
    else:
        markup.add(types.KeyboardButton("Да, удалить"), types.KeyboardButton("Нет"))
        bot.send_message(message.from_user.id,
                         f"Пользователь находится в очереди на {classes_names[num]}, удалить?",
                         reply_markup=markup)
        bot.register_next_step_handler(message, change_status_4, num, message.text)


def change_status_4(message, num, name):
    cur = con.cursor()
    cur.execute(f'SELECT tg_id FROM users WHERE name = "{name}";')
    tg = cur.fetchall()[0][0]
    if message.text == 'Да, поставить':
        cur.execute(f'SELECT MAX({classes[num]}) FROM users;')
        cur_num = cur.fetchall()[0][0] + 1
        cur.execute(f'UPDATE users SET {classes[num]} = {cur_num} WHERE tg_id = {tg};')
        con.commit()
        bot.send_message(tg, f"🚨 Администратор поставил тебя в очередь на {classes_names[num]}")
        markup, st = get_queues_list_text(tg)
        cur.execute(f'SELECT last_message FROM users WHERE tg_id = {tg};')
        lst_msg = cur.fetchall()[0][0]
        bot.edit_message_text(st, tg, lst_msg, reply_markup=markup)
        bot.send_message(message.from_user.id, f"Добавлено, теперь он имеет номер - {cur_num}")
        send_admin(message)
    elif message.text == 'Да, удалить':
        cur.execute(f'UPDATE users SET {classes[num]} = 0 WHERE tg_id = {tg};')
        con.commit()
        markup, st = get_queues_list_text(tg)
        cur.execute(f'SELECT last_message FROM users WHERE tg_id = {tg};')
        lst_msg = cur.fetchall()[0][0]
        bot.edit_message_text(st, tg, lst_msg, reply_markup=markup)
        bot.send_message(tg, f"🚨 Администратор удалил тебя из очереди на {classes_names[num]}")
        bot.send_message(message.from_user.id, "Удалено")
        send_admin(message)
    else:
        bot.send_message(message.from_user.id, "Отменено")
        send_admin(message)


@bot.message_handler(func=lambda message: message.text == "⛔ Остановка опроса" and message.from_user.id in admins_id)
def stop_poll_1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for i in classes_names:
        markup.add(types.KeyboardButton(i))
    markup.add(types.KeyboardButton("⬅️ Вернуться в меню"))
    bot.send_message(message.from_user.id, "По какому предмету остановить опрос?", reply_markup=markup)
    bot.register_next_step_handler(message, stop_poll_2)


def stop_poll_2(message):
    if message.text == "⬅️ Вернуться в меню":
        send_admin(message)
    else:
        num = classes_names.index(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("Да"), types.KeyboardButton("Нет"))
        bot.send_message(message.from_user.id,
                         f"Точно завершить опрос по {classes_names[num]} и удалить неответивших?", reply_markup=markup)
        bot.register_next_step_handler(message, stop_poll_3, num)


def stop_poll_3(message, num):
    if message.text == 'Да':
        bot.send_message(message.from_user.id, f"Остановлен опрос по {classes_names[num]} от {class_dates[num]}")
        stop_poll(num)
        send_admin(message)
    else:
        bot.send_message(message.from_user.id, f"Отменено")
        send_admin(message)


@bot.message_handler(func=lambda message: message.text == '🏁 Старт опроса' and message.from_user.id in admins_id)
def start_poll_1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for i in classes_names:
        markup.add(types.KeyboardButton(i))
    markup.add(types.KeyboardButton("⬅️ Вернуться в меню"))
    bot.send_message(message.from_user.id, "По какому предмету запустить опрос?", reply_markup=markup)
    bot.register_next_step_handler(message, start_poll_2)


def start_poll_2(message):
    if message.text == "⬅️ Вернуться в меню":
        send_admin(message)
    else:
        num = classes_names.index(message.text)
        bot.send_message(message.from_user.id, f"Введи дату последнего занятия по {classes_names[num]}")
        bot.register_next_step_handler(message, start_poll_3, num)


def start_poll_3(message, num):
    class_dates[num] = message.text
    bot.send_message(message.from_user.id, f"Начат опрос по {classes_names[num]} от {class_dates[num]}")
    select_fb_list(num)
    send_admin(message)



def auto_stop_poll(num):
    cur = con.cursor()
    cur.execute(f'SELECT tg_id FROM users WHERE {fb_list[num]} = 1;')
    if len(cur.fetchall()) == 0:
        stop_poll(num)


def stop_poll(num):
    cur = con.cursor()
    cur.execute(f'SELECT tg_id, name, {fb_list[num]} FROM users WHERE ({fb_list[num]} = 1) OR ({fb_list[num]} = 2) '
                f'OR ({fb_list[num]} = 3) GROUP BY {classes[num]};')
    s = f'Опрос по {classes_names[num]} от {class_dates[num]} завершён!\nВот его результаты:\n'
    temp = cur.fetchall()
    for i in range(len(temp)):
        if temp[i][2] == 1:
            s += f'\n{i + 1}. {temp[i][1]} — ❓ (== ✅)'
        elif temp[i][2] == 2:
            s += f'\n{i + 1}. {temp[i][1]} — ✅'
        elif temp[i][2] == 3:
            s += f'\n{i + 1}. {temp[i][1]} — ❌'
    cur.execute(f'UPDATE users SET {classes[num]} = 0 WHERE ({fb_list[num]} = 1) OR ({fb_list[num]} = 2);')
    cur.execute(f'UPDATE users SET {fb_list[num]} = 0 WHERE {fb_list[num]} <> 0;')
    con.commit()
    s += f'\n\n\nТаким образом, список {classes_names[num]} выглядит так:\n'
    s += get_full_list(num, None)
    s += '\n\n<i>Теперь ты можешь входить и выходить из очереди по этому предмету</i>'
    for i in temp:
        bot.send_message(i[0], s)


@bot.message_handler(func=lambda message: message.text == "Открытые опросы")
def show_polls(message):
    cur = con.cursor()
    s, markup = get_polls_list(message.from_user.id)
    if s == 'ℹ️ Сейчас нет открытых опросов, достуных тебе для участия':
        send_welcome(message)
        bot.send_message(message.from_user.id, s)
    else:
        cur.execute(f'SELECT last_fb FROM users WHERE tg_id = {message.from_user.id};')
        temp = cur.fetchall()[0][0]
        if temp is not None:
            bot.delete_message(message.from_user.id, temp)
        send_welcome(message)
        lst = bot.send_message(message.from_user.id, s, reply_markup=markup).message_id
        cur.execute(f'UPDATE users SET last_fb = {lst} WHERE tg_id = {message.from_user.id};')
        con.commit()


def get_polls_list(id):
    cur = con.cursor()
    cur.execute(f'SELECT {", ".join(fb_list)} FROM users WHERE tg_id = {id};')
    s = ''
    k = 0
    markup = types.InlineKeyboardMarkup()
    for i in cur.fetchall()[0]:
        if i == 1:
            s += f'\n{classes_names[k]} от {class_dates[k]}'
            markup.add(types.InlineKeyboardButton(f"✅ Выступил(а) на {classes_names[k]} {class_dates[k]}",
                                                  callback_data=f'fbY_{k}'))
            markup.add(types.InlineKeyboardButton(f"❌ НЕ выступил(а) на {classes_names[k]} {class_dates[k]}",
                                                  callback_data=f'fbN_{k}'))
        elif i == 2:
            s += f'\n{classes_names[k]} от {class_dates[k]} — ✅ Ты выступил(а) на занятии'
        elif i == 3:
            s += f'\n{classes_names[k]} от {class_dates[k]} — ❌ Ты НЕ выступил(а) на занятии'
        k += 1
    if s == '':
        s = "ℹ️ Сейчас нет открытых опросов, достуных тебе для участия"
    else:
        s = "Сейчас тебе доступны следующие опросы для участия:\n" + s
        s += "\n\nВыбери, удалось ли тебе выступить на последних занятиях:"
    return s, markup


@bot.callback_query_handler(func=lambda call: call.data[:2] == "fb")
def callbacks_fb(call):
    cur = con.cursor()
    num = int(call.data[4:])
    if call.data[2] == 'Y':
        cur.execute(f'UPDATE users SET {fb_list[num]} = 2 WHERE tg_id = {call.message.chat.id};')
        con.commit()
        s, markup = get_polls_list(call.message.chat.id)
        bot.edit_message_text(s, call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, "Ты выступил на занятии")
    elif call.data[2] == 'N':
        cur.execute(f'UPDATE users SET {fb_list[num]} = 3 WHERE tg_id = {call.message.chat.id};')
        con.commit()
        s, markup = get_polls_list(call.message.chat.id)
        bot.edit_message_text(s, call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, "Ты НЕ выступил на занятии")
    auto_stop_poll(num)


def select_fb_list(num):
    cur = con.cursor()
    cur.execute(f'SELECT tg_id FROM users WHERE {classes[num]} <> 0;')
    for i in cur.fetchall():
        if i[0] != 0:
            cur.execute(f'UPDATE users SET {fb_list[num]} = 1 WHERE tg_id = {i[0]};')
            bot.send_message(i[0], f"❗️ Открыт опрос по {classes_names[num]} от {class_dates[num]}\nТебе необходимо "
                                f"принять в нём участие!")
    con.commit()


# Returns True if there are NOT any started polls in this class
def restrictions_check(id, num):
    cur = con.cursor()
    cur.execute(f'SELECT {fb_list[num]} FROM users WHERE tg_id = {id};')
    if all(i == 0 for i in cur.fetchall()[0]):
        return True
    else:
        return False


def fb_alert(id):
    cur = con.cursor()
    cur.execute(f'SELECT {", ".join(fb_list)} FROM users WHERE tg_id = {id};')
    if any(i == 1 for i in cur.fetchall()[0]):
        return True
    else:
        return False


@bot.message_handler(func=lambda message: message.text == 'Полные списки')
def see_lists_1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for clas in classes_names:
        markup.add(types.KeyboardButton(clas))
    markup.add(types.KeyboardButton("⬅️ Вернуться в меню"))
    bot.send_message(message.from_user.id, "Выбери нужный предмет для просмотры полных списков очереди:",
                     reply_markup=markup)
    bot.register_next_step_handler(message, see_lists_2)


def see_lists_2(message):
    if message.text == '⬅️ Вернуться в меню':
        send_welcome(message)
    elif message.text in classes_names:
        ind = classes_names.index(message.text)
        st = get_full_list(ind, message.from_user.id)
        st = f'Полный список {classes_names[ind]}:\n' + st + '\n\n<i>Ты выделен(а) жирным шрифтом</i>'
        send_welcome(message)
        bot.send_message(message.from_user.id, st)
    else:
        bot.send_message(message.from_user.id, "⚠️ Такого предмета не существует, введи другой")
        see_lists_1(message)


def get_full_list(num, id):
    refresh_queues()
    cur = con.cursor()
    cur.execute(f'SELECT tg_id, name, {classes[num]} FROM users WHERE {classes[num]} <> 0 GROUP BY {classes[num]};')
    s = ''
    for i in cur.fetchall():
        if i[0] == id:
            s += f'\n<b>{i[2]}. {i[1]}</b>'
        else:
            s += f'\n{i[2]}. {i[1]}'
    return s

@bot.callback_query_handler(func=lambda call: call.data == 'update')
def callbacks_update(call):
    markup, st = get_queues_list_text(call.message.chat.id)
    try:
        bot.edit_message_text(st, call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, "Обновлено")
    except telebot.apihelper.ApiTelegramException:
        bot.answer_callback_query(call.id, "Обновлений нет")


@bot.callback_query_handler(func=lambda call: call.data[:6] == 'change')
def callbacks_change(call):
    num = int(call.data[7:])
    if restrictions_check(call.message.chat.id, num):
        cur = con.cursor()
        cur.execute(f'SELECT {classes[num]} FROM users WHERE tg_id = {call.message.chat.id};')
        if cur.fetchall()[0][0] != 0:
            cur.execute(f'UPDATE users SET {classes[num]} = 0 WHERE tg_id = {call.message.chat.id};')
            con.commit()
            markup, st = get_queues_list_text(call.message.chat.id)
            bot.edit_message_text(st, call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, f"Удалено из {classes_names[num]}")
        else:
            cur.execute(f'SELECT MAX({classes[num]}) FROM users;')
            cur_num = cur.fetchall()[0][0] + 1
            cur.execute(f'UPDATE users SET {classes[num]} = {cur_num} WHERE tg_id = {call.message.chat.id};')
            con.commit()
            markup, st = get_queues_list_text(call.message.chat.id)
            bot.edit_message_text(st, call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, f"Добавлено в {classes_names[num]}")
    else:
        bot.answer_callback_query(call.id,
                                  f"⚠️ Запрещено ⚠️ \nОткрыт опрос о прошеднем занятии, в который ты внесен(а) \nЖди "
                                  f"закрытия", show_alert=True)


def get_queues_list(id):
    global classes
    cur = con.cursor()
    cur.execute(f'SELECT {", ".join(classes)} FROM users WHERE tg_id = {id}')
    return [i for i in cur.fetchall()[0]]


def get_queues_list_text(id):
    refresh_queues()
    s = 'Сейчас ты находишься в списках:\n'
    q = get_queues_list(id)
    markup = types.InlineKeyboardMarkup()
    for i in range(len(q)):
        s += f'\n{classes_names[i]} — {"❌ Ты не в очереди" if q[i] == 0 else ("✅ Твой номер: " + str(q[i]))}'
        markup.add(types.InlineKeyboardButton(f"✅ Записаться в {classes_names[i]}", callback_data=f'change_{i}') if q[i] == 0
                   else types.InlineKeyboardButton(f"❌ Выйти из {classes_names[i]}", callback_data=f'change_{i}'))
    markup.add(types.InlineKeyboardButton("🔄 Обновить номера", callback_data='update'))
    s += '\n\nТы можешь изменить статус участия в очереди:'
    return markup, s


def refresh_queues():
    cur = con.cursor()
    for clas in classes:
        cur.execute(f'SELECT id FROM users WHERE {clas} <> 0 GROUP BY {clas};')
        k = 1
        for i in cur.fetchall():
            cur.execute(f'UPDATE users SET {clas} = {k} WHERE id = {i[0]};')
            k += 1
    con.commit()


def new_reg(message):
    cur = con.cursor()
    cur.execute(f'SELECT tg_id FROM users WHERE name = "{message.text}";')
    temp = cur.fetchall()
    if len(temp) == 0:
        bot.send_message(message.from_user.id, "Неправильное имя, попробуй другое")
        bot.register_next_step_handler(message, new_reg)
    elif temp[0][0] != 0:
        bot.send_message(message.from_user.id, "Это имя уже зарегистрировано, попробуй другое")
        bot.register_next_step_handler(message, new_reg)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("/menu"))
        cur.execute(f'UPDATE users SET tg_id = {message.from_user.id} WHERE name = "{message.text}";')
        bot.send_message(message.from_user.id, "Регистрация успешна!")
        con.commit()
        send_welcome(message)


bot.polling(none_stop=True, interval=2)