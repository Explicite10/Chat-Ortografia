from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.corrector import CorrectorError, corregir, modelo_disponible
from app.diff import calcular_cambios, contar_cambios

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Corrector de ortografía", version="0.1.0")


class PeticionCorreccion(BaseModel):
    texto: str = Field(..., min_length=1)


class RespuestaCorreccion(BaseModel):
    original: str
    corregido: str
    cambios: list[dict]
    num_cambios: int
    modelo: str
    intentos: int
    advertencias: list[str]
    validado_por_juez: bool | None


@app.post("/api/corregir", response_model=RespuestaCorreccion)
async def api_corregir(peticion: PeticionCorreccion):
    texto = peticion.texto.strip()
    if not texto:
        raise HTTPException(400, "Escribe algo para corregir.")
    if len(texto) > settings.max_chars:
        raise HTTPException(413, f"El texto es muy largo (máximo {settings.max_chars} caracteres).")
    try:
        res = await corregir(texto)
    except CorrectorError as e:
        raise HTTPException(503, str(e))
    cambios = calcular_cambios(texto, res.corregido)
    return RespuestaCorreccion(
        original=texto,
        corregido=res.corregido,
        cambios=cambios,
        num_cambios=contar_cambios(cambios),
        modelo=settings.ollama_model,
        intentos=res.intentos,
        advertencias=res.advertencias,
        validado_por_juez=res.validado_por_juez,
    )


@app.get("/api/salud")
async def salud():
    ok = await modelo_disponible()
    return {"ok": ok, "modelo": settings.ollama_model, "ollama": settings.ollama_url}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
