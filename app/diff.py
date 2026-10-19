"""Cálculo de diferencias palabra por palabra entre el texto original y el corregido."""
import re
from difflib import SequenceMatcher

_TOKEN_RE = re.compile(r"\s+|[^\s]+")


def tokenizar(texto: str) -> list[str]:
    """Separa en palabras y espacios, conservando ambos para poder reconstruir el texto."""
    return _TOKEN_RE.findall(texto)


def calcular_cambios(original: str, corregido: str) -> list[dict]:
    """Devuelve una lista de segmentos: {"tipo": "igual"|"cambio", "antes": str, "despues": str}."""
    a = tokenizar(original)
    b = tokenizar(corregido)
    sm = SequenceMatcher(None, a, b, autojunk=False)
    segmentos: list[dict] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        antes = "".join(a[i1:i2])
        despues = "".join(b[j1:j2])
        if op == "equal":
            segmentos.append({"tipo": "igual", "antes": antes, "despues": despues})
        else:
            segmentos.append({"tipo": "cambio", "antes": antes, "despues": despues})
    return _fusionar(segmentos)


def _fusionar(segmentos: list[dict]) -> list[dict]:
    """Une cambios separados sólo por espacios para que se resalten como una sola unidad."""
    out: list[dict] = []
    for seg in segmentos:
        if (
            out
            and seg["tipo"] == "cambio"
            and out[-1]["tipo"] == "igual"
            and out[-1]["antes"].isspace()
            and len(out) >= 2
            and out[-2]["tipo"] == "cambio"
        ):
            espacio = out.pop()
            prev = out[-1]
            prev["antes"] += espacio["antes"] + seg["antes"]
            prev["despues"] += espacio["despues"] + seg["despues"]
            continue
        out.append(seg)
    return out


def contar_cambios(segmentos: list[dict]) -> int:
    return sum(1 for s in segmentos if s["tipo"] == "cambio")
