import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8258635825:AAHRJpE2Mu2Qncm1sszladyjip6bXQRlo6o"

# Стандартное напоминание (20 минут)
DEFAULT_INTERVAL = 20 * 60  # секунд

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.bot_data["user_id"] = user_id
    await update.message.reply_text(
        "✅ Бот запущен.\n"
        "Пиши: /remind [минуты] [текст]\n"
        "Пример: /remind 10 Сделай перерыв"
    )
    print(f"Твой ID: {user_id}")

    # Запускаем стандартное напоминание (каждые 20 минут)
    if "default_job" not in context.bot_data:
        job = context.job_queue.run_repeating(
            default_reminder,
            interval=DEFAULT_INTERVAL,
            first=DEFAULT_INTERVAL
        )
        context.bot_data["default_job"] = job

async def default_reminder(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.bot_data.get("user_id")
    if user_id:
        await context.bot.send_message(
            chat_id=user_id,
            text="⏰ 20 минут прошло.\nСделай **одно** действие. Не геройство — просто шаг."
        )

# Команда: /remind 5 Текст
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /remind [минуты] [текст]")
        return

    try:
        minutes = int(context.args[0])
        text = " ".join(context.args[1:])
        if not text:
            raise ValueError
        if minutes <= 0 or minutes > 1440:  # макс — 1 день
            await update.message.reply_text("Минуты должны быть от 1 до 1440.")
            return
    except (ValueError, IndexError):
        await update.message.reply_text("Неверный формат. Пример: /remind 10 Проверь дыхание")
        return

    # Отменяем предыдущее кастомное напоминание
    if "user_reminder_job" in context.bot_data:
        context.bot_data["user_reminder_job"].schedule_removal()

    job = context.job_queue.run_once(
        send_custom_reminder,
        when=minutes * 60,
        data={"text": text, "chat_id": update.effective_chat.id}
    )
    context.bot_data["user_reminder_job"] = job

    await update.message.reply_text(f"✅ Напомню через {minutes} мин:\n«{text}»")

async def send_custom_reminder(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    await context.bot.send_message(
        chat_id=job_data["chat_id"],
        text=f"🔔 Напоминание:\n{job_data['text']}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Получено. Следующее стандартное напоминание через 20 минут.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", set_reminder))  # ← латиница!
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен. Напиши ему /start")
    app.run_polling()

if __name__ == "__main__":
    main()