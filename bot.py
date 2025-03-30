from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
from scraper import get_working_hours  # Импортируем функцию из scraper.py

# Вставьте ваш токен сюда
API_TOKEN = '7667656634:AAFGezCC6FxuKiDofhiAMMJ4DLOyP97KOzU'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот, который показывает часы работы клиники. Напишите /hours.")

# Обработчик команды /hours
@dp.message(Command("hours"))
async def send_working_hours(message: types.Message):
    # Получаем отформатированное расписание из scraper.py
    formatted_schedule = get_working_hours()

    if formatted_schedule:
        # Формируем сообщение с отформатированным расписанием
        response = "Часы работы клиники:\n\n" + formatted_schedule
    else:
        response = "Не удалось получить часы работы. Попробуйте позже."

    # Отправляем ответ пользователю
    await message.answer(response)

# Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())