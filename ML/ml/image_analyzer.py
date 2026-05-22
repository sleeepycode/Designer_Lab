from ml.ocr import extract_text_from_image
from ml.ai_image import analyze_image_semantics
from ml.placement_suggester import suggest_placement
from ml.schemas import build_image_error

def analyze_image(image_path: str, document_text: str, topic: str) -> tuple[dict,bool]:
    try:
        ocr_text=extract_text_from_image(image_path); semantics,ai_used=analyze_image_semantics(ocr_text,topic,document_text)
        image_type=semantics.get('type','unknown'); keywords=semantics.get('keywords',[]); caption=semantics.get('caption','Иллюстрация к отчёту')
        suggestions=suggest_placement(document_text,ocr_text,image_type); placement=suggestions[0] if suggestions else {'paragraph_index':0,'score':0.0,'reason':'Место вставки не найдено'}
        return {'path':image_path,'type':image_type,'ocr_text':ocr_text,'keywords':keywords,'caption':caption,'number':None,'numbering_type':'figure','placement':placement,'alternatives':suggestions[1:] if len(suggestions)>1 else [],'confidence':calculate_confidence(ocr_text,image_type,placement,ai_used),'error':None}, ai_used
    except Exception as e:
        return build_image_error(image_path,str(e)), False

def calculate_confidence(ocr_text: str, image_type: str, placement: dict, ai_used: bool) -> float:
    return round(min((0.15 if ai_used else 0)+(0.3 if ocr_text.strip() else 0)+(0.2 if image_type!='unknown' else 0)+min(float(placement.get('score',0.0)),1.0)*0.35,1.0),2)
