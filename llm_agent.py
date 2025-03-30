import os
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMAgent:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.base_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "mistral-small-latest"

    def generate_response(self, query, context=""):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "Ты помощник поликлиники. Отвечай на русском языке, используя формальный стиль. "
            f"Контекст: {context}"
        )

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        }

        response = requests.post(self.base_url, headers=headers, json=data).json()
        return response['choices'][0]['message']['content']

    def format_schedule(self, schedule):
        """
        Отправляет расписание в нейросеть для форматирования.

        Args:
            schedule (list): Список строк с расписанием.

        Returns:
            str: Отформатированное расписание.
        """
        schedule_text = "\n".join(schedule)  # Преобразуем список строк в одну строку
        prompt = (
            "Приведи следующее расписание в удобный для чтения вид. "
            "Сгруппируй данные по отделениям или дням недели, если это возможно. "
            "Используй формальный стиль и русский язык.\n\n"
            f"Расписание:\n{schedule_text}"
        )
        formatted_schedule = self.generate_response(prompt)

        # Убедитесь, что возвращается строка
        return formatted_schedule.strip()