from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import sqlite3
from aiogram.types import FSInputFile
from scraper import parse_images, get_working_hours, get_phones, \
    get_patient_memo  # Импортируем функции для работы с расписанием и телефонами
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
    fio TEXT,
    phone TEXT,
    email TEXT,
    message_text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new',
    response TEXT
)
''')
conn.commit()

# Определение состояний
class FeedbackForm(StatesGroup):
    waiting_for_fio = State()       # Ожидание ФИО
    waiting_for_phone = State()    # Ожидание номера телефона
    waiting_for_email = State()    # Ожидание почты
    waiting_for_message = State()  # Ожидание текста сообщения

# Инициализация нейросети
llm_agent = LLMAgent()


# Определение состояний
class Form(StatesGroup):
    waiting_for_neural_question = State()  # Состояние ожидания вопроса нейросети


# Обработчик кнопки "График приема"
@dp.message(lambda message: message.text == "График приема")
async def show_schedule_images(message: types.Message):
    await message.answer("Ищу график приема специалистов...")

    # Парсим изображения
    images = parse_images()

    if not images:
        await message.answer("Не удалось найти график приема. Попробуйте позже.")
        return

    # Отправляем каждое изображение пользователю
    for img_path in images:
        try:
            # Используем FSInputFile для отправки локального файла
            photo = FSInputFile(img_path)
            await message.answer_photo(photo)
        except Exception as e:
            print(f"Ошибка при отправке изображения {img_path}: {e}")
            await message.answer("Не удалось отправить одно из изображений.")


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="График приема")],
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


# Обработчик кнопки "Отправить отзыв"
@dp.message(lambda message: message.text == "Отправить отзыв")
async def ask_for_feedback(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, укажите ваше ФИО:")
    await state.set_state(FeedbackForm.waiting_for_fio)

# Обработчик кнопки "Задать вопрос специалисту"
@dp.message(lambda message: message.text == "Задать вопрос специалисту")
async def ask_for_question(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, укажите ваше ФИО:")
    await state.set_state(FeedbackForm.waiting_for_fio)

# Обработчик ввода ФИО
@dp.message(FeedbackForm.waiting_for_fio)
async def process_fio(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пожалуйста, укажите ваше ФИО.")
        return

    # Сохраняем ФИО в состояние
    await state.update_data(fio=message.text)
    await message.answer("Укажите ваш номер телефона:")
    await state.set_state(FeedbackForm.waiting_for_phone)

# Обработчик ввода номера телефона
@dp.message(FeedbackForm.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пожалуйста, укажите ваш номер телефона.")
        return

    # Сохраняем номер телефона в состояние
    await state.update_data(phone=message.text)
    await message.answer("Укажите вашу почту:")
    await state.set_state(FeedbackForm.waiting_for_email)

# Обработчик ввода почты
@dp.message(FeedbackForm.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пожалуйста, укажите вашу почту.")
        return

    # Сохраняем почту в состояние
    await state.update_data(email=message.text)
    await message.answer("Напишите ваш отзыв или вопрос:")
    await state.set_state(FeedbackForm.waiting_for_message)

# Обработчик ввода текста сообщения
@dp.message(FeedbackForm.waiting_for_message)
async def process_message(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пожалуйста, напишите ваш отзыв или вопрос.")
        return

    # Получаем данные из состояния
    data = await state.get_data()
    fio = data.get("fio")
    phone = data.get("phone")
    email = data.get("email")
    message_text = message.text

    # Сохраняем данные в базу данных
    cursor.execute('''
    INSERT INTO feedback (user_id, fio, phone, email, message_text)
    VALUES (?, ?, ?, ?, ?)
    ''', (message.from_user.id, fio, phone, email, message_text))
    conn.commit()

    # Уведомляем пользователя
    await message.answer("Спасибо за ваш отзыв или вопрос! Мы свяжемся с вами в ближайшее время.")

    # Сбрасываем состояние
    await state.clear()



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
