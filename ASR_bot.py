from telegram.ext import CallbackQueryHandler, Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram

import os
import subprocess
import shutil
import json

import traceback
import hashlib
from utils import ffmpegit, recognize


def check_authorization(update: telegram.Update, context: telegram.ext.CallbackContext) -> bool:
    global AUTHS
    username = update.message.from_user.full_name.replace(' ', '_')
    user_id = update.message.from_user.id
    if f'{user_id}' in AUTHS['users']:
        return True
    else:
        return False


def auth_decorator(func):
    def wrapper(*args, **kwargs):
        update: telegram.Update = args[0]
        context: telegram.ext.CallbackContext = args[1]
        if check_authorization(update, context) is True:
            func(*args, **kwargs)
        else:
            auth_text = "Permission denied! Enter command /auth"
            context.bot.send_message(chat_id=update.effective_chat.id, text=auth_text)
    return wrapper


def start(update, context):
    start_text = [
        'Hello there!\n'
        'Send me videofile or audiofile and I will transcribe it for you.',
        'You need to use /auth command to get access to recognition.'
    ]
    context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(start_text))


def authorize(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Enter password:")
    return 0


def enter_password(update: telegram.Update, context: telegram.ext.CallbackContext):
    global AUTHS
    password = update.message.text
    if hashlib.md5(password.encode('utf-8')).hexdigest() == '647229d9c3ce267854c85a4b38823cef':
        username = update.message.from_user.full_name.replace(' ', '_')
        user_id = update.message.from_user.id
        AUTHS['users'].append(f'{user_id}')
        json.dump(AUTHS, open('auth.json', 'w'), ensure_ascii=False)
        update.message.reply_text('Access granted.')
        return ConversationHandler.END
    else:
        update.message.reply_text('Enter CORRECT password:')
        return 0


def cancel(update, context) -> int:
    update.message.reply_text('Good luck next time.')
    return ConversationHandler.END


@auth_decorator
def handle_text(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Send audio or video!")
    return 0


@auth_decorator
def handle_record(update, context):
    chat_dir = os.path.join('chats', str(update.effective_chat.id))
    os.makedirs(chat_dir, exist_ok=True)

    file_name = update.message.document.file_name
    file_path = os.path.join(chat_dir, file_name)
    update.message.document.get_file().download(file_path)

    text_to_output = []
    text_to_output.append(f'Got it: {file_name}')
    write_txt = '\n'.join(text_to_output)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=write_txt,
                             reply_markup=reply_markup)




def main():
    try:
        with open('/run/secrets/telegram_key', 'r') as f:
            token = f.readline()[:-1]
    except FileNotFoundError:
        print('No telegram.key has been found!')
        return -1

    start_handler = CommandHandler('start', start)
    auth_handler = ConversationHandler(
        entry_points=[CommandHandler('auth', authorize)],
        states={
            0: [MessageHandler(Filters.text & ~Filters.command, enter_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    text_handler = MessageHandler(Filters.text & (~Filters.command), handle_text)
    record_handler = MessageHandler(Filters.video | Filters.audio | Filters.document, handle_record)
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(auth_handler)
    dispatcher.add_handler(text_handler)
    dispatcher.add_handler(record_handler)

    updater.start_polling()
    print('BOT IS RUNNING!')
    updater.idle()


AUTHS = dict()

if __name__ == "__main__":
    print("bot started")
    try:
        AUTHS = json.load(open('auth.json', 'r'))
        if "users" not in AUTHS:
            raise FileNotFoundError
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        AUTHS = {'users': []}
        json.dump(AUTHS, open('auth.json', 'w'), ensure_ascii=False)

    # read azure creds

    main()
