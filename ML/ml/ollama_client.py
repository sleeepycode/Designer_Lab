import requests

from ml.config import OLLAMA_BASE_URL, OLLAMA_MODEL, is_ollama_enabled


STRICT_RUSSIAN_SYSTEM_PROMPT = """
Ты AI-модуль для анализа русскоязычных учебных отчётов.

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Отвечай только на русском языке.
2. Не используй английский язык в значениях JSON, кроме технических ключей.
3. Не используй markdown.
4. Не добавляй пояснения вокруг JSON.
5. Возвращай только валидный JSON.
6. Если нужно сгенерировать текст раздела, текст должен быть полностью на русском языке.
7. Если нужно сгенерировать подпись, подпись должна быть полностью на русском языке.
8. Если не уверен — всё равно верни корректный JSON на русском языке.
"""


def ask_ollama_json(
    prompt: str,
    system_prompt: str = "Ты полезный AI-анализатор учебных отчётов.",
) -> str:
    if not is_ollama_enabled():
        raise RuntimeError("Ollama is not enabled. Set AI_PROVIDER=ollama.")

    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"

    full_system_prompt = (
        STRICT_RUSSIAN_SYSTEM_PROMPT
        + "\n\n"
        + system_prompt
        + "\n\n"
        + "Ответ должен быть строго JSON. Все текстовые значения внутри JSON должны быть на русском языке."
    )

    full_user_prompt = (
        prompt
        + "\n\n"
        + "Напоминание: верни только JSON. Все фразы, заголовки, подписи и сгенерированный текст — строго на русском языке."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": full_user_prompt},
        ],
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "repeat_penalty": 1.1,
        },
    }

    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()

    data = response.json()
    return data["message"]["content"]
