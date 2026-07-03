import os
import asyncio
import logging
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, MessageCreated

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="👋 Привет! Напиши что-нибудь!"
    )


@dp.message_created()
async def echo(event: MessageCreated):
    print(f"Получено сообщение: {event}")
    try:
        text = event.message.body.text
        await event.message.answer(f"🔁 Эхо: {text}")
    except Exception as e:
        print(f"Ошибка: {e}")


async def main():
    print("=== БОТ ЗАПУЩЕН ===")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
