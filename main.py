from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import random
import time

# Constants
APP_TOKEN = 'd28721be-fd2d-4b45-869e-9f253b554e50'
PROMO_ID = '43e35910-c168-4634-ad4f-52fd764a843f'
DEBUG_MODE = False
EVENTS_DELAY = 1000 if DEBUG_MODE else 5000  # Reduced delay for faster generation
BOT_TOKEN = '7486294270:AAH8cOXMcvp6nxc33mWiI4PYwTbxbSskS4I'
CHANNEL_USERNAME = '@hamster_mini_game'
CHANNEL_MEMBER_BOT_TOKEN = '7401151771:AAGiX-ZbDSIM8GJDo8ciab_Os9U-HxqqUkM'  # Replace with the token of the channel member bot

# Functions
def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(19)])
    return f"{timestamp}-{random_numbers}"

def delay_random():
    return (random.random() / 3 + 1)

def sleep(ms):
    time.sleep(ms / 1000)

def login(client_id):
    if DEBUG_MODE:
        return 'debug-client-token'
    url = 'https://api.gamepromo.io/promo/login-client'
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Host': 'api.gamepromo.io'
    }
    data = {
        'appToken': APP_TOKEN,
        'clientId': client_id,
        'clientOrigin': 'deviceid'
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('clientToken')

def emulate_progress(client_token):
    if DEBUG_MODE:
        return True
    url = 'https://api.gamepromo.io/promo/register-event'
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Host': 'api.gamepromo.io',
        'Authorization': f'Bearer {client_token}'
    }
    data = {
        'promoId': PROMO_ID,
        'eventId': str(random.randint(0, 100000)),
        'eventOrigin': 'undefined'
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('hasCode')

def generate_key(client_token):
    if DEBUG_MODE:
        return 'DEBUG-KEY-1234'
    url = 'https://api.gamepromo.io/promo/create-code'
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Host': 'api.gamepromo.io',
        'Authorization': f'Bearer {client_token}'
    }
    data = {
        'promoId': PROMO_ID
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('promoCode')

def is_subscribed(user_id):
    url = f'https://api.telegram.org/bot{CHANNEL_MEMBER_BOT_TOKEN}/getChatMember'
    params = {
        'chat_id': CHANNEL_USERNAME,
        'user_id': user_id
    }
    try:
        response = requests.get(url, params=params)
        result = response.json()
        if result.get('ok'):
            status = result.get('result', {}).get('status')
            return status in ['member', 'administrator', 'creator']
    except requests.RequestException as e:
        print(f"Error checking membership: {e}")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    keyboard = [
        [InlineKeyboardButton("Subscribe to Channel", callback_data='subscribe')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Hello {user.first_name}! Please use the button below to subscribe to our channel.", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == 'subscribe':
        await query.edit_message_text(f"Please confirm that you have subscribed to our channel: {CHANNEL_USERNAME}. Reply with /confirm to proceed.")

    elif data == 'get_code':
        if is_subscribed(user_id):
            await query.edit_message_text("Generating your codes. Please wait...")
            keys = []
            for _ in range(4):
                client_id = generate_client_id()
                client_token = login(client_id)
                while not emulate_progress(client_token):
                    sleep(EVENTS_DELAY * delay_random())
                key = generate_key(client_token)
                keys.append(key if key else 'Failed to generate key')

            keys_text = "\n".join(f"Key {i+1}: `{key}`" for i, key in enumerate(keys))
            await query.edit_message_text(f"Here are your codes:\n{keys_text}", parse_mode='MarkdownV2')
        else:
            await query.edit_message_text(f"You need to subscribe to the channel {CHANNEL_USERNAME} to get the code. Please confirm your subscription by sending /confirm.")

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if is_subscribed(user_id):
        keyboard = [
            [InlineKeyboardButton("Get Code", callback_data='get_code')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Thank you for confirming your subscription! Click the button below to get your code.", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"You need to subscribe to the channel {CHANNEL_USERNAME} to get the code. Please subscribe and send /confirm again.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    main()
