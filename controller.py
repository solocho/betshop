import subprocess
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TOKEN = "8051053485:AAFFtkFEllZ0mqAdDUFQvi1FyguZ5rqlZoY"
PYTHON_PATH = r"C:\Users\chome\Downloads\ai-marketing-bot\venv\Scripts\python.exe"

SCRIPTS = {
    "main": "main.py",
    "video": "video_ad_creator.py",
    "blog": "blog.py"
}

AUTO_NOTIFY_CHAT_ID =5802469496 # <-- Fill this with your user or group chat ID

def run_script(script_path):
    try:
        result = subprocess.run(
            [PYTHON_PATH, script_path],
            capture_output=True,
            text=True
        )
        success = result.returncode == 0
        output = result.stdout.strip() if result.stdout else "(No output)"
        error = result.stderr.strip() if result.stderr else ""
        return success, output, error
    except Exception as e:
        return False, "", str(e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("▶️ Run All", callback_data="run_all")],
        [
            InlineKeyboardButton("🟢 Run Main Only", callback_data="run_main"),
            InlineKeyboardButton("🔵 Run Video Only", callback_data="run_video"),
            InlineKeyboardButton("🟣 Run Blog Only", callback_data="run_blog")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an action:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "run_all":
        await run_all_flow(query, context)
    else:
        script_key = action.replace("run_", "")
        await run_single_script(query, context, script_key)

async def run_all_flow(query, context):
    chat_id = query.message.chat_id

    await query.edit_message_text("Starting sequential execution:\n1️⃣ main.py → 2️⃣ video_ad_creator.py → 3️⃣ blog.py")

    # 1. Run main.py
    await context.bot.send_message(chat_id=chat_id, text="▶️ Running main.py...")
    success, output, error = run_script(SCRIPTS["main"])
    if success:
        await context.bot.send_message(chat_id=chat_id, text=f"✅ main.py completed!\n{output}")
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ main.py failed!\n{error or output}")
        return

    await context.bot.send_message(chat_id=chat_id, text="⏳ Waiting 2 minutes before next step...")
    await asyncio.sleep(120)

    # 2. Run video_ad_creator.py
    await context.bot.send_message(chat_id=chat_id, text="▶️ Running video_ad_creator.py...")
    success, output, error = run_script(SCRIPTS["video"])
    if success:
        await context.bot.send_message(chat_id=chat_id, text=f"✅ video_ad_creator.py completed!\n{output}")
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ video_ad_creator.py failed!\n{error or output}")
        return

    await context.bot.send_message(chat_id=chat_id, text="⏳ Waiting 2 minutes before final step...")
    await asyncio.sleep(120)

    # 3. Run blog.py
    await context.bot.send_message(chat_id=chat_id, text="▶️ Running blog.py...")
    success, output, error = run_script(SCRIPTS["blog"])
    if success:
        await context.bot.send_message(chat_id=chat_id, text=f"✅ blog.py completed!\n{output}")
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ blog.py failed!\n{error or output}")

async def run_single_script(query, context, script_key):
    chat_id = query.message.chat_id
    script_path = SCRIPTS.get(script_key)
    if not script_path:
        await context.bot.send_message(chat_id=chat_id, text="❌ Unknown script!")
        return
    await query.edit_message_text(f"▶️ Running {script_path} ...")
    success, output, error = run_script(script_path)
    if success:
        await context.bot.send_message(chat_id=chat_id, text=f"✅ {script_path} completed!\n{output}")
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ {script_path} failed!\n{error or output}")

# ---- SCHEDULED AUTO-RUN ----
async def scheduled_run_all(bot):
    chat_id = AUTO_NOTIFY_CHAT_ID
    await bot.send_message(chat_id=chat_id, text="⏰ Scheduled Run: Starting sequential execution:\n1️⃣ main.py → 2️⃣ video_ad_creator.py → 3️⃣ blog.py")

    # 1. main.py
    await bot.send_message(chat_id=chat_id, text="▶️ Running main.py...")
    success, output, error = run_script(SCRIPTS["main"])
    if success:
        await bot.send_message(chat_id=chat_id, text=f"✅ main.py completed!\n{output}")
    else:
        await bot.send_message(chat_id=chat_id, text=f"❌ main.py failed!\n{error or output}")
        return

    await bot.send_message(chat_id=chat_id, text="⏳ Waiting 2 minutes before next step...")
    await asyncio.sleep(120)

    # 2. video_ad_creator.py
    await bot.send_message(chat_id=chat_id, text="▶️ Running video_ad_creator.py...")
    success, output, error = run_script(SCRIPTS["video"])
    if success:
        await bot.send_message(chat_id=chat_id, text=f"✅ video_ad_creator.py completed!\n{output}")
    else:
        await bot.send_message(chat_id=chat_id, text=f"❌ video_ad_creator.py failed!\n{error or output}")
        return

    await bot.send_message(chat_id=chat_id, text="⏳ Waiting 2 minutes before final step...")
    await asyncio.sleep(120)

    # 3. blog.py
    await bot.send_message(chat_id=chat_id, text="▶️ Running blog.py...")
    success, output, error = run_script(SCRIPTS["blog"])
    if success:
        await bot.send_message(chat_id=chat_id, text=f"✅ blog.py completed!\n{output}")
    else:
        await bot.send_message(chat_id=chat_id, text=f"❌ blog.py failed!\n{error or output}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("Bot started! Open Telegram and send /start to your bot.")

    # Scheduler setup
    scheduler = AsyncIOScheduler()
    def job():
        asyncio.create_task(scheduled_run_all(app.bot))
    scheduler.add_job(job, CronTrigger(hour='6,12,18', minute=0))
    scheduler.start()
    print("Scheduler started.")

    # Wait forever (Ctrl+C to quit)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
