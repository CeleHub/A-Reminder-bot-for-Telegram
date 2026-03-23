import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm your Reminder Bot. "
        "Use /help to see what I can do."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/remind <time> <message> - Set a reminder (e.g., /remind 8:40 Breakfast or /remind 10m Take a break)"
    )
    await update.message.reply_text(help_text)

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=rf"⏰ Reminder: {job.data}")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        if not context.args:
            raise IndexError

        time_str = context.args[0]
        
        # Check if the time is in HH:MM format
        if ':' in time_str:
            try:
                target_time = datetime.strptime(time_str, "%H:%M").time()
                now = datetime.now()
                target_dt = datetime.combine(now.date(), target_time)
                
                # If the time has already passed today, schedule for tomorrow
                if target_dt <= now:
                    target_dt += timedelta(days=1)
                
                seconds = (target_dt - now).total_seconds()
            except ValueError:
                await update.effective_message.reply_text("Invalid time format. Please use HH:MM (e.g., 08:40).")
                return
        else:
            # parse time_str as relative duration
            if time_str.endswith('s'):
                seconds = int(time_str[:-1])
            elif time_str.endswith('m'):
                seconds = int(time_str[:-1]) * 60
            elif time_str.endswith('h'):
                seconds = int(time_str[:-1]) * 3600
            elif time_str.endswith('d'):
                seconds = int(time_str[:-1]) * 86400
            else:
                seconds = int(time_str) # Assume seconds
                time_str = f"{seconds}s"
            
        if seconds <= 0:
            await update.effective_message.reply_text("Time must be greater than 0.")
            return

        text = ' '.join(context.args[1:]) if len(context.args) > 1 else "Time's up!"

        context.job_queue.run_once(alarm, seconds, chat_id=chat_id, name=str(chat_id), data=text)
        
        if ':' in time_str:
            await update.effective_message.reply_text(f"Reminder successfully set for {target_dt.strftime('%H:%M')}!")
        else:
            await update.effective_message.reply_text(f"Reminder successfully set! I will remind you in {time_str}.")

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /remind <time> <message>\nExample: /remind 8:40 Breakfast or /remind 10m Take a break")

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Please set your TELEGRAM_BOT_TOKEN in the .env file.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("remind", remind))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
