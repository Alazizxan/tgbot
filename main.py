import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, JobQueue
import datetime
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# .env faylidan muhim ma'lumotlarni yuklash
load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
ADMIN_ID = int(os.getenv('ADMIN_ID'))
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
WEEKLY_PRICE = int(os.getenv('WEEKLY_PRICE'))
MONTHLY_PRICE = int(os.getenv('MONTHLY_PRICE'))
SUPPORT_GROUP_LINK = os.getenv('SUPPORT_GROUP_LINK')
FEEDBACK_CHANNEL_LINK = os.getenv('FEEDBACK_CHANNEL_LINK')

# MongoDB ulanish ma'lumotlari
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')

# MongoDB-ga ulanish
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db['users']

# Foydalanuvchi ma'lumotlarini olish funksiyasi
def get_user(user_id):
    return users_collection.find_one({'_id': user_id})

# Foydalanuvchi ma'lumotlarini saqlash funksiyasi
def save_user(user_data):
    users_collection.update_one({'_id': user_data['_id']}, {'$set': user_data}, upsert=True)

# Multilingual support
LANGUAGES = {
    'en': {
        'welcome': "🎉 Welcome to our bot! 🎉\n\nWith this bot, you can subscribe to our special channel. 📲\nPress 'Subscribe' to subscribe. 📝\nPress 'My Subscriptions' to view your subscription status. 📋\nPress 'Channel' to visit our channel. 🔗\nPress 'Change Language' to change the interface language. 🌐",
        'subscribe': "Subscribe 📝",
        'my_subscriptions': "My Subscriptions 📋",
        'channel': "Channel 🔗",
        'change_language': "Change Language 🌐",
        'subscription_types': "Subscription types:\n\nWeekly subscription: ${} 🗓️\nMonthly subscription: ${} 📅\n\nPlease select a subscription type:",
        'weekly': "Weekly subscription 🗓️",
        'monthly': "Monthly subscription 📅",
        'back': "Back 🔙",
        'active_subscription': "Your subscription is valid until {}. ✅",
        'no_active_subscription': "You don't have an active subscription. ❌",
        'payment_info': "{} subscription payment: ${} 💵\n\nUSDT TRC20 wallet address:\n`{}` 💰\n\nPlease send the receipt after making the payment. 🧾",
        'receipt_sent': "Payment receipt sent to admin. Please wait for confirmation. ⏳",
        'select_plan_first': "Please select a subscription plan first. 📋",
        'payment_confirmed': "Your payment has been confirmed. Please join the channel: 🎉",
        'payment_rejected': "Unfortunately, the payment was not processed. Please make the payment again or contact the admin. ⚠️",
        'subscription_expired': "Your subscription has expired and you have been removed from the channel. Please renew your subscription. 🔄",
        'select_language': "Please select your preferred language: 🌐",
    },
    'ru': {
        'welcome': "🎉 Добро пожаловать в наш бот! 🎉\n\nС помощью этого бота вы можете подписаться на наш специальный канал. 📲\nНажмите 'Подписаться' для подписки. 📝\nНажмите 'Мои подписки' для просмотра статуса подписки. 📋\nНажмите 'Канал' для перехода на наш канал. 🔗\nНажмите 'Изменить язык' для смены языка интерфейса. 🌐",
        'subscribe': "Подписаться 📝",
        'my_subscriptions': "Мои подписки 📋",
        'channel': "Канал 🔗",
        'change_language': "Изменить язык 🌐",
        'subscription_types': "Типы подписки:\n\nНедельная подписка: ${} 🗓️\nМесячная подписка: ${} 📅\n\nПожалуйста, выберите тип подписки:",
        'weekly': "Недельная подписка 🗓️",
        'monthly': "Месячная подписка 📅",
        'back': "Назад 🔙",
        'active_subscription': "Ваша подписка действительна до {}. ✅",
        'no_active_subscription': "У вас нет активной подписки. ❌",
        'payment_info': "Оплата за {} подписку: ${} 💵\n\nАдрес кошелька USDT TRC20:\n`{}` 💰\n\nПожалуйста, отправьте чек после оплаты. 🧾",
        'receipt_sent': "Чек об оплате отправлен администратору. Пожалуйста, ожидайте подтверждения. ⏳",
        'select_plan_first': "Пожалуйста, сначала выберите план подписки. 📋",
        'payment_confirmed': "Ваш платеж подтвержден. Пожалуйста, присоединитесь к каналу: 🎉",
        'payment_rejected': "К сожалению, платеж не был обработан. Пожалуйста, произведите оплату снова или свяжитесь с администратором. ⚠️",
        'subscription_expired': "Срок действия вашей подписки истек, и вы были удалены из канала. Пожалуйста, обновите вашу подписку. 🔄",
        'select_language': "Пожалуйста, выберите предпочитаемый язык: 🌐",
    },
    'uz': {
        'welcome': "🎉 Botimizga xush kelibsiz! 🎉\n\nUshbu bot orqali siz maxsus kanalimizga obuna bo'lishingiz mumkin. 📲\n'Obuna bo'lish' tugmasini bosing. 📝\n'Obunalarim' tugmasini bosib obuna holatini ko'ring. 📋\n'Kanal' tugmasini bosib kanalimizga o'ting. 🔗\n'Tilni o'zgartirish' tugmasini bosib interfeys tilini o'zgartiring. 🌐",
        'subscribe': "Obuna bo'lish 📝",
        'my_subscriptions': "Obunalarim 📋",
        'channel': "Kanal 🔗",
        'change_language': "Tilni o'zgartirish 🌐",
        'subscription_types': "Obuna turlari:\n\nHaftalik obuna: ${} 🗓️\nOylik obuna: ${} 📅\n\nIltimos, obuna turini tanlang:",
        'weekly': "Haftalik obuna 🗓️",
        'monthly': "Oylik obuna 📅",
        'back': "Orqaga 🔙",
        'active_subscription': "Sizning obunangiz {} gacha amal qiladi. ✅",
        'no_active_subscription': "Sizda hozirda faol obuna yo'q. ❌",
        'payment_info': "{} obuna uchun to'lov: ${} 💵\n\nUSDT TRC20 hamyon manzili:\n`{}` 💰\n\nIltimos, to'lovni amalga oshirgach, chekni yuboring. 🧾",
        'receipt_sent': "To'lov cheki adminga yuborildi. Iltimos, tasdiqlanishini kuting. ⏳",
        'select_plan_first': "Iltimos, avval obuna turini tanlang. 📋",
        'payment_confirmed': "To'lovingiz tasdiqlandi. Iltimos, kanalga qo'shiling: 🎉",
        'payment_rejected': "Afsuski, to'lov amalga oshirilmadi. Iltimos, to'lovni qayta amalga oshiring yoki admin bilan bog'laning. ⚠️",
        'subscription_expired': "Sizning obunangiz tugadi va kanaldan olib tashlandingiz. Iltimos, obunani yangilang. 🔄",
        'select_language': "Iltimos, afzal ko'rgan tilingizni tanlang: 🌐",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        user = {'_id': user_id, 'language': 'en'}
        save_user(user)

    lang = user['language']
    keyboard = [
        [InlineKeyboardButton(LANGUAGES[lang]['subscribe'], callback_data="show_subscription"),
         InlineKeyboardButton(LANGUAGES[lang]['my_subscriptions'], callback_data="my_subscriptions")],
        [InlineKeyboardButton(LANGUAGES[lang]['channel'], url=FEEDBACK_CHANNEL_LINK),
         InlineKeyboardButton(LANGUAGES[lang]['change_language'], callback_data="change_language")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(LANGUAGES[lang]['welcome'], reply_markup=reply_markup)

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
         InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru"),
         InlineKeyboardButton("O'zbek 🇺🇿", callback_data="set_lang_uz")],
        [InlineKeyboardButton(LANGUAGES[user['language']]['back'], callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        LANGUAGES[user['language']]['select_language'],
        reply_markup=reply_markup
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lang = query.data.split('_')[2]
    user = get_user(query.from_user.id)
    user['language'] = lang
    save_user(user)

    await start(update, context)

async def show_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    lang = user['language']
    keyboard = [
        [InlineKeyboardButton(LANGUAGES[lang]['weekly'], callback_data="weekly"),
         InlineKeyboardButton(LANGUAGES[lang]['monthly'], callback_data="monthly")],
        [InlineKeyboardButton(LANGUAGES[lang]['back'], callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        LANGUAGES[lang]['subscription_types'].format(WEEKLY_PRICE, MONTHLY_PRICE),
        reply_markup=reply_markup
    )

async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    lang = user['language']
    keyboard = [[InlineKeyboardButton(LANGUAGES[lang]['back'], callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'end_date' in user:
        end_date = user['end_date']
        await query.edit_message_text(
            LANGUAGES[lang]['active_subscription'].format(end_date.strftime('%Y-%m-%d %H:%M:%S')),
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            LANGUAGES[lang]['no_active_subscription'],
            reply_markup=reply_markup
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "start":
        await start(update, context)
    elif query.data == "show_subscription":
        await show_subscription(update, context)
    elif query.data == "my_subscriptions":
        await my_subscriptions(update, context)
    elif query.data == "change_language":
        await change_language(update, context)
    elif query.data.startswith("set_lang_"):
        await set_language(update, context)
    elif query.data in ["weekly", "monthly"]:
        user = get_user(query.from_user.id)
        user["plan"] = query.data
        user["price"] = WEEKLY_PRICE if query.data == "weekly" else MONTHLY_PRICE
        save_user(user)
        await send_payment_info(query, user["price"], query.data)
    elif query.data.startswith("admin_confirm_"):
        await admin_confirm_payment(update, context)
    elif query.data.startswith("admin_reject_"):
        await admin_reject_payment(update, context)

async def send_payment_info(query, price, plan):
    user = get_user(query.from_user.id)
    lang = user['language']
    keyboard = [[InlineKeyboardButton(LANGUAGES[lang]['back'], callback_data="show_subscription")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        LANGUAGES[lang]['payment_info'].format(LANGUAGES[lang][plan], price, WALLET_ADDRESS),
        reply_markup=reply_markup
    )

async def handle_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user = get_user(user_id)
    lang = user['language']
    if "plan" in user:
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data=f"admin_confirm_{user_id}"),
             InlineKeyboardButton("Reject", callback_data=f"admin_reject_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"User info:\nTelegram ID: {user_id}\nUsername: @{username}\nPlan: {user['plan']}, Price: ${user['price']}",
            reply_markup=reply_markup
        )
        await update.message.reply_text(LANGUAGES[lang]['receipt_sent'])
    else:
        await update.message.reply_text(LANGUAGES[lang]['select_plan_first'])

async def admin_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, action, user_id = query.data.split('_')
    user_id = int(user_id)
    user = get_user(user_id)
    lang = user['language']

    try:
        invite_link = await context.bot.create_chat_invite_link(chat_id=CHANNEL_ID, member_limit=1)
        keyboard = [[InlineKeyboardButton(LANGUAGES[lang]['channel'], url=invite_link.invite_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if 'plan' in user:
            if user['plan'] == 'weekly':
                end_date = datetime.datetime.now() + datetime.timedelta(weeks=1)
            else:
                end_date = datetime.datetime.now() + datetime.timedelta(days=30)
            user['end_date'] = end_date
            save_user(user)

            await context.bot.send_message(
                chat_id=user_id,
                text=LANGUAGES[lang]['payment_confirmed'],
                reply_markup=reply_markup
            )

            username = user.get('username') or f"user_{user_id}"
            await query.edit_message_text(
                f"@{username} subscribed. Subscription end date: {end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            await query.edit_message_text("User information not found.")

    except Exception as e:
        logger.error(f"Error in admin confirmation process: {e}")
        await query.edit_message_text(f"An error occurred: {str(e)}")

async def admin_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, action, user_id = query.data.split('_')
    user_id = int(user_id)
    user = get_user(user_id)
    lang = user['language']

    if user:
        keyboard = [[InlineKeyboardButton(LANGUAGES[lang]['back'], callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user_id,
            text=LANGUAGES[lang]['payment_rejected'],
            reply_markup=reply_markup
        )
        user.pop('plan', None)
        user.pop('price', None)
        save_user(user)
        await query.edit_message_text("Payment rejected and user notified.")
    else:
        await query.edit_message_text("User information not found.")

async def check_subscriptions(context: ContextTypes.DEFAULT_TYPE) -> None:
    current_time = datetime.datetime.now()
    expired_users = users_collection.find({'end_date': {'$lt': current_time}})
    for user in expired_users:
        await remove_user_from_channel(context, user['_id'])
        users_collection.update_one({'_id': user['_id']}, {'$unset': {'end_date': ''}})

async def remove_user_from_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    try:
        bot = context.bot
        await bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        user = get_user(user_id)
        lang = user['language']
        await bot.send_message(chat_id=user_id, text=LANGUAGES[lang]['subscription_expired'])
    except Exception as e:
        logger.error(f"Error removing user from channel: {e}")

async def testchannellink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = get_user(update.effective_user.id)
        lang = user['language']
        invite_link = await context.bot.create_chat_invite_link(chat_id=CHANNEL_ID, member_limit=1)
        keyboard = [[InlineKeyboardButton(LANGUAGES[lang]['channel'], url=invite_link.invite_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text('Kanalga ulanish:', reply_markup=reply_markup)
        logger.info(f"Invite link created and sent to user {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Error in testchannellink command: {e}")
        await update.message.reply_text('Kechirasiz, xatolik yuz berdi.')

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("commandcomanderbuild", testchannellink))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO & filters.USER, handle_payment_receipt))

    job_queue: JobQueue = application.job_queue
    job_queue.run_repeating(check_subscriptions, interval=datetime.timedelta(hours=1))

    application.run_polling()

if __name__ == "__main__":
    main()