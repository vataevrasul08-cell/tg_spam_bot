import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ====== Настройки через переменные окружения ======
TOKEN = os.environ.get("TOKEN")             # Токен бота из BotFather
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # Твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ====== Словарь для активных диалогов ======
# Структура: {user_id: {"username": str, "last_message": datetime}}
active_users = {}

# ====== Сообщения от пользователей ======
@dp.message_handler(lambda message: message.from_user.id != ADMIN_ID)
async def forward_to_admin(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Сохраняем пользователя и время последнего сообщения
    active_users[user_id] = {"username": username, "last_message": datetime.now()}

    # Пересылаем сообщение администратору
    await bot.send_message(
        ADMIN_ID,
        f"Сообщение от @{username} (ID: {user_id}):\n{message.text}"
    )

# ====== Ответ администратора ======
@dp.message_handler(lambda message: message.from_user.id == ADMIN_ID)
async def admin_reply(message: types.Message):
    # Ответить можно только на пересланное сообщение от пользователя
    if not message.reply_to_message:
        await message.reply("Ответьте на пересланное сообщение пользователя.")
        return

    # Получаем user_id из текста пересланного сообщения
    try:
        first_line = message.reply_to_message.text.splitlines()[0]
        user_id = int(first_line.split("(ID: ")[1].split(")")[0])
    except Exception:
        await message.reply("Не удалось определить пользователя. Пересылай сообщение заново.")
        return

    reply_text = message.text
    await bot.send_message(user_id, f"Ответ администратора:\n{reply_text}")
    # Обновляем время последнего сообщения
    active_users[user_id]["last_message"] = datetime.now()
    await message.reply(f"Сообщение отправлено @{active_users[user_id]['username']}")

# ====== Фоновая очистка старых диалогов ======
async def cleanup_old_dialogs():
    while True:
        now = datetime.now()
        to_remove = [
            uid for uid, info in active_users.items()
            if now - info["last_message"] > timedelta(days=1)
        ]
        for uid in to_remove:
            del active_users[uid]
            print(f"Диалог с пользователем {uid} очищен (более 24 часов без сообщений).")
        await asyncio.sleep(3600)  # проверка каждый час

# ====== Запуск бота ======
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_old_dialogs())
    executor.start_polling(dp, skip_updates=True)

