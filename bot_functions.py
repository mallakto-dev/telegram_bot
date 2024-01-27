def safe_send_message(bot, call, chat_id, message_id, message_text, inline_message_id, reply_markup):
    if call.message.photo:
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, message_text, reply_markup=reply_markup)
    else:
        bot.edit_message_text(message_text, chat_id, message_id, inline_message_id, reply_markup=reply_markup)

def safe_send_photo(bot, call, chat_id, message_id, caption, photo, inline_message_id, reply_markup):
    if call.message.photo:
        bot.edit_message_reply_markup(chat_id, message_id, inline_message_id, reply_markup)
