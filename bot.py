import os
import re
import csv
import io
import json
import time
import asyncio
import logging
from datetime import date

import aiohttp

from maxapi import Bot, Dispatcher
from maxapi.filters.command import CommandStart, Command
from maxapi.types import BotStarted, MessageCreated, MessageCallback, CallbackButton, LinkButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mzk_bot")

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================= ИСТОЧНИКИ ДАННЫХ (Google Sheets) =======================
# Данные редактируются в самой Google Таблице (листы "Цены", "Вакансии", "Пункты").
# Бот периодически перечитывает опубликованные CSV-версии этих листов и кеширует
# результат в памяти, поэтому изменения в таблице появляются в боте автоматически,
# без каких-либо команд редактирования в мессенджере.

PRICES_SHEET_URL = os.getenv(
    "PRICES_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRRIt0VXVeQzCHNuchxHTzqeMTz67gui7OYOamrMDnq5c7XaJRe_lgZjDoX8hUYlAiVMlrmZtOb0APV/pub?gid=0&single=true&output=csv",
)
VACANCIES_SHEET_URL = os.getenv(
    "VACANCIES_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRRIt0VXVeQzCHNuchxHTzqeMTz67gui7OYOamrMDnq5c7XaJRe_lgZjDoX8hUYlAiVMlrmZtOb0APV/pub?gid=1300710276&single=true&output=csv",
)
POINTS_SHEET_URL = os.getenv(
    "POINTS_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRRIt0VXVeQzCHNuchxHTzqeMTz67gui7OYOamrMDnq5c7XaJRe_lgZjDoX8hUYlAiVMlrmZtOb0APV/pub?gid=722284172&single=true&output=csv",
)

# Как часто фоновым образом обновлять кеш из Google Таблиц (в секундах).
CACHE_TTL_SECONDS = int(os.getenv("SHEETS_CACHE_TTL", "300"))
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=15)

WELCOME_TEXT = (
    '👋 Здравствуйте! Я — бот компании "МЗК".\n\n'
    '🚚 Мы — самая крупная сеть пунктов приема цветного и черного '
    'металла с вывозом в Республике Мордовия\n\n'
    'Чем могу быть полезен:\n'
    '⚙️ Помогу подобрать ближайший пункт приема для Вас\n'
    '⚙️ Помогу узнать актуальные цены на чёрный и цветной металл\n'
    '⚙️ Расскажу про вакансии на предприятии\n\n'
    '🤝 Я всегда на связи и готов помочь Вам!\n\n'
)

PHONE = " (8-8342) 27-03-71"
VACANCIES_URL = "https://lom-rm.ru/vakansii/"
CALL_PHONE_NUMBER = "+79271714364"

HELP_TEXT = (
    "📋 Список команд\n\n"
    "/start — главное меню\n"
    "/help — этот список команд\n\n"
    "💰 Цены, 💼 вакансии и 📍 пункты приёма подтягиваются напрямую из "
    "Google Таблицы. Чтобы что-то изменить, отредактируйте данные в "
    f"таблице — бот подхватит изменения автоматически в течение "
    f"{max(1, CACHE_TTL_SECONDS // 60)} мин."
)


# ======================= КЕШ ДАННЫХ =======================

def _cache_path(name: str) -> str:
    return os.path.join(BASE_DIR, f"{name}_cache.json")


def load_disk_cache(name: str):
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("data")
    except Exception as e:
        logger.warning(f"[{name}] не удалось прочитать локальный кеш: {e}")
        return None


def save_disk_cache(name: str, data) -> None:
    path = _cache_path(name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": data, "fetched_at": time.time()}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"[{name}] не удалось сохранить локальный кеш: {e}")


# В памяти: последние успешно полученные данные. При старте подставляем то,
# что было сохранено на диске в прошлый раз, чтобы бот не оставался пустым,
# если Google Таблица временно недоступна.
DATA = {
    "prices": load_disk_cache("prices") or [],
    "vacancies": load_disk_cache("vacancies") or [],
    "points": load_disk_cache("points") or {},
}


def format_price(value) -> str:
    if float(value) == int(value):
        return str(int(value))
    return str(value)


def _clean(value) -> str:
    return (value or "").strip()


def _parse_price_value(raw: str):
    raw = (raw or "").strip().replace("\xa0", " ").replace(",", ".")
    if not raw:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", raw)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def _csv_reader(text: str) -> csv.DictReader:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [(f or "").strip() for f in reader.fieldnames]
    return reader


def parse_prices_csv(text: str) -> list:
    items = []
    for row in _csv_reader(text):
        name = _clean(row.get("Название"))
        price = _parse_price_value(row.get("Цена"))
        if not name or price is None:
            continue
        items.append({"name": name, "price": price})
    return items


def parse_vacancies_csv(text: str) -> list:
    vacancies = []
    for row in _csv_reader(text):
        title = _clean(row.get("Должность"))
        if not title:
            continue
        vacancies.append({
            "title": title,
            "salary": _clean(row.get("Зарплата")) or "не указана",
            "schedule": _clean(row.get("График")) or "-",
            "desc": _clean(row.get("Описание")),
        })
    return vacancies


def parse_points_csv(text: str) -> dict:
    raw_rows = []
    for row in _csv_reader(text):
        district = _clean(row.get("Район"))
        address = _clean(row.get("Адрес"))
        if not district or not address:
            continue
        raw_rows.append({
            "district": district,
            "sub": _clean(row.get("Подрайон")),
            "address": address,
            "hours": _clean(row.get("Режим работы")) or "-",
        })

    has_sub = {}
    for r in raw_rows:
        has_sub.setdefault(r["district"], False)
        if r["sub"]:
            has_sub[r["district"]] = True

    points = {}
    for r in raw_rows:
        district = r["district"]
        point = {"address": r["address"], "hours": r["hours"]}
        if has_sub[district]:
            sub_key = r["sub"] or "Прочее"
            points.setdefault(district, {}).setdefault(sub_key, []).append(point)
        else:
            points.setdefault(district, []).append(point)
    return points


async def _fetch_sheet_text(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=HTTP_TIMEOUT) as resp:
        resp.raise_for_status()
        raw = await resp.read()
    return raw.decode("utf-8-sig")


async def _refresh_one(session: aiohttp.ClientSession, name: str, url: str, parser) -> None:
    try:
        text = await _fetch_sheet_text(session, url)
        parsed = parser(text)
    except Exception as e:
        logger.warning(f"[{name}] не удалось обновить из Google Таблицы, использую прежние данные: {e}")
        return

    if not parsed:
        logger.warning(f"[{name}] Google Таблица вернула пустой лист, оставляю прежние данные")
        return

    DATA[name] = parsed
    save_disk_cache(name, parsed)
    logger.info(f"[{name}] обновлено из Google Таблицы ({len(parsed)} записей)")


async def refresh_all(session: aiohttp.ClientSession) -> None:
    await asyncio.gather(
        _refresh_one(session, "prices", PRICES_SHEET_URL, parse_prices_csv),
        _refresh_one(session, "vacancies", VACANCIES_SHEET_URL, parse_vacancies_csv),
        _refresh_one(session, "points", POINTS_SHEET_URL, parse_points_csv),
    )


async def cache_refresh_loop(session: aiohttp.ClientSession) -> None:
    while True:
        await asyncio.sleep(CACHE_TTL_SECONDS)
        await refresh_all(session)


# ======================= ТЕКСТЫ И КЛАВИАТУРЫ =======================

def get_prices_text() -> str:
    today = date.today().strftime("%d.%m.%Y")
    lines = [f'📊 Актуальный прайс на {today}\n']
    prices = DATA["prices"]
    if not prices:
        lines.append("Прайс временно недоступен, попробуйте чуть позже.")
    else:
        for item in prices:
            lines.append(f'➡️ {item["name"]}: {format_price(item["price"])} ₽/кг')
    lines.append('')
    lines.append('Ждем вас на наших площадках!')
    lines.append('Контакты: ☎️ +7 (8342) 36-76-76')
    return "\n".join(lines)


def format_vacancies() -> str:
    vacancies = DATA["vacancies"]
    text = "💼 Открытые вакансии:\n\n"
    if not vacancies:
        text += "Список вакансий временно недоступен, попробуйте чуть позже.\n\n"
    else:
        for i, v in enumerate(vacancies, start=1):
            text += (
                f"{i}. {v['title']}\n"
                f"   💰 {v['salary']} | 🗓 {v['schedule']}\n"
                f"   {v['desc']}\n\n"
            )
    text += "📞 По вопросам трудоустройства звоните: " + PHONE
    return text


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


def main_menu() -> list:
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="💰 Цены на металл", payload="prices"))
    kb.row(CallbackButton(text="📍 Пункты приёма", payload="points"))
    kb.row(CallbackButton(text="💼 Вакансии", payload="vacancies"))
    kb.row(LinkButton(text="📞 Позвонить", url=f"tel:{CALL_PHONE_NUMBER}"))
    return [kb.as_markup()]


def back_menu() -> list:
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def vacancies_menu() -> list:
    kb = InlineKeyboardBuilder()
    kb.row(LinkButton(text="🔗 Подробнее", url=VACANCIES_URL))
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def districts_menu() -> list:
    kb = InlineKeyboardBuilder()
    for district in DATA["points"].keys():
        kb.row(CallbackButton(text=f"📍 {district}", payload=f"district:{district}"))
    kb.row(CallbackButton(text="⬅️ Назад в меню", payload="menu"))
    return [kb.as_markup()]


def subdistricts_menu(district: str) -> list:
    kb = InlineKeyboardBuilder()
    subdistricts = DATA["points"][district]
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


# ======================= ОБРАБОТЧИКИ =======================

@dp.message_created(CommandStart())
async def cmd_start(event: MessageCreated):
    await event.message.answer(WELCOME_TEXT, attachments=main_menu())


@dp.message_created(Command('help'))
async def cmd_help(event: MessageCreated):
    await event.message.answer(HELP_TEXT)


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
        logger.info(f"Не удалось удалить сообщение: {e}")

    if payload == "prices":
        await event.message.answer(get_prices_text(), attachments=back_menu())

    elif payload == "points":
        if not DATA["points"]:
            await event.message.answer(
                "Список пунктов приёма временно недоступен, попробуйте чуть позже.",
                attachments=back_menu(),
            )
        else:
            await event.message.answer(
                "Выберите район, чтобы увидеть пункты приёма 👇",
                attachments=districts_menu(),
            )

    elif payload.startswith("district:"):
        district = payload.split("district:", 1)[1]
        data = DATA["points"].get(district)

        if isinstance(data, dict):
            await event.message.answer(
                f"Выберите район города {district.split(' (')[0]} 👇",
                attachments=subdistricts_menu(district),
            )
        elif data:
            await event.message.answer(
                format_points_list(district, data),
                attachments=district_back_menu(),
            )
        else:
            await event.message.answer(
                "Не нашёл пункты приёма в этом районе.",
                attachments=district_back_menu(),
            )

    elif payload.startswith("sub:"):
        raw = payload.split("sub:", 1)[1]
        district, sub = raw.split("|", 1)
        points = DATA["points"].get(district, {}).get(sub)
        if points:
            title = f"{district.split(' (')[0]}, {sub} район"
            await event.message.answer(
                format_points_list(title, points),
                attachments=subdistrict_back_menu(district),
            )
        else:
            await event.message.answer(
                "Не нашёл пункты приёма в этом районе.",
                attachments=subdistrict_back_menu(district),
            )

    elif payload == "vacancies":
        await event.message.answer(format_vacancies(), attachments=vacancies_menu())

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
    logger.info("=== БОТ МЗК ЗАПУЩЕН ===")
    async with aiohttp.ClientSession() as session:
        await refresh_all(session)
        asyncio.create_task(cache_refresh_loop(session))
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
