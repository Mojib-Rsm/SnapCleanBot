Of course! This is a great idea to make the bot much more user-friendly.

This new workflow will be:

Auto-Remove: The user just sends a photo. The bot will automatically process it without needing any command.

Persistent Menu: The bot will show a permanent menu button at the bottom of the chat for easy access to other commands like /help and /quality.

Here are the ready-to-use files for this improved bot.

1. snap_clean_bot.py

This is the updated main script. It now handles photos automatically and displays the menu.

code
Python
download
content_copy
expand_less

import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)

# --- Configuration (Loaded from Environment Variables) ---
try:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    REMOVE_BG_API_KEY = os.getenv('REMOVE_BG_API_KEY')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
    TELEGRAM_CHANNEL_URL = os.getenv('TELEGRAM_CHANNEL_URL', 'https://t.me/MrTools_BD')
    DEVELOPER_USERNAME = os.getenv('DEVELOPER_USERNAME', '@Mojibrsm')
except (TypeError, ValueError) as e:
    print(f"CRITICAL ERROR: Environment variable not set correctly - {e}. Please check your Railway variables.")
    if any(v is None for v in [TELEGRAM_BOT_TOKEN, REMOVE_BG_API_KEY, os.getenv('ADMIN_USER_ID')]):
        exit()


# --- Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Conversation Handler States ---
CHOOSING_QUALITY, CHOOSING_FORMAT = range(2)

# --- Persistent Menu Keyboard ---
main_menu_keyboard = [
    ['/quality', '/format'],
    ['/help', '/contact']
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)

# --- Bot Data Initialization ---
def setup_bot_data(dispatcher):
    if 'users' not in dispatcher.bot_data:
        dispatcher.bot_data['users'] = {}

# --- Helper Function to track users ---
def track_user(update: Update, context: CallbackContext):
    if not update or not update.effective_user:
        return
    user_id = update.effective_user.id
    if user_id not in context.bot_data['users']:
        context.bot_data['users'][user_id] = {
            'first_name': update.effective_user.first_name,
            'username': update.effective_user.username,
            'requests': 0
        }

# --- Command Handlers ---
def start_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    user = update.effective_user
    welcome_message = (
        f"Hey {user.first_name}! 👋\n\n"
        "I'm SnapCleanBot. Just send me any photo, and I'll automatically remove the background for you!\n\n"
        "Use the menu buttons below to change settings or get help."
    )
    update.message.reply_text(welcome_message, reply_markup=main_menu_markup)

def help_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    help_text = (
        "✨ **How to Use SnapCleanBot** ✨\n\n"
        "It's simple! Just send any photo directly to this chat.\n\n"
        "The bot will automatically process it and send back the image with the background removed.\n\n"
        "**Menu Commands:**\n"
        "**/quality**: Change output image quality (HD/Standard).\n"
        "**/format**: Choose output format (PNG/JPG).\n"
        "**/contact**: Get the developer's contact info.\n"
        "**/help**: Shows this message again."
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_markup)

def contact_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    contact_text = (
        "**Developer Contact**\n\n"
        "Feel free to reach out to the developer for any inquiries:\n\n"
        f"👤 **Name:** Mojib rsm\n"
        f"✈️ **Telegram:** {DEVELOPER_USERNAME}"
    )
    update.message.reply_text(contact_text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_markup)

def admin_command(update: Update, context: CallbackContext) -> None:
    # This command remains hidden and works as before
    if update.effective_user.id != ADMIN_USER_ID:
        update.message.reply_text("Sorry, this command is for the bot administrator only.")
        return
    users_data = context.bot_data.get('users', {})
    total_users = len(users_data)
    total_requests = sum(user.get('requests', 0) for user in users_data.values())
    admin_text = f"👑 **Admin Panel** 👑\n\n👥 **Total Users:** {total_users}\n🔄 **Total Requests:** {total_requests}"
    update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)


# --- Settings Conversations ---
def quality_command(update: Update, context: CallbackContext) -> int:
    track_user(update, context)
    keyboard = [
        [InlineKeyboardButton("Standard (Free)", callback_data='standard')],
        [InlineKeyboardButton("HD (Requires remove.bg Credits)", callback_data='hd')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose your desired output quality:", reply_markup=reply_markup)
    return CHOOSING_QUALITY

def quality_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    quality = query.data
    context.user_data['quality'] = '4k' if quality == 'hd' else 'auto'
    quality_text = "HD (4K)" if quality == 'hd' else "Standard"
    query.edit_message_text(text=f"✅ Quality set to: **{quality_text}**", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

def format_command(update: Update, context: CallbackContext) -> int:
    track_user(update, context)
    keyboard = [
        [InlineKeyboardButton("PNG (Transparent)", callback_data='png')],
        [InlineKeyboardButton("JPG (White Background)", callback_data='jpg')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose your desired output format:", reply_markup=reply_markup)
    return CHOOSING_FORMAT

def format_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    context.user_data['format'] = query.data
    query.edit_message_text(text=f"✅ Format set to: **{query.data.upper()}**", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


# --- Core Functionality ---
def auto_remove_background(update: Update, context: CallbackContext) -> None:
    """Handles photo messages to automatically remove the background."""
    track_user(update, context)
    context.bot_data['users'][update.effective_user.id]['requests'] += 1
    
    processing_message = update.message.reply_text('✨ Processing your image, please wait...')
    photo_path = f'{update.effective_chat.id}_input.jpg'

    try:
        photo_file = update.message.photo[-1].get_file()
        photo_file.download(photo_path)

        output_size = context.user_data.get('quality', 'auto')
        output_format = context.user_data.get('format', 'png')

        with open(photo_path, 'rb') as image_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': output_size, 'format': output_format},
                headers={'X-Api-Key': REMOVE_BG_API_KEY},
                timeout=45
            )

        if response.status_code == requests.codes.ok:
            output_filename = f'SnapCleaned.{output_format}'
            with open(output_filename, 'wb') as out:
                out.write(response.content)

            with open(output_filename, 'rb') as final_image:
                context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=final_image,
                    filename=output_filename,
                    caption=f'Here is your image!'
                )
            os.remove(output_filename)
        else:
            error_details = response.json()
            error_message = error_details.get('errors', [{}])[0].get('title', 'Authorization failed')
            update.message.reply_text(f"API Error: {error_message}. Please check that your remove.bg API Key is correct.")

    except Exception as e:
        logger.error(f"Error in auto_remove_background: {e}")
        update.message.reply_text(f"An unexpected error occurred. Please try again later.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=processing_message.message_id
        )

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Action cancelled.', reply_markup=main_menu_markup)
    return ConversationHandler.END

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    setup_bot_data(dispatcher)

    # Conversation handlers for settings
    quality_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('quality', quality_command)],
        states={CHOOSING_QUALITY: [CallbackQueryHandler(quality_choice)]},
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    format_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('format', format_command)],
        states={CHOOSING_FORMAT: [CallbackQueryHandler(format_choice)]},
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("contact", contact_command))
    dispatcher.add_handler(CommandHandler("admin", admin_command))
    dispatcher.add_handler(quality_conv_handler)
    dispatcher.add_handler(format_conv_handler)
    
    # This is the new main handler for photos
    dispatcher.add_handler(MessageHandler(Filters.photo, auto_remove_background))
    
    updater.start_polling()
    print("SnapCleanBot (Auto-Remove Version) is now running...")
    updater.idle()

if __name__ == '__main__':
    main()
2. requirements.txt

This file remains the same. It lists the necessary libraries for Railway to install.

code
Text
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
python-telegram-bot==13.15
requests
3. Procfile

This file also remains the same. It tells Railway how to run your bot.

code
Text
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
worker: python snap_clean_bot.py
How to Deploy the New Version

Replace your code: Overwrite your old snap_clean_bot.py file with the new code provided above. The other two files (requirements.txt and Procfile) do not need to be changed.

Push to GitHub: Commit the change and push it to your repository.

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
git add snap_clean_bot.py
git commit -m "feat: Implement auto-remove and menu buttons"
git push

Check Railway: Railway will automatically detect the push and deploy the new version.

Test the Bot: Go to Telegram. You may need to restart the bot by typing /start to see the new menu buttons. Then, just send it a photo and it should work automatically
