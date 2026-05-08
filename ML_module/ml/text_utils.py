import json, re
STOP_WORDS = {'и','в','во','на','с','со','по','для','от','до','это','как','что','при','из','за','к','а','но','или','также','the','and','with','from','this','that'}
def normalize_text(text: str) -> str:
    text = (text or '').lower().replace('ё','е')
    text = re.sub(r'[^а-яa-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
def split_paragraphs(document_text: str) -> list[str]:
    return [p.strip() for p in (document_text or '').split('\n') if p.strip()]
def extract_keywords(text: str, limit: int = 10) -> list[str]:
    words = re.findall(r'[а-яa-z]{4,}', normalize_text(text))
    out=[]
    for w in words:
        if w not in STOP_WORDS and w not in out: out.append(w)
    return out[:limit]
def compact_text(text: str, max_len: int = 4000) -> str:
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text if len(text) <= max_len else text[:max_len].rstrip() + '...'
def extract_json_from_text(text: str) -> dict | list:
    cleaned=(text or '').strip()
    if cleaned.startswith('```'):
        cleaned=cleaned.strip('`').replace('json','',1).strip()
    try: return json.loads(cleaned)
    except Exception: pass
    s,e=cleaned.find('{'), cleaned.rfind('}')
    if s!=-1 and e!=-1 and e>s: return json.loads(cleaned[s:e+1])
    s,e=cleaned.find('['), cleaned.rfind(']')
    if s!=-1 and e!=-1 and e>s: return json.loads(cleaned[s:e+1])
    raise ValueError('AI response does not contain valid JSON')
