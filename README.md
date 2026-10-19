# Corrector de ortografía

Chat de una sola pantalla para corregir la ortografía de frases en español. Pensado para personas con poca práctica
escribiendo: letras grandes, dictado por voz, lectura en voz alta del resultado y resaltado de lo que cambió.

- **Backend:** FastAPI + [Ollama](https://ollama.com) con el modelo `qwen3:4b-instruct` (open source, ~2.5 GB, cabe en 8 GB de VRAM).
- **Frontend:** HTML/CSS/JS sin dependencias, servido por la misma API.
- Todo corre en el servidor de la empresa; el texto no sale a internet.

## Correr en local (Mac)

```bash
brew install ollama && ollama serve &
ollama pull qwen3:4b-instruct
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Abre <http://localhost:8000>.

## Correr en el servidor (Docker + GPU)

```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen3:4b-instruct
```

La app queda en el puerto **8090**. Para cambiar de modelo, edita `OLLAMA_MODEL` en `.env`.

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
app/        config.py (variables), corrector.py (prompt + cliente Ollama), diff.py (resaltado), main.py (rutas)
static/     index.html, styles.css, app.js
tests/      pruebas unitarias del diff y la limpieza de respuesta
docs/       notas de diseño y decisiones
```

Ver [docs/decisiones.md](docs/decisiones.md) para el porqué de cada elección.
