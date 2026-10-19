from app.corrector import _limpiar


def test_quita_comillas_y_think():
    assert _limpiar('"Hoy voy."') == "Hoy voy."
    assert _limpiar("<think>x</think>\nHoy voy.") == "Hoy voy."
    assert _limpiar("  Hoy voy.  ") == "Hoy voy."
