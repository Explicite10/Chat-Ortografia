"""Cliente de Ollama para corregir ortografía en español, con validación por capas y reintento."""
import re
from dataclasses import dataclass, field

import httpx

from app.config import settings
from app.validacion import validar

SYSTEM_PROMPT = """Eres un corrector ortográfico de ESPAÑOL DE MÉXICO.
Recibirás un texto escrito por una persona que puede tener poca práctica escribiendo.
Tu única tarea es devolver el MISMO texto con la ortografía corregida.

Reglas:
- Responde ÚNICAMENTE en español. Nunca uses palabras de portugués, inglés ni otro idioma. "ola" como saludo es "Hola"; "olá" NO existe en español.
- Corrige acentos, letras cambiadas (b/v, s/c/z, y/ll, h muda, g/j, k/qu), palabras pegadas o separadas, mayúsculas y signos (¿? ¡!).
- Usa el contexto de toda la frase para decidir la palabra correcta (por ejemplo "oy" al inicio es "Hoy", "boy" es "voy").
- Conserva el significado, el orden, las palabras elegidas y el tono. No agregues ni quites información. No resumas.
- No expliques nada, no saludes, no pongas comillas ni notas. Responde SOLO con el texto corregido.
- Si el texto ya está bien, devuélvelo tal cual.

Ejemplos:
Entrada: ola, como estas
Salida: Hola, ¿cómo estás?
Entrada: oy no boy a ir por que estoy enfermo
Salida: Hoy no voy a ir porque estoy enfermo.
Entrada: ke ora es la junta de mañana
Salida: ¿Qué hora es la junta de mañana?
Entrada: disculpe jefe boi a yegar tarde por el trafico
Salida: Disculpe, jefe, voy a llegar tarde por el tráfico.
Entrada: nesesito permiso para salir temprano aser un tramite
Salida: Necesito permiso para salir temprano a hacer un trámite.
Entrada: Ya entregué el reporte.
Salida: Ya entregué el reporte."""

REPARACION_PROMPT = """Tu corrección anterior fue:
{anterior}

Tuvo estos problemas:
{problemas}

Corrige de nuevo el texto original. DEBES corregir TODAS las palabras mal escritas (cada palabra corregida
reemplaza a una palabra del original en su misma posición), pero NO agregues palabras nuevas ni quites ninguna.
Responde SOLO con el texto corregido, en español.
Texto original:
{texto}"""

JUEZ_PROMPT = """Revisa este texto y responde con UNA sola palabra: "OK" si todo está escrito en español correcto,
o "NO" si contiene palabras de otro idioma, palabras inventadas o errores ortográficos evidentes.

Texto:
{texto}"""

MAX_INTENTOS = 3


class CorrectorError(Exception):
    pass


@dataclass
class Resultado:
    corregido: str
    intentos: int = 1
    advertencias: list[str] = field(default_factory=list)
    validado_por_juez: bool | None = None


def _limpiar(respuesta: str) -> str:
    r = respuesta.strip()
    r = re.sub(r"<think>.*?</think>", "", r, flags=re.S).strip()
    r = re.sub(r"^(salida|texto corregido)\s*:\s*", "", r, flags=re.I).strip()
    if len(r) >= 2 and r[0] == r[-1] and r[0] in "\"'“”«»":
        r = r[1:-1].strip()
    return r


async def _chat(messages: list[dict], num_predict: int = 1024) -> str:
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
    except httpx.ConnectError as e:
        raise CorrectorError("No se pudo conectar con el modelo (Ollama).") from e
    except httpx.TimeoutException as e:
        raise CorrectorError("El modelo tardó demasiado en responder.") from e
    if resp.status_code != 200:
        raise CorrectorError(f"Ollama respondió {resp.status_code}: {resp.text[:200]}")
    return resp.json().get("message", {}).get("content", "")


async def _juez(texto: str) -> bool:
    """Capa 4: el modelo confirma que el resultado está en español. True = aprobado."""
    r = await _chat([{"role": "user", "content": JUEZ_PROMPT.format(texto=texto)}], num_predict=8)
    return _limpiar(r).upper().startswith("OK")


async def corregir(texto: str) -> Resultado:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": texto},
    ]
    mejor: tuple[str, list[str]] | None = None  # (candidato, problemas) con menos problemas
    for intento in range(1, MAX_INTENTOS + 1):
        candidato = _limpiar(await _chat(messages))
        problemas = validar(texto, candidato)
        if not problemas:
            juez_ok = await _juez(candidato) if settings.usar_juez else None
            if juez_ok is False:
                problemas = ["El verificador detectó palabras que no son español."]
            else:
                return Resultado(corregido=candidato, intentos=intento, validado_por_juez=juez_ok)
        if candidato and (mejor is None or len(problemas) < len(mejor[1])):
            mejor = (candidato, problemas)
        messages = messages[:1] + [
            {
                "role": "user",
                "content": REPARACION_PROMPT.format(
                    anterior=candidato, problemas="\n".join(f"- {p}" for p in problemas), texto=texto
                ),
            }
        ]
    # Se agotaron los intentos: entregamos el mejor candidato con advertencias
    if mejor is None:
        raise CorrectorError("El modelo devolvió una respuesta vacía.")
    return Resultado(corregido=mejor[0], intentos=MAX_INTENTOS, advertencias=mejor[1], validado_por_juez=False)


async def modelo_disponible() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_url}/api/tags")
        nombres = [m.get("name", "") for m in resp.json().get("models", [])]
        return any(n == settings.ollama_model or n.split(":")[0] == settings.ollama_model for n in nombres)
    except Exception:
        return False
