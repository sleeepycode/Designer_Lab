from ml.ollama_client import ask_ollama_json
from ml.image_classifier import classify_image_fallback
from ml.text_utils import compact_text, extract_json_from_text, extract_keywords
from ml.language_guard import force_russian_in_dict


def analyze_image_semantics(
    ocr_text: str,
    topic: str,
    document_text: str,
) -> tuple[dict, bool]:
    try:
        return analyze_image_semantics_ollama(ocr_text, topic, document_text), True
    except Exception as error:
        print(f"[AI FALLBACK] image semantics: {error}")
        return analyze_image_semantics_fallback(ocr_text, topic), False


def analyze_image_semantics_ollama(ocr_text: str, topic: str, document_text: str) -> dict:
    prompt = f"""
Проанализируй OCR-текст изображения для русскоязычного учебного отчёта.

Тема отчёта: {topic}

OCR-текст изображения:
{ocr_text}

Нужно определить:
- type: graph, table, scheme, formula или unknown
- caption: короткая академическая подпись на русском языке без слов "Рисунок 1"
- keywords: 3-7 ключевых слов на русском языке

Важно:
- caption строго на русском языке;
- keywords строго на русском языке;
- не используй английские слова;
- верни только JSON.

Формат ответа:
{{
  "type": "graph",
  "caption": "График зависимости температуры от времени",
  "keywords": ["температура", "время", "график"]
}}

Контекст отчёта:
{compact_text(document_text, 2500)}
"""

    data = extract_json_from_text(ask_ollama_json(prompt))
    data = force_russian_in_dict(data)

    image_type = data.get("type", "unknown")

    if image_type not in ["graph", "table", "scheme", "formula", "unknown"]:
        image_type = "unknown"

    keywords = data.get("keywords", [])

    if not isinstance(keywords, list):
        keywords = extract_keywords(str(keywords))

    return {
        "type": image_type,
        "caption": data.get("caption", "Иллюстрация к отчёту"),
        "keywords": [str(item) for item in keywords][:10],
    }


def analyze_image_semantics_fallback(ocr_text: str, topic: str) -> dict:
    image_type = classify_image_fallback(ocr_text)
    keywords = extract_keywords(ocr_text)

    if image_type == "graph":
        caption = (
            "График зависимости температуры от времени"
            if any("температ" in w for w in keywords) or "время" in keywords
            else "График зависимости исследуемых величин"
        )
    elif image_type == "table":
        caption = "Результаты измерений"
    elif image_type == "scheme":
        caption = "Схема выполнения процесса"
    elif image_type == "formula":
        caption = "Формула расчёта"
    else:
        caption = f"Иллюстрация к теме «{topic}»"

    return {
        "type": image_type,
        "caption": caption,
        "keywords": keywords,
    }
