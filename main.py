import telebot
from telebot import types
from telebot.util import quick_markup
from dotenv import load_dotenv
from os import getenv

import bot_functions
import db
import view_functions as view
from bot_functions import safe_send_message

load_dotenv()

token = getenv('BOT_TOKEN')
bot = telebot.TeleBot(token, parse_mode="Markdown")
admin_id = int(getenv('ADMIN_ID'))


# admin section
@bot.message_handler(func=lambda message: message.chat.id == admin_id, commands=['start', 'orders'])
def choose_orders_status(message):
    bot.send_message(admin_id, text='Выбери статус заказа:', reply_markup=get_choose_orders_status_markup())
    bot.register_callback_query_handler(choose_orders_type, func=lambda x: x.data in ['активен', 'завершен'])

def get_choose_orders_status_markup():
    keyboard = quick_markup({'Активные': {'callback_data': 'активен'},
                             'Завершенные': {'callback_data': 'завершен'}})
    return keyboard

def choose_orders_type(call):
    mid = call.message.message_id
    imid = call.inline_message_id

    orders_status = call.data
    bot.edit_message_text('Выбери тип заказа:', admin_id, mid, imid,
                          reply_markup=get_choose_orders_type_markup(orders_status))
    bot.register_callback_query_handler(list_spec_orders,
                                        func=lambda x: x.data.split()[0] in ['доставка', 'самовывоз'])
    bot.register_callback_query_handler(choose_orders_status, func=lambda x: x.data == 'статус')


def get_choose_orders_type_markup(orders_status):
    keyboard = quick_markup({'Доставка': {'callback_data': 'доставка ' + orders_status},
                             'Самовывоз': {'callback_data': 'самовывоз ' + orders_status},
                             '◀ Статус заказа': {'callback_data': 'статус'}})
    return keyboard

def list_spec_orders(call):
    message_id = call.message.message_id
    inline_message_id = call.inline_message_id

    [orders_type, orders_status]= call.data.split()
    spec_orders = db.get_specified_orders(orders_type, orders_status)
    bot.edit_message_text('Выбери заказ:', admin_id, message_id, inline_message_id,
                          reply_markup=get_list_spec_orders_markup(spec_orders, orders_status))
    bot.register_callback_query_handler(get_admin_order, func=lambda x: x.data.split()[0] == 'Админзаказ')

def get_list_spec_orders_markup(spec_orders, orders_status):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    order_buttons = [types.InlineKeyboardButton(
        text=f'№{order.get("order_id")} {order.get("date")}',
        callback_data='Админзаказ ' + order.get("order_id")) for order in spec_orders]
    keyboard.add(*order_buttons)
    keyboard.add(types.InlineKeyboardButton("◀ Тип заказа", callback_data=orders_status))
    return keyboard

def get_admin_order(call):
    mid = call.message.message_id
    imid = call.inline_message_id

    order_id = call.data.split()[1]

    order_info_dict = db.get_order_info_admin(order_id)
    order_view = view.render_order_admin(order_info_dict)
    order_status = order_info_dict.get('status')
    order_type = order_info_dict.get('order_type')
    bot.edit_message_text(order_view, admin_id, mid, imid, reply_markup=get_admin_order_markup(
        order_status, order_type, order_id))
    bot.register_callback_query_handler(archive_order, func=lambda x: x.data.split()[0] == 'Архивировать')

def get_admin_order_markup(order_status, order_type, order_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if order_status == 'активен':
        keyboard.add(types.InlineKeyboardButton('Завершить', callback_data='Архивировать ' + order_id))
    keyboard.add(types.InlineKeyboardButton('◀ Список заказов', callback_data=order_type + ' ' + order_status))
    return keyboard

def archive_order(call):
    order_id = call.data.split()[1]

    db.archive_order(order_id)

    call.data = 'Админзаказ ' + order_id
    get_admin_order(call)





# main menu
@bot.message_handler(commands=['start'])
def start_message(message):
    logo = open('l3O1dZo4b2A.jpg', 'rb')
    user = message.chat.id
    bot.send_photo(
        user,
        logo,
        caption='Привет, это телеграм бот Mallakto,\
        с его помощью Вы можете сделать заказ на нашем производстве', reply_markup=get_main_menu_keyboard())


def get_main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    item_buttons = [
        types.InlineKeyboardButton(
            item,
            callback_data=item
        ) for item in ['Каталог Товаров', "Моя Корзина", "Мои Заказы", "Контакты"]]
    keyboard.add(*item_buttons)
    return keyboard


# back to menu
@bot.callback_query_handler(func=lambda call: call.data == 'В меню')
def return_to_menu(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id
    bot.edit_message_text('Выберите раздел:',
                          chat_id,
                          message_id,
                          inline_message_id,
                          reply_markup=get_main_menu_keyboard())



# contacts
@bot.callback_query_handler(func=lambda call: call.data == 'Контакты')
def page_contacts(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("◀ В меню", callback_data="В меню"))
    message = f'''*Адрес производства:*
г.Москва, ул. Электродная, д.2, стр. 23

*Телефон:* +79164230377

[VK](https://vk.com/mallakto) [Instagram](https://www.instagram.com/mal_lakto) [Сайт](https://mallakto.ru)'''
    safe_send_message(bot, call, chat_id, message_id, message, inline_message_id, keyboard)


# cart
@bot.callback_query_handler(func=lambda call: call.data == 'Моя Корзина')
def get_user_cart(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id
    cart_dict = db.get_user_cart(chat_id)
    if cart_dict.get('cart_items'):
        bot_functions.safe_send_message(
            bot, call, chat_id, message_id,
            message_text=view.render_cart_view(cart_dict),
            inline_message_id=inline_message_id,
            reply_markup=get_cart_keyboard()
        )
    else:
        cqid = call.id
        bot.answer_callback_query(cqid, 'Корзина пуста', show_alert=True)

def get_cart_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton('Оформить заказ', callback_data="Тип Заказа"))
    keyboard.add(types.InlineKeyboardButton('Очистить корзину', callback_data='Очистить корзину'))
    keyboard.add(types.InlineKeyboardButton('◀ В меню', callback_data="В меню"))
    return keyboard


# clear cart
@bot.callback_query_handler(func=lambda call: call.data == 'Очистить корзину')
def clear_cart(call):
    chat_id = call.message.chat.id
    db.clear_cart(chat_id)
    call.data = 'Моя Корзина'
    get_user_cart(call)
    return_to_menu(call)


# categories menu
@bot.callback_query_handler(func=lambda call: call.data == 'Каталог Товаров')
def categories_menu(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id

    bot_functions.safe_send_message(bot, call, chat_id, message_id, 'Выберите категорию:',
                                    inline_message_id, reply_markup=get_categories_keyboard())


def get_categories_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    categories = db.get_categories()
    categories_buttons = [
        types.InlineKeyboardButton(
            category.get('name'),
            callback_data='категория' + category.get('id')) for category in categories]
    keyboard.add(*categories_buttons)
    keyboard.add(types.InlineKeyboardButton('◀ В меню', callback_data="В меню"))
    return keyboard


# items menu
@bot.callback_query_handler(func=lambda call: call.data.startswith('категория'))
def get_category_items(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id
    category_id = call.data[9:]
    bot.edit_message_text('Выберите товар:', chat_id,
                          message_id, inline_message_id, reply_markup=get_category_items_menu(category_id))

def get_category_items_menu(category_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    category_items = db.get_category_items(category_id)
    back_button = types.InlineKeyboardButton('◀ назад', callback_data='Каталог Товаров')
    item_buttons = [
        types.InlineKeyboardButton(
            item.get('name'), callback_data='товар' + item.get('id')) for item in category_items]
    keyboard.add(back_button, *item_buttons)
    return keyboard


# item page
@bot.callback_query_handler(func=lambda call: call.data.startswith('товар'))
def get_item_page(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id
    item_id = call.data[5:]
    photo_path = db.get_item_photo_path(item_id)
    photo = open(photo_path, 'rb')
    item_details = db.get_item_details(item_id)
    bot.delete_message(user_id, message_id)
    bot.send_photo(
        user_id,
        photo,
        caption=view.render_item_details(**item_details),
        reply_markup=get_item_menu(user_id, item_id))


def get_item_menu(user_id, item_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    item_quantity = db.get_item_quantity(user_id, item_id)

    quantity_window = types.InlineKeyboardButton(
        'В корзине: ' + str(item_quantity),
        callback_data='123')
    add_button = types.InlineKeyboardButton('Добавить в корзину', callback_data='Добавить' + item_id)
    remove_button = types.InlineKeyboardButton('Убрать из корзины', callback_data='Убрать' + item_id)
    cart_button = types.InlineKeyboardButton('Корзина', callback_data='Моя Корзина')
    back_button = types.InlineKeyboardButton('◀ назад', callback_data='Каталог Товаров')
    keyboard.add(
        quantity_window,
        add_button,
        remove_button,
        cart_button,
        back_button
    )
    return keyboard


# add item to cart
@bot.callback_query_handler(func=lambda call: call.data.startswith('Добавить'))
def add_item(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id
    inline_message_id = call.inline_message_id
    item_id = call.data[8:]

    db.add_to_cart(user_id, item_id)

    bot.edit_message_reply_markup(user_id, message_id, inline_message_id, reply_markup=get_item_menu(user_id, item_id))


# remove item from cart
@bot.callback_query_handler(func=lambda call: call.data.startswith('Убрать'))
def remove_item(call):
    user_id = call.message.chat.id
    item_id = call.data[6:]
    message_id = call.message.message_id
    inline_message_id = call.inline_message_id

    operation_status = db.remove_from_cart(user_id, item_id)

    if operation_status:
        bot.edit_message_reply_markup(user_id, message_id,
                                      inline_message_id, reply_markup=get_item_menu(user_id, item_id))
    else:
        callback_query_id = call.id
        bot.answer_callback_query(callback_query_id, 'Товар отсутствует в корзине', show_alert=True)


# create order
@bot.callback_query_handler(func=lambda call: call.data == 'Тип Заказа')
def choose_type_order(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id
    inline_message_id = call.inline_message_id

    bot.edit_message_text('Выберите тип заказа', user_id, message_id,
                          inline_message_id, reply_markup=get_order_type_keyboard())

def get_order_type_keyboard():
    keyboard = quick_markup({
        'Доставка': {'callback_data': 'Оформить доставка'},
        'Самовывоз': {'callback_data': 'Оформить самовывоз'},
        '◀ назад': {'callback_data': 'Моя Корзина'}
                             })
    return keyboard


@bot.callback_query_handler(func=lambda call: call.data.startswith('Оформить'))
def get_user_name(call):
    user = call.message.chat.id
    message_id = call.message.message_id
    inline_message_id = call.inline_message_id

    order_type = call.data[9:]
    msg = bot.edit_message_text('Как к Вам можно обращаться? (Ответьте сообщением)',
                                user, message_id, inline_message_id,
                                reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                                    types.InlineKeyboardButton('◀ назад', callback_data='Тип Заказа')))
    bot.register_next_step_handler(msg, get_user_phone, order_type)

def get_user_phone(message, order_type):
    cid = message.chat.id
    user_name = message.text
    msg = bot.send_message(cid, 'Укажите ваш котактный телефон (Ответьте сообщением)',
                           reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                               types.InlineKeyboardButton('◀ назад', callback_data='Тип Заказа')))
    bot.register_next_step_handler(msg, get_user_address, order_type, user_name)

def get_user_address(message, order_type, user_name):
    cid = message.chat.id
    user_phone = message.text

    if order_type == 'доставка':
        msg = bot.send_message(cid, 'Укажите адрес доставки (Ответьте сообщением)',
                               reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                                   types.InlineKeyboardButton('◀ назад', callback_data='Тип Заказа')))
        bot.register_next_step_handler(msg, create_order, order_type, user_name, user_phone)
    else:
        message.text = '-'
        create_order(message, order_type, user_name, user_phone)


def create_order(message, order_type, user_name, user_phone):
    cid = message.chat.id
    user_address = message.text

    order_id = db.create_order(cid, order_type, user_name, user_phone, user_address)

    bot.send_message(
        cid,
        f'*Заказ оформлен №:* {order_id}\n\nВ ближайшее время с вами свяжуться, для уточнения деталей.',
        reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('Мои заказы', callback_data='Мои Заказы'))
    )

    bot.send_message(admin_id, f'Заказ № {order_id}')
    bot.send_contact(admin_id, user_phone, user_name)


# list orders
@bot.callback_query_handler(func=lambda call: call.data == "Мои Заказы")
def list_orders(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id
    user_orders = db.get_user_orders(chat_id)

    safe_send_message(bot, call, chat_id, message_id, 'Выберите заказ: ', inline_message_id,
                      reply_markup=get_list_orders_keyboard(user_orders))


def get_list_orders_keyboard(user_orders):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    order_buttons = [types.InlineKeyboardButton(
        text=f'№{order.get("order_id")} {order.get("date")}',
        callback_data='Заказ' + order.get("order_id")) for order in user_orders]
    keyboard.add(*order_buttons)
    keyboard.add(types.InlineKeyboardButton("◀ В меню", callback_data="В меню"))
    return keyboard


@bot.callback_query_handler(func=lambda call: call.data.startswith('Заказ'))
def get_order_info(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    inline_message_id = call.inline_message_id

    order_id = call.data[5:]
    order_info_dict = db.get_order_info(chat_id, order_id)
    order_info = view.render_order_info(order_info_dict)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton('Мои заказы', callback_data='Мои Заказы'))

    bot.edit_message_text(order_info, chat_id, message_id, inline_message_id,
                          reply_markup=keyboard)


bot.infinity_polling()
