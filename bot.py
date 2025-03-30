from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import sqlite3
from scraper import get_working_hours, get_phones, get_patient_memo  # Импортируем функции для работы с расписанием и телефонами
from llm_agent import LLMAgent  # Импортируем класс LLMAgent

# Вставьте ваш токен сюда
API_TOKEN = '7667656634:AAFGezCC6FxuKiDofhiAMMJ4DLOyP97KOzU'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение к базе данных
conn = sqlite3.connect('cache/feedback.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для обратной связи (если она еще не существует)
cursor.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new',
    response TEXT
)
''')
conn.commit()

# Инициализация нейросети
llm_agent = LLMAgent()

# Определение состояний
class Form(StatesGroup):
    waiting_for_neural_question = State()  # Состояние ожидания вопроса нейросети

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Отправить отзыв или предложение")],
            [types.KeyboardButton(text="Задать вопрос специалисту")],
            [types.KeyboardButton(text="Просмотреть расписание")],
            [types.KeyboardButton(text="Просмотреть телефоны")],
            [types.KeyboardButton(text="Просмотреть памятку пациенту")],
            [types.KeyboardButton(text="Задать вопрос нейросети")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! Я бот для обратной связи и просмотра информации о клинике. Выберите действие:",
        reply_markup=keyboard
    )

# Обработчик кнопки "Задать вопрос нейросети"
@dp.message(lambda message: message.text == "Задать вопрос нейросети")
async def ask_neural_network_button(message: types.Message, state: FSMContext):
    await message.answer("Задайте ваш вопрос:")
    # Устанавливаем состояние ожидания вопроса
    await state.set_state(Form.waiting_for_neural_question)

# Обработчик текстовых сообщений в состоянии "ожидание вопроса нейросети"
@dp.message(Form.waiting_for_neural_question)
async def handle_neural_question(message: types.Message, state: FSMContext):
    # Проверяем, что текст существует
    if not message.text:
        await message.answer("Ошибка: пожалуйста, отправьте текстовое сообщение.")
        return

    # Отправляем вопрос в нейросеть
    response = llm_agent.generate_response(message.text)

    # Отправляем ответ пользователю
    await message.answer(f"Ответ нейросети:\n{response}")

    # Сбрасываем состояние
    await state.clear()

# Обработчик кнопки "Отправить отзыв или предложение"
@dp.message(lambda message: message.text == "Отправить отзыв или предложение")
async def ask_for_feedback(message: types.Message):
    await message.answer("Пожалуйста, напишите ваш отзыв или предложение:")

# Обработчик кнопки "Задать вопрос специалисту"
@dp.message(lambda message: message.text == "Задать вопрос специалисту")
async def ask_for_question(message: types.Message):
    await message.answer("Пожалуйста, напишите ваш вопрос. Мы ответим вам как можно скорее.")

# Обработчик кнопки "Просмотреть расписание"
@dp.message(lambda message: message.text == "Просмотреть расписание")
async def show_schedule(message: types.Message):
    # Получаем отформатированное расписание
    formatted_schedule = get_working_hours()

    if formatted_schedule:
        response = "Часы работы клиники:\n\n" + formatted_schedule
    else:
        response = "Не удалось получить часы работы. Попробуйте позже."

    await message.answer(response)

# Обработчик кнопки "Просмотреть телефоны"
@dp.message(lambda message: message.text == "Просмотреть телефоны")
async def show_phones(message: types.Message):
    # Получаем телефоны
    phones = get_phones()

    if phones:
        response = "Контактные телефоны клиники:\n\n" + phones
    else:
        response = "Не удалось получить телефоны. Попробуйте позже."

    await message.answer(response)

# Обработчик кнопки "Просмотреть памятку пациенту"
@dp.message(lambda message: message.text == "Просмотреть памятку пациенту")
async def show_patient_memo(message: types.Message):
    # Получаем памятку пациенту
    memo = get_patient_memo()

    if memo:
        response = "Памятка пациенту:\n\n" + memo
    else:
        response = "Не удалось получить памятку пациенту. Попробуйте позже."

    await message.answer(response)

# Обработчик текстовых сообщений для отзывов и предложений
@dp.message()
async def handle_text(message: types.Message):
    # Проверяем, что текст существует
    if not message.text:
        await message.answer("Ошибка: пожалуйста, отправьте текстовое сообщение.")
        return

    # Сохраняем сообщение в базу данных
    cursor.execute('''
    INSERT INTO feedback (user_id, message_text)
    VALUES (?, ?)
    ''', (message.from_user.id, message.text))
    conn.commit()

    # Уведомляем пользователя
    if "вопрос" in message.text.lower():
        await message.answer("Ваш вопрос принят! Мы ответим вам как можно скорее.")
    else:
        await message.answer("Спасибо за ваш отзыв или предложение!")

# Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())