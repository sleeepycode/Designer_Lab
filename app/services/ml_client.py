from typing import List, Dict, Any


def analyze_project(document_text: str, image_paths: List[str], topic: str) -> Dict[str, Any]:
    """Заглушка для ML-сервиса. Возвращает пустые результаты.
    В реальной системе здесь должен быть HTTP-запрос к ML сервису.
    """
    # Пример возвращаемой структуры
    return {
        'generated_sections': [],
        'bibliography': [],
        'images': [],
        'meta': {'note': 'ml stub'}
    }