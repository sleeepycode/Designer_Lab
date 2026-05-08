from ml.ollama_client import ask_ollama_json
from ml.text_utils import compact_text, extract_json_from_text, normalize_text
SECTION_RULES={'introduction':{'title':'Введение','signals':['введение','цель работы','задачи работы','актуальность']},'theory':{'title':'Теоретическая часть','signals':['теоретическая часть','теория','теоретические сведения','основные понятия']},'practice':{'title':'Практическая часть','signals':['практическая часть','ход работы','выполнение работы','эксперимент','результаты измерений']},'conclusion':{'title':'Заключение','signals':['заключение','вывод','выводы','в результате работы']},'references':{'title':'Список литературы','signals':['список литературы','литература','источники','библиографический список']}}
def analyze_report_structure(document_text: str) -> tuple[dict,bool]:
    try: return analyze_report_structure_ollama(document_text), True
    except Exception as e:
        print(f'[AI FALLBACK] report structure: {e}')
        return analyze_report_structure_fallback(document_text), False
def analyze_report_structure_ollama(document_text: str) -> dict:
    prompt=f'''Проанализируй текст учебного отчёта. Определи, какие разделы присутствуют, а каких не хватает. Используй только ключи: introduction, theory, practice, conclusion, references. Верни строго JSON: {{"found_sections":["introduction"],"missing_sections":["theory"],"has_required_structure":false}} Текст отчёта: {compact_text(document_text,5000)}'''
    data=extract_json_from_text(ask_ollama_json(prompt))
    found=data.get('found_sections',[]); missing=data.get('missing_sections',[])
    return {'found_sections':found,'missing_sections':missing,'has_required_structure':len(missing)==0}
def analyze_report_structure_fallback(document_text: str) -> dict:
    text=normalize_text(document_text); found=[]; missing=[]
    for k,d in SECTION_RULES.items():
        (found if any(s in text for s in d['signals']) else missing).append(k)
    return {'found_sections':found,'missing_sections':missing,'has_required_structure':len(missing)==0}
def get_section_title(section_key: str) -> str:
    return SECTION_RULES.get(section_key,{}).get('title',section_key)
