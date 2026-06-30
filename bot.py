import os
import asyncio
import maxapi.types as t

# Выводим все доступные типы
print("=== Доступные типы в maxapi.types ===")
print([x for x in dir(t) if not x.startswith('_')])

from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="👋 Привет! Я запустился!"
    )

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
