from __future__ import annotations

from pathlib import Path
import warnings

from PIL import Image, ImageEnhance

warnings.filterwarnings("ignore", category=UserWarning)

_paddle_reader = None
_easy_reader = None


def prepare_image_for_ocr(image_path: str) -> Image.Image:
    image = Image.open(image_path).convert("L")
    width, height = image.size
    image = image.resize((width * 2, height * 2))
    image = ImageEnhance.Contrast(image).enhance(1.7)
    image = ImageEnhance.Sharpness(image).enhance(1.8)
    return image


def get_paddle_reader():
    global _paddle_reader

    if _paddle_reader is None:
        from paddleocr import PaddleOCR

        print("[OCR] Initializing PaddleOCR...")

        try:
            _paddle_reader = PaddleOCR(
                lang="ru",
                use_angle_cls=True,
                show_log=False,
            )
        except TypeError:
            _paddle_reader = PaddleOCR(
                lang="ru",
                use_angle_cls=True,
            )

    return _paddle_reader


def get_easy_reader():
    global _easy_reader

    if _easy_reader is None:
        import easyocr

        print("[OCR] Initializing EasyOCR fallback...")
        _easy_reader = easyocr.Reader(["ru", "en"], gpu=False)

    return _easy_reader


def extract_text_from_image(image_path: str) -> str:
    """
    OCR pipeline:
    1. PaddleOCR
    2. EasyOCR fallback
    3. Empty text safe fallback

    OCR fallback is independent from AI/Ollama fallback.
    If PaddleOCR fails, the system can still run:
    EasyOCR -> Ollama -> JSON.
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    paddle_error = None
    easy_error = None

    try:
        text = extract_text_paddle(str(path))

        if text.strip():
            print(f"[OCR] PaddleOCR text from {path.name}: {text}")
            return text

        print(f"[OCR FALLBACK] PaddleOCR returned empty text for {path.name}")

    except Exception as error:
        paddle_error = error
        print(f"[OCR FALLBACK] PaddleOCR failed for {path.name}: {error}")

    try:
        text = extract_text_easy(str(path))

        if text.strip():
            print(f"[OCR] EasyOCR text from {path.name}: {text}")
            return text

        print(f"[OCR FALLBACK] EasyOCR returned empty text for {path.name}")

    except Exception as error:
        easy_error = error
        print(f"[OCR ERROR] EasyOCR failed for {path.name}: {error}")

    print(
        "[OCR ERROR] All OCR engines failed. "
        f"PaddleOCR error: {paddle_error}; EasyOCR error: {easy_error}"
    )

    return ""


def extract_text_paddle(image_path: str) -> str:
    reader = get_paddle_reader()
    result = reader.ocr(image_path, cls=True)

    lines: list[str] = []

    if not result:
        return ""

    for page in result:
        if not page:
            continue

        for item in page:
            text = _extract_text_from_paddle_item(item)

            if text:
                lines.append(text)

    return " ".join(lines).strip()


def _extract_text_from_paddle_item(item) -> str:
    if not item:
        return ""

    if isinstance(item, str):
        return item.strip()

    if isinstance(item, (list, tuple)):
        if len(item) >= 2:
            text_data = item[1]

            if isinstance(text_data, str):
                return text_data.strip()

            if isinstance(text_data, (list, tuple)) and text_data:
                if isinstance(text_data[0], str):
                    return text_data[0].strip()

        for sub_item in item:
            text = _extract_text_from_paddle_item(sub_item)
            if text:
                return text

    return ""


def extract_text_easy(image_path: str) -> str:
    prepared = prepare_image_for_ocr(image_path)
    reader = get_easy_reader()

    result = reader.readtext(prepared, detail=0)
    result = [line.strip() for line in result if line and line.strip()]

    return " ".join(result).strip()
