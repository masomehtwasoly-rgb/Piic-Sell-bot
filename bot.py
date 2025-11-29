import json
import os
from datetime import datetime, date
import telebot
from telebot import types
import threading
import time

TOKEN = "8540348371:AAGvKcGIpABiqXoU4NoFHmg74RArhNqWS4o"
bot = telebot.TeleBot(TOKEN)
DATA = "users.json"
STATUS_FILE = "bot_status.json"
FORCE_JOIN_FILE = "force_join.json"
ADMIN_ID = 6880898571

# ================== توابع ذخیره‌سازی ایمن ==================

def safe_load_json(file_path, default):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False)
            return default
    except Exception as e:
        print(f"خطا در بارگذاری {file_path}: {e}")
        return default

def safe_save_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطا در ذخیره {file_path}: {e}")

# ================== مدیریت کاربران ==================
def load_users():
    return safe_load_json(DATA, {})

def save_users(users):
    safe_save_json(DATA, users)

def get_or_create_user(user_id, first_name="کاربر"):
    users = load_users()
    sid = str(user_id)
    if sid not in users:
        users[sid] = {
            "name": first_name,
            "user_id": user_id,
            "balance": 0,
            "photo_count": 0,
            "join_date": datetime.now().strftime("%Y-%m-%d")
        }
        save_users(users)
    return users[sid]

# ================== توابع وضعیت ربات و قفل ==================
def load_bot_status():
    data = safe_load_json(STATUS_FILE, {"is_active": True})
    return data.get("is_active", True)

def save_bot_status(is_active: bool):
    safe_save_json(STATUS_FILE, {"is_active": is_active})

def load_force_join():
    default = {"enabled": False, "channels": []}
    data = safe_load_json(FORCE_JOIN_FILE, default)
    enabled = bool(data.get("enabled", False))
    channels = [ch for ch in data.get("channels", []) if isinstance(ch, str) and ch.startswith("@")]
    return {"enabled": enabled, "channels": channels}

def save_force_join(enabled: bool, channels: list):
    safe_save_json(FORCE_JOIN_FILE, {"enabled": enabled, "channels": channels})

# ================== پیام استارت ==================
def send_welcome_message(chat_id, user_id):
    get_or_create_user(user_id, "کاربر")
    welcome_text = (
        "🌌 *پیک سل | ربات واقعی کسب درامد* 🌌\n"
        "⚡️ *دیگه بی پول نمیمونی !* 👾\n\n"
        "┃ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "┃ 🪐 *کیفیت کهکشانی — فراتر از رقبا*\n"
        "┃ 💸 *واریزی فوری و کسب درآمد بالا — درآمد راحت*\n"
        "┃ 🚀 *سرعت پردازش بالا — بدون تاخیر و دردسر*\n"
        "┃ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📌 *قبل از شروع، حتماً قوانین رو بخون*\n"
        "🖇 : [@pic_gavanin](https://t.me/pic_gavanin)\n\n"
        "🔽 *یک گزینه رو از پایین انتخاب کن*"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=main_menu(user_id), parse_mode="Markdown")

def check_access(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return True
    if not load_bot_status():
        bot.reply_to(message, "🛑 ربات در حال حاضر غیرفعال است.")
        return False
    fj = load_force_join()
    if fj["enabled"] and fj["channels"]:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ch in fj["channels"]:
            markup.add(types.InlineKeyboardButton(f"عضویت در {ch}", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))
        bot.send_message(
            message.chat.id,
            "🔐 برای استفاده از ربات، ابتدا باید در کانال(های) زیر عضو شوید:",
            reply_markup=markup
        )
        return False
    return True

# ================== منوها ==================
def main_menu(user_id):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.add("برداشت موجودی 💳")
    mk.add("موجودی من 💸", "فروش عکس ☑️")
    if user_id == ADMIN_ID:
        mk.add("پنل مدیریت 🔐")
    return mk

def admin_panel_menu():
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.add("📊 آمار ربات")
    mk.add("👤 مدیریت کاربران")  # ✅ دکمه جدید
    mk.add("✉️ پیام همگانی")
    mk.add("✅ ربات روشن", "☑️ ربات خاموش")
    mk.add("🔒قفل ربات")
    mk.add("🔙 بازگشت به منوی اصلی")
    return mk

def cancel_menu():
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("⭕ لغو")
    return mk

# ================== نمایش پنل قفل ربات ==================
def show_force_join_panel(chat_id):
    fj = load_force_join()
    if not fj["channels"]:
        msg = "📭 هیچ کانالی برای عضویت اجباری تنظیم نشده است."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ افزودن کانال جدید", callback_data="add_channel"))
        bot.send_message(chat_id, msg, reply_markup=markup)
        return

    msg = "🔐 کانال‌های عضویت اجباری:\n\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    for ch in fj["channels"]:
        msg += f"• {ch}\n"
        markup.add(
            types.InlineKeyboardButton("❌ حذف", callback_data=f"del_{ch}"),
            types.InlineKeyboardButton(ch, url=f"https://t.me/{ch[1:]}")
        )
    markup.add(types.InlineKeyboardButton("➕ افزودن کانال جدید", callback_data="add_channel"))
    markup.add(types.InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_admin"))
    bot.send_message(chat_id, msg, reply_markup=markup)

# ================== 👤 مدیریت کاربران ==================

@bot.message_handler(func=lambda m: m.text == "👤 مدیریت کاربران")
def manage_users_start(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.send_message(
        m.chat.id,
        "🆔 *آیدی عددی کاربر را وارد کنید:*",
        reply_markup=cancel_menu(),
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(m, manage_users_get_id)

def manage_users_get_id(m):
    if m.text == "⭕ لغو":
        bot.send_message(m.chat.id, "❌ عملیات لغو شد.", reply_markup=admin_panel_menu())
        return

    try:
        user_id = int(m.text.strip())
    except:
        bot.send_message(m.chat.id, "❌ لطفاً یک آیدی عددی معتبر وارد کنید.")
        bot.register_next_step_handler(m, manage_users_get_id)
        return

    # ذخیره آیدی موقت در حافظه (در کاربر ادمین)
    admin_data = get_or_create_user(m.from_user.id, "ادمین")
    admin_data["target_user_id"] = user_id
    users = load_users()
    users[str(m.from_user.id)] = admin_data
    save_users(users)

    bot.send_message(
        m.chat.id,
        "💰 *مقدار تغییر را وارد کنید (مثبت برای افزایش، منفی برای کاهش):*\n\n"
        "مثال:\n+500000 یا -200000",
        reply_markup=cancel_menu(),
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(m, manage_users_apply_change)

def manage_users_apply_change(m):
    if m.text == "⭕ لغو":
        bot.send_message(m.chat.id, "❌ عملیات لغو شد.", reply_markup=admin_panel_menu())
        return

    # بازیابی آیدی هدف از داده‌های ادمین
    admin_data = get_or_create_user(m.from_user.id)
    target_user_id = admin_data.get("target_user_id")
    if not target_user_id:
        bot.send_message(m.chat.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.", reply_markup=admin_panel_menu())
        return

    try:
        change = int(m.text.strip().replace("+", ""))
    except:
        bot.send_message(m.chat.id, "❌ لطفاً یک عدد صحیح وارد کنید (مثلاً: +500000 یا -200000)")
        bot.register_next_step_handler(m, manage_users_apply_change)
        return

    # ایجاد/بروزرسانی کاربر هدف
    target_user = get_or_create_user(target_user_id)
    old_balance = target_user["balance"]
    target_user["balance"] += change
    save_users(load_users())  # ذخیره کامل

# پیام تأیید
    bot.send_message(
        m.chat.id,
        f"✅ موجودی کاربر {target_user_id} به مقدار {change:,} تغییر کرد.\n"
        f"💰 موجودی جدید: {target_user['balance']:,} تومان",
        reply_markup=admin_panel_menu(),
        parse_mode="Markdown"
    )

# ================== 🧾 برداشت موجودی ==================

@bot.message_handler(func=lambda m: m.text == "برداشت موجودی 💳")
def withdraw_start(m):
    if not check_access(m):
        return

    uid = m.from_user.id
    user_data = get_or_create_user(uid)
    bal = user_data["balance"]

    if bal < 1000000:
        bot.send_message(
            m.chat.id,
            "❌ موجودی شما برای برداشت کافی نیست!\nحداقل موجودی برای برداشت: 1,000,000 تومان.",
            reply_markup=main_menu(uid)
        )
        return

    msg = (
        "💰 *مبلغ برداشت خود را وارد کنید*\n"
        "توجه داشته باشید که حداقل مبلغ برداشت 1,000,000 تومان میباشد.\n"
        "حال مبلغ مد نظر رو ارسال کن 💶\n\n"
        f"💰 *موجودی فعلی شما:* {bal:,} تومان"
    )
    bot.send_message(m.chat.id, msg, reply_markup=cancel_menu(), parse_mode="Markdown")
    bot.register_next_step_handler(m, withdraw_amount_input)

def withdraw_amount_input(m):
    if m.text == "⭕ لغو":
        bot.send_message(m.chat.id, "❌ عملیات برداشت لغو شد.", reply_markup=main_menu(m.from_user.id))
        return

    try:
        amount = int(m.text.replace(",", "").replace(" ", ""))
    except:
        bot.send_message(m.chat.id, "❌ لطفاً فقط عدد وارد کنید (مثال: 1000000)")
        bot.register_next_step_handler(m, withdraw_amount_input)
        return

    user_data = get_or_create_user(m.from_user.id)
    bal = user_data["balance"]

    if amount < 1000000:
        bot.send_message(m.chat.id, "❌ حداقل مبلغ برداشت 1,000,000 تومان است.")
        bot.register_next_step_handler(m, withdraw_amount_input)
        return
    if amount > 50000000:
        bot.send_message(m.chat.id, "❌ حداکثر مبلغ برداشت 50,000,000 تومان است.")
        bot.register_next_step_handler(m, withdraw_amount_input)
        return
    if amount > bal:
        bot.send_message(m.chat.id, f"❌ موجودی شما کافی نیست!\nموجودی فعلی: {bal:,} تومان")
        bot.register_next_step_handler(m, withdraw_amount_input)
        return

    user_data["withdraw_amount"] = amount
    users = load_users()
    users[str(m.from_user.id)] = user_data
    save_users(users)

    msg = (
        "💳 *برای برداشت، شماره کارت خود را به این فرمت بنویسید:*\n\n"
        "6037992021121487\n\n"
        "🚫 اگر نمی‌خواهید الان برداشت کنید، روی دکمه زیر کلیک کنید:"
    )
    bot.send_message(m.chat.id, msg, reply_markup=cancel_menu(), parse_mode="Markdown")
    bot.register_next_step_handler(m, withdraw_card_input)

def withdraw_card_input(m):
    if m.text == "⭕ لغو":
        bot.send_message(m.chat.id, "❌ عملیات برداشت لغو شد.", reply_markup=main_menu(m.from_user.id))
        return

    card = m.text.strip().replace(" ", "").replace("-", "")
    if not card.isdigit() or len(card) != 16:
        bot.send_message(m.chat.id, "❌ شماره کارت باید 16 رقمی و فقط عدد باشد.\nمثال: 6037992021121487")
        bot.register_next_step_handler(m, withdraw_card_input)
        return

    user_data = get_or_create_user(m.from_user.id)
    amount = user_data.get("withdraw_amount", 0)
    if amount <= 0:
        bot.send_message(m.chat.id, "❌ خطایی رخ داده. لطفاً دوباره تلاش کنید.", reply_markup=main_menu(m.from_user.id))
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_withdraw_{amount}"),
        types.InlineKeyboardButton("❌ لغو", callback_data="cancel_withdraw")
    )
    bot.send_message(m.chat.id, "⭕️ *ایا از انجام واریزی اطمینان دارید ❓*", reply_markup=markup, parse_mode="Markdown")

def send_withdraw_success_and_menu(chat_id, user_id, amount):
    user_data = get_or_create_user(user_id)
    
    msg1 = (
        "✅ *درخواست برداشت شما ثبت و تایید شد!* ✅\n\n"
        f"⏳ مبلغ {amount:,} تومان، شما حداکثر تا 7 روز آینده به حساب شما واریز خواهد شد.\n\n"
        "⚠️ *هشدار مهم:*\n\n"
        "🔒 اگر متوجه شویم عکس های شما با چت جی پی تی ساخته نشده باشد،"
        " و یا عکس های ارسالی تکراری باشند، حساب شما از ربات مسدود خواهد شد❌\n\n"
        f"*موجودی جدید:* {user_data['balance']:,} تومان\n"
        "*زمان برداشت:* ۷ روز"
    )

    msg2 = (
        "📅 *زمان برداشت شما: ۷ روز*\n"
        "⏳ این زمان رو صبر کن و از فرصت استفاده کن!\n"
        "💡 می‌تونی تا زمان واریز پول، دوباره از ربات میلیونی برداشت کنی و درآمدت رو افزایش بدی!"
    )

    bot.send_message(chat_id, msg1, parse_mode="Markdown")
    bot.send_message(chat_id, msg2, parse_mode="Markdown")
    time.sleep(2)
    bot.send_message(chat_id, "منوی اصلی:", reply_markup=main_menu(user_id))

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_withdraw_"))
def confirm_withdraw(c):
    amount = int(c.data.replace("confirm_withdraw_", ""))
    user_id = c.from_user.id
    user_data = get_or_create_user(user_id)

    if user_data["balance"] < amount:
        bot.answer_callback_query(c.id, "❌ موجودی کافی نیست!", show_alert=True)
        return

    user_data["balance"] -= amount
    users = load_users()
    users[str(user_id)] = user_data
    save_users(users)

    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except:
        pass

    threading.Thread(
        target=send_withdraw_success_and_menu,
        args=(c.message.chat.id, user_id, amount)
    ).start()

@bot.callback_query_handler(func=lambda c: c.data == "cancel_withdraw")
def cancel_withdraw(c):
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except:
        pass
    bot.send_message(c.message.chat.id, "❌ عملیات برداشت لغو شد.", reply_markup=main_menu(c.from_user.id))

# ================== سایر هندلرها ==================

@bot.message_handler(commands=['start'])
def start(m):
    if not check_access(m):
        return
    send_welcome_message(m.chat.id, m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "پنل مدیریت 🔐")
def admin_panel(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.send_message(m.chat.id, "🔐 *پنل مدیریت فعال شد*", reply_markup=admin_panel_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "✅ ربات روشن")
def turn_on(m):
    if m.from_user.id != ADMIN_ID:
        return
    save_bot_status(True)
    bot.send_message(m.chat.id, "🟢 ربات با موفقیت روشن شد!", reply_markup=admin_panel_menu())

@bot.message_handler(func=lambda m: m.text == "☑️ ربات خاموش")
def turn_off(m):
    if m.from_user.id != ADMIN_ID:
        return
    save_bot_status(False)
    bot.send_message(m.chat.id, "🔴 ربات با موفقیت خاموش شد!", reply_markup=admin_panel_menu())

@bot.message_handler(func=lambda m: m.text == "🔒قفل ربات")
def manage_force_join(m):
    if m.from_user.id != ADMIN_ID:
        return
    show_force_join_panel(m.chat.id)

@bot.message_handler(func=lambda m: m.text == "📊 آمار ربات")
def bot_stats(m):
    if m.from_user.id != ADMIN_ID:
        return
    users = load_users()
    total_users = len(users)
    today = datetime.now().strftime("%Y-%m-%d")
    today_users = sum(1 for u in users.values() if u.get("join_date") == today)
    week_users = 0
    for u in users.values():
        try:
            join_date = datetime.strptime(u.get("join_date", ""), "%Y-%m-%d").date()
            if (date.today() - join_date).days <= 7:
                week_users += 1
        except:
            pass
    active_users = sum(1 for u in users.values() if u.get("photo_count", 0) > 0)

stats_text = (
        "🆔 *ایدی ربات:* piic_sell_bot\n\n"
        f"📊 *کل اعضای ربات :* {total_users}\n"
        f"💡 *کاربران فعال:* {active_users}\n"
        f"🆕 *افراد عضو شده امروز:* {today_users}\n"
        f"📋 *افراد عضو شده 7روز گذشته:* {week_users}\n"
        "⛔️ *افراد مسدود شده :* 0\n"
        "⌨ *دکمه ها:* 5\n"
        "⛑ *ادمین ها:* 1"
    )
    bot.send_message(m.chat.id, stats_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "✉️ پیام همگانی")
def broadcast_start(m):
    if m.from_user.id != ADMIN_ID:
        return
    msg = (
        "📩 *پیام مورد نظرتان را برای ارسال همگانی بفرستید:*\n\n"
        "🔴 شما می توانید از متغیر های عمومی درج شده در بخش راهنما مثل* FIRSTNAME *و ...استفاده کنید.\n\n"
        "🔴همچنین می توانید از قالب دکمه ی شیشه ای و هایپرلینک استفاده کنید."
    )
    bot.send_message(m.chat.id, msg, reply_markup=cancel_menu(), parse_mode="Markdown")
    bot.register_next_step_handler(m, broadcast_message)

def broadcast_message(m):
    if m.text == "⭕ لغو":
        bot.send_message(m.chat.id, "❌ عملیات پیام همگانی لغو شد.", reply_markup=admin_panel_menu())
        return
    if m.from_user.id != ADMIN_ID:
        return

    users = load_users()
    sent_count = 0
    for user_id in users:
        try:
            bot.forward_message(int(user_id), m.chat.id, m.message_id)
            sent_count += 1
        except:
            pass

    bot.send_message(
        m.chat.id,
        f"✅ پیام همگانی ارسال شد!\n"
        f"📬 به {sent_count} کاربر ارسال شد.",
        reply_markup=admin_panel_menu()
    )

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منوی اصلی")
def back_to_main(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.send_message(m.chat.id, "🔙 بازگشت به منوی اصلی", reply_markup=main_menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text == "فروش عکس ☑️")
def sell_photo_request(m):
    if not check_access(m):
        return
    bot.send_message(
        m.chat.id,
        "عکس خود را آپلود کنید (توجه کنید عکس باید با CHAT GPT ساخته شده باشند)\n\n"
        "میتوانید از ربات عکس ساز زیر هم استفاده کنید.\n"
        "@image_makerrbot",
        reply_markup=cancel_menu()
    )
    bot.register_next_step_handler(m, process_photo)

def process_photo(m):
    if m.text == "⭕ لغو":
        bot.send_message(m.chat.id, "عملیات لغو شد ❌", reply_markup=main_menu(m.from_user.id))
        return
    if m.photo:
        uid = m.from_user.id
        name = m.from_user.first_name
        users = load_users()
        sid = str(uid)
        if sid not in users:
            get_or_create_user(uid, name)
            users = load_users()
        users[sid]["balance"] += 50000
        users[sid]["photo_count"] += 1
        save_users(users)
        bal = users[sid]["balance"]
        bot.send_message(
            m.chat.id,
            f"عکس پردازش شد\n+ ۵۰,۰۰۰ تومان به موجودی شما اضافه شد\n\n"
            f"موجودی فعلی: {bal:,} تومان",
            reply_markup=main_menu(m.from_user.id)
        )
    else:
        bot.send_message(m.chat.id, "لطفاً فقط عکس بفرستید یا «⭕ لغو» کنید!")
        bot.register_next_step_handler(m, process_photo)

@bot.message_handler(func=lambda m: m.text == "موجودی من 💸")
def balance(m):
    if not check_access(m):
        return
    uid = m.from_user.id
    name = m.from_user.first_name
    user_data = get_or_create_user(uid, name)
    msg = (
        "💎 *📊 کارت کاربری شما*\n\n"
        f"👤 *📝 نام اکانت شما :* {user_data['name']}\n"
        f"🔢 *🆔 آیدی عددی شما :* {user_data['user_id']}\n"
        f"📦 *🛒 تعداد کل عکس‌های ارسالی :* {user_data['photo_count']}\n"
        f"💰 *💳 موجودی کیف پول شما :* {user_data['balance']:,} تومان\n\n"
        f"🗓 *⏳ تاریخ عضویت :* {user_data['join_date']}\n\n"
        "✅ *همیشه به موقع و سریع — مثل یه کهکشان!* 🌌"
    )
    bot.send_message(m.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def other(m):
    if m.text != "⭕ لغو":
        if not check_access(m):
            return
        bot.reply_to(m, "یکی از دکمه‌ها رو بزن", reply_markup=main_menu(m.from_user.id))

@bot.callback_query_handler(func=lambda c: c.data == "add_channel")
def add_channel_start(c):
    bot.answer_callback_query(c.id)
    msg = "✉️ یوزرنیم کانال را ارسال کنید (مثال: @pic_gavanin)"
    bot.send_message(c.message.chat.id, msg, reply_markup=cancel_menu(), parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(c.message.
