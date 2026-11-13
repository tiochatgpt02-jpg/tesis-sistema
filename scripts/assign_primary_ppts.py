"""Assign the professor-provided primary PPTs to the intended grade sessions.

The script is idempotent: re-running it updates the same grade/session record
instead of creating duplicates.  It only uses files already stored under the
application's static presentation directory.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.db_service import (
    fetch_all_topics,
    fetch_presentation_by_topic_session,
    insert_presentation,
    insert_topic,
    update_presentation,
    update_topic,
)


PRESENTATION_DIR = PROJECT_ROOT / "static/uploads/presentations"
ASSIGNMENTS = (
    # grade, session, visible title, stored filename
    (4, 1, "El presupuesto", "TEORIA 3.pptx"),
    (5, 1, "Encuestas para el estudio de mercado", "1790280039_TEORIA_1.pptx"),
    (5, 2, "SmartArt", "1790280721_TEORIA_2.pptx"),
    (6, 1, "Microsoft Excel", "1790281296_TEORIA_4.pptx"),
)


def ensure_session_topic(grade: int, session_number: int) -> int:
    session_title = f"Sesión {session_number}"
    for topic in fetch_all_topics() or []:
        if int(topic.get("grade") or 0) == grade and topic.get("title") == session_title:
            update_topic(topic["id"], status="Publicado")
            return int(topic["id"])
    return int(insert_topic(
        session_title,
        f"Material de primaria asignado por el docente para la sesión {session_number}.",
        grade,
        "Publicado",
    ))


def assign(grade: int, session_number: int, title: str, filename: str) -> None:
    source = PRESENTATION_DIR / filename
    if not source.is_file():
        raise FileNotFoundError(f"No se encontró el archivo preparado: {source}")
    topic_id = ensure_session_topic(grade, session_number)
    file_path = f"/static/uploads/presentations/{filename}"
    description = f"PPT de primaria proporcionado por el docente: {title}."
    existing = fetch_presentation_by_topic_session(topic_id, session_number)
    if existing:
        update_presentation(existing["id"], title, description, file_path, filename, source.stat().st_size)
        action = "actualizado"
    else:
        insert_presentation(topic_id, title, session_number, description, file_path, filename, source.stat().st_size, 3)
        action = "asignado"
    print(f"{grade}° · sesión {session_number} · {title} · {action}")


if __name__ == "__main__":
    for item in ASSIGNMENTS:
        assign(*item)
