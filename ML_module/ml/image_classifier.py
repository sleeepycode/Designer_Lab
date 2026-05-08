from ml.text_utils import normalize_text

def classify_image_fallback(ocr_text: str) -> str:
    t=normalize_text(ocr_text)
    if any(w in t for w in ['таблица','строка','столбец','значение','измерение']): return 'table'
    if any(w in t for w in ['график','зависимость','ось','температура','время','диаграмма']): return 'graph'
    if any(w in t for w in ['схема','алгоритм','блок','процесс','начало','конец']): return 'scheme'
    if any(w in t for w in ['формула','уравнение','расчет','расчёт']): return 'formula'
    return 'unknown'
