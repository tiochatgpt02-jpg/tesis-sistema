"""Contrato central del motor de actividades gamificadas.

El motor contiene reglas compartidas, nunca HTML ni decisiones de presentación.
Las plantillas y JavaScript son los únicos responsables de cómo se ve cada juego.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


class GameEngine:
    """Reglas y nombres canónicos de los juegos publicados por la plataforma."""

    GAME_TYPES = (
        "multiple_choice",
        "true_false",
        "fill_blank",
        "matching",
        "memory",
        "ordering",
        "drag_drop",
        "challenge",
    )

    TYPE_ALIASES = {
        "opcion_multiple": "multiple_choice",
        "opción_múltiple": "multiple_choice",
        "multiple": "multiple_choice",
        "verdadero_falso": "true_false",
        "vf": "true_false",
        "truefalse": "true_false",
        "completar": "fill_blank",
        "fill": "fill_blank",
        "rellenar": "fill_blank",
        "unir": "matching",
        "relacionar": "matching",
        "parejas": "matching",
        "match": "matching",
        "memoria": "memory",
        "ordenar": "ordering",
        "orden": "ordering",
        "arrastrar": "drag_drop",
        "arrastrar_soltar": "drag_drop",
        "aventura": "challenge",
        "adventure": "challenge",
    }

    @classmethod
    def normalize_type(cls, value: Any) -> str:
        game_type = str(value or "").lower().strip()
        return cls.TYPE_ALIASES.get(game_type, game_type)

    @classmethod
    def score_attempt(cls, game_type: str, content: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, float]:
        """Evalúa un intento sin depender de la interfaz que lo envió."""
        game_type = cls.normalize_type(game_type)
        answer = payload.get("answer")

        if game_type == "multiple_choice":
            return cls._same(answer, content.get("answer")), 1.0
        if game_type == "true_false":
            expected_raw = content.get("correct_answer")
            expected = expected_raw if isinstance(expected_raw, bool) else str(expected_raw).strip().lower() in ("true", "verdadero", "si", "sí", "1")
            received = answer if isinstance(answer, bool) else str(answer).strip().lower() in ("true", "verdadero", "si", "sí", "1")
            return expected == received, 1.0
        if game_type == "fill_blank":
            answers = content.get("answers") or [content.get("blank_word", "")]
            received = str(answer or "").strip().lower()
            correct = any(received == str(item).strip().lower() for item in answers if str(item).strip())
            return correct, 1.0
        if game_type == "matching":
            return cls._score_pairs(payload.get("matches") or answer, content.get("pairs") or [])
        if game_type == "memory":
            return cls._score_pairs(payload.get("matches") or answer, content.get("pairs") or [])
        if game_type == "ordering":
            expected = [str(item).strip().lower() for item in content.get("items") or []]
            received = [str(item).strip().lower() for item in (payload.get("order") or answer or [])]
            return bool(expected) and received == expected, 1.0
        if game_type == "drag_drop":
            return cls._score_categories(payload.get("placements") or answer, content.get("items") or [])
        if game_type == "challenge":
            return cls._score_challenge(payload.get("answers") or answer, content.get("levels") or [])
        return False, 0.0

    @staticmethod
    def _same(left: Any, right: Any) -> bool:
        return bool(str(right or "").strip()) and str(left or "").strip().lower() == str(right).strip().lower()

    @classmethod
    def _score_pairs(cls, submitted: Any, expected_pairs: Iterable[Dict[str, Any]]) -> Tuple[bool, float]:
        expected = {
            str(pair.get("left", "")).strip().lower(): str(pair.get("right", "")).strip().lower()
            for pair in expected_pairs if isinstance(pair, dict)
        }
        submitted_map: Dict[str, str] = {}
        if isinstance(submitted, list):
            for item in submitted:
                if isinstance(item, dict):
                    submitted_map[str(item.get("left", "")).strip().lower()] = str(item.get("right", "")).strip().lower()
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    submitted_map[str(item[0]).strip().lower()] = str(item[1]).strip().lower()
        correct = sum(1 for left, right in expected.items() if submitted_map.get(left) == right)
        ratio = correct / len(expected) if expected else 0.0
        return bool(expected) and correct == len(expected), ratio

    @classmethod
    def _score_categories(cls, submitted: Any, expected_items: Iterable[Dict[str, Any]]) -> Tuple[bool, float]:
        expected = {
            str(item.get("item", "")).strip().lower(): str(item.get("category", "")).strip().lower()
            for item in expected_items if isinstance(item, dict)
        }
        submitted_map = {}
        if isinstance(submitted, list):
            for item in submitted:
                if isinstance(item, dict):
                    submitted_map[str(item.get("item", "")).strip().lower()] = str(item.get("category", "")).strip().lower()
        correct = sum(1 for item, category in expected.items() if submitted_map.get(item) == category)
        ratio = correct / len(expected) if expected else 0.0
        return bool(expected) and correct == len(expected), ratio

    @classmethod
    def _score_challenge(cls, submitted: Any, levels: Iterable[Dict[str, Any]]) -> Tuple[bool, float]:
        answers = submitted if isinstance(submitted, list) else []
        expected = [str(level.get("answer", "")).strip().lower() for level in levels if isinstance(level, dict)]
        received = [str(answer).strip().lower() for answer in answers]
        correct = sum(1 for index, answer in enumerate(expected) if index < len(received) and received[index] == answer)
        ratio = correct / len(expected) if expected else 0.0
        return bool(expected) and correct == len(expected), ratio
