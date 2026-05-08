from ml.ai_report import get_section_title
from ml.bibliography_fallback import generate_bibliography_fallback
from ml.ollama_client import ask_ollama_json
from ml.text_utils import compact_text, extract_json_from_text

def generate_missing_section(section_key: str, topic: str, document_text: str='') -> tuple[dict,bool]:
    try: return generate_missing_section_ollama(section_key,topic,document_text), True
    except Exception as e:
        print(f'[AI FALLBACK] section generation: {e}')
        return generate_missing_section_fallback(section_key,topic), False

def generate_missing_section_ollama(section_key: str, topic: str, document_text: str) -> dict:
    title=get_section_title(section_key)
    prompt=f'''Сгенерируй недостающий раздел учебного отчёта. Тема: {topic}. Раздел: {title}. Требования: русский язык; академический стиль; 1-2 абзаца; без выдуманных результатов эксперимента. Верни строго JSON: {{"section":"{section_key}","title":"{title}","text":"..."}} Контекст: {compact_text(document_text,3000)}'''
    data=extract_json_from_text(ask_ollama_json(prompt))
    return {'section':section_key,'title':data.get('title',title),'text':data.get('text',''),'source':'ollama'}

def generate_missing_section_fallback(section_key: str, topic: str) -> dict:
    title=get_section_title(section_key)
    texts={'introduction':f'{title}\n\nВ данной работе рассматривается тема «{topic}». Целью работы является изучение основных теоретических положений, а также закрепление полученных знаний на практике.','theory':f'{title}\n\nТеоретическая часть посвящена рассмотрению основных понятий, связанных с темой «{topic}». В данном разделе приводятся базовые сведения, необходимые для понимания дальнейшей практической части.','practice':f'{title}\n\nВ практической части выполняются необходимые действия, расчёты, измерения или эксперименты, после чего проводится анализ полученных результатов.','conclusion':f'{title}\n\nВ результате выполнения работы по теме «{topic}» были рассмотрены основные теоретические сведения и получены практические навыки. Поставленные задачи можно считать выполненными.'}
    return {'section':section_key,'title':title,'text':texts.get(section_key,f'{title}\n\nРаздел сформирован автоматически на основе темы «{topic}».'),'source':'fallback'}

def generate_bibliography(topic: str, document_text: str='') -> tuple[list[str],bool]:
    try: return generate_bibliography_ollama(topic,document_text), True
    except Exception as e:
        print(f'[AI FALLBACK] bibliography: {e}')
        return generate_bibliography_fallback(topic), False

def generate_bibliography_ollama(topic: str, document_text: str) -> list[str]:
    prompt=f'''Сгенерируй список литературы для учебного отчёта. Тема: {topic}. Требования: 4-6 источников; русский язык; включи ГОСТ; не добавляй несуществующие сайты. Верни строго JSON: {{"items":["источник 1","источник 2"]}} Контекст: {compact_text(document_text,2000)}'''
    data=extract_json_from_text(ask_ollama_json(prompt)); items=data.get('items',[])
    if not isinstance(items,list) or not items: raise ValueError('Ollama returned empty bibliography')
    return [str(x) for x in items]
