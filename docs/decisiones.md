# Decisiones de diseño

## ¿Por qué un LLM pequeño y no un corrector clásico?

Se evaluaron tres caminos (octubre 2026):

| Opción | Pros | Contras |
|---|---|---|
| **LanguageTool** (reglas, Java, autohospedado) | Determinista, rápido, marca posición exacta de cada error | Falla con escritura fonética ("ke aser oi", "boy a ir") típica de personas con poca alfabetización; sólo sugiere, no reescribe |
| **Modelos seq2seq de GEC en español en Hugging Face** (mT5/BART ajustados) | Pequeños | Poco mantenidos, pocas descargas, calidad no verificada; entrenados con textos de estudiantes de español, no con escritura fonética |
| **LLM pequeño instruido (Qwen3-4B, Gemma 3 4B) vía Ollama** | Entiende contexto y errores fonéticos, reescribe completo, español de México aceptable, cabe en 8 GB de VRAM | No determinista (se mitiga con `temperature: 0`); puede "mejorar" de más (se mitiga con el prompt) |

Se eligió la tercera. El diff palabra por palabra se calcula en Python para que la UI resalte qué cambió sin depender del modelo.

## Decisiones de UX para usuarios con baja alfabetización

- Una sola pantalla, un botón principal grande ("Corregir").
- Dictado por voz (Web Speech API, `es-MX`) para quien no quiere escribir. Requiere Chrome/Edge y HTTPS o localhost.
- Lectura en voz alta del resultado (`speechSynthesis`) para quien no puede leer con fluidez.
- Texto a 22–24 px, alto contraste, sin jerga técnica en los mensajes.
- "Ver qué cambió" va plegado: rojo tachado = antes, verde = después. No se muestra por defecto para no abrumar.
- No hay historial de chat: cada corrección es independiente y el texto no se guarda.

## Pendientes / ideas

- Botón "Explícame" que pida al modelo una explicación sencilla de cada corrección.
- Registrar métricas de uso (sin guardar el texto) para medir adopción.
- Evaluar `gemma3:4b` como alternativa si Qwen cambia demasiado el estilo.
