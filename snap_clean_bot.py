import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = '8428733956:AAFpRMPc5yL98m-HwMemSQ5w2lyjgYybMyM'
REMOVE_BG_API_KEY = 'xHe7tNo1UGsXDcjgoz8gXDoQ'
TELEGRAM_CHANNEL_URL = 'https://t.me/MrTools_BD'
ADMIN_USER_ID = 1875687264  # <--- IMPORTANT: REPLACE with your personal Telegram User ID
DEVELOPER_USERNAME = "@Mojibrsm"

# --- Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Conversation Handler States ---
CHOOSING_QUALITY, CHOOSING_FORMAT = range(2)

# --- Bot Data Initialization ---
def setup_bot_data(dispatcher):
    """Initialize bot_data structure for storing user info."""
    if 'users' not in dispatcher.bot_data:
        dispatcher.bot_data['users'] = {}

# --- Helper Function to track users ---
def track_user(update: Update, context: CallbackContext):
    """Saves or updates user info for admin panel."""
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
        "I'm SnapCleanBot, your go-to bot for instantly removing backgrounds.\n\n"
        "To get started, just **reply** to any photo with the `/remove` command.\n\n"
        "Type /help to see all available commands."
    )
    update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

def help_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    help_text = (
        "✨ **How to Use SnapCleanBot** ✨\n\n"
        "1️⃣ Send any image to this chat.\n"
        "2️⃣ Reply to that image with the command `/remove`.\n"
        "3️⃣ I will process it and send you the clean image!\n\n"
        "**Available Commands:**\n"
        "/start - Welcome message\n"
        "/help - Shows this help message\n"
        "/remove - Removes the background from a photo\n"
        "/quality - Change output image quality (HD/Standard)\n"
        "/format - Choose output format (PNG/JPG)\n"
        "/about - Learn more about me\n"
        "/privacy - View our Privacy Policy\n"
        "/feedback - Send your feedback to the developer\n"
        "/donate - Support the project\n"
        "/join - Get the link to our community channel\n"
        "/contact - Developer's contact info"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def about_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    about_text = (
        "**About SnapCleanBot**\n\n"
        "SnapCleanBot is a user-friendly Telegram bot designed to make background removal quick and effortless. "
        "Powered by the remove.bg API, it delivers high-quality results in just a few seconds."
    )
    update.message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)

def privacy_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    privacy_text = (
        "**Privacy Policy**\n\n"
        "1. We do not store your images. All photos are sent to the remove.bg API, processed, and then sent back to you. They are not saved on our servers.\n"
        "2. We do not collect any personal data other than your Telegram user ID for bot functionality.\n"
        "3. Your feedback and interactions are used solely to improve the bot."
    )
    update.message.reply_text(privacy_text, parse_mode=ParseMode.MARKDOWN)

def feedback_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    feedback_text = (
        "Got feedback or a feature request? I'd love to hear it!\n\n"
        f"Please send your thoughts directly to my developer: {DEVELOPER_USERNAME}"
    )
    update.message.reply_text(feedback_text)

def donate_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    donate_text = (
        "Thank you for considering supporting SnapCleanBot! ❤️\n\n"
        "Your donations help cover server costs and API fees, keeping the bot running smoothly for everyone.\n\n"
        "*(You can add your donation links here, e.g., PayPal, Patreon, or a crypto address)*"
    )
    update.message.reply_text(donate_text)

def contact_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    contact_text = (
        "**Developer Contact**\n\n"
        "Feel free to reach out to the developer for any inquiries:\n\n"
        "👤 **Name:** Mojib rsm\n"
        "✈️ **Telegram:** {DEVELOPER_USERNAME}"
    )
    update.message.reply_text(contact_text, parse_mode=ParseMode.MARKDOWN)

def join_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)
    keyboard = [[InlineKeyboardButton("🚀 Join Our Channel! 🚀", url=TELEGRAM_CHANNEL_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Stay updated with the latest news and features by joining our channel!',
        reply_markup=reply_markup
    )

def admin_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        update.message.reply_text("Sorry, this command is for the bot administrator only.")
        return

    users_data = context.bot_data.get('users', {})
    total_users = len(users_data)
    total_requests = sum(user['requests'] for user in users_data.values())

    admin_text = (
        f"**👑 Admin Panel 👑**\n\n"
        f"**Total Users:** {total_users}\n"
        f"**Total API Requests:** {total_requests}\n\n"
        f"**Recent Users:**\n"
    )

    # List last 5 users for brevity
    recent_users = list(users_data.values())[-5:]
    for user in recent_users:
        admin_text += f"- {user.get('first_name')} (@{user.get('username')}) - Requests: {user.get('requests')}\n"

    update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)

# --- Settings Conversations ---

def quality_command(update: Update, context: CallbackContext) -> int:
    """Asks user to choose a quality."""
    track_user(update, context)
    keyboard = [
        [InlineKeyboardButton("Standard (Free)", callback_data='standard')],
        [InlineKeyboardButton("HD (Requires remove.bg Credits)", callback_data='hd')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose your desired output quality:", reply_markup=reply_markup)
    return CHOOSING_QUALITY

def quality_choice(update: Update, context: CallbackContext) -> int:
    """Stores the quality choice."""
    query = update.callback_query
    query.answer()
    quality = query.data
    context.user_data['quality'] = 'full' if quality == 'hd' else 'auto'
    quality_text = "HD (4K)" if quality == 'hd' else "Standard"

    query.edit_message_text(text=f"✅ Quality set to: **{quality_text}**")
    return ConversationHandler.END

def format_command(update: Update, context: CallbackContext) -> int:
    """Asks user to choose a format."""
    track_user(update, context)
    keyboard = [
        [InlineKeyboardButton("PNG (Transparent)", callback_data='png')],
        [InlineKeyboardButton("JPG (White Background)", callback_data='jpg')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose your desired output format:", reply_markup=reply_markup)
    return CHOOSING_FORMAT

def format_choice(update: Update, context: CallbackContext) -> int:
    """Stores the format choice."""
    query = update.callback_query
    query.answer()
    context.user_data['format'] = query.data
    query.edit_message_text(text=f"✅ Format set to: **{query.data.upper()}**")
    return ConversationHandler.END

# --- Core Functionality ---

def remove_background_command(update: Update, context: CallbackContext) -> None:
    track_user(update, context)

    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        update.message.reply_text("💡 **Hint:** Please reply to a photo with the `/remove` command.")
        return

    # Increment user's request count
    context.bot_data['users'][update.effective_user.id]['requests'] += 1
    
    processing_message = update.message.reply_text('✨ Processing your image, please wait...')

    try:
        photo_file = update.message.reply_to_message.photo[-1].get_file()
        photo_path = f'{update.effective_chat.id}_input.jpg'
        photo_file.download(photo_path)

        # Get user preferences or use defaults
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
                    caption=f'Here is your image! (Quality: {output_size.replace("auto", "Standard")}, Format: {output_format.upper()})'
                )
            os.remove(output_filename)
        else:
            error_details = response.json()
            error_message = error_details.get('errors', [{}])[0].get('title', 'Unknown error')
            update.message.reply_text(f"API Error: {error_message}. If using HD, check your remove.bg credits.")

    except Exception as e:
        logger.error(f"Error in remove_background: {e}")
        update.message.reply_text(f"An unexpected error occurred. Please try again later.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=processing_message.message_id
        )

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Action cancelled.')
    return ConversationHandler.END

# --- Main Bot Setup ---
def main() -> None:
    """Starts and runs the bot."""
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Initialize bot data storage
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

    # --- Register Command Handlers ---
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("about", about_command))
    dispatcher.add_handler(CommandHandler("privacy", privacy_command))
    dispatcher.add_handler(CommandHandler("feedback", feedback_command))
    dispatcher.add_handler(CommandHandler("donate", donate_command))
    dispatcher.add_handler(CommandHandler("contact", contact_command))
    dispatcher.add_handler(CommandHandler("join", join_command))
    dispatcher.add_handler(CommandHandler("admin", admin_command))
    dispatcher.add_handler(CommandHandler("remove", remove_background_command))
    
    # Add conversation handlers
    dispatcher.add_handler(quality_conv_handler)
    dispatcher.add_handler(format_conv_handler)
    
    # A generic message handler to guide users who just send a photo
    dispatcher.add_handler(MessageHandler(Filters.photo, lambda u,c: u.message.reply_text("Nice photo! Now reply to it with /remove to edit it.")))


    # Start the Bot
    updater.start_polling()
    print("SnapCleanBot is now running with advanced features...")
    updater.idle()

if __name__ == '__main__':
    main()
