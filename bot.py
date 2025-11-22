import logging
import requests
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.helpers import escape_markdown

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === CONFIG ===
API_BASE = "https://numapi.anshapi.workers.dev?num="
BOT_TOKEN = "7745907914:AAEJvwRZqPkDpw-gPTi9oseeYHVMHy1Usww"

ENTER_NUMBER = 1

# === HEADERS ===
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,*/*;q=0.8",
    "Referer": "https://anish-axploits.vercel.app/"
}

FIELD_NAME_MAP = {
    'number': '📱 Mobile Number',
    'mobile': '📱 Mobile Number',
    'name': '👤 Full Name',
    'fathername': '👨‍🦳 Father Name',
    'fname': '👨‍🦳 Father Name',
    'father_name': '👨‍🦳 Father Name',
    'address': '🏠 Address',
    'altmobile': '📞 Alternate Mobile',
    'alt_mobile': '📞 Alternate Mobile',
    'circle': '📍 Circle',
    'operator': '🏢 Operator',
    'state': '🗺️ State',
    'sim': '📲 SIM Type',
    'idnumber': '🆔 ID Number',
    'id_number': '🆔 ID Number'
}

def get_display_name(field_name):
    f = field_name.lower()
    return FIELD_NAME_MAP.get(f, field_name.replace("_", " ").title())

def normalize_response(data):
    if isinstance(data, dict) and "data" in data and data["data"]:
        if isinstance(data["data"], list):
            return data["data"]
        return [data["data"]]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and v:
                return v
            if isinstance(v, dict):
                return [v]
    return []

def format_address(addr):
    if not addr:
        return addr
    return " ".join(addr.split())

# === START CMD ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🔎 Search Number"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🤖 Welcome To Sharlix M7 Project", reply_markup=reply_markup)

# === ENTER NUMBER ===
async def enter_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 Send 10 digit mobile number:", reply_markup=ReplyKeyboardRemove())
    return ENTER_NUMBER

# === SEARCH ===
async def search_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ Invalid number! Send exactly 10 digits.\n/start")
        return ConversationHandler.END

    searching_msg = await update.message.reply_text("🔍 Searching database...")

    try:
        url = f"{API_BASE}{number}"
        response = requests.get(url, headers=HEADERS, timeout=20)
        raw = response.text.strip()

        try:
            data = json.loads(raw)
        except:
            s = raw.find("{")
            e = raw.rfind("}")
            if s != -1 and e != -1:
                try:
                    data = json.loads(raw[s:e+1])
                except:
                    await safe_delete(searching_msg)
                    await update.message.reply_text("❌ No information found.\n/start")
                    return ConversationHandler.END
            else:
                await safe_delete(searching_msg)
                await update.message.reply_text("❌ No information found.\n/start")
                return ConversationHandler.END

        records = normalize_response(data)

        if not records:
            await safe_delete(searching_msg)
            await update.message.reply_text("❌ No information found.\n/start")
            return ConversationHandler.END

        await safe_delete(searching_msg)

        # Start formatting safely
        result = f"✅ *Information Found*\n\n"
        result += f"🔢 *Target Number:* `{escape_markdown(number, version=2)}`\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for idx, user in enumerate(records, 1):
            if isinstance(user, dict):
                result += f"*📄 Record {idx}:*\n"

                priority = [
                    'name','fathername','father_name','fname','mobile','number',
                    'idnumber','id_number','address','altmobile','alt_mobile',
                    'circle','operator','state','sim'
                ]

                added = set()

                for field in priority:
                    if field in user and user[field]:
                        val = user[field]
                        if field == "address":
                            val = format_address(val)
                        display = get_display_name(field)
                        val = escape_markdown(str(val), version=2)
                        result += f"• *{display}:* `{val}`\n"
                        added.add(field)

                for key, val in user.items():
                    if key not in added and val:
                        val = format_address(val) if key == "address" else val
                        display = get_display_name(key)
                        val = escape_markdown(str(val), version=2)
                        result += f"• *{display}:* `{val}`\n"

                result += "\n────────────────────\n\n"

        # Credit safely
        credit = "💻 *Created By Sharlix*\n📱 Join: https://t.me/starmaker_in"
        result += escape_markdown(credit, version=2)

        await update.message.reply_text(result, parse_mode="MarkdownV2")

        # Show menu again
        keyboard = [["🔎 Search Number"]]
        await update.message.reply_text("Search another number:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

        return ConversationHandler.END

    except:
        await safe_delete(searching_msg)
        await update.message.reply_text("❌ Error occurred.\n/start")
        return ConversationHandler.END

# === SAFE DELETE ===
async def safe_delete(msg):
    try:
        await msg.delete()
    except:
        pass

# === CANCEL ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.\n/start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# === MAIN ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🔎 Search Number$"), enter_number),
            CommandHandler("start", start)
        ],
        states={
            ENTER_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_number)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()+
