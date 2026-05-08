from pathlib import Path
import warnings
import easyocr
from PIL import Image, ImageEnhance
warnings.filterwarnings('ignore', category=UserWarning)
_reader = None
def get_reader():
    global _reader
    if _reader is None:
        print('[OCR] Initializing EasyOCR...')
        _reader = easyocr.Reader(['ru','en'], gpu=False)
    return _reader
def prepare_image_for_ocr(image_path: str) -> Image.Image:
    image = Image.open(image_path).convert('L')
    w,h=image.size
    image=image.resize((w*2,h*2))
    image=ImageEnhance.Contrast(image).enhance(1.7)
    image=ImageEnhance.Sharpness(image).enhance(1.8)
    return image
def extract_text_from_image(image_path: str) -> str:
    path=Path(image_path)
    if not path.exists(): raise FileNotFoundError(f'Image not found: {image_path}')
    result=get_reader().readtext(prepare_image_for_ocr(str(path)), detail=0)
    result=[x.strip() for x in result if x and x.strip()]
    text=' '.join(result).strip()
    print(f'[OCR] Extracted text from {path.name}: {text}')
    return text
