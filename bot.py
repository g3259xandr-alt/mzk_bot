import os
import asyncio
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="👋 Привет! Напиши что-нибудь!"
    )

@dp.message()
async def echo(event):
    print(f"Получено сообщение: {event}")
    print(f"Тип события: {type(event)}")
    try:
        text = event.message.body.text
        await event.bot.send_message(
            chat_id=event.chat_id,
            text=f"🔁 Эхо: {text}"
        )
    except Exception as e:
        print(f"Ошибка: {e}")

async def main():
    print("=== БОТ ЗАПУЩЕН ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
