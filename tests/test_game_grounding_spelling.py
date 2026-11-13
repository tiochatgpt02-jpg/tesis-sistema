import pytest

from services.ai_game_generator_service import AIGameGeneratorService


@pytest.mark.parametrize('source,label', [
    ('El raton mueve el puntero.', 'Ratón'),
    ('El ratón mueve el puntero.', 'Raton'),
    ('La información se muestra en el monitor.', 'Informacio\u0301n'),
])
def test_grounding_accepts_equivalent_vowel_accents(source, label):
    game = {'content': {'pairs': [{'left': label, 'right': 'Definicion'}]}}
    assert AIGameGeneratorService._grounding_error(game, source, 'matching') == ''


@pytest.mark.parametrize('label', ['Dinosaurio', 'Montaña', 'Concepto 1'])
def test_grounding_still_rejects_unrelated_concepts(label):
    game = {'content': {'pairs': [{'left': label, 'right': 'Definicion'}]}}
    error = AIGameGeneratorService._grounding_error(game, 'El raton mueve el puntero.', 'matching')
    assert error == 'Las parejas no usan conceptos identificables del material docente.'
