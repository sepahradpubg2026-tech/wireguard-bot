import os, threading
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ['BOT_TOKEN']
WEBHOOK_URL = os.environ['WEBHOOK_URL'].rstrip('/')
WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET']
CHANNEL_ID = int(os.environ.get('CHANNEL_ID','-1001234567890'))
CHANNEL_LINK = os.environ.get('CHANNEL_LINK','https://t.me/+DQOdRTktXu03MTRk')
ADMIN_IDS = [int(x.strip()) for x in os.environ.get('ADMIN_IDS','7821236561,8865473342').split(',') if x.strip()]
CARD_NUMBER = os.environ.get('CARD_NUMBER','YOUR_CARD_NUMBER')
CONFIG_FILE = os.environ.get('CONFIG_FILE','TDM.conf')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
pending_orders = {}

def main_menu():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.row('🟢 وایرگارد گیمینگ 🎮','🟢 پشتیبانی 🎧'); kb.row('❓ سؤالات متداول'); return kb

def join_menu():
    kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton('📢 عضویت در کانال',url=CHANNEL_LINK)); kb.add(types.InlineKeyboardButton('✅ عضو شدم',callback_data='check_join')); return kb

def is_member(uid):
    try: return bot.get_chat_member(CHANNEL_ID,uid).status in ('member','administrator','creator')
    except Exception as e: print('Join check error:',e); return False

def send_join_message(cid):
    bot.send_message(cid,'🔒 برای استفاده از ربات ابتدا باید در کانال ما عضو شوید.\n\n1️⃣ روی «عضویت در کانال» بزنید.\n2️⃣ عضو کانال شوید.\n3️⃣ سپس روی «عضو شدم» بزنید.',reply_markup=join_menu())

@bot.message_handler(commands=['start'])
def start(m):
    if not is_member(m.from_user.id): send_join_message(m.chat.id); return
    bot.send_message(m.chat.id,'سلام 👋\n\nبه ربات فروش WireGuard خوش آمدید 💚\n\nیکی از گزینه‌های زیر را انتخاب کنید:',reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c:c.data=='check_join')
def check_join(c):
    if is_member(c.from_user.id): bot.answer_callback_query(c.id,'عضویت شما تأیید شد ✅'); bot.send_message(c.message.chat.id,'✅ عضویت شما تأیید شد.\n\nحالا می‌توانید از ربات استفاده کنید.',reply_markup=main_menu())
    else: bot.answer_callback_query(c.id,'❌ هنوز عضو کانال نشده‌اید.',show_alert=True)

@bot.message_handler(func=lambda m:m.text=='🟢 وایرگارد گیمینگ 🎮')
def gaming(m):
    if not is_member(m.from_user.id): send_join_message(m.chat.id); return
    kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton('🎮 ۱۰ گیگ — ۱۰۰,۰۰۰ تومان',callback_data='plan_10')); kb.add(types.InlineKeyboardButton('🎮 ۲۰ گیگ — ۲۰۰,۰۰۰ تومان',callback_data='plan_20'))
    bot.send_message(m.chat.id,'🎮 پلن‌های WireGuard گیمینگ\n\nیکی از پلن‌های زیر را انتخاب کنید:',reply_markup=kb)

def show_payment(cid,uid,plan,price):
    pending_orders[uid]={'plan':plan,'price':price}; kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton('📸 ارسال فیش پرداخت',callback_data='send_receipt'))
    bot.send_message(cid,f'📦 پلن انتخابی: {plan}\n\n💰 مبلغ: {price:,} تومان\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n\nپس از پرداخت، روی دکمه زیر بزنید و عکس فیش را ارسال کنید.',parse_mode='Markdown',reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data=='plan_10')
def plan10(c): show_payment(c.message.chat.id,c.from_user.id,'۱۰ گیگ',100000); bot.answer_callback_query(c.id)
@bot.callback_query_handler(func=lambda c:c.data=='plan_20')
def plan20(c): show_payment(c.message.chat.id,c.from_user.id,'۲۰ گیگ',200000); bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c:c.data=='send_receipt')
def send_receipt(c):
    o=pending_orders.get(c.from_user.id)
    if not o: bot.answer_callback_query(c.id,'❌ ابتدا یک پلن را انتخاب کنید.',show_alert=True); return
    bot.send_message(c.message.chat.id,f"📸 لطفاً عکس فیش پرداخت پلن {o['plan']} به مبلغ {o['price']:,} تومان را همینجا ارسال کنید."); bot.answer_callback_query(c.id)

@bot.message_handler(content_types=['photo'])
def receive_receipt(m):
    o=pending_orders.get(m.from_user.id)
    if not o: bot.send_message(m.chat.id,'❌ ابتدا از بخش «وایرگارد گیمینگ» یک پلن انتخاب کنید.'); return
    u=m.from_user; username=f'@{u.username}' if u.username else 'ندارد'
    caption=f'💰 فیش پرداخت جدید\n\n📦 پلن: {o["plan"]}\n💵 مبلغ: {o["price"]:,} تومان\n👤 نام: {u.first_name}\n🆔 آیدی: {u.id}\n🔗 Username: {username}'
    kb=types.InlineKeyboardMarkup(); kb.row(types.InlineKeyboardButton('✅ تأیید پرداخت',callback_data=f'approve_{u.id}'),types.InlineKeyboardButton('❌ رد پرداخت',callback_data=f'reject_{u.id}'))
    for aid in ADMIN_IDS:
        try: bot.send_photo(aid,m.photo[-1].file_id,caption=caption,reply_markup=kb)
        except Exception as e: print('ERROR sending receipt:',e)
    bot.send_message(m.chat.id,'✅ فیش شما دریافت شد.\n\n⏳ منتظر بررسی و تأیید پرداخت باشید.')

@bot.callback_query_handler(func=lambda c:c.data.startswith('approve_'))
def approve(c):
    if c.from_user.id not in ADMIN_IDS: bot.answer_callback_query(c.id,'❌ شما دسترسی مدیریت ندارید.',show_alert=True); return
    uid=int(c.data.split('_')[1]); o=pending_orders.get(uid); plan=o['plan'] if o else 'WireGuard'; price=f'{o["price"]:,}' if o else ''
    try:
        with open(CONFIG_FILE,'rb') as f: bot.send_document(uid,f,caption=f'✅ پرداخت شما تأیید شد!\n\n📦 پلن: {plan}\n💰 مبلغ: {price} تومان\n\n📥 فایل WireGuard شما:')
    except FileNotFoundError: bot.answer_callback_query(c.id,f'❌ فایل {CONFIG_FILE} پیدا نشد.',show_alert=True); return
    except Exception as e: print('ERROR sending config:',e); bot.answer_callback_query(c.id,'❌ ارسال فایل انجام نشد.',show_alert=True); return
    pending_orders.pop(uid,None)
    try: bot.edit_message_reply_markup(c.message.chat.id,c.message.message_id,reply_markup=None)
    except Exception: pass
    bot.answer_callback_query(c.id,'پرداخت تأیید شد و فایل ارسال شد ✅')

@bot.callback_query_handler(func=lambda c:c.data.startswith('reject_'))
def reject(c):
    if c.from_user.id not in ADMIN_IDS: bot.answer_callback_query(c.id,'❌ شما دسترسی مدیریت ندارید.',show_alert=True); return
    uid=int(c.data.split('_')[1]); bot.send_message(uid,'❌ پرداخت شما تأیید نشد.\n\nلطفاً فیش صحیح را ارسال کنید.'); pending_orders.pop(uid,None)
    try: bot.edit_message_reply_markup(c.message.chat.id,c.message.message_id,reply_markup=None)
    except Exception: pass
    bot.answer_callback_query(c.id,'پرداخت رد شد ❌')

@bot.message_handler(func=lambda m:m.text=='🟢 پشتیبانی 🎧')
def support(m):
    if not is_member(m.from_user.id): send_join_message(m.chat.id); return
    bot.send_message(m.chat.id,'🎧 پشتیبانی\n\nاگر مشکلی دارید، پیام خود را همینجا ارسال کنید.')

@bot.message_handler(func=lambda m:m.text=='❓ سؤالات متداول')
def faq(m):
    if not is_member(m.from_user.id): send_join_message(m.chat.id); return
    bot.send_message(m.chat.id,'❓ سؤالات متداول\n\n🔹 WireGuard چیست؟\nیک پروتکل VPN سریع و سبک برای اتصال امن است.\n\n🔹 بعد از خرید چطور دریافت کنم؟\nبعد از تأیید پرداخت، فایل کانفیگ برای شما ارسال می‌شود.\n\n🔹 پرداخت را انجام دادم چه کنم؟\nعکس فیش پرداخت را برای ربات ارسال کنید.\n\n🔹 اگر کانفیگ کار نکرد چه کنم؟\nاز بخش 🟢 پشتیبانی 🎧 با پشتیبانی در ارتباط باشید.')

@app.get('/')
def health(): return 'WireGuard bot is running.',200
@app.post('/webhook/<secret>')
def webhook(secret):
    if secret!=WEBHOOK_SECRET: return 'Forbidden',403
    try:
        update=telebot.types.Update.de_json(request.data.decode('utf-8'))
        threading.Thread(target=bot.process_new_updates,args=([update],),daemon=True).start()
        return 'OK',200
    except Exception as e: print('Webhook error:',e); return 'Bad Request',400

try:
    bot.remove_webhook(); bot.set_webhook(url=f'{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}'); print('Webhook set successfully')
except Exception as e: print('ERROR setting webhook:',e)

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))
