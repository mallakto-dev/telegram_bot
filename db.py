from dotenv import load_dotenv
import psycopg2
from os import getenv
from datetime import datetime


load_dotenv()


def connect():
    database = getenv('DATABASE_URL')
    conn = psycopg2.connect(database)
    return conn


def get_user_cart(user_id):
    with connect().cursor() as cursor:
        cursor.execute(
            """SELECT item_name, quantity
            FROM carts
            JOIN shop_items
            ON carts.product_id = shop_items.item_id
            WHERE user_id = %(user_id)s""", {'user_id': user_id}
        )
        user_cart_items_raw = cursor.fetchall()
        user_cart_items = list(map(lambda x: {'name': x[0], 'quantity': x[1]}, user_cart_items_raw))

        if user_cart_items:
            with connect().cursor() as cursor:
                cursor.execute(
                    """SELECT SUM(price * quantity)
                    FROM carts
                    JOIN shop_items
                    ON carts.product_id = shop_items.item_id
                    WHERE user_id = %(user_id)s""", {'user_id': user_id}
                )
                total_cost = cursor.fetchone()[0]
                return {'cart_items': user_cart_items, 'total_cost': total_cost}
        else:
            return {}

def get_item_quantity(user_id, item_id):
    with connect().cursor() as cursor:
        cursor.execute(
            """SELECT quantity
            FROM carts
            JOIN shop_items
            ON carts.product_id = shop_items.item_id
            WHERE user_id = %(user_id)s AND item_id = %(item_id)s""", {'user_id': user_id, 'item_id': int(item_id)}
        )
        item_quantity = cursor.fetchone()
        if item_quantity:
            return item_quantity[0]
        else:
            return 0


def get_categories():
    with connect().cursor() as cursor:
        cursor.execute(
            """SELECT id, name
            FROM categories"""
        )
        categories_raw = cursor.fetchall()
        categories = list(map(lambda x: {'id': str(x[0]), 'name': x[1]}, categories_raw))
        return categories


def get_category_items(category_id):
    with connect().cursor() as cursor:
        cursor.execute(
            """SELECT item_id, item_name
            FROM shop_items
            JOIN categories
            ON shop_items.category = categories.name
            WHERE id = %(category_id)s;""", {'category_id': int(category_id)}
        )
        category_items_raw = cursor.fetchall()
        category_items = list(map(lambda x: {'id': str(x[0]), 'name': x[1]}, category_items_raw))
        return category_items


def get_item_details(item_id):
    with connect().cursor() as cursor:
        cursor.execute(
            """SELECT item_name, ingredients, nutrition_facts, shelf_life, price, weight 
            FROM shop_items
            WHERE item_id = %(item_id)s""", {'item_id': int(item_id)}
        )
        item_details_raw = cursor.fetchone()
        item_name, ingredients, nutrition_facts,shelf_life, price, weight = item_details_raw
        return {
            'name': item_name,
            'weight': weight,
            'ingredients': ingredients,
            'nutrition_facts': nutrition_facts,
            'shelf_life': shelf_life,
            'price': price}


def get_item_photo_path(item_id):
    with connect().cursor() as cursor:
        cursor.execute(
            """SELECT photo_path
            FROM shop_items
            WHERE item_id = %(item_id)s""", {'item_id': int(item_id)}
        )
        photo_path = cursor.fetchone()[0]
        return photo_path


def add_to_cart(user_id, item_id):
    conn = connect()
    if get_item_quantity(user_id, item_id):
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE carts
                SET quantity = quantity + 1
                WHERE product_id = %(item_id)s AND user_id = %(user_id)s""",
                {'item_id': int(item_id), 'user_id': user_id}
            )
    else:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO carts (user_id, product_id, quantity)
                VALUES (%(user_id)s, %(item_id)s, %(quantity)s)""",
                {'user_id': user_id, 'item_id': int(item_id), 'quantity': 1}
            )
    conn.commit()


def remove_from_cart(user_id, item_id):
    conn = connect()
    item_quantity = get_item_quantity(user_id, item_id)
    if item_quantity:
        if item_quantity == 1:
            with conn.cursor() as cursor:
                cursor.execute(
                    """DELETE FROM carts
                    WHERE user_id = %(user_id)s AND product_id = %(item_id)s;""",
                    {'user_id': user_id, 'item_id': int(item_id)}
                )
        else:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE carts
                    SET quantity = quantity - 1
                    WHERE product_id = %(item_id)s AND user_id = %(user_id)s""",
                    {'item_id': int(item_id), 'user_id': user_id}
                )
        conn.commit()
        return True
    else:
        return False


def create_order(user_id, order_type, user_name, user_phone, user_address):
    current_date_raw = datetime.now()
    current_date = f'{current_date_raw.year}-{current_date_raw.month}-{current_date_raw.day}'

    user_cart_dict = get_user_cart(user_id)
    user_cart_items_str = cart_dict_to_str_order(user_cart_dict.get('cart_items'))
    total_cost = user_cart_dict.get('total_cost')

    conn = connect()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO orders (user_id, order_items, order_type, order_status, created_at, total_cost, user_name, user_phone, user_address)
            VALUES (%(user_id)s, %(order_items)s, %(order_type)s, %(order_status)s, %(created_at)s, %(total_cost)s, %(user_name)s, %(user_phone)s, %(user_address)s)
            RETURNING order_id""",
            {
                'user_id': user_id,
                'order_items': user_cart_items_str,
                'order_type': order_type,
                'order_status': 'активен',
                'created_at': current_date,
                'total_cost': total_cost,
                'user_name': user_name,
                'user_phone': user_phone,
                'user_address': user_address
            }
        )
        order_id = cursor.fetchone()[0]
        conn.commit()

    clear_cart(user_id)

    return order_id


def clear_cart(user_id):
    conn = connect()
    with conn.cursor() as cursor:
        cursor.execute("""
        DELETE FROM carts
        WHERE user_id = %(user_id)s""", {'user_id': user_id})
        conn.commit()


def cart_dict_to_str_order(cart_items_dict):
    result = ''
    for item in cart_items_dict:
        result += f"{item.get('name')}: *{item.get('quantity')}*\n"
    return result


def get_user_orders(chat_id):
    with connect().cursor() as cursor:
        cursor.execute("""
        SELECT order_id, created_at
        FROM orders
        WHERE user_id = %(user_id)s""", {'user_id': chat_id})
        orders_raw = cursor.fetchall()
        orders = list(map(lambda x: {'order_id': str(x[0]), 'date': x[1]}, orders_raw))
        return orders


def get_order_info(chat_id, order_id):
    with connect().cursor() as cursor:
        cursor.execute("""
        SELECT order_id, order_status, order_type, order_items, user_address, total_cost, created_at
        FROM orders
        WHERE user_id = %(user_id)s AND order_id = %(order_id)s""", {'user_id': chat_id, 'order_id': order_id})
        order_raw = cursor.fetchone()
        order_dict = {'order_id': order_raw[0],
                      'status': order_raw[1],
                      'order_type': order_raw[2],
                      'items': order_raw[3],
                      'user_address': order_raw[4],
                      'total_cost': order_raw[5],
                      'created_at': order_raw[6]}

        return order_dict


def get_specified_orders(order_type, order_status):
    with connect().cursor() as cursor:
        cursor.execute("""
        SELECT order_id, created_at
        FROM orders
        WHERE order_type = %(order_type)s AND order_status = %(order_status)s
        ORDER BY order_id DESC""", {'order_type': order_type,
                                    'order_status': order_status})
        orders_raw = cursor.fetchall()
        orders = list(map(lambda x: {'order_id': str(x[0]), 'date': x[1]}, orders_raw))
        return orders


def get_order_info_admin(order_id):
    with connect().cursor() as cursor:
        cursor.execute("""
        SELECT order_id, order_status, order_type, order_items, user_address, 
        total_cost, created_at, user_name, user_phone
        FROM orders
        WHERE order_id = %(order_id)s""", {'order_id': order_id})
        order_raw = cursor.fetchone()
        order_dict = {'order_id': order_raw[0],
                      'status': order_raw[1],
                      'order_type': order_raw[2],
                      'items': order_raw[3],
                      'user_address': order_raw[4],
                      'total_cost': order_raw[5],
                      'created_at': order_raw[6],
                      'user_name': order_raw[7],
                      'user_phone': order_raw[8]}

        return order_dict


def archive_order(order_id):
    conn = connect()
    with conn.cursor() as cursor:
        cursor.execute("""
        UPDATE orders
        SET order_status = %(order_status)s
        WHERE order_id = %(order_id)s""", {'order_id': order_id, 'order_status': 'завершен'})
        conn.commit()