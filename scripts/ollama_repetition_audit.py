"""Auditoría reproducible de estabilidad del generador sobre los PPT de primaria.

No escribe en PostgreSQL ni publica actividades. Imprime una fila JSON por intento
para que la ejecución pueda conservarse como evidencia de la sustentación.
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ai_game_generator_service import AIGameGeneratorService
from services.material_extractor_service import MaterialExtractorService


CASES = (
    ('4.º · El presupuesto', ROOT / 'static/uploads/presentations/TEORIA 3.pptx', 4),
    ('5.º · Encuestas', ROOT / 'static/uploads/presentations/1790280039_TEORIA_1.pptx', 5),
    ('5.º · SmartArt', ROOT / 'static/uploads/presentations/1790280721_TEORIA_2.pptx', 5),
    ('6.º · Microsoft Excel', ROOT / 'static/uploads/presentations/1790281296_TEORIA_4.pptx', 6),
)


def main():
    repetitions = max(1, int(os.getenv('AUDIT_REPETITIONS', '3')))
    case_limit = max(1, min(len(CASES), int(os.getenv('AUDIT_CASE_LIMIT', str(len(CASES))))))
    for label, ppt_path, grade in CASES[:case_limit]:
        material = MaterialExtractorService.extract_from_pptx(str(ppt_path))
        for attempt in range(1, repetitions + 1):
            started = time.monotonic()
            result = AIGameGeneratorService.generate_game(
                material_data=material,
                game_type='multiple_choice',
                grade=grade,
            )
            game = result.get('game') or {}
            print(json.dumps({
                'material': label,
                'attempt': attempt,
                'success': bool(result.get('success')),
                'source': result.get('source'),
                'fallback_reason': result.get('fallback_reason', ''),
                'question': (game.get('content') or {}).get('question', ''),
                'seconds': round(time.monotonic() - started, 2),
            }, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
