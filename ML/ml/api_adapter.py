from ml.service import analyze_project

def analyze_project_payload(payload: dict) -> dict:
    return analyze_project(payload.get('document_text',''), payload.get('image_paths',[]), payload.get('topic','лабораторной работы'))
