from ml.ai_report import get_section_title
from ml.bibliography_fallback import generate_bibliography_fallback
from ml.ollama_client import ask_ollama_json
from ml.text_utils import compact_text, extract_json_from_text
from ml.language_guard import force_russian_in_dict


def generate_missing_section(section_key: str, topic: str, document_text: str = "") -> tuple[dict, bool]:
    try:
        return generate_missing_section_ollama(section_key, topic, document_text), True
    except Exception as error:
        print(f"[AI FALLBACK] section generation: {error}")
        return generate_missing_section_fallback(section_key, topic), False


def generate_missing_section_ollama(section_key: str, topic: str, document_text: str) -> dict:
    title = get_section_title(section_key)

    prompt = f"""
Сгенерируй недостающий раздел русскоязычного учебного отчёта.

Тема отчёта: {topic}
Нужный раздел: {title}

Требования к тексту:
- строго русский язык;
- не использовать английские слова и фразы;
- академический стиль студенческого отчёта;
- 1-2 абзаца;
- без выдуманных численных результатов эксперимента;
- без markdown;
- текст должен подходить для вставки в DOCX.

Верни строго JSON такого вида:
{{
  "section": "{section_key}",
  "title": "{title}",
  "text": "полностью русский текст раздела"
}}

Контекст исходного отчёта:
{compact_text(document_text, 3000)}
"""

    data = extract_json_from_text(ask_ollama_json(prompt))
    data = force_russian_in_dict(data)

    return {
        "section": section_key,
        "title": data.get("title", title),
        "text": data.get("text", ""),
        "source": "ollama",
    }


def generate_missing_section_fallback(section_key: str, topic: str) -> dict:
    title = get_section_title(section_key)

    texts = {
        "introduction": (
            f"{title}\n\n"
            f"В данной работе рассматривается тема «{topic}». "
            "Целью работы является изучение основных теоретических положений, "
            "а также закрепление полученных знаний на практике."
        ),
        "theory": (
            f"{title}\n\n"
            f"Теоретическая часть посвящена рассмотрению основных понятий, "
            f"связанных с темой «{topic}». В данном разделе приводятся базовые "
            "сведения, необходимые для понимания дальнейшей практической части."
        ),
        "practice": (
            f"{title}\n\n"
            "В практической части выполняются необходимые действия, расчёты, "
            "измерения или эксперименты, после чего проводится анализ полученных результатов."
        ),
        "conclusion": (
            f"{title}\n\n"
            f"В результате выполнения работы по теме «{topic}» были рассмотрены "
            "основные теоретические сведения и получены практические навыки. "
            "Поставленные задачи можно считать выполненными."
        ),
    }

    return {
        "section": section_key,
        "title": title,
        "text": texts.get(section_key, f"{title}\n\nРаздел сформирован автоматически на основе темы «{topic}»."),
        "source": "fallback",
    }


def generate_bibliography(topic: str, document_text: str = "") -> tuple[list[str], bool]:
    try:
        return generate_bibliography_ollama(topic, document_text), True
    except Exception as error:
        print(f"[AI FALLBACK] bibliography: {error}")
        return generate_bibliography_fallback(topic), False


def generate_bibliography_ollama(topic: str, document_text: str) -> list[str]:
    prompt = f"""
Сгенерируй список литературы для русскоязычного учебного отчёта.

Тема отчёта: {topic}

Требования:
- строго русский язык;
- 4-6 источников;
- включи ГОСТ по оформлению отчётов;
- не добавляй несуществующие сайты;
- не используй английские пояснения;
- формат — список строк.

Верни строго JSON:
{{
  "items": ["источник 1", "источник 2"]
}}

Контекст отчёта:
{compact_text(document_text, 2000)}
"""

    data = extract_json_from_text(ask_ollama_json(prompt))
    data = force_russian_in_dict(data)
    items = data.get("items", [])

    if not isinstance(items, list) or not items:
        raise ValueError("Ollama returned empty bibliography")

    return [str(item) for item in items]
