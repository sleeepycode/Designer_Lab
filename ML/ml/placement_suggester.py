from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ml.text_utils import split_paragraphs, normalize_text, extract_keywords
CONTEXT_BONUS_WORDS=['рисунок','график','схема','таблица','результат','эксперимент','измерение','зависимость','данные']
def suggest_placement(document_text: str, ocr_text: str, image_type: str='unknown') -> list[dict]:
    paragraphs=split_paragraphs(document_text)
    if not paragraphs: return [{'paragraph_index':0,'score':0.0,'reason':'Текст документа пустой, место вставки определить невозможно'}]
    query=normalize_text(ocr_text)
    if not query: return [{'paragraph_index':find_structural_fallback(paragraphs),'score':0.25,'reason':'OCR не дал текста, выбран fallback по структуре документа'}]
    normalized=[normalize_text(p) for p in paragraphs]
    try:
        m=TfidfVectorizer().fit_transform(normalized+[query]); sims=cosine_similarity(m[-1],m[:-1]).flatten()
    except ValueError: sims=[0.0 for _ in paragraphs]
    keywords=extract_keywords(ocr_text); results=[]
    for i,p in enumerate(normalized):
        tf=float(sims[i]); ks=sum(1 for k in keywords if k in p)*0.12; cs=sum(1 for w in CONTEXT_BONUS_WORDS if w in p)*0.08; total=min(tf+ks+cs,1.0)
        if total>0: results.append({'paragraph_index':i,'score':round(total,2),'reason':build_reason(tf,ks,cs)})
    results.sort(key=lambda x:x['score'], reverse=True)
    return results[:3] if results else [{'paragraph_index':find_structural_fallback(paragraphs),'score':0.25,'reason':'Совпадения не найдены, выбран fallback по структуре документа'}]
def find_structural_fallback(paragraphs: list[str]) -> int:
    preferred=['практическая часть','ход работы','результаты','анализ результатов','экспериментальная часть']
    for i,p in enumerate(paragraphs):
        if any(s in normalize_text(p) for s in preferred): return i
    for i,p in enumerate(paragraphs):
        if 'заключение' in normalize_text(p): return max(i-1,0)
    return max(len(paragraphs)-1,0)
def build_reason(tfidf_score: float, keyword_score: float, context_score: float) -> str:
    parts=[]
    if tfidf_score>0: parts.append(f'семантическая близость: {round(tfidf_score,2)}')
    if keyword_score>0: parts.append('совпадение ключевых слов')
    if context_score>0: parts.append('контекст отчёта')
    return '; '.join(parts) if parts else 'fallback'
