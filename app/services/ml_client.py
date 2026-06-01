import logging
import requests
import base64
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class MLClient:
    """
    Клиент для отправки данных в ML сервис
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.ml_service_url
        self.timeout = settings.ml_timeout
        self.max_image_size_mb = 10  # Максимальный размер изображения для base64
        logger.info(f"ML Client initialized with URL: {self.base_url}")
    
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
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        Конвертирует изображение в base64 строку
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.warning(f"Image not found: {image_path}")
                return None
            
            # Проверяем размер
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > self.max_image_size_mb:
                logger.warning(f"Image too large ({size_mb:.2f} MB), skipping: {image_path}")
                return None
            
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {str(e)}")
            return None
    
    def extract_images_with_base64(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Извлекает изображения из структуры и конвертирует в base64
        """
        images = structure.get('images', [])
        result = []
        
        for img in images:
            img_path = img.get('path', '') if isinstance(img, dict) else str(img)
            if img_path:
                img_base64 = self.encode_image_to_base64(img_path)
                if img_base64:
                    result.append({
                        'id': img.get('id', ''),
                        'filename': Path(img_path).name,
                        'data': img_base64,
                        'position': img.get('position', 0),
                        'insert_before_paragraph': img.get('insert_before_paragraph')
                    })
        
        logger.info(f"Encoded {len(result)} images to base64")
        return result
    
    def analyze_document(
        self,
        project_id: str,
        structure: Dict[str, Any],
        topic: str = None
    ) -> Dict[str, Any]:
        """
        Отправляет документ в ML сервис для анализа
        
        Args:
            project_id: ID проекта
            structure: структура из extract_response.json
            topic: тема работы (из формы, lab_title)
        
        Returns:
            ml_response: ответ от ML сервиса
        """
        # Подготавливаем данные
        document_text = self.extract_document_text(structure)
        images_base64 = self.extract_images_with_base64(structure)
        
        # Формируем payload
        payload = {
            "project_id": project_id,
            "document_text": document_text,
            "images": images_base64,  # передаём base64
            "topic": topic or ""
        }
        
        # Логируем
        logger.info(f"Sending request to ML service: {self.base_url}/analyze")
        logger.debug(f"Project ID: {project_id}")
        logger.debug(f"Document text length: {len(document_text)} chars")
        logger.debug(f"Images count: {len(images_base64)}")
        logger.debug(f"Topic: {topic}")
        
        # Сохраняем payload для отладки
        if settings.debug:
            debug_dir = Path("storage/debug")
            debug_dir.mkdir(parents=True, exist_ok=True)
            with open(debug_dir / f"{project_id}_ml_payload.json", "w", encoding='utf-8') as f:
                # Не сохраняем огромные base64 в лог
                debug_payload = {
                    "project_id": project_id,
                    "document_text": document_text[:500] + "...",
                    "images_count": len(images_base64),
                    "topic": topic
                }
                json.dump(debug_payload, f, ensure_ascii=False, indent=2)
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            ml_response = response.json()
            logger.info(f"ML service responded successfully")
            logger.debug(f"ML response keys: {list(ml_response.keys())}")
            return ml_response
            
        except requests.exceptions.Timeout:
            logger.error(f"ML service timeout after {self.timeout}s")
            return self._get_error_response("Timeout", "ML service did not respond in time")
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to ML service: {self.base_url}")
            return self._get_error_response("ConnectionError", f"Cannot connect to {self.base_url}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return self._get_error_response("HTTPError", f"Status {e.response.status_code}")
        except Exception as e:
            logger.error(f"ML service error: {str(e)}")
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