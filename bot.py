import os
import threading

import telebot
from telebot import types
from flask import Flask, request


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")

ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
]

CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CONFIG_FILE = os.getenv("CONFIG_FILE", "TDM.conf")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

pending_orders = {}


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        "🟢 وایرگارد گیمینگ 🎮",
        "🟢 پشتیبانی 🎧"
    )
    kb.row("❓ سؤالات متداول")
    return kb


def join_menu():
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "📢 عضویت در کانال",
            url=CHANNEL_LINK
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "✅ عضو شدم",
            callback_data="check_join"
        )
    )

    return kb


def is_member(user_id):
    try:
        member = bot.get_chat_member(
            CHANNEL_ID,
            user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as e:
        print("Join check error:", e)
        return False
def send_join_message(chat_id):
    bot.send_message(
        chat_id,
        "🔒 برای استفاده از ربات ابتدا باید "
        "در کانال ما عضو شوید.\n\n"
        "1️⃣ روی «عضویت در کانال» بزنید.\n"
        "2️⃣ عضو کانال شوید.\n"
        "3️⃣ سپس روی «عضو شدم» بزنید.",
        reply_markup=join_menu()
    )


@bot.message_handler(commands=["start"])
def start(message):
    print(
        "START received:",
        message.from_user.id
    )

    if not is_member(message.from_user.id):
        send_join_message(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        "سلام 👋\n\n"
        "به ربات فروش WireGuard خوش آمدید 💚\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "check_join"
)
def check_join(call):
    if is_member(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "عضویت شما تأیید شد ✅"
        )

        bot.send_message(
            call.message.chat.id,
            "✅ عضویت شما تأیید شد.\n\n"
            "حالا می‌توانید از ربات استفاده کنید.",
            reply_markup=main_menu()
        )

    else:
        bot.answer_callback_query(
            call.id,
            "❌ هنوز عضو کانال نشده‌اید.",
            show_alert=True
        )


@bot.message_handler(
    func=lambda message:
    message.text == "🟢 وایرگارد گیمینگ 🎮"
)
def gaming(message):
    if not is_member(message.from_user.id):
        send_join_message(message.chat.id)
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎮 ۱۰ گیگ — ۱۰۰,۰۰۰ تومان",
            callback_data="plan_10"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🎮 ۲۰ گیگ — ۲۰۰,۰۰۰ تومان",
            callback_data="plan_20"
        )
    )

    bot.send_message(
        message.chat.id,
        "🎮 پلن‌های WireGuard گیمینگ\n\n"
        "یکی از پلن‌های زیر را انتخاب کنید:",
        reply_markup=kb
    )


def show_payment(chat_id, user_id, plan, price):
    pending_orders[user_id] = {
        "plan": plan,
        "price": price
    }

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "📸 ارسال فیش پرداخت",
            callback_data="send_receipt"
        )
    )

    bot.send_message(
        chat_id,
        f"📦 پلن انتخابی: {plan}\n\n"
        f"💰 مبلغ: {price:,} تومان\n\n"
        f"💳 شماره کارت:\n`{CARD_NUMBER}`\n\n"
        "پس از پرداخت، روی دکمه زیر بزنید "
        "و عکس فیش را ارسال کنید.",
        parse_mode="Markdown",
        reply_markup=kb
    )
@bot.callback_query_handler(
    func=lambda call: call.data == "plan_10"
)
def plan_10(call):
    show_payment(
        call.message.chat.id,
        call.from_user.id,
        "۱۰ گیگ",
        100000
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data == "plan_20"
)
def plan_20(call):
    show_payment(
        call.message.chat.id,
        call.from_user.id,
        "۲۰ گیگ",
        200000
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data == "send_receipt"
)
def send_receipt(call):
    order = pending_orders.get(call.from_user.id)

    if not order:
        bot.answer_callback_query(
            call.id,
            "❌ ابتدا یک پلن را انتخاب کنید.",
            show_alert=True
        )
        return

    bot.send_message(
        call.message.chat.id,
        f"📸 لطفاً عکس فیش پرداخت "
        f"پلن {order['plan']} به مبلغ "
        f"{order['price']:,} تومان را همینجا ارسال کنید."
    )

    bot.answer_callback_query(call.id)


@bot.message_handler(content_types=["photo"])
def receive_receipt(message):
    user = message.from_user
    order = pending_orders.get(user.id)

    if not order:
        bot.send_message(
            message.chat.id,
            "❌ ابتدا از بخش "
            "«وایرگارد گیمینگ» یک پلن انتخاب کنید."
        )
        return

    username = (
        f"@{user.username}"
        if user.username
        else "ندارد"
    )

    caption = (
        "💰 فیش پرداخت جدید\n\n"
        f"📦 پلن: {order['plan']}\n"
        f"💵 مبلغ: {order['price']:,} تومان\n"
        f"👤 نام: {user.first_name}\n"
        f"🆔 آیدی: {user.id}\n"
        f"🔗 Username: {username}"
    )

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✅ تأیید پرداخت",
            callback_data=f"approve_{user.id}"
        ),
        types.InlineKeyboardButton(
            "❌ رد پرداخت",
            callback_data=f"reject_{user.id}"
        )
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=caption,
                reply_markup=kb
            )
        except Exception as e:
            print(
                "Error sending receipt:",
                e
            )

    bot.send_message(
        message.chat.id,
        "✅ فیش شما دریافت شد.\n\n"
        "⏳ منتظر بررسی و تأیید پرداخت باشید."
    )
@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("approve_")
)
def approve_payment(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(
            call.id,
            "❌ شما دسترسی مدیریت ندارید.",
            show_alert=True
        )
        return

    user_id = int(
        call.data.split("_")[1]
    )

    order = pending_orders.get(user_id)

    if order:
        plan_text = order["plan"]
        price_text = f"{order['price']:,}"
    else:
        plan_text = "WireGuard"
        price_text = ""

    try:
        with open(
            CONFIG_FILE,
            "rb"
        ) as file:
            bot.send_document(
                user_id,
                file,
                caption=(
                    "✅ پرداخت شما تأیید شد!\n\n"
                    f"📦 پلن: {plan_text}\n"
                    f"💰 مبلغ: {price_text} تومان\n\n"
                    "📥 فایل WireGuard شما:"
                )
            )

    except FileNotFoundError:
        bot.answer_callback_query(
            call.id,
            "❌ فایل TDM.conf پیدا نشد.",
            show_alert=True
        )
        print("ERROR: TDM.conf not found")
        return

    except Exception as e:
        bot.answer_callback_query(
            call.id,
            "❌ ارسال فایل انجام نشد.",
            show_alert=True
        )
        print("ERROR sending config:", e)
        return

    pending_orders.pop(user_id, None)

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    bot.answer_callback_query(
        call.id,
        "پرداخت تأیید شد و فایل ارسال شد ✅"
    )


@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("reject_")
)
def reject_payment(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(
            call.id,
            "❌ شما دسترسی مدیریت ندارید.",
            show_alert=True
        )
        return

    user_id = int(
        call.data.split("_")[1]
    )

    bot.send_message(
        user_id,
        "❌ پرداخت شما تأیید نشد.\n\n"
        "لطفاً فیش صحیح را ارسال کنید."
    )

    pending_orders.pop(user_id, None)

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    bot.answer_callback_query(
        call.id,
        "پرداخت رد شد ❌"
    )
@bot.message_handler(
    func=lambda message:
    message.text == "🟢 پشتیبانی 🎧"
)
def support(message):
    if not is_member(message.from_user.id):
        send_join_message(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        "🎧 پشتیبانی\n\n"
        "اگر مشکلی دارید، پیام خود را همینجا ارسال کنید."
    )


@bot.message_handler(
    func=lambda message:
    message.text == "❓ سؤالات متداول"
)
def faq(message):
    if not is_member(message.from_user.id):
        send_join_message(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        "❓ سؤالات متداول\n\n"
        "🔹 WireGuard چیست؟\n"
        "یک پروتکل VPN سریع و سبک برای اتصال امن است.\n\n"
        "🔹 بعد از خرید چطور دریافت کنم؟\n"
        "بعد از تأیید پرداخت، فایل TDM.conf برای شما ارسال می‌شود.\n\n"
        "🔹 پرداخت را انجام دادم چه کنم؟\n"
        "عکس فیش پرداخت را برای ربات ارسال کنید.\n\n"
        "🔹 اگر کانفیگ کار نکرد چه کنم؟\n"
        "از بخش 🟢 پشتیبانی 🎧 با پشتیبانی در ارتباط باشید."
    )


@app.get("/")
def health():
    return "WireGuard bot is running.", 200


@app.post("/webhook/<secret>")
def telegram_webhook(secret):
    if secret != WEBHOOK_SECRET:
        return "Forbidden", 403

    try:
        update = telebot.types.Update.de_json(
            request.data.decode("utf-8")
        )
        
        print("UPDATE RECEIVED:", update)
        print("UPDATE RECEIVED:", update)
        print("BEFORE PROCESS")
        bot.process_new_updates([update])
        print("AFTER PROCESS")
       
        return "OK", 200
        
    except Exception as e:
        print("Webhook error:", e)
        return "Bad Request", 400


def set_webhook():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is missing")
        return

    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL is missing")
        return

    if not WEBHOOK_SECRET:
        print("ERROR: WEBHOOK_SECRET is missing")
        return

    webhook_url = (
        f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}"
    )

    try:
        bot.remove_webhook()
        bot.set_webhook(
            url=webhook_url,
            timeout=30
        )
        print("Webhook set successfully")

    except Exception as e:
        print(
            "ERROR setting webhook:",
            e
        )


threading.Thread(
    target=set_webhook,
    daemon=True
).start()
    
