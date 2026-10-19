# Corrector de ortografía

Chat de una sola pantalla para corregir la ortografía de frases en español. Pensado para personas con poca práctica
escribiendo: letras grandes y lectura en voz alta del resultado.

- **Backend:** FastAPI + [Ollama](https://ollama.com) con el modelo `qwen3:4b-instruct` (open source, ~2.5 GB, cabe en 8 GB de VRAM).
- **Frontend:** HTML/CSS/JS sin dependencias, servido por la misma API.
- **Validación en 6 capas** (estructura, extranjerismos, diccionario Hunspell es_MX, fidelidad fonética, palabras sin corregir, juez) con reintento automático. Ver [docs/decisiones.md](docs/decisiones.md).
- Sólo español. Todo corre en el servidor de la empresa; el texto no sale a internet.

## Correr en local (Mac)

```bash
brew install ollama && ollama serve &
ollama pull qwen3:4b-instruct
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Abre <http://localhost:8000>.

## Correr en el servidor (Docker + GPU)

Requisitos: Docker con Compose v2 y NVIDIA Container Toolkit.

```bash
docker compose up -d --build
```

La primera vez el servicio `ollama-pull` descarga el modelo (~2.5 GB) y la API espera a que termine.
La app queda en el puerto **18620** (cámbialo con `APP_PORT` en `.env`). Ollama no se expone fuera de Docker.

## API

| Método | Ruta            | Descripción                                   |
|--------|-----------------|-----------------------------------------------|
| POST   | `/api/corregir` | `{"texto": "..."}` → original, corregido, cambios, num_cambios |
| GET    | `/api/salud`    | Indica si el modelo está disponible           |
| GET    | `/docs`         | Swagger                                       |

Ejemplo:

```bash
curl -s localhost:8000/api/corregir -H 'Content-Type: application/json' -d '{"texto":"oy no boy a ir por que estoy enfermo"}'
```

## Pruebas

```bash
pytest -q
```

## Estructura

```
app/        config.py (variables), corrector.py (prompt + reintentos + juez), validacion.py (capas), diff.py (resaltado), main.py (rutas)
app/dic/    diccionario Hunspell es_MX (LibreOffice, licencia LGPL/GPL/MPL)
static/     index.html, styles.css, app.js
tests/      pruebas unitarias del diff y la limpieza de respuesta
docs/       notas de diseño y decisiones
```

Ver [docs/decisiones.md](docs/decisiones.md) para el porqué de cada elección.
