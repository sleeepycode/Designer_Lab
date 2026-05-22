import json
from pathlib import Path

from ml.service import analyze_project

from tests.conftest import ASSETS_DIR, generated_image_paths, fake_ocr_for_generated_images, read_asset


def test_generated_images_exist_and_are_valid_png():
    from PIL import Image

    for image_path in generated_image_paths():
        path = Path(image_path)
        assert path.exists(), f"Нет тестовой картинки: {path}"
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.width >= 500
            assert image.height >= 300


def test_full_image_pipeline_classifies_numbers_and_places_images(monkeypatch):
    import ml.image_analyzer as image_analyzer

    monkeypatch.setattr(image_analyzer, "extract_text_from_image", fake_ocr_for_generated_images)

    result = analyze_project(
        document_text=read_asset("report_complete.txt"),
        image_paths=generated_image_paths(),
        topic="Анализ экспериментальных данных",
    )

    assert result["success"] is True
    assert result["summary"]["images_count"] == 4

    by_name = {Path(item["path"]).name: item for item in result["images"]}
    expected = json.loads((ASSETS_DIR / "expected_images.json").read_text(encoding="utf-8"))

    for filename, rules in expected.items():
        image = by_name[filename]
        assert image["error"] is None
        assert image["type"] == rules["type"]
        assert image["numbering_type"] == rules["numbering_type"]
        assert rules["expected_caption_contains"] in image["caption"]
        assert image["confidence"] >= 0.45
        assert image["placement"]["paragraph_index"] >= 0
        assert image["placement"]["score"] > 0

    assert by_name["graph_temperature.png"]["number"] == 1
    assert by_name["table_measurements.png"]["number"] == 1
    assert by_name["scheme_algorithm.png"]["number"] == 2
    assert by_name["formula_average.png"]["number"] == 3


def test_image_classification_accuracy_on_generated_dataset(monkeypatch):
    import ml.image_analyzer as image_analyzer

    monkeypatch.setattr(image_analyzer, "extract_text_from_image", fake_ocr_for_generated_images)

    result = analyze_project(
        document_text=read_asset("report_complete.txt"),
        image_paths=generated_image_paths(),
        topic="Анализ экспериментальных данных",
    )

    expected = json.loads((ASSETS_DIR / "expected_images.json").read_text(encoding="utf-8"))
    correct = 0

    for image in result["images"]:
        filename = Path(image["path"]).name
        if image["type"] == expected[filename]["type"]:
            correct += 1

    accuracy = correct / len(expected)
    assert accuracy >= 0.95
