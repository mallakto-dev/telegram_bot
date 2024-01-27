def render_item_details(name, weight, ingredients, nutrition_facts, shelf_life, price):
    view = f'''*{name}*

*Состав:* {ingredients}
*Пищевая ценность на 100г:* {nutrition_facts}
*Срок годности:* {shelf_life}

*Масса нетто:* {weight}
*Цена:* {price}руб.
'''
    return view


def render_cart_view(cart_dict):
    view = '*Моя Корзина:*\n\n'
    for item in cart_dict.get('cart_items'):
        view += f"{item.get('name')}: *{item.get('quantity')}*\n"
    view += f'\n*Сумма: * {cart_dict.get("total_cost")} руб'
    return view


def render_order_info(order_info_dict):
    order = order_info_dict

    view = f'*Заказ №{order.get("order_id")}*\n_{order.get("status")}_\n({order.get("order_type")})\n\n'\
           f'{order.get("items")}\n{order.get("user_address")}\n\n'\
           f'*Сумма:* {order.get("total_cost")}руб.'

    return view


def render_order_admin(order_info_dict):
    order = order_info_dict

    view = f'*Заказ №{order.get("order_id")}*\n_{order.get("status")}_\n({order.get("order_type")})\n\n' \
           f'*Имя:*{order.get("user_name")}\n*тел.* {order.get("user_phone")}\n\n' \
           f'{order.get("items")}\n{order.get("user_address")}\n\n' \
           f'*Сумма:* {order.get("total_cost")}руб.'

    return view
