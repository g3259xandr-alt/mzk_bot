import os
import asyncio
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, NewMessage

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="👋 Привет! Я эхо-бот!\n\nНапиши мне что-нибудь — я повторю!"
    )

@dp.message()
async def echo(event: NewMessage):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=f"🔁 Эхо: {event.message.body.text}"
    )

async def main():
    print("Эхо-бот запущен и ждет сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
