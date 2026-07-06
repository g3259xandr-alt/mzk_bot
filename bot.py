import os
import json
import asyncio
import logging
from datetime import date

from maxapi import Bot, Dispatcher
from maxapi.filters.command import CommandStart, Command
from maxapi.types import BotStarted, MessageCreated, MessageCallback, CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRICES_FILE = os.path.join(BASE_DIR, "prices.json")

# ID пользователей MAX, которым разрешено менять цены.
# Узнать свой ID можно, написав боту команду /myid, затем вписать число сюда
# (или в переменную окружения ADMIN_IDS через запятую: "123456,789012")
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x
}


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

# Список позиций прайса: key — внутренний идентификатор, label — как показывать,
# aliases — другие слова, по которым бот тоже узнает эту позицию в командах.
PRICE_ITEMS = [
    {"key": "med", "label": "Медь", "aliases": ["медь"]},
    {"key": "latun", "label": "Латунь", "aliases": ["латунь"]},
    {"key": "alum", "label": "Алюминий", "aliases": ["алюминий", "алюминии"]},
    {"key": "nerzh", "label": "Нержавейка", "aliases": ["нержавейка", "нержа", "нержавеющая сталь"]},
    {"key": "akb", "label": "Аккумуляторы (АКБ)", "aliases": ["акб", "аккумуляторы", "аккумулятор"]},
    {"key": "chern", "label": "Чёрный лом", "aliases": ["чёрный лом", "черный лом", "чермет", "лом"]},
]

DEFAULT_PRICES = {
    "med": 780,
    "latun": 480,
    "alum": 125,
    "nerzh": 35,
    "akb": 40,
    "chern": 13,
}


def load_prices() -> dict:
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # на случай если в файле не хватает какой-то позиции
            for k, v in DEFAULT_PRICES.items():
                data.setdefault(k, v)
            return data
        except Exception as e:
            print(f"Не удалось прочитать {PRICES_FILE}, использую значения по умолчанию: {e}")
    return dict(DEFAULT_PRICES)


def save_prices(prices: dict) -> None:
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)


PRICES = load_prices()


def format_price(value) -> str:
    # 780.0 -> "780", 780.5 -> "780.5"
    if float(value) == int(value):
        return str(int(value))
    return str(value)


def get_prices_text() -> str:
    today = date.today().strftime("%d.%m.%Y")
    lines = [f'📊 Актуальный прайс на {today}\n']
    for item in PRICE_ITEMS:
        price = PRICES.get(item["key"], "—")
        lines.append(f'➡️ {item["label"]}: {format_price(price)} ₽/кг')
    lines.append('')
    lines.append('Ждем вас на наших площадках!')
    lines.append('Контакты: ☎️ +7 (8342) 36-76-76')
    return "\n".join(lines)


def prices_template_text() -> str:
    """Текст в формате, который можно скопировать, поправить и отправить обратно в /setprices."""
    return "\n".join(f'{item["label"]}: {format_price(PRICES.get(item["key"], 0))}' for item in PRICE_ITEMS)


def normalize(text: str) -> str:
    return text.strip().lower().replace("ё", "е")


def find_price_key(user_text: str):
    """Находит внутренний key позиции по названию/алиасу, которое ввёл человек."""
    norm = normalize(user_text)
    for item in PRICE_ITEMS:
        candidates = [item["label"]] + item["aliases"]
        if norm in (normalize(c) for c in candidates):
            return item["key"]
    return None


def label_for(key: str) -> str:
    for item in PRICE_ITEMS:
        if item["key"] == key:
            return item["label"]
    return key


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

# Пункты приёма, сгруппированные по официальным районам Республики Мордовия.
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
    "Саранск (городской округ)": {
        "Ленинский": [
            {"address": "Саранск, ул. Рабочая, 126", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, Юго-западное шоссе, 10", "hours": "Пн-Пт: 8:00-17:00"},
        ],
        "Октябрьский": [
            {"address": "Саранск, рп. Николаевка, ул. Ленина, 89", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, Александровское шоссе, 37Б", "hours": "Вт-Сб: 9:00-18:00"},
            {"address": "р.п. Ялга, ул. Российская, 25/1", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "р.п. Ялга, пер. Вокзальный, 3", "hours": "Ежедневно: 8:00-20:00"},
            {"address": "Саранск, ул. Рузаевская, 36Б", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, ул. Крылова, 2", "hours": "Вт-Сб: 8:00-17:00"},
            {"address": "Саранск, ул. Косарева, 128", "hours": "Пн-Пт: 8:00-17:00 (Не работает)"},
            {"address": "Саранск, Проспект 70 лет Октября, 167", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, ул. Сущинского (тер. ГК Таврия)", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, ул. Севастопольская, 128а", "hours": "Пн-Пт: 8:00-17:00"},
        ],
        "Пролетарский": [
            {"address": "Саранск, ул. 1-я Промышленная, 13", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, ул. 1-я Промышленная, 41", "hours": "Ежедневно: 8:00-17:00"},
            {"address": "Саранск, ул. Пролетарская, 144", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, ул. Пушкина (тер. ГК Жигули)", "hours": "Пн-Пт: 8:30-17:30"},
            {"address": "Саранск, ул. Веселовского, 58Б", "hours": "Пн-Пт: 9:00-18:00"},
            {"address": "с. Берсеневка, ул. Северная, 12Б", "hours": "Пн-Пт: 8:00-17:00"},
            {"address": "Саранск, ул. Строительная, 2/1", "hours": "Пн-Пт: 8:00-17:00"},
        ],
    },
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
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="💰 Цены на металл", payload="prices"))
    kb.row(CallbackButton(text="📍 Пункты приёма", payload="points"))
    kb.row(CallbackButton(text="💼 Вакансии", payload="vacancies"))
    return [kb.as_markup()]


def back_menu() -> list:
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def districts_menu() -> list:
    kb = InlineKeyboardBuilder()
    for district in POINTS_BY_DISTRICT.keys():
        kb.row(CallbackButton(text=f"📍 {district}", payload=f"district:{district}"))
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def subdistricts_menu(district: str) -> list:
    kb = InlineKeyboardBuilder()
    subdistricts = POINTS_BY_DISTRICT[district]
    for sub in subdistricts.keys():
        kb.row(CallbackButton(text=f"📍 {sub}", payload=f"sub:{district}|{sub}"))
    kb.row(CallbackButton(text="⬅️ К списку районов", payload="points"))
    kb.row(CallbackButton(text="🏠 Главное меню", payload="menu"))
    return [kb.as_markup()]


def district_back_menu() -> list:
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="⬅️ К списку районов", payload="points"))
    kb.row(CallbackButton(text="🏠 Главное меню", payload="menu"))
    return [kb.as_markup()]


def subdistrict_back_menu(district: str) -> list:
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="⬅️ К районам города", payload=f"district:{district}"))
    kb.row(CallbackButton(text="📍 К списку районов", payload="points"))
    kb.row(CallbackButton(text="🏠 Главное меню", payload="menu"))
    return [kb.as_markup()]


def format_points_list(title: str, points: list) -> str:
    text = f"📍 {title}:\n\n"
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


# ======================= АДМИНСКИЕ КОМАНДЫ (управление ценами) =======================

@dp.message_created(Command('myid'))
async def cmd_myid(event: MessageCreated):
    await event.message.answer(
        f"Ваш ID в MAX: {event.from_user.user_id}\n\n"
        f"Чтобы получить право менять цены, передайте это число разработчику "
        f"бота — он добавит его в список администраторов."
    )


@dp.message_created(Command('editprices'))
async def cmd_editprices(event: MessageCreated):
    if event.from_user.user_id not in ADMIN_IDS:
        await event.message.answer("⛔ У вас нет прав для изменения цен.")
        return

    text = (
        "✏️ Скопируйте текст ниже, поправьте цифры и отправьте его обратно, "
        "добавив в начало команду /setprices (в первой строке):\n\n"
        "/setprices\n" + prices_template_text()
    )
    await event.message.answer(text)


@dp.message_created(Command('setprices'))
async def cmd_setprices(event: MessageCreated):
    if event.from_user.user_id not in ADMIN_IDS:
        await event.message.answer("⛔ У вас нет прав для изменения цен.")
        return

    full_text = event.message.body.text
    # убираем саму команду /setprices из текста, дальше идут строки с ценами
    lines = full_text.split("\n")[1:]

    updated = []
    not_recognized = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # разделитель может быть ":" или "-"
        for sep in (":", "-", "—"):
            if sep in line:
                name_part, value_part = line.split(sep, 1)
                break
        else:
            not_recognized.append(line)
            continue

        key = find_price_key(name_part)
        if not key:
            not_recognized.append(line)
            continue

        value_str = value_part.strip().replace(",", ".").split()[0]
        try:
            new_value = float(value_str)
        except ValueError:
            not_recognized.append(line)
            continue

        PRICES[key] = new_value
        updated.append(f"{label_for(key)}: {format_price(new_value)}")

    if updated:
        save_prices(PRICES)

    reply = ""
    if updated:
        reply += "✅ Обновлены цены:\n" + "\n".join(updated) + "\n\n"
    if not_recognized:
        reply += "⚠️ Не удалось распознать строки:\n" + "\n".join(not_recognized) + "\n\n"
    if not updated and not not_recognized:
        reply = "Не нашёл ни одной строки с ценами. Формат: Медь: 800"

    await event.message.answer(reply.strip())


@dp.message_created(Command('setprice'))
async def cmd_setprice(event: MessageCreated):
    if event.from_user.user_id not in ADMIN_IDS:
        await event.message.answer("⛔ У вас нет прав для изменения цен.")
        return

    parts = event.message.body.text.split(maxsplit=2)
    if len(parts) < 3:
        await event.message.answer(
            "Формат: /setprice <металл> <цена>\nНапример: /setprice медь 800"
        )
        return

    key = find_price_key(parts[1])
    if not key:
        available = ", ".join(item["label"] for item in PRICE_ITEMS)
        await event.message.answer(f"Не знаю такую позицию.\nДоступные: {available}")
        return

    try:
        new_value = float(parts[2].replace(",", "."))
    except ValueError:
        await event.message.answer("Цена должна быть числом. Например: /setprice медь 800")
        return

    PRICES[key] = new_value
    save_prices(PRICES)
    await event.message.answer(f"✅ {label_for(key)}: {format_price(new_value)} ₽/кг")


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
        data = POINTS_BY_DISTRICT.get(district)

        if isinstance(data, dict):
            await event.message.answer(
                f"Выберите район города {district.split(' (')[0]} 👇",
                attachments=subdistricts_menu(district),
            )
        else:
            await event.message.answer(
                format_points_list(district, data),
                attachments=district_back_menu(),
            )

    elif payload.startswith("sub:"):
        raw = payload.split("sub:", 1)[1]
        district, sub = raw.split("|", 1)
        points = POINTS_BY_DISTRICT[district][sub]
        title = f"{district.split(' (')[0]}, {sub} район"
        await event.message.answer(
            format_points_list(title, points),
            attachments=subdistrict_back_menu(district),
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
