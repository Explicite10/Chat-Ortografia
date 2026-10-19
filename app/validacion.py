"""Capas de validación sobre la salida del modelo.

Cada capa devuelve una lista de problemas legibles en español. Lista vacía = corrección aceptada.

Capa 1 - Estructura: salida no vacía, sin explicaciones ("Aquí tienes…"), longitud parecida al original.
Capa 2 - Extranjerismos: palabras de portugués/inglés/italiano que un modelo multilingüe suele colar.
Capa 3 - Diccionario Hunspell es_MX (LibreOffice): toda palabra NUEVA (que no venía en el original)
         debe existir en español. Las que ya traía el usuario (nombres, jerga) se respetan.
Capa 4 - Fidelidad: cada palabra nueva debe parecerse (fonéticamente) a alguna del original y ninguna
         palabra del original puede desaparecer. Evita que el modelo agregue o quite ideas ("hoy no").
Capa 5 - Sin corregir: palabras del original que no existen en el diccionario y quedaron idénticas.
Capa 6 - Juez (en corrector.py): segunda consulta al modelo para confirmar que todo está en español.
"""
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from spylls.hunspell import Dictionary

_DIC_PATH = Path(__file__).resolve().parent / "dic" / "es_MX"
_dic = Dictionary.from_files(str(_DIC_PATH))

_PALABRA_RE = re.compile(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+")

# Se comparan sin acentos y en minúsculas.
EXTRANJERISMOS = {
    # portugués
    "ola", "voce", "voces", "obrigado", "obrigada", "nao", "bom", "tudo", "bem", "muito", "sim",
    "tambem", "ate", "coisa", "trabalho", "amanha", "hoje", "estou", "entao", "voltar",
    # inglés
    "hello", "hi", "the", "you", "and", "with", "today", "tomorrow", "sorry", "thanks", "please",
    # italiano
    "ciao", "grazie", "sono", "oggi", "domani", "perche",
}
# Existen también en español con otro sentido: sólo se marcan si llevan un acento inválido ("olá").
_AMBIGUOS = {"ola", "sim", "ate", "bem", "bom", "sono", "voltar"}

_FRASES_EXPLICACION = (
    "aquí tienes", "aquí está", "texto corregido", "la corrección", "corrección:", "versión corregida",
    "he corregido", "claro,", "por supuesto", "entrada:", "salida:",
)


def _sin_acentos(p: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", p) if unicodedata.category(c) != "Mn")


def _palabras(texto: str) -> list[str]:
    return _PALABRA_RE.findall(texto)


def en_diccionario(p: str) -> bool:
    return _dic.lookup(p) or _dic.lookup(p.lower())


# ---------- Capa 1 ----------
def validar_estructura(original: str, corregido: str) -> list[str]:
    if not corregido.strip():
        return ["La respuesta quedó vacía."]
    problemas = []
    bajo = corregido.lower()
    if any(f in bajo[:40] for f in _FRASES_EXPLICACION):
        problemas.append("La respuesta incluye una explicación en lugar de sólo el texto.")
    po, pc = len(_palabras(original)), len(_palabras(corregido))
    if po >= 3 and (pc < po * 0.6 or pc > po * 1.6):
        problemas.append(f"La longitud cambió demasiado ({po} → {pc} palabras).")
    if "\n" not in original and corregido.count("\n") >= 2:
        problemas.append("Se agregaron saltos de línea que no existían.")
    return problemas


# ---------- Capa 2 ----------
def validar_extranjerismos(original: str, corregido: str) -> list[str]:
    problemas = []
    for p in _palabras(corregido):
        bajo = p.lower()
        base = _sin_acentos(bajo)
        if base not in EXTRANJERISMOS:
            continue
        if base in _AMBIGUOS and en_diccionario(bajo):
            continue
        problemas.append(f'"{p}" no es una palabra en español.')
    return problemas


# ---------- Capa 3 ----------
def validar_diccionario(original: str, corregido: str) -> list[str]:
    orig = {_sin_acentos(p.lower()) for p in _palabras(original)}
    problemas = []
    for p in _palabras(corregido):
        if _sin_acentos(p.lower()) in orig:
            continue
        if not en_diccionario(p):
            problemas.append(f'"{p}" no aparece en el diccionario de español.')
    return problemas


# ---------- Capa 4 ----------
def _fonetico(p: str) -> str:
    """Normaliza como suena en español de México para comparar escritura fonética con la correcta."""
    p = _sin_acentos(p.lower())
    p = p.replace("qu", "k").replace("ch", "X")
    p = re.sub(r"c(?=[ei])", "s", p)
    p = p.replace("c", "k").replace("z", "s").replace("x", "s")
    p = p.replace("ll", "y").replace("y", "i").replace("v", "b")
    p = p.replace("h", "").replace("w", "u")
    p = re.sub(r"g(?=[ei])", "j", p)
    p = p.replace("X", "ch")
    return p


def _similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _candidatos(palabras: list[str]) -> set[str]:
    """Formas fonéticas de cada palabra y de cada par de palabras pegadas (para 'por que' → 'porque')."""
    f = [_fonetico(p) for p in palabras]
    out = set(f)
    for i in range(len(f) - 1):
        out.add(f[i] + f[i + 1])
    return out


def _tiene_pareja(p: str, candidatos: set[str], umbral: float) -> bool:
    fp = _fonetico(p)
    if fp in candidatos:
        return True
    for c in candidatos:
        if (len(fp) <= 2 and fp in c) or _similitud(fp, c) >= umbral:
            return True
    return False


def validar_fidelidad(original: str, corregido: str) -> list[str]:
    po, pc = _palabras(original), _palabras(corregido)
    co, cc = _candidatos(po), _candidatos(pc)
    problemas = []
    for p in pc:
        if not _tiene_pareja(p, co, 0.6):
            problemas.append(f'Se agregó la palabra "{p}", que no estaba en el texto original.')
    for p in po:
        if len(p) >= 3 and not _tiene_pareja(p, cc, 0.6):
            problemas.append(f'Se quitó la palabra "{p}" del texto original.')
    return problemas


# ---------- Capa 5 ----------
_NOMBRE_PROPIO_RE = re.compile(r"(?<![.?!¿¡]\s)(?<!^)\b([A-ZÁÉÍÓÚÑ][a-záéíóúüñ]+)\b")


def _nombres_propios(texto: str) -> set[str]:
    """Palabras con mayúscula inicial que no abren oración: el modelo las trató como nombre propio."""
    return {m.lower() for m in _NOMBRE_PROPIO_RE.findall(texto)}


def validar_sin_corregir(original: str, corregido: str) -> list[str]:
    nuevas = {p.lower() for p in _palabras(corregido)}
    propios = _nombres_propios(corregido)
    problemas = []
    for p in _palabras(original):
        bajo = p.lower()
        if bajo in propios:
            continue
        if len(p) >= 3 and bajo in nuevas and not en_diccionario(p):
            problemas.append(f'La palabra "{p}" quedó sin corregir y no existe en español.')
    return problemas


def validar(original: str, corregido: str) -> list[str]:
    problemas = validar_estructura(original, corregido)
    if problemas and problemas[0] == "La respuesta quedó vacía.":
        return problemas
    problemas += validar_extranjerismos(original, corregido)
    problemas += validar_diccionario(original, corregido)
    problemas += validar_fidelidad(original, corregido)
    problemas += validar_sin_corregir(original, corregido)
    return list(dict.fromkeys(problemas))
