"""
Клиент для взаимодействия с ML сервисом.

Главная задача этого файла:
1. взять extract-структуру Doc Service;
2. склеить paragraphs[] в document_text;
3. преобразовать локальные пути картинок storage\\... в HTTP URL;
4. отправить в ML payload строго по контракту /analyze.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class MLClient:
    """
    Клиент для отправки данных в ML сервис.
    """

    def __init__(self, base_url: str | None = None, service_url: str | None = None):
        self.base_url = (base_url or settings.ml_service_url).rstrip("/")
        self.service_url = (service_url or settings.service_url).rstrip("/")
        self.timeout = settings.ml_timeout

        logger.info("ML Client initialized")
        logger.info("ML service URL: %s", self.base_url)
        logger.info("Doc Service public URL: %s", self.service_url)

    def extract_document_text(self, structure: Dict[str, Any]) -> str:
        """
        Склеивает paragraphs[].text в одну строку document_text для ML.

        ML НЕ принимает raw paragraphs напрямую.
        ML ждёт поле document_text: str.
        """
        paragraphs = structure.get("paragraphs", []) or []
        texts: list[str] = []

        for paragraph in paragraphs:
            if isinstance(paragraph, dict):
                text = paragraph.get("text", "")
            else:
                text = str(paragraph)

            text = str(text).strip()
            if text:
                texts.append(text)

        document_text = "\n".join(texts)
        logger.info("Built document_text len=%s from paragraphs=%s", len(document_text), len(paragraphs))
        return document_text

    def get_image_url(self, image_path: str, project_id: str | None = None) -> str:
        """
        Преобразует локальный путь картинки в публичный URL Doc Service.

        Было:
            storage\\projects\\123\\media\\image1.png

        Стало:
            http://127.0.0.1:8000/storage/projects/123/media/image1.png
        """
        if not image_path:
            return ""

        path_str = str(image_path).replace("\\", "/")

        if path_str.startswith("http://") or path_str.startswith("https://"):
            return path_str

        storage_index = path_str.find("storage/")
        if storage_index != -1:
            relative_path = path_str[storage_index:]
        else:
            relative_path = path_str.lstrip("/")

        image_url = f"{self.service_url}/{relative_path.lstrip('/')}"
        logger.debug("Image path converted to URL: %s -> %s", image_path, image_url)
        return image_url

    def extract_images_with_urls(self, structure: Dict[str, Any], project_id: str) -> List[Dict[str, Any]]:
        """
        Готовит images[] для ML.

        ВАЖНО:
        - в поле path кладём URL, а не локальный путь;
        - local_path сохраняем отдельно только для отладки;
        - ML скачивает именно images[].path.
        """
        images = structure.get("images", []) or []
        result: list[dict[str, Any]] = []

        for img in images:
            if not isinstance(img, dict):
                continue

            img_path = img.get("path", "")
            if not img_path:
                continue

            image_url = self.get_image_url(img_path, project_id)

            item = {
                "image_id": img.get("id", ""),
                "path": image_url,
                "source": img.get("source", "original_docx_image"),
                "filename": Path(str(img_path).replace("\\", "/")).name,
                "position": img.get("position", 0),
                "insert_before_paragraph": img.get("insert_before_paragraph"),
                "local_path": str(img_path),
            }

            result.append(item)

        logger.info("Prepared %s image URLs for ML", len(result))
        if result:
            logger.info("First ML image path: %s", result[0].get("path"))
        return result

    def build_ml_payload(
        self,
        project_id: str,
        structure: Dict[str, Any],
        topic: str | None = None,
    ) -> Dict[str, Any]:
        """
        Собирает правильный JSON-контракт для ML.
        """
        document_text = self.extract_document_text(structure)
        images = self.extract_images_with_urls(structure, project_id)

        payload = {
            "project_id": project_id,
            "document_text": document_text,
            "image_paths": [],
            "image_urls": [],
            "images": images,
            "topic": topic or "лабораторная работа",
        }

        logger.info("ML payload built")
        logger.info("Payload document_text len=%s", len(payload["document_text"]))
        logger.info("Payload images count=%s", len(payload["images"]))
        return payload

    def analyze_document(
        self,
        project_id: str,
        structure: Dict[str, Any],
        topic: str | None = None,
    ) -> Dict[str, Any]:
        """
        Отправляет документ в ML сервис для анализа.
        """
        from app.services.docx_core import ensure_project_dir, save_json

        project_dir = ensure_project_dir(project_id)
        payload = self.build_ml_payload(project_id, structure, topic)

        payload_path = project_dir / "ml_request_payload.json"
        save_json(payload_path, payload)
        logger.info("ML request payload saved to: %s", payload_path)

        if not payload["document_text"]:
            logger.warning("ML payload document_text is empty")

        logger.info("Sending request to ML: %s/analyze", self.base_url)

        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            logger.info("ML response HTTP status=%s", response.status_code)

            raw_response_path = project_dir / "ml_response_raw.txt"
            raw_response_path.write_text(response.text, encoding="utf-8")

            response.raise_for_status()
            ml_response = response.json()

            response_path = project_dir / "ml_response.json"
            save_json(response_path, ml_response)
            logger.info("ML response saved to: %s", response_path)

            return ml_response

        except requests.exceptions.RequestException as e:
            logger.error("ML service request error: %s", str(e))
            error_payload = {
                "error": str(e),
                "payload": payload,
            }
            save_json(project_dir / "ml_error.json", error_payload)
            return self._get_error_response("MLRequestError", str(e))

        except json.JSONDecodeError as e:
            logger.error("ML returned invalid JSON: %s", str(e))
            error_payload = {
                "error": str(e),
                "payload": payload,
                "raw_response_file": "ml_response_raw.txt",
            }
            save_json(project_dir / "ml_error.json", error_payload)
            return self._get_error_response("MLInvalidJSON", str(e))

        except Exception as e:
            logger.error("ML service unknown error: %s", str(e))
            error_payload = {
                "error": str(e),
                "payload": payload,
            }
            save_json(project_dir / "ml_error.json", error_payload)
            return self._get_error_response("UnknownError", str(e))

    def _get_error_response(self, error_code: str, error_message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "topic": "",
            "status": "error",
            "summary": {
                "status": "error",
                "missing_sections_count": 0,
                "images_count": 0,
                "suggestions_count": 0,
            },
            "generated_sections": [],
            "bibliography": [],
            "images": [],
            "errors": [{"code": error_code, "message": error_message}],
            "meta": {
                "module": "document-service",
                "fallback": True,
                "error": error_message,
            },
        }


ml_client = MLClient()


def analyze_document_with_ml(
    project_id: str,
    structure: Dict[str, Any],
    topic: str | None = None,
) -> Dict[str, Any]:
    return ml_client.analyze_document(project_id, structure, topic)
