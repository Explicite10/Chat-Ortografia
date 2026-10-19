from app.diff import calcular_cambios, contar_cambios


def test_sin_cambios():
    seg = calcular_cambios("Hola mundo", "Hola mundo")
    assert contar_cambios(seg) == 0
    assert "".join(s["despues"] for s in seg) == "Hola mundo"


def test_una_palabra():
    seg = calcular_cambios("oy no boy", "hoy no voy")
    cambios = [s for s in seg if s["tipo"] == "cambio"]
    assert [c["antes"] for c in cambios] == ["oy", "boy"]
    assert [c["despues"] for c in cambios] == ["hoy", "voy"]
    assert "".join(s["despues"] for s in seg) == "hoy no voy"


def test_cambios_contiguos_se_fusionan():
    seg = calcular_cambios("por que estoy", "porque estoy")
    assert contar_cambios(seg) == 1


def test_reconstruye_original():
    o, c = "el niño  come\nmanzanas", "El niño come\nmanzanas."
    seg = calcular_cambios(o, c)
    assert "".join(s["antes"] for s in seg) == o
    assert "".join(s["despues"] for s in seg) == c
