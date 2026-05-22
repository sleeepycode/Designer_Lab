from pathlib import Path
import os
import sys

# Чтобы тесты не зависели от локально запущенной Ollama.
os.environ.setdefault("AI_PROVIDER", "off")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ASSETS_DIR = PROJECT_ROOT / "tests" / "assets" / "generated"
IMAGES_DIR = ASSETS_DIR / "images"

OCR_TEXT_BY_FILE = {
    "graph_temperature.png": "График зависимости температуры от времени. Ось X время, ось Y температура.",
    "table_measurements.png": "Таблица результатов измерений: номер, время, температура, значение.",
    "scheme_algorithm.png": "Схема алгоритма обработки данных: начало, чтение данных, расчёт среднего значения, сохранение результата, конец.",
    "formula_average.png": "Формула расчёта среднего значения. Среднее равно сумма значений разделить на количество измерений.",
}


def read_asset(name: str) -> str:
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


def generated_image_paths() -> list[str]:
    return [str(IMAGES_DIR / name) for name in OCR_TEXT_BY_FILE]


def fake_ocr_for_generated_images(image_path: str) -> str:
    name = Path(image_path).name
    if name not in OCR_TEXT_BY_FILE:
        raise FileNotFoundError(f"Нет тестового OCR-текста для файла: {name}")
    return OCR_TEXT_BY_FILE[name]
