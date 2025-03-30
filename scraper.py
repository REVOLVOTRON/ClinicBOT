import os
import requests
from bs4 import BeautifulSoup
from llm_agent import LLMAgent  # Импортируем класс LLMAgent

# Путь к файлу кэша
CACHE_FILE = "schedule_cache.txt"

def get_working_hours():
    """
    Парсит часы работы с указанного URL или читает их из кэша.

    Returns:
        str: Отформатированное расписание.
    """
    # Если файл кэша существует, читаем из него
    if os.path.exists(CACHE_FILE):
        print("Чтение расписания из кэша...")
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return file.read()

    # URL страницы, которую нужно спарсить
    url = "https://clinica.chitgma.ru/grafik-raboty"

    try:
        # Отправляем GET-запрос к странице
        response = requests.get(url)
        response.raise_for_status()  # Проверяем статус ответа

        # Получаем HTML-код страницы
        html_content = response.text

        # Создаем объект BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Находим элемент с itemprop="articleBody"
        article_body = soup.find(attrs={"itemprop": "articleBody"})
        if not article_body:
            print("Элемент с itemprop='articleBody' не найден.")
            return ""

        # Извлекаем все строки с расписанием
        schedule = []
        for element in article_body.find_all(['p', 'span']):
            text = element.get_text(strip=True)  # Извлекаем текст из каждого элемента
            if text:  # Добавляем только непустые строки
                schedule.append(text)

        # Форматируем расписание с помощью нейросети
        llm_agent = LLMAgent()
        formatted_schedule = llm_agent.format_schedule(schedule)

        # Сохраняем отформатированное расписание в файл кэша
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            file.write(formatted_schedule)

        return formatted_schedule

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных: {e}")
        return ""