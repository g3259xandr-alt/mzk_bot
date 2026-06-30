import os
import asyncio
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted

# Получаем токен из настроек хостинга (не пишем его прямо в коде для безопасности!)
BOT_TOKEN = os.getenv("f9LHodD0cOLpiUUqZl2woipOkeMzfejHZtXHFW4ukquMz9Eicejd3Jyov5gTbLqSljepOxiZIvtRt0ir7MOc")

# Инициализируем бота
bot = Bot(f9LHodD0cOLpiUUqZl2woipOkeMzfejHZtXHFW4ukquMz9Eicejd3Jyov5gTbLqSljepOxiZIvtRt0ir7MOc)
dp = Dispatcher()

# Этот обработчик срабатывает, когда пользователь нажимает кнопку "Старт" (или запускает бота впервые)
@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я тестовый бот. Рад знакомству! Вы нажали кнопку Старт."
    )

async def main():
    # Отключаем вебхуки на всякий случай, чтобы работал режим опроса (polling)
    try:
        await bot.delete_webhook()
    except:
        pass
    
    # Запускаем бота
    print("Бот запущен и ждет сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
