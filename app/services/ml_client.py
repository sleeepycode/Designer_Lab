"""
Клиент для взаимодействия с ML сервисом
"""

import logging
import requests
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class MLClient:
    """
    Клиент для отправки данных в ML сервис
    """
    
    def __init__(self, base_url: str = None, service_url: str = None):
        self.base_url = base_url or settings.ml_service_url
        self.service_url = service_url or settings.service_url  # URL вашего сервиса
        self.timeout = settings.ml_timeout
        logger.info(f"ML Client initialized with URL: {self.base_url}")
        logger.info(f"Service public URL: {self.service_url}")
    
    def extract_document_text(self, structure: Dict[str, Any]) -> str:
        """
        Извлекает текст всех параграфов из структуры
        """
        paragraphs = structure.get('paragraphs', [])
        texts = []
        for p in paragraphs:
            text = p.get('text', '') if isinstance(p, dict) else str(p)
            if text.strip():
                texts.append(text.strip())
        return '\n'.join(texts)
    
    def get_image_url(self, image_path: str, project_id: str) -> str:
        """
        Формирует публичный URL для изображения
        
        Пример: http://localhost:8001/storage/projects/123/media/image1.png
        """
        # Преобразуем путь к относительному от storage
        path = Path(image_path)
        
        # Путь должен быть относительно storage
        # Например: storage/projects/123/media/image1.png
        try:
            # Ищем часть пути после 'storage'
            storage_index = str(path).find('storage')
            if storage_index != -1:
                relative_path = str(path)[storage_index:]
            else:
                relative_path = str(path)
        except Exception:
            relative_path = str(path)
        
        # Формируем полный URL
        url = f"{self.service_url}/{relative_path.replace('\\', '/')}"
        logger.debug(f"Generated image URL: {url}")
        return url
    
    def extract_images_with_urls(self, structure: Dict[str, Any], project_id: str) -> List[Dict[str, Any]]:
        """
        Извлекает изображения и формирует публичные URL
        """
        images = structure.get('images', [])
        result = []
        
        for img in images:
            img_path = img.get('path', '')
            if img_path and Path(img_path).exists():
                image_url = self.get_image_url(img_path, project_id)
                result.append({
                    'id': img.get('id', ''),
                    'filename': Path(img_path).name,
                    'url': image_url,           # публичный URL
                    'path': img_path,           # <-- ДОБАВЛЯЕМ локальный путь (для совместимости)
                    'position': img.get('position', 0),
                    'insert_before_paragraph': img.get('insert_before_paragraph')
                })
            elif img_path:
                logger.warning(f"Image not found: {img_path}")
        
        logger.info(f"Generated URLs for {len(result)} images")
        return result
    
    def analyze_document(
        self,
        project_id: str,
        structure: Dict[str, Any],
        topic: str = None
    ) -> Dict[str, Any]:
        """
        Отправляет документ в ML сервис для анализа
        """
        from app.services.docx_core import ensure_project_dir, save_json
        
        # Подготавливаем данные
        document_text = self.extract_document_text(structure)
        images_urls = self.extract_images_with_urls(structure, project_id)
        
        # Формируем payload
        payload = {
            "project_id": project_id,
            "document_text": document_text,
            "images": images_urls,
            "topic": topic or ""
        }
        
        # Сохраняем payload в файл для отладки
        project_dir = ensure_project_dir(project_id)
        payload_path = project_dir / 'ml_request_payload.json'
        save_json(payload_path, payload)
        logger.info(f"ML request payload saved to: {payload_path}")
        
        # Логируем
        logger.info(f"Sending request to ML service: {self.base_url}/analyze")
        logger.debug(f"Project ID: {project_id}")
        logger.debug(f"Document text length: {len(document_text)} chars")
        logger.debug(f"Images count: {len(images_urls)}")
        for img in images_urls:
            logger.debug(f"  Image: {img['filename']} -> {img.get('url', img.get('path'))}")
        logger.debug(f"Topic: {topic}")
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            ml_response = response.json()
            
            # Сохраняем ответ ML
            response_path = project_dir / 'ml_response.json'
            save_json(response_path, ml_response)
            logger.info(f"ML response saved to: {response_path}")
            
            return ml_response
            
        except Exception as e:
            logger.error(f"ML service error: {str(e)}")
            
            # Сохраняем ошибку
            error_path = project_dir / 'ml_error.json'
            save_json(error_path, {
                'error': str(e),
                'payload': payload
            })
            
            return self._get_error_response("UnknownError", str(e))
    
    def _get_error_response(self, error_code: str, error_message: str) -> Dict[str, Any]:
        """
        Возвращает ответ с ошибкой
        """
        return {
            'success': False,
            'topic': '',
            'summary': {
                'status': 'error',
                'missing_sections_count': 0,
                'images_count': 0,
                'suggestions_count': 0
            },
            'generated_sections': [],
            'bibliography': [],
            'errors': [{'code': error_code, 'message': error_message}],
            'meta': {
                'module': 'document-service',
                'fallback': True,
                'error': error_message
            }
        }


# Создаём глобальный экземпляр
ml_client = MLClient()


def analyze_document_with_ml(
    project_id: str,
    structure: Dict[str, Any],
    topic: str = None
) -> Dict[str, Any]:
    """
    Упрощённая функция для вызова ML
    """
    return ml_client.analyze_document(project_id, structure, topic)