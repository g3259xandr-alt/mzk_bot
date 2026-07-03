import os
import asyncio
import logging
from datetime import date

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


def get_prices_text() -> str:
    today = date.today().strftime("%d.%m.%Y")
    return (
        f'📊 Актуальный прайс на {today}\n\n'
        '➡️ Медь: 780 ₽/кг\n'
        '➡️ Латунь: 480 ₽/кг\n'
        '➡️ Алюминий: 125 ₽/кг\n'
        '➡️ Нержавейка: 35 ₽/кг\n'
        '➡️ Аккумуляторы (АКБ): 40 ₽/кг\n'
        '➡️ Чёрный лом: 13 ₽/кг\n\n'
        'Ждем вас на наших площадках!\n'
        'Контакты: ☎️ +7 (8342) 36-76-76'
    )


VACANCIES = [
    {
        "title": "Инженер-строитель",
        "salary": "от 90 000 руб.",
        "schedule": "5/2",
        "desc": "Планирование и организация строительных работ, составление смет, контроль строительного процесса, работа с надзорными органами.",
    },
    {
        "title": "Заместитель директора по финансам и экономике",
        "salary": "По результатам собеседования",
        "schedule": "5/2",
        "desc": "Руководство финансово-экономическим блоком, управление бюджетом, анализ рисков, финансовое планирование и взаимодействие с банками.",
    },
    {
        "title": "Юрисконсульт",
        "salary": "70 000 руб.",
        "schedule": "5/2",
        "desc": "Ведение претензионно-исковой и договорной работы, подготовка правовых заключений, мониторинг законодательства.",
    },
    {
        "title": "Электромонтер",
        "salary": "от 60 000 руб.",
        "schedule": "3/3 (08:00–20:00)",
        "desc": "Техническое обслуживание и ремонт электрооборудования предприятия, работа с электрическими схемами.",
    },
    {
        "title": "Слесарь-ремонтник",
        "salary": "60 000 руб.",
        "schedule": "3/3 (08:00–20:00)",
        "desc": "Техническое обслуживание и ремонт производственного оборудования. Опыт от 2 лет.",
    },
    {
        "title": "Водитель автомобиля 6 разряда (категория СЕ)",
        "salary": "140 000 руб.",
        "schedule": "Сменный",
        "desc": "Доставка грузов транспортом компании. Требуется опыт работы на грузовиках Scania от 3 лет.",
    },
    {
        "title": "Инженер-метролог",
        "salary": "55 000 руб.",
        "schedule": "5/2",
        "desc": "Поверка средств измерения, обслуживание весового хозяйства и дозиметрических приборов, подготовка документации.",
    },
    {
        "title": "Специалист по тендерным закупкам",
        "salary": "85 000 руб.",
        "schedule": "5/2",
        "desc": "Проведение тендеров, подготовка закупочной документации, заключение договоров поставки, логистика и контроль остатков ТМЦ.",
    },
    {
        "title": "Слесарь по ремонту автомобилей",
        "salary": "55 000 руб.",
        "schedule": "5/2 (08:00–17:00)",
        "desc": "Ремонт электрооборудования, проводки и агрегатов транспортных средств (КамАЗ, МАЗ, ГАЗ, ВАЗ, Scania).",
    },
]

PHONE = " (8-8342) 27-03-71"

# Пункты приёма, сгруппированные по официальным районам Республики Мордовия
POINTS_BY_DISTRICT = {
    "Ардатовский район": [
        {"address": "Ардатов, ул. Чапаева, 41", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Атюрьевский район": [
        {"address": "с. Атюрьево, ул. Дорожная, 5Б", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Атяшевский район": [
        {"address": "р.п. Атяшево, ул. Гражданская, 3А", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Большеберезниковский район": [
        {"address": "Б. Березники, ул. М.Горького, 127", "hours": "Пн-Пт: 9:00-18:00"},
    ],
    "Большеигнатовский район": [
        {"address": "с. Б.Игнатово, ул. Советская", "hours": "Ср-Вс: 13:00-17:00"},
    ],
    "Дубёнский район": [
        {"address": "с. Дубёнки, ул. Пионерская, 1", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Ельниковский район": [
        {"address": "с. Ельники, ул. Мира, 1", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Инсарский район": [
        {"address": "Инсар, ул. Транспортная, 1а", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Ичалковский район": [
        {"address": "с. Ичалки, ул. Первомайская, 29", "hours": "Ежедневно: 8:00-20:00"},
    ],
    "Кадошкинский район": [
        {"address": "р.п. Кадошкино, проезд Железнодорожный", "hours": "Пн, Ср: 11:00-17:00, Сб: 9:00-17:00"},
    ],
    "Ковылкинский район": [
        {"address": "Ковылкино, ул. Мичурина, 9А", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Кочкуровский район": [
        {"address": "с. Кочкурово, ул. Советская, 65", "hours": "Вт-Сб: 8:00-17:00"},
    ],
    "Краснослободский район": [
        {"address": "Краснослободск, ул. Кирова, 107Д", "hours": "Вс-Чт: 8:00-16:00"},
        {"address": "Краснослободск, Бобылевские выселки, ул. Трудовая, 1А", "hours": "Вт-Сб: 8:00-17:00"},
        {"address": "Краснослободск, Кировский пер., 16", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Лямбирский район": [
        {"address": "с. Лямбирь, ул. Октябрьская, 115Б", "hours": "Вт-Сб: 8:00-17:00"},
        {"address": "Атемар, ул. Центральная", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Ромодановский район": [
        {"address": "р.п. Ромоданово, ул. Полежаева, 44", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Рузаевский район": [
        {"address": "Рузаевка, ул. Тимирязева, 15", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Рузаевка, ул. Маяковского, 173", "hours": "Ежедневно: 8:00-20:00"},
        {"address": "Рузаевка, ул. Рубцова, 16А", "hours": "Ежедневно: 8:00-20:00"},
    ],
    "Саранск (городской округ)": [
        {"address": "Саранск, ул. 1-я Промышленная, 41", "hours": "Ежедневно: 8:00-17:00"},
        {"address": "Саранск, ул. 1-я Промышленная, 13", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Крылова, 2", "hours": "Вт-Сб: 8:00-17:00"},
        {"address": "Саранск, ул. Пролетарская, 144", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Севастопольская, 128а", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Рузаевская, 36Б", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Рабочая, 126", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "р.п. Ялга, пер. Вокзальный, 3", "hours": "Ежедневно: 8:00-20:00"},
        {"address": "р.п. Ялга, ул. Российская, 25/1", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, Юго-западное шоссе, 10", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Строительная, 2/1", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Веселовского, 58Б", "hours": "Пн-Пт: 9:00-18:00"},
        {"address": "Саранск, ул. Сущинского (тер. ГК Таврия)", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, ул. Пушкина (тер. ГК Жигули)", "hours": "Пн-Пт: 8:30-17:30"},
        {"address": "Саранск, Проспект 70 лет Октября, 167", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Саранск, Александровское шоссе, 37Б", "hours": "Вт-Сб: 9:00-18:00"},
        {"address": "Саранск, ул. Косарева, 128", "hours": "Пн-Пт: 8:00-17:00 (Не работает)"},
        {"address": "Саранск, рп. Николаевка, ул. Ленина, 89", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "с. Берсеневка, ул. Северная, 12Б", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Старошайговский район": [
        {"address": "Ст. Шайгово, ул. Больничная, 15А", "hours": "Пн-Пт: 9:00-18:00"},
    ],
    "Темниковский район": [
        {"address": "Темников, ул. Ленина, 47", "hours": "Пн-Пт: 8:00-17:00"},
    ],
    "Теньгушевский район": [
        {"address": "с. Теньгушево, ул. Ленина, 133д", "hours": "Ср-Вс: 9:00-18:00"},
    ],
    "Торбеевский район": [
        {"address": "р.п. Торбеево, ул. Сельхозтехника, 55", "hours": "Ежедневно: 8:00-20:00"},
    ],
    "Чамзинский район": [
        {"address": "р.п. Комсомольский", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "р.п. Комсомольский, ул. Заречная, гараж 28", "hours": "Ежедневно: 8:00-17:00"},
        {"address": "р.п. Чамзинка, ул. Зеленая, 46", "hours": "Пн-Пт: 8:00-17:00"},
        {"address": "Чамзинка, ул. Победы, 6", "hours": "Ежедневно: 8:00-17:00"},
    ],
}
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


def districts_menu() -> list:
    """Клавиатура со списком районов."""
    kb = InlineKeyboardBuilder()
    for district in POINTS_BY_DISTRICT.keys():
        kb.row(CallbackButton(text=f"📍 {district}", payload=f"district:{district}"))
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def district_back_menu() -> list:
    """Клавиатура: назад к списку районов и в главное меню."""
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="⬅️ К списку районов", payload="points"))
    kb.row(CallbackButton(text="🏠 Главное меню", payload="menu"))
    return [kb.as_markup()]


def format_district_points(district: str) -> str:
    points = POINTS_BY_DISTRICT.get(district, [])
    text = f"📍 {district}:\n\n"
    for p in points:
        text += (
            f"🏢 Приёмный пункт\n"
            f"   Адрес: {p['address']}\n"
            f"   Режим работы: {p['hours']}\n"
            f"   Телефон: {PHONE}\n\n"
        )
    return text.strip()


def format_vacancies() -> str:
    text = "💼 Открытые вакансии:\n\n"
    for i, v in enumerate(VACANCIES, start=1):
        text += (
            f"{i}. {v['title']}\n"
            f"   💰 {v['salary']} | 🗓 {v['schedule']}\n"
            f"   {v['desc']}\n\n"
        )
    text += "📞 По вопросам трудоустройства звоните: " + PHONE
    return text


# ======================= ОБРАБОТЧИКИ =======================

@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=WELCOME_TEXT,
        attachments=main_menu(),
    )


@dp.message_callback()
async def on_callback(event: MessageCallback):
    payload = event.callback.payload

    try:
        await event.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

    if payload == "prices":
        await event.message.answer(get_prices_text(), attachments=back_menu())
    elif payload == "points":
        await event.message.answer(
            "Выберите район, чтобы увидеть пункты приёма 👇",
            attachments=districts_menu(),
        )
    elif payload.startswith("district:"):
        district = payload.split("district:", 1)[1]
        await event.message.answer(
            format_district_points(district),
            attachments=district_back_menu(),
        )
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
