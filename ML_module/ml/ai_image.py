from ml.ollama_client import ask_ollama_json
from ml.image_classifier import classify_image_fallback
from ml.text_utils import compact_text, extract_json_from_text, extract_keywords

def analyze_image_semantics(ocr_text: str, topic: str, document_text: str) -> tuple[dict,bool]:
    try: return analyze_image_semantics_ollama(ocr_text,topic,document_text), True
    except Exception as e:
        print(f'[AI FALLBACK] image semantics: {e}')
        return analyze_image_semantics_fallback(ocr_text,topic), False

def analyze_image_semantics_ollama(ocr_text: str, topic: str, document_text: str) -> dict:
    prompt=f'''Проанализируй OCR-текст изображения для учебного отчёта. Тема: {topic}. OCR-текст: {ocr_text}. Определи type: graph, table, scheme, formula или unknown. Сделай короткую академическую подпись без "Рисунок 1". Верни строго JSON: {{"type":"graph","caption":"График зависимости температуры от времени","keywords":["температура","время","график"]}} Контекст: {compact_text(document_text,2500)}'''
    data=extract_json_from_text(ask_ollama_json(prompt)); image_type=data.get('type','unknown')
    if image_type not in ['graph','table','scheme','formula','unknown']: image_type='unknown'
    keywords=data.get('keywords',[])
    if not isinstance(keywords,list): keywords=extract_keywords(str(keywords))
    return {'type':image_type,'caption':data.get('caption','Иллюстрация к отчёту'),'keywords':[str(x) for x in keywords][:10]}

def analyze_image_semantics_fallback(ocr_text: str, topic: str) -> dict:
    image_type=classify_image_fallback(ocr_text); keywords=extract_keywords(ocr_text)
    if image_type=='graph': caption='График зависимости температуры от времени' if any('температ' in w for w in keywords) or 'время' in keywords else 'График зависимости исследуемых величин'
    elif image_type=='table': caption='Результаты измерений'
    elif image_type=='scheme': caption='Схема выполнения процесса'
    elif image_type=='formula': caption='Формула расчёта'
    else: caption=f'Иллюстрация к теме «{topic}»'
    return {'type':image_type,'caption':caption,'keywords':keywords}
