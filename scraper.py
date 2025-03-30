import os
import re
import requests
from bs4 import BeautifulSoup
from llm_agent import LLMAgent  # Импортируем класс LLMAgent

# Создаем папку cache, если она не существует
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

CACHE_DIR = "cache"
IMAGE_DIR = os.path.join(CACHE_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Пути к файлам кэша
SCHEDULE_CACHE_FILE = os.path.join(CACHE_DIR, "schedule_cache.txt")
PHONES_CACHE_FILE = os.path.join(CACHE_DIR, "phones_cache.txt")
MEMO_CACHE_FILE = os.path.join(CACHE_DIR, "memo_cache.txt")


def parse_images():
    """
    Парсит изображения с указанного URL и сохраняет их в папку cache/images.

    Returns:
        list: Список путей к сохраненным изображениям.
    """
    url = "https://clinica.chitgma.ru/grafik-priema-spetsialistov-1"
    base_url = "https://clinica.chitgma.ru"

    try:
        # Отправляем GET-запрос к странице
        response = requests.get(url)
        response.raise_for_status()

        # Получаем HTML-код страницы
        html_content = response.text

        # Создаем объект BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Находим все теги <img>
        img_tags = soup.find_all("img")

        # Фильтруем только нужные изображения (например, по alt="appdp")
        image_urls = []
        for img in img_tags:
            if "appdp" in img.get("alt", ""):
                img_src = img.get("src")
                if img_src.startswith("/"):
                    img_src = base_url + img_src  # Формируем полный URL
                image_urls.append(img_src)

        # Скачиваем и сохраняем изображения
        saved_images = []
        for i, img_url in enumerate(image_urls):
            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()

                # Сохраняем изображение в папку cache/images
                file_extension = os.path.splitext(img_url)[-1]
                file_name = f"schedule_{i}{file_extension}"
                file_path = os.path.join(IMAGE_DIR, file_name)

                with open(file_path, "wb") as img_file:
                    img_file.write(img_response.content)

                saved_images.append(file_path)
            except Exception as e:
                print(f"Ошибка при скачивании изображения {img_url}: {e}")

        return saved_images

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных: {e}")
        return []


def get_patient_memo():
    """
    Получает памятку пациенту из кэша или парсит её с сайта,
    нормализует через нейросеть и сохраняет в кэш.

    Returns:
        str: Нормализованная памятка пациенту.
    """
    # Если файл кэша существует, читаем из него
    if os.path.exists(MEMO_CACHE_FILE):
        print("Чтение памятки пациента из кэша...")
        with open(MEMO_CACHE_FILE, "r", encoding="utf-8") as file:
            return file.read()

    # URL страницы, которую нужно спарсить
    url = "https://clinica.chitgma.ru/informatsiya-po-otdeleniyu-12"

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

        # Извлекаем текст из articleBody
        raw_data = article_body.get_text(strip=True)

        # Нормализуем текст через нейросеть
        memo_prompt = (
            "Приведи следующую информацию в удобный для чтения вид и сократи ее насколько возможно. "
            "Сгруппируй данные по разделам, если это возможно. "
            "Используй формальный стиль и русский язык.\n\n"
            "Памятка пациенту:\n"
        )
        normalized_memo = normalize_data_with_neural_network(raw_data, memo_prompt)

        # Сохраняем отформатированную памятку в файл кэша
        with open(MEMO_CACHE_FILE, "w", encoding="utf-8") as file:
            file.write(normalized_memo)

        return normalized_memo

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных: {e}")
        return ""



def extract_phone_numbers(text):
    """
    Извлекает номера телефонов из текста с помощью регулярного выражения.

    Args:
        text (str): Текст для поиска телефонов.

    Returns:
        list: Список найденных номеров телефонов.
    """
    phone_pattern = r"\b\d{2,3}[-\s]?\d{2,3}[-\s]?\d{2,4}(?:[-\s]?\d{2,4})?\b"
    phones = re.findall(phone_pattern, text)
    return [phone.strip() for phone in phones]

def normalize_data_with_neural_network(data, prompt):
    """
    Нормализует данные с помощью нейросети.

    Args:
        data (list): Список строк для нормализации.
        prompt (str): Инструкция для нейросети.

    Returns:
        str: Нормализованные данные.
    """
    llm_agent = LLMAgent()
    data_text = "\n".join(data)  # Преобразуем список строк в одну строку
    formatted_data = llm_agent.generate_response(prompt + data_text)
    return formatted_data.strip()

def initialize_data():
    """
    Инициализирует данные: парсит расписание и телефоны,
    нормализует их через нейросеть и сохраняет в кэш.

    Returns:
        tuple: Нормализованное расписание и телефоны.
    """
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
            return "", ""

        # Извлекаем весь текст из articleBody
        raw_data = []
        for element in article_body.find_all(['p', 'span']):
            text = element.get_text(strip=True)
            if text:
                raw_data.append(text)

        # Разделяем данные на расписание и телефоны
        schedule_lines = []
        phone_lines = []
        for line in raw_data:
            if any(char.isdigit() for char in line) and ("телефон" in line.lower() or re.search(r"\b\d{2,3}", line)):
                phone_lines.append(line)
            else:
                schedule_lines.append(line)

        # Нормализуем расписание через нейросеть
        schedule_prompt = (
            "Приведи следующее расписание в удобный для чтения вид. "
            "Сгруппируй данные по отделениям или дням недели, если это возможно. "
            "Используй формальный стиль и русский язык.\n\n"
            "Расписание:\n"
        )
        normalized_schedule = normalize_data_with_neural_network(schedule_lines, schedule_prompt)

        # Нормализуем телефоны через нейросеть
        phones_prompt = (
            "Приведи следующие телефоны в удобный для чтения вид. "
            "Убери дубликаты и отсортируй их по алфавиту или номерам. "
            "Используй формальный стиль и русский язык.\n\n"
            "Телефоны:\n"
        )
        normalized_phones = normalize_data_with_neural_network(phone_lines, phones_prompt)

        # Сохраняем данные в кэш
        with open(SCHEDULE_CACHE_FILE, "w", encoding="utf-8") as file:
            file.write(normalized_schedule)

        with open(PHONES_CACHE_FILE, "w", encoding="utf-8") as file:
            file.write(normalized_phones)

        return normalized_schedule, normalized_phones

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных: {e}")
        return "", ""

def get_working_hours():
    """
    Возвращает расписание из кэша. Если кэш отсутствует, инициализирует данные.

    Returns:
        str: Отформатированное расписание.
    """
    if os.path.exists(SCHEDULE_CACHE_FILE):
        print("Чтение расписания из кэша...")
        with open(SCHEDULE_CACHE_FILE, "r", encoding="utf-8") as file:
            return file.read()
    else:
        print("Кэш расписания отсутствует. Инициализация данных...")
        schedule, _ = initialize_data()
        return schedule

def get_phones():
    """
    Возвращает телефоны из кэша. Если кэш отсутствует, инициализирует данные.

    Returns:
        str: Отформатированные телефоны.
    """
    if os.path.exists(PHONES_CACHE_FILE):
        print("Чтение телефонов из кэша...")
        with open(PHONES_CACHE_FILE, "r", encoding="utf-8") as file:
            return file.read()
    else:
        print("Кэш телефонов отсутствует. Инициализация данных...")
        _, phones = initialize_data()
        return phones