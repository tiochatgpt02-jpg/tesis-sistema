from __future__ import annotations

from typing import Any, Union


def score_20_to_percentage_100(score_20: Union[int, float, str, None]) -> float:
    """Convierte una calificación en escala vigesimal (0–20) a porcentaje (0–100%).
    
    Casos canónicos:
      0 / 20  -> 0.0%
      10 / 20 -> 50.0%
      20 / 20 -> 100.0%
    """
    try:
        val = float(score_20 if score_20 is not None else 0.0)
    except (ValueError, TypeError):
        return 0.0
    val = max(0.0, min(20.0, val))
    return round((val / 20.0) * 100.0, 2)


def percentage_100_to_score_20(percentage_100: Union[int, float, str, None]) -> float:
    """Convierte un porcentaje (0–100%) a calificación en escala vigesimal (0–20).
    
    Casos canónicos:
      0.0%   -> 0.0 / 20
      50.0%  -> 10.0 / 20
      100.0% -> 20.0 / 20
    """
    try:
        val = float(percentage_100 if percentage_100 is not None else 0.0)
    except (ValueError, TypeError):
        return 0.0
    val = max(0.0, min(100.0, val))
    return round((val / 100.0) * 20.0, 2)


def normalize_to_scale_20(value: Any) -> float:
    """Garantiza que cualquier valor numérico (0-100 o 0-20) quede normalizado a escala 0-20."""
    try:
        val = float(value if value is not None else 0.0)
    except (ValueError, TypeError):
        return 0.0
    if val > 20.0:
        return percentage_100_to_score_20(val)
    return round(max(0.0, val), 2)
