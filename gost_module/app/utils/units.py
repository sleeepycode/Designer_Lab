from __future__ import annotations

EMU_PER_CM = 360000


def emu_to_cm(value) -> float | None:
    if value is None:
        return None
    return round(value / EMU_PER_CM, 2)


def safe_pt(value) -> float | None:
    if value is None:
        return None
    try:
        return round(value.pt, 2)
    except AttributeError:
        return None
