import json
from pathlib import Path

from ml.service import analyze_project
from ml.image_classifier import classify_image_fallback

from tests.conftest import read_asset


def test_response_is_json_serializable_and_backend_contract_is_stable():
    result = analyze_project(
        document_text=read_asset("report_complete.txt"),
        image_paths=[],
        topic="Анализ экспериментальных данных",
    )

    json.dumps(result, ensure_ascii=False)

    assert set(result.keys()) == {
        "success",
        "topic",
        "summary",
        "report",
        "images",
        "content_suggestions",
        "errors",
        "meta",
    }
    assert set(result["summary"].keys()) == {
        "status",
        "missing_sections_count",
        "images_count",
        "suggestions_count",
    }
    assert set(result["report"].keys()) == {
        "found_sections",
        "missing_sections",
        "has_required_structure",
        "generated_sections",
        "bibliography",
    }


def test_bad_image_path_is_returned_as_error_inside_json():
    bad_path = "tests/assets/generated/images/no_such_image.png"

    result = analyze_project(
        document_text=read_asset("report_complete.txt"),
        image_paths=[bad_path],
        topic="Анализ экспериментальных данных",
    )

    assert result["success"] is False
    assert result["summary"]["status"] == "error"
    assert len(result["errors"]) == 1
    assert bad_path in result["errors"][0]
    assert result["images"][0]["type"] == "unknown"
    assert result["images"][0]["error"] is not None


def test_fallback_classifier_recognizes_core_image_types():
    cases = {
        "График зависимости температуры от времени, ось X, ось Y": "graph",
        "Таблица результатов измерений, строка, столбец, значение": "table",
        "Схема алгоритма: начало, процесс, блок, конец": "scheme",
        "Формула расчёта среднего значения и уравнение": "formula",
        "Обычная фотография рабочего окна без ключевых слов": "unknown",
    }

    for text, expected_type in cases.items():
        assert classify_image_fallback(text) == expected_type
