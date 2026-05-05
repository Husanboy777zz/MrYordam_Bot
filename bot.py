import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Render uchun kichik veb-server (uyg'oq tutish uchun)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown

from database import (
    delete_client,
    get_clients_for_owner,
    get_pending_clients,
    get_clients_history,
    get_user,
    init_db,
    mark_notified,
    save_client,
    save_user,
    update_shop_name,
    update_user_phone,
    update_user_template,
)
from sms import send_sms
from userbot_client import send_userbot_msg, app_ub

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
UZ_TZ = pytz.timezone("Asia/Tashkent")

# ──────────────────────────────────────────
# Conversation states
# ──────────────────────────────────────────
REG_NAME, REG_SHOP, REG_PHONE = range(3)
CLI_NAME, CLI_PHONE, CLI_TIME  = range(3, 6)
HIST_SELECT = 6
SET_CHOICE, SET_SHOP, SET_PHONE, SET_TEMPLATE = range(7, 11)

# ──────────────────────────────────────────
# Keyboards
# ──────────────────────────────────────────
BTN_REGISTER   = "📝 Ro'yxatdan o'tish"
BTN_ADD_CLIENT = "➕ Mijoz qo'shish"
BTN_CLIENTS    = "📋 Mijozlar ro'yxati"
BTN_SETTINGS   = "⚙️ Sozlamalar"
BTN_INFO       = "ℹ️ Ma'lumot"
BTN_CANCEL     = "❌ Bekor qilish"
BTN_HISTORY    = "📊 Mijozlar tarixi"
BTN_1_MONTH    = "📅 1 oylik"
BTN_2_MONTH    = "📅 2 oylik"
BTN_3_MONTH    = "📅 3 oylik"
BTN_ALL_TIME   = "🌐 Hammasi"
BTN_SET_SHOP   = "🏪 Do'kon nomini o'zgartirish"
BTN_SET_PHONE  = "📱 Telefonni o'zgartirish"
BTN_SET_TEMPLATE = "📝 Xabar matni"
BTN_BACK       = "⬅️ Ortga"
BTN_MAIN_MENU  = "🏠 Bosh menyu"


def main_menu(registered: bool) -> ReplyKeyboardMarkup:
    if registered:
        rows = [
            [KeyboardButton(BTN_ADD_CLIENT)],
            [KeyboardButton(BTN_CLIENTS), KeyboardButton(BTN_HISTORY)],
            [KeyboardButton(BTN_SET_TEMPLATE), KeyboardButton(BTN_SETTINGS)],
            [KeyboardButton(BTN_INFO)],
        ]
    else:
        rows = [
            [KeyboardButton(BTN_REGISTER)],
            [KeyboardButton(BTN_INFO)],
        ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(BTN_ADD_CLIENT)],
        [KeyboardButton(BTN_MAIN_MENU)],
        [KeyboardButton(BTN_CANCEL)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def after_add_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(BTN_ADD_CLIENT)],
        [KeyboardButton(BTN_MAIN_MENU)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# ──────────────────────────────────────────
# /start
# ──────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.effective_message:
        return

    tg_user = update.effective_user
    logger.info(f"START: ID={tg_user.id}, Name={tg_user.full_name}")
    
    try:
        user = get_user(tg_user.id)
        if user:
            name_esc = escape_markdown(user[1], version=2)
            shop_esc = escape_markdown(user[2], version=2)
            text = (
                f"👋 Xush kelibsiz, *{name_esc}*\\!\n"
                f"🏪 Do'kon: *{shop_esc}*\n\n"
                "Quyidagi tugmalardan birini tanlang 👇"
            )
        else:
            text = (
                "👋 *Yordamchi Botiga Xush Kelibsiz\\!*\n\n"
                "Bu bot yordamida:\n"
                "✅ Ro'yxatdan o'ting\n"
                "👥 Mijozlaringizni navbatga qo'ying\n"
                "📱 Vaqt kelganda mijozga avtomatik SMS yuboriladi\n\n"
                "Boshlash uchun *Ro'yxatdan o'tish* tugmasini bosing 👇"
            )
            
        await update.effective_message.reply_text(
            text, 
            reply_markup=main_menu(bool(user)), 
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"START error: {e}")
        return ConversationHandler.END


# ──────────────────────────────────────────
# REGISTRATION conversation
# ──────────────────────────────────────────
async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📝 *Ro'yxatdan o'tish*\n\n1️⃣ Ismingizni kiriting:",
        reply_markup=cancel_kb(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return REG_NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val in [BTN_CANCEL, BTN_MAIN_MENU]:
        return await _cancel(update, context)
    if val == BTN_ADD_CLIENT:
        return await client_start(update, context)
    if val in [BTN_REGISTER, BTN_CLIENTS, BTN_SETTINGS, BTN_INFO, BTN_SET_TEMPLATE]:
        return
    context.user_data["reg_name"] = val
    await update.message.reply_text(f"✅ Ism: {val}\n\n2️⃣ Do'kon nomini kiriting:")
    return REG_SHOP


async def reg_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == BTN_CANCEL: return await _cancel(update, context)
    context.user_data["reg_shop"] = val
    await update.message.reply_text(f"✅ Do'kon: {val}\n\n3️⃣ Telefon raqamingizni kiriting:")
    return REG_PHONE


async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == BTN_CANCEL: return await _cancel(update, context)
    
    user_id = update.effective_user.id
    name = context.user_data["reg_name"]
    shop = context.user_data["reg_shop"]
    save_user(user_id, name, shop, val)
    
    await update.message.reply_text(
        "🎉 *Muvaffaqiyatli ro'yxatdan o'tdingiz\\!*",
        reply_markup=main_menu(True),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ConversationHandler.END


# ──────────────────────────────────────────
# ADD CLIENT conversation
# ──────────────────────────────────────────
async def client_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "👥 *Mijoz qo'shish*\n\n1️⃣ Mijoz ismini kiriting:",
        reply_markup=cancel_kb(),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CLI_NAME


async def client_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val in [BTN_CANCEL, BTN_MAIN_MENU]:
        return await _cancel(update, context)
    if val == BTN_ADD_CLIENT:
        return await client_start(update, context)
    if val in [BTN_REGISTER, BTN_CLIENTS, BTN_SETTINGS, BTN_INFO, BTN_SET_TEMPLATE]:
        return
    context.user_data["cli_name"] = val
    await update.message.reply_text(f"✅ Mijoz: {val}\n\n2️⃣ Telefonini kiriting:")
    return CLI_PHONE


async def client_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val in [BTN_CANCEL, BTN_MAIN_MENU]:
        return await _cancel(update, context)
    if val == BTN_ADD_CLIENT:
        return await client_start(update, context)
    if val in [BTN_REGISTER, BTN_CLIENTS, BTN_SETTINGS, BTN_INFO, BTN_SET_TEMPLATE]:
        return
    context.user_data["cli_phone"] = val
    now = datetime.now(UZ_TZ)
    await update.message.reply_text(
        f"✅ Tel: {val}\n\n3️⃣ Kelish vaqtini kiriting (masalan `15:30`):",
    )
    return CLI_TIME


async def client_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val in [BTN_CANCEL, BTN_MAIN_MENU]:
        return await _cancel(update, context)
    if val == BTN_ADD_CLIENT:
        return await client_start(update, context)
    if val in [BTN_REGISTER, BTN_CLIENTS, BTN_SETTINGS, BTN_INFO, BTN_SET_TEMPLATE]:
        return
    
    now = datetime.now(UZ_TZ)
    apt = _parse_time(val, now)
    if not apt:
        await update.message.reply_text("❌ Noto'g'ri vaqt format! (Masalan: 15:30)")
        return CLI_TIME

    owner_id = update.effective_user.id
    cli_name = context.user_data["cli_name"]
    cli_phone = context.user_data["cli_phone"]
    
    save_client(owner_id, cli_name, cli_phone, apt.strftime("%Y-%m-%d %H:%M:%S"))
    
    await update.message.reply_text(
        f"✅ *Mijoz qo'shildi\\!*\n🕐 Vaqti: {apt.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=after_add_kb(),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ConversationHandler.END


def _parse_time(text: str, now: datetime) -> datetime | None:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text.strip())
    if m:
        h, mi = map(int, m.groups())
        dt = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        if dt < now: dt += timedelta(days=1)
        return dt
    return None


# ──────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────
async def show_clients_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clients = get_clients_for_owner(update.effective_user.id)
    if not clients:
        await update.message.reply_text("📋 Ro'yxat bo'sh.")
        return
    
    msg = "📋 *Mijozlar ro'yxati:*\n\n"
    for cl in clients:
        msg += f"• {cl[1]} ({cl[3]})\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


# ──────────────────────────────────────────
# SETTINGS handlers
# ──────────────────────────────────────────
async def settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    kb = ReplyKeyboardMarkup([
        [KeyboardButton(BTN_SET_SHOP)],
        [KeyboardButton(BTN_SET_PHONE)],
        [KeyboardButton(BTN_SET_TEMPLATE)],
        [KeyboardButton(BTN_BACK)]
    ], resize_keyboard=True)
    
    text = (
        "⚙️ *Sozlamalar*\n\n"
        f"🏪 Do'kon: *{user[2]}*\n"
        f"📱 Tel: *{user[3]}*\n"
        f"📝 Matn: *{user[4]}*\n\n"
        "O'zgartirmoqchi bo'lgan ma'lumotni tanlang 👇"
    )
    await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    return SET_CHOICE

async def set_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == BTN_BACK or val == BTN_CANCEL:
        return await _cancel(update, context)
    
    if val == BTN_SET_SHOP:
        await update.message.reply_text("🏪 Yangi do'kon nomini kiriting:", reply_markup=cancel_kb())
        return SET_SHOP
    elif val == BTN_SET_PHONE:
        await update.message.reply_text("📱 Yangi telefon raqamingizni kiriting:", reply_markup=cancel_kb())
        return SET_PHONE
    elif val == BTN_SET_TEMPLATE:
        await update.message.reply_text(
            "📝 Yangi xabar matnini kiriting:\n\n"
            "Eslatma: Bot boshiga mijoz ismini va oxiriga do'kon nomini o'zi qo'shadi.\n"
            "Masalan: `vaqtingiz keldi, kiring` deb yozsangiz, mijozga \n"
            "`Hurmatli Ism, vaqtingiz keldi, kiring! Do'kon` shaklida boradi.",
            reply_markup=cancel_kb()
        )
        return SET_TEMPLATE
    return SET_CHOICE

async def set_template_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 *Mijozga yuboriladigan matnni kiriting:*\n\n"
        "Eslatma: Bot boshiga mijoz ismini va oxiriga do'kon nomini o'zi qo'shadi.\n"
        "Masalan: `vaqtingiz keldi, kiring` deb yozsangiz, mijozga \n"
        "`Hurmatli Ism, vaqtingiz keldi, kiring! Do'kon` shaklida boradi.",
        reply_markup=cancel_kb(),
        parse_mode=ParseMode.MARKDOWN
    )
    return SET_TEMPLATE

async def set_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    # Tugmalar bosilganda ularni matn sifatida saqlamaslik
    if val in [BTN_CANCEL, BTN_MAIN_MENU, BTN_BACK]:
        return await _cancel(update, context)
    if val == BTN_ADD_CLIENT:
        return await client_start(update, context)
    if val in [BTN_REGISTER, BTN_CLIENTS, BTN_SETTINGS, BTN_INFO, BTN_SET_TEMPLATE]:
        return
    
    update_user_template(update.effective_user.id, val)
    await update.message.reply_text(
        f"✅ Xabar matni muvaffaqiyatli saqlandi:\n\n*\"{val}\"*", 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(True)
    )
    return ConversationHandler.END

async def set_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == BTN_CANCEL: return await settings_start(update, context)
    
    update_shop_name(update.effective_user.id, val)
    await update.message.reply_text(f"✅ Do'kon nomi o'zgartirildi: *{val}*", parse_mode=ParseMode.MARKDOWN)
    return await settings_start(update, context)

async def set_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == BTN_CANCEL: return await settings_start(update, context)
    
    update_user_phone(update.effective_user.id, val)
    await update.message.reply_text(f"✅ Telefon raqami o'zgartirildi: *{val}*", parse_mode=ParseMode.MARKDOWN)
    return await settings_start(update, context)


# ──────────────────────────────────────────


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Bu bot navbatlarni boshqarish uchun!*\n\n"
        "Siz ish qilayotgan vaqtingizda mijozlarga qo'ng'iroq qilib, navbati kelganini "
        "aytib o'tirishingiz shart emas. Shunchaki mijozning ismi va telefon raqamini "
        "kiritib qo'ysangiz kifoya. \n\n"
        "Sizning yodingizdan ko'tarilgan vaqtda ham bot belgilangan vaqtda "
        "avtomatik tarzda mijozga xabar yuboradi."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = get_user(update.effective_user.id)
    await update.message.reply_text("🏠 Bosh menyu.", reply_markup=main_menu(bool(user)))
    return ConversationHandler.END


# ──────────────────────────────────────────
# HISTORY handlers
# ──────────────────────────────────────────
async def history_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([
        [KeyboardButton(BTN_1_MONTH), KeyboardButton(BTN_2_MONTH)],
        [KeyboardButton(BTN_3_MONTH), KeyboardButton(BTN_ALL_TIME)],
        [KeyboardButton(BTN_CANCEL)]
    ], resize_keyboard=True)
    
    await update.message.reply_text(
        "📊 *Mijozlar tarixi*\n\nQaysi davrni ko'rmoqchisiz?",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    return HIST_SELECT

async def history_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == BTN_CANCEL: return await _cancel(update, context)
    
    months = None
    if val == BTN_1_MONTH: months = 1
    elif val == BTN_2_MONTH: months = 2
    elif val == BTN_3_MONTH: months = 3
    elif val == BTN_ALL_TIME: months = None
    else: return # Noma'lum tugma
    
    clients = get_clients_history(update.effective_user.id, months)
    
    if not clients:
        await update.message.reply_text(f"📭 {val} davrida mijozlar topilmadi.")
        return
        
    msg = f"📊 *Mijozlar ro'yxati ({val}):*\n\n"
    msg += f"Umumiy soni: *{len(clients)}* ta\n\n"
    
    for cl in clients[:20]:
        status = "✅" if cl[4] else "⏳"
        msg += f"{status} {cl[1]} | {cl[2]}\n"
        
    if len(clients) > 20:
        msg += f"\n_...va yana {len(clients)-20} ta mijoz_"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(True))
    return ConversationHandler.END


# ──────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────
async def sms_job(application: Application):
    pending = get_pending_clients()
    if pending:
        logger.info(f"Navbati kelgan {len(pending)} ta mijoz topildi.")
    
    for row in pending:
        client_id, client_name, client_phone, apt_time, owner_name, shop_name, owner_id, template = row
        
        # Xabar matnini shakllantirish
        msg = f"Hurmatli {client_name}, {template}! {shop_name}"
        
        # 1. Userbot orqali Telegram xabar yuborishga urinish
        logger.info(f"Userbot orqali xabar yuborishga urinish: {client_name} ({client_phone})")
        ok = await send_userbot_msg(client_phone, msg)
        
        # 2. Agar Userbot o'xshamasa, SMS ga urinish (ixtiyoriy)
        if not ok:
            logger.info(f"Userbot orqali xabar ketmadi, SMS ga urinish: {client_phone}")
            ok = send_sms(client_phone, msg)
        
        mark_notified(client_id)
        
        try:
            if ok:
                status = "✅ Xabar yuborildi"
            else:
                status = "⚠️ Yuborib bo'lmadi"

            notify_text = f"{status}\nMijoz: {client_name}\nTel: {client_phone}"
            await application.bot.send_message(
                chat_id=owner_id, 
                text=notify_text,
                reply_markup=main_menu(True)
            )
        except Exception as e:
            logger.error(f"Egalarini xabardor qilishda xato: {e}")


def main():
    # Render uchun veb-serverni fonda ishga tushiramiz
    threading.Thread(target=run_health_server, daemon=True).start()
    
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan!")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # ── Registration ──
    reg_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{re.escape(BTN_REGISTER)}$"), reg_start)],
        states={
            REG_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_SHOP:  [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_shop)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CommandHandler("cancel", _cancel),
            MessageHandler(filters.Regex(f"^{re.escape(BTN_CANCEL)}$"), _cancel)
        ],
    )

    # ── Add Client ──
    cli_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{re.escape(BTN_ADD_CLIENT)}$"), client_start)],
        states={
            CLI_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CLI_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_phone)],
            CLI_TIME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, client_time)],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CommandHandler("cancel", _cancel),
            MessageHandler(filters.Regex(f"^{re.escape(BTN_CANCEL)}$"), _cancel)
        ],
    )

    async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("pong")

    # ── History ──
    hist_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{re.escape(BTN_HISTORY)}$"), history_start)],
        states={
            HIST_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, history_show)],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            MessageHandler(filters.Regex(f"^{re.escape(BTN_CANCEL)}$"), _cancel)
        ],
    )

    # ── Settings ──
    set_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f"^{re.escape(BTN_SETTINGS)}$"), settings_start),
            MessageHandler(filters.Regex(f"^{re.escape(BTN_SET_TEMPLATE)}$"), set_template_entry)
        ],
        states={
            SET_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_choice)],
            SET_SHOP:   [MessageHandler(filters.TEXT & ~filters.COMMAND, set_shop)],
            SET_PHONE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, set_phone)],
            SET_TEMPLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_template)],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            MessageHandler(filters.Regex(f"^{re.escape(BTN_CANCEL)}$"), _cancel),
            MessageHandler(filters.Regex(f"^{re.escape(BTN_BACK)}$"), _cancel)
        ],
    )

    # ── Handlers ──
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", ping_handler))
    app.add_handler(reg_conv)
    app.add_handler(cli_conv)
    app.add_handler(hist_conv)
    app.add_handler(set_conv)
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(BTN_CLIENTS)}$"), show_clients_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(BTN_SETTINGS)}$"), settings_start))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(BTN_INFO)}$"), info_handler))

    # ── Scheduler ──
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(sms_job, "interval", seconds=30, args=[app])
    scheduler.start()
    logger.info("Scheduler started.")

    async def on_startup(application: Application):
        logger.info("Userbot fonda ulanmoqda...")
        # Fonda ishga tushiramiz, toki asosiy botni bloklamasin
        asyncio.create_task(start_userbot())

    async def start_userbot():
        try:
            if not app_ub.is_connected:
                await app_ub.start()
                logger.info("Userbot muvaffaqiyatli ulandi.")
        except Exception as e:
            logger.error(f"Userbot ulanishda xato: {e}")
            logger.error("Iltimos, 'python login_userbot.py' buyrug'ini ishga tushirib akkauntga kiring.")

    app.post_init = on_startup

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
