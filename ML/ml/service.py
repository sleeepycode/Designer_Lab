from ml.ai_report import analyze_report_structure
from ml.content_suggestions import build_content_suggestions
from ml.image_analyzer import analyze_image
from ml.numbering_generator import apply_numbering
from ml.schemas import build_project_response

def analyze_project(document_text: str, image_paths: list[str], topic: str='лабораторной работы') -> dict:
    errors=[]; ai_used_total=False; document_text=document_text or ''; image_paths=image_paths or []; topic=topic or 'лабораторной работы'
    if not document_text.strip(): errors.append('document_text is empty')
    structure,used=analyze_report_structure(document_text); ai_used_total=ai_used_total or used
    generated,bibliography,suggestions,used=build_content_suggestions(structure,topic,document_text); ai_used_total=ai_used_total or used
    report={'found_sections':structure['found_sections'],'missing_sections':structure['missing_sections'],'has_required_structure':structure['has_required_structure'],'generated_sections':generated,'bibliography':bibliography}
    images=[]
    for image_path in image_paths:
        item,used=analyze_image(image_path,document_text,topic); ai_used_total=ai_used_total or used
        if item.get('error'): errors.append(f"{image_path}: {item['error']}")
        images.append(item)
    images=apply_numbering(images)
    return build_project_response(topic,report,images,suggestions,errors,ai_used_total)
