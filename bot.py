import logging
import time
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Хранит активные напоминания для пользователей
active_reminders = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Установить напоминание", callback_data='set_reminder')],
        [InlineKeyboardButton("Отменить напоминание", callback_data='cancel_reminder')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Привет! Я бот для напоминаний. Выберите действие:', reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # необходимо, чтобы убрать индикатор загрузки

    if query.data == 'set_reminder':
        await query.message.reply_text('Введите время в секундах для установки напоминания (например, 10):')
    elif query.data == 'cancel_reminder':
        user_id = query.from_user.id
        if user_id in active_reminders:
            del active_reminders[user_id]  # Удаляем напоминание
            await query.message.reply_text('Ваше напоминание отменено.')
        else:
            await query.message.reply_text('У вас нет активных напоминаний для отмены.')


async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    # Проверяем, есть ли активные напоминания у пользователя
    if user_id in active_reminders:
        await update.message.reply_text(
            'У вас уже есть активное напоминание. Пожалуйста, отмените его перед установкой нового.')
        return

    try:
        time_in_seconds = int(update.message.text)  # Пробуем преобразовать текст в число
        if time_in_seconds <= 0:
            await update.message.reply_text('Пожалуйста, введите корректное положительное время в секундах.')
            return

        await update.message.reply_text('Введите текст вашего напоминания:')
        # Сохраняем время в user_data для доступа при дальнейшем вводе
        context.user_data['reminder_time'] = time_in_seconds
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректное время в секундах (например, 10).')


async def handle_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if 'reminder_time' in context.user_data:
        reminder_text = update.message.text
        time_in_seconds = context.user_data['reminder_time']

        # Создаем новый поток для напоминания
        active_reminders[user_id] = reminder_text  # Сохраняем активное напоминание
        threading.Thread(target=schedule_reminder, args=(user_id, reminder_text, time_in_seconds)).start()

        await update.message.reply_text(f'Напоминание установлено на {time_in_seconds} секунд.')
        del context.user_data['reminder_time']  # Очищаем данные о времени
    else:
        await update.message.reply_text('Сначала установите время напоминания.')


def schedule_reminder(user_id, reminder_text, delay):
    time.sleep(delay)  # Ждем указанное время
    application = ApplicationBuilder().token('YOUR_BOT_TOKEN').build()
    application.bot.send_message(chat_id=user_id, text=f'Напоминание: {reminder_text}')
    if user_id in active_reminders:
        del active_reminders[user_id]  # Удаляем после напоминания


def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    global application
    application = ApplicationBuilder().token('YOUR_BOT_TOKEN').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_input))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_text))

    application.run_polling()


if __name__ == '__main__':
    main()