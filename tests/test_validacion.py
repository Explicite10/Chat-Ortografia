from app.validacion import validar


def test_rechaza_portugues():
    assert validar("ola, como estas", "¿Olá, cómo estás?")


def test_acepta_espanol_correcto():
    assert validar("ola, como estas", "Hola, ¿cómo estás?") == []
    assert validar("oy no boy", "Hoy no voy.") == []
    assert validar("ke ago", "¿Qué hago?") == []


def test_ola_del_mar_es_valida():
    assert validar("la ola del mar", "La ola del mar.") == []


def test_respeta_palabras_del_usuario():
    assert validar("voy con el lic garcia a xochimilco", "Voy con el Lic. García a Xochimilco.") == []


def test_rechaza_explicacion_y_resumen():
    assert validar("me duele la caveza", "Aquí tienes: me duele la cabeza")
    assert validar("uno dos tres cuatro cinco seis", "uno")


def test_rechaza_palabra_inventada():
    assert validar("tengo kalentura", "Tengo kalenturia.")


def test_rechaza_palabras_agregadas():
    assert any("agregó" in p for p in validar(
        "disculpe jefe boi a yegar tarde por el trafico",
        "Disculpe, jefe, hoy no voy a llegar tarde por el tráfico."))


def test_rechaza_palabras_quitadas():
    assert any("quitó" in p for p in validar("oy no boy a trabajar", "Hoy no voy."))


def test_fidelidad_acepta_correcciones_foneticas():
    casos = [
        ("disculpe jefe boi a yegar tarde por el trafico", "Disculpe, jefe, voy a llegar tarde por el tráfico."),
        ("nesesito permiso para salir temprano aser un tramite", "Necesito permiso para salir temprano a hacer un trámite."),
        ("oy no boy a ir por que estoy enfermo, me duele la caveza y tengo kalentura", "Hoy no voy a ir porque estoy enfermo, me duele la cabeza y tengo calentura."),
        ("ke ora es la junta", "¿Qué hora es la junta?"),
        ("la maquina no sirbe, nesesito ke benga el tecnico", "La máquina no sirve, necesito que venga el técnico."),
    ]
    for o, c in casos:
        assert validar(o, c) == [], (o, c, validar(o, c))


def test_detecta_palabras_sin_corregir():
    probs = validar("disculpe jefe boi a yegar tarde", "Disculpe, jefe, boi a yegar tarde.")
    assert any("boi" in p and "sin corregir" in p for p in probs)
    assert any("yegar" in p for p in probs)
