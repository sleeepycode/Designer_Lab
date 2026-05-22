import os
from pathlib import Path

import pytest

from tests.conftest import IMAGES_DIR


@pytest.mark.integration
def test_real_ocr_can_read_at_least_some_text_from_generated_graph():
    if os.getenv("RUN_REAL_OCR") != "1":
        pytest.skip("Real OCR test is disabled. Run with RUN_REAL_OCR=1 pytest -m integration")

    from ml.ocr import extract_text_from_image

    text = extract_text_from_image(str(IMAGES_DIR / "graph_temperature.png"))

    assert isinstance(text, str)
    assert len(text.strip()) > 0
