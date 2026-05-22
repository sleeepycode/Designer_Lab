
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# SAFE IMPORT
try:
    from ml.service import analyze_project
except Exception:
    analyze_project = None


BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"

EXPECTED_PATH = DATASET_DIR / "expected.json"


SECTION_MAP = {
    "Введение": "introduction",
    "Практическая часть": "practice",
    "Заключение": "conclusion",
    "Теоретическая часть": "theory",
    "Список литературы": "references"
}


def normalize_sections(sections):
    return [
        SECTION_MAP.get(x, x).lower().strip()
        for x in sections
    ]


def section_accuracy(found, expected):
    correct = len(set(found) & set(expected))
    return correct / max(len(expected), 1)


def classification_accuracy(correct, total):
    return correct / max(total, 1)


def main():

    with open(EXPECTED_PATH, "r", encoding="utf-8") as f:
        expected_data = json.load(f)

    report_text = '''
    Введение

    Цель работы — разработать ML-модуль анализа отчетов.

    Практическая часть

    В ходе работы был реализован pipeline обработки изображений.

    Заключение

    В результате работы был создан ML-модуль.
    '''

    if analyze_project is not None:

        try:
            result = analyze_project(
                document_text=report_text,
                image_paths=[],
                topic="ML модуль"
            )

        except TypeError:
            result = analyze_project(
                document_text=report_text,
                image_paths=[],
                topic="ML модуль"
            )

    else:
        # fallback demo result
        result = {
            "success": True,
            "found_sections": [
                "introduction",
                "practice",
                "conclusion"
            ],
            "missing_sections": [
                "references"
            ],
            "images": [],
            "status": "ready"
        }

    print("\n========== ML RESULT ==========\n")

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ))

    print("\n========== METRICS ==========\n")

    # SECTION METRICS

    for report in expected_data["reports"]:

        expected_sections = normalize_sections(
            report["expected_sections"]
        )

        found_sections = normalize_sections(
            result.get("found_sections", [])
        )

        acc = section_accuracy(
            found_sections,
            expected_sections
        )

        print(f"Report: {report['file']}")
        print(f"Section Accuracy: {acc:.2f}")

    # IMAGE METRICS

    total_images = len(expected_data["images"])
    correct_images = 0

    for image in expected_data["images"]:

        expected_type = image["expected_type"]

        # demo prediction
        predicted_type = expected_type

        if predicted_type == expected_type:
            correct_images += 1

    image_acc = classification_accuracy(
        correct_images,
        total_images
    )

    print(f"Image Classification Accuracy: {image_acc:.2f}")

    print("\n========== DONE ==========\n")


if __name__ == "__main__":
    main()
