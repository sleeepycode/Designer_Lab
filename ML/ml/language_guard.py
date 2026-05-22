import re

ENGLISH_REPLACEMENTS = {
    "Introduction": "Введение",
    "Theory": "Теоретическая часть",
    "Theoretical part": "Теоретическая часть",
    "Practice": "Практическая часть",
    "Practical part": "Практическая часть",
    "Conclusion": "Заключение",
    "References": "Список литературы",
    "Bibliography": "Список литературы",
    "Figure": "Рисунок",
    "Table": "Таблица",
    "Graph": "График",
    "Scheme": "Схема",
    "Formula": "Формула",
    "temperature": "температура",
    "time": "время",
    "dependency": "зависимость",
    "experiment": "эксперимент",
    "results": "результаты",
}


def force_russian_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    result = text

    for eng, rus in ENGLISH_REPLACEMENTS.items():
        result = re.sub(rf"\b{re.escape(eng)}\b", rus, result, flags=re.IGNORECASE)

    result = result.replace("Here is the JSON:", "")
    result = result.replace("Here is your JSON:", "")
    result = result.replace("Output:", "")
    result = result.replace("Result:", "")

    return result.strip()


def force_russian_in_dict(data):
    if isinstance(data, dict):
        return {key: force_russian_in_dict(value) for key, value in data.items()}

    if isinstance(data, list):
        return [force_russian_in_dict(item) for item in data]

    if isinstance(data, str):
        return force_russian_text(data)

    return data
