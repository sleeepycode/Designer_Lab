from ml.service import analyze_project

from tests.conftest import read_asset


def test_complete_report_has_required_structure():
    result = analyze_project(
        document_text=read_asset("report_complete.txt"),
        image_paths=[],
        topic="Анализ экспериментальных данных",
    )

    assert result["success"] is True
    assert result["summary"]["status"] == "ready"
    assert result["report"]["has_required_structure"] is True
    assert set(result["report"]["found_sections"]) == {
        "introduction",
        "theory",
        "practice",
        "conclusion",
        "references",
    }
    assert result["report"]["missing_sections"] == []
    assert result["content_suggestions"] == []


def test_missing_sections_are_detected_and_suggestions_are_created():
    result = analyze_project(
        document_text=read_asset("report_missing_sections.txt"),
        image_paths=[],
        topic="Обработка экспериментальных данных",
    )

    missing = set(result["report"]["missing_sections"])

    assert result["success"] is True
    assert result["summary"]["status"] == "needs_review"
    assert "introduction" in result["report"]["found_sections"]
    assert "practice" in result["report"]["found_sections"]
    assert {"theory", "conclusion", "references"}.issubset(missing)
    assert result["summary"]["suggestions_count"] >= 3

    targets = {item["target"] for item in result["content_suggestions"]}
    assert {"theory", "conclusion", "references"}.issubset(targets)


def test_empty_report_returns_controlled_error_not_crash():
    result = analyze_project(
        document_text=read_asset("report_empty.txt"),
        image_paths=[],
        topic="Пустой отчёт",
    )

    assert result["success"] is False
    assert result["summary"]["status"] == "error"
    assert "document_text is empty" in result["errors"]
    assert set(result["report"]["missing_sections"]) == {
        "introduction",
        "theory",
        "practice",
        "conclusion",
        "references",
    }
