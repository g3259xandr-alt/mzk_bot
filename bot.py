import os
import asyncio
import logging

from maxapi import Bot, Dispatcher
from maxapi.filters.command import CommandStart
from maxapi.types import BotStarted, MessageCreated, MessageCallback, CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# ======================= ДАННЫЕ (редактируйте здесь) =======================

WELCOME_TEXT = (
    '👋 Здравствуйте! Я — бот компании "МЗК".\n\n'
    '🚚 Мы — самая крупная сеть пунктов приема цветного и черного '
    'металла с вывозом в Республике Мордовия\n\n'
    'Чем могу быть полезен:\n'
    '⚙️ Помогу подобрать ближайший пункт приема для Вас\n'
    '⚙️ Помогу узнать актуальные цены на чёрный и цветной металл\n'
    '⚙️ Расскажу про вакансии на предприятии\n\n'
    '🤝 Я всегда на связи и готов помочь Вам!'
)

PRICES_TEXT = (
    '💰 Актуальные цены на металлолом:\n\n'
    '🔩 Чёрный металл:\n'
    '  • Лом стальной — 18 000 ₽/т\n'
    '  • Чугун — 15 000 ₽/т\n\n'
    '🟠 Цветной металл:\n'
    '  • Медь — 650 ₽/кг\n'
    '  • Алюминий — 130 ₽/кг\n'
    '  • Латунь — 340 ₽/кг\n\n'
    'ℹ️ Цены могут меняться в зависимости от объёма и качества сырья. '
    'Уточняйте у оператора пункта приёма.'
)

POINTS = [
    {
        "name": "Пункт приёма №1 (г. Саранск)",
        "address": "г. Саранск, ул. Промышленная, д. 10",
        "hours": "Пн-Сб: 08:00–18:00, Вс: выходной",
        "phone": "+7 (834) 000-00-01",
    },
    {
        "name": "Пункт приёма №2 (г. Рузаевка)",
        "address": "г. Рузаевка, ул. Заводская, д. 5",
        "hours": "Пн-Пт: 09:00–17:00, Сб-Вс: выходной",
        "phone": "+7 (834) 000-00-02",
    },
]

VACANCIES = [
    {
        "title": "Приёмщик металлолома",
        "salary": "от 45 000 ₽",
        "desc": "Приём, взвешивание и сортировка металла на пункте приёма.",
    },
    {
        "title": "Водитель (вывоз металлолома)",
        "salary": "от 55 000 ₽",
        "desc": "Вывоз металлолома от клиентов, наличие категории C приветствуется.",
    },
]

# =============================================================================


def main_menu() -> list:
    """Собирает клавиатуру главного меню."""
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="💰 Цены на металл", payload="prices"))
    kb.row(CallbackButton(text="📍 Пункты приёма", payload="points"))
    kb.row(CallbackButton(text="💼 Вакансии", payload="vacancies"))
    return [kb.as_markup()]


def back_menu() -> list:
    """Клавиатура с одной кнопкой 'Назад в меню'."""
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def format_points() -> str:
    text = "📍 Наши пункты приёма:\n\n"
    for p in POINTS:
        text += (
            f"🏢 {p['name']}\n"
            f"   Адрес: {p['address']}\n"
            f"   Режим работы: {p['hours']}\n"
            f"   Телефон: {p['phone']}\n\n"
        )
    return text.strip()


def format_vacancies() -> str:
    text = "💼 Открытые вакансии:\n\n"
    for v in VACANCIES:
        text += (
            f"▪️ {v['title']}\n"
            f"   Зарплата: {v['salary']}\n"
            f"   {v['desc']}\n\n"
        )
    text += "Резюме и вопросы — напишите нам, и мы свяжемся с Вами!"
    return text


# ======================= ОБРАБОТЧИКИ =======================

@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=WELCOME_TEXT,
        attachments=main_menu(),
    )


@dp.message_created(CommandStart())
async def on_start_command(event: MessageCreated):
    await event.message.answer(WELCOME_TEXT, attachments=main_menu())


@dp.message_callback()
async def on_callback(event: MessageCallback):
    payload = event.callback.payload

    if payload == "prices":
        await event.message.answer(PRICES_TEXT, attachments=back_menu())

    elif payload == "points":
        await event.message.answer(format_points(), attachments=back_menu())

    elif payload == "vacancies":
        await event.message.answer(format_vacancies(), attachments=back_menu())

    elif payload == "menu":
        await event.message.answer(WELCOME_TEXT, attachments=main_menu())


@dp.message_created()
async def on_any_message(event: MessageCreated):
    # На любое другое сообщение показываем меню ещё раз
    await event.message.answer(
        "Пожалуйста, выберите пункт меню 👇",
        attachments=main_menu(),
    )


async def main():
    print("=== БОТ МЗК ЗАПУЩЕН ===")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
