import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from rates import convert

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CURRENCIES = [
    ("USD", "🇺🇸 USD"),
    ("KZT", "🇰🇿 KZT"),
    ("EUR", "🇪🇺 EUR"),
    ("CNY", "🇨🇳 CNY"),
    ("RUB", "🇷🇺 RUB"),
    ("CHF", "🇨🇭 CHF"),
    ("GBP", "🇬🇧 GBP"),
    ("TRY", "🇹🇷 TRY"),
]


def currency_keyboard(prefix: str, exclude: str = None):
    buttons = []
    row = []
    for code, label in CURRENCIES:
        if code == exclude:
            continue
        row.append(InlineKeyboardButton(label, callback_data=f"{prefix}_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "💱 <b>Конвертер валют</b>\n\nВыбери исходную валюту:",
        parse_mode="HTML",
        reply_markup=currency_keyboard("from")
    )


async def handle_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    base = query.data.split("_")[1]
    context.user_data["base"] = base
    await query.edit_message_text(
        f"✅ Исходная: <b>{base}</b>\n\nТеперь выбери целевую валюту:",
        parse_mode="HTML",
        reply_markup=currency_keyboard("to", exclude=base)
    )


async def handle_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target = query.data.split("_")[1]
    context.user_data["target"] = target
    base = context.user_data.get("base")
    await query.edit_message_text(
        f"✅ <b>{base} → {target}</b>\n\nВведи сумму:",
        parse_mode="HTML"
    )


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base = context.user_data.get("base")
    target = context.user_data.get("target")

    if not base or not target:
        await update.message.reply_text(
            "Нажми /start чтобы начать.",
        )
        return

    text = update.message.text.strip().replace(",", ".")
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text("⚠️ Введи число, например: <code>100</code>", parse_mode="HTML")
        return

    result = await convert(base, target, amount)
    if result is None:
        await update.message.reply_text("⚠️ Не удалось получить курс. Попробуй позже.")
        return

    rate = await convert(base, target, 1)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Конвертировать ещё", callback_data="restart")]
    ])
    await update.message.reply_text(
        f"💰 <b>{amount} {base} = {result} {target}</b>\n\n"
        f"📊 1 {base} = {rate} {target}",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text(
        "💱 <b>Конвертер валют</b>\n\nВыбери исходную валюту:",
        parse_mode="HTML",
        reply_markup=currency_keyboard("from")
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_from, pattern=r"^from_"))
    app.add_handler(CallbackQueryHandler(handle_to, pattern=r"^to_"))
    app.add_handler(CallbackQueryHandler(handle_restart, pattern=r"^restart$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()