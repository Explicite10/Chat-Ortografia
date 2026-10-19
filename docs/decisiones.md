# Decisiones de diseño

## ¿Por qué un LLM pequeño y no un corrector clásico?

Se evaluaron tres caminos (octubre 2026):

| Opción | Pros | Contras |
|---|---|---|
| **LanguageTool** (reglas, Java, autohospedado) | Determinista, rápido, marca posición exacta de cada error | Falla con escritura fonética ("ke aser oi", "boy a ir") típica de personas con poca alfabetización; sólo sugiere, no reescribe |
| **Modelos seq2seq de GEC en español en Hugging Face** (mT5/BART ajustados) | Pequeños | Poco mantenidos, pocas descargas, calidad no verificada; entrenados con textos de estudiantes de español, no con escritura fonética |
| **LLM pequeño instruido (Qwen3-4B, Gemma 3 4B) vía Ollama** | Entiende contexto y errores fonéticos, reescribe completo, español de México aceptable, cabe en 8 GB de VRAM | No determinista (se mitiga con `temperature: 0`); puede "mejorar" de más (se mitiga con el prompt) |

Se eligió la tercera. El diff palabra por palabra se calcula en Python para que la UI resalte qué cambió sin depender del modelo.

## Capas de validación (agregadas 2026-10-19)

El modelo solo no es confiable: coló "Olá" (portugués) y en una frase agregó "hoy no", cambiando el sentido.
Por eso la salida pasa por `app/validacion.py` antes de mostrarse. Si alguna capa falla, se reintenta hasta
3 veces con un prompt de reparación que le dice al modelo qué estuvo mal; si aun así falla, se entrega el mejor
intento con una advertencia amarilla en la UI.

| Capa | Qué revisa | Ejemplo que atrapa |
|---|---|---|
| 1. Estructura | Salida vacía, explicaciones ("Aquí tienes…"), longitud muy distinta, saltos de línea inventados | "Aquí tienes: me duele la cabeza" |
| 2. Extranjerismos | Lista de palabras de portugués/inglés/italiano que el modelo suele colar | "Olá", "você", "hello" |
| 3. Diccionario | Toda palabra nueva debe existir en Hunspell es_MX (diccionario de LibreOffice, en `app/dic/`) | "kalenturia" |
| 4. Fidelidad | Cada palabra nueva debe parecerse fonéticamente a una del original; ninguna del original puede desaparecer | "hoy **no** voy" cuando el usuario no escribió "no" |
| 5. Sin corregir | Palabras del original que no existen en español y quedaron iguales (salvo nombres propios con mayúscula) | "boi a yegar" devuelto tal cual |
| 6. Juez | Segunda llamada al modelo: "¿todo está en español correcto? OK/NO" (`USAR_JUEZ` en `.env`) | Casos que escapan a las reglas |

La comparación fonética (capa 4) normaliza b/v, s/c/z, y/ll, h muda, k/qu, g/j y acentos, para que "boi" y
"voy" cuenten como la misma palabra y "aser" y "a hacer" también.

Limitaciones conocidas: una palabra mal escrita que por casualidad existe en español ("ola", "esta") no se
detecta por diccionario; depende del contexto que da el modelo. Nombres propios desconocidos se aceptan si el
modelo los escribe con mayúscula.

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
