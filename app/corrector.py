"""Cliente de Ollama para corregir ortografía en español."""
import re

import httpx

from app.config import settings

SYSTEM_PROMPT = """Eres un corrector ortográfico de español de México.
Recibirás un texto escrito por una persona que puede tener poca práctica escribiendo.
Tu única tarea es devolver el MISMO texto con la ortografía corregida:
- Corrige acentos, letras cambiadas (b/v, s/c/z, y/ll, h muda, g/j, k/qu), palabras pegadas o separadas, mayúsculas y puntuación básica.
- Conserva el significado, el orden de las ideas, las palabras elegidas y el tono. No agregues ni quites información.
- No expliques nada, no saludes, no pongas comillas ni notas. Responde SOLO con el texto corregido.
- Si el texto ya está bien, devuélvelo tal cual.

Ejemplos:
Entrada: oy no boy a ir por que estoy enfermo
Salida: Hoy no voy a ir porque estoy enfermo.
Entrada: ke ora es la junta de mañana
Salida: ¿Qué hora es la junta de mañana?
Entrada: nesesito permiso para salir temprano aser un tramite
Salida: Necesito permiso para salir temprano a hacer un trámite.
Entrada: Ya entregué el reporte.
Salida: Ya entregué el reporte."""


class CorrectorError(Exception):
    pass


def _limpiar(respuesta: str) -> str:
    r = respuesta.strip()
    r = re.sub(r"<think>.*?</think>", "", r, flags=re.S).strip()
    # Quita comillas envolventes que a veces agrega el modelo
    if len(r) >= 2 and r[0] == r[-1] and r[0] in "\"'“”«»":
        r = r[1:-1].strip()
    return r


async def corregir(texto: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texto},
        ],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 1024},
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
    contenido = resp.json().get("message", {}).get("content", "")
    corregido = _limpiar(contenido)
    if not corregido:
        raise CorrectorError("El modelo devolvió una respuesta vacía.")
    return corregido


async def modelo_disponible() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_url}/api/tags")
        nombres = [m.get("name", "") for m in resp.json().get("models", [])]
        return any(n == settings.ollama_model or n.split(":")[0] == settings.ollama_model for n in nombres)
    except Exception:
        return False
