import sqlite3
from aiogram import Bot
import asyncio
# Вставьте ваш токен сюда
API_TOKEN = '7667656634:AAFGezCC6FxuKiDofhiAMMJ4DLOyP97KOzU'

# Инициализация бота
bot = Bot(token=API_TOKEN)

# Подключение к базе данных
conn = sqlite3.connect('cache/feedback.db')
cursor = conn.cursor()

def view_new_messages():
    """Показывает новые сообщения."""
    cursor.execute('SELECT id, user_id, message_text FROM feedback WHERE status = "new"')
    messages = cursor.fetchall()
    if not messages:
        print("Новых сообщений нет.")
    else:
        print("Новые сообщения:")
        for msg in messages:
            print(f"ID: {msg[0]}, User ID: {msg[1]}, Сообщение: {msg[2]}")

def respond_to_message(message_id, user_id, response_text):
    """Обновляет статус сообщения и отправляет ответ пользователю."""
    # Обновляем запись в базе данных
    cursor.execute('''
    UPDATE feedback
    SET status = "answered", response = ?
    WHERE id = ?
    ''', (response_text, message_id))
    conn.commit()

    # Отправляем ответ пользователю
    asyncio.run(send_response_to_user(user_id, response_text))

async def send_response_to_user(user_id, response_text):
    """Отправляет ответ пользователю через Telegram API."""
    await bot.send_message(chat_id=user_id, text=f"Ответ от администратора: {response_text}")
    print(f"Ответ отправлен пользователю с ID {user_id}: {response_text}")

# Интерфейс администратора
if __name__ == "__main__":
    while True:
        print("\n1. Просмотреть новые сообщения")
        print("2. Ответить на сообщение")
        print("3. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            view_new_messages()
        elif choice == "2":
            message_id = int(input("Введите ID сообщения: "))
            user_id = int(input("Введите User ID: "))
            response_text = input("Введите ответ: ")
            respond_to_message(message_id, user_id, response_text)
        elif choice == "3":
            break
        else:
            print("Неверный выбор. Попробуйте снова.")