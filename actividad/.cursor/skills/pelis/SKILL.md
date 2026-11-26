---
name: pelis
description: >-
  Consulta las últimas películas en cartelera de Cine Colombia
  (https://www.cinecolombia.com). Usar cuando el usuario invoca /pelis,
  pide la cartelera, los estrenos o las películas en sala de Cine Colombia.
disable-model-invocation: true
---

# Pelis

Muestra las películas que ya están en cartelera en Cine Colombia, de la más reciente a la más antigua.

## Qué consultar

Películas de cine regular que ya se pueden ver en sala (`state=live`, `programming=normal`, `is_upcoming` falso). No incluyas preventa, «pronto», ópera ni Cineco Alternativo, salvo que el usuario lo pida.

Ciudad por defecto: Bogotá (`bogota`). Si el usuario nombra otra ciudad, pásala al script.

## Pasos

1. Ejecuta el script que está junto a esta skill. Sin ciudad usa Bogotá; con ciudad, pásala como argumento:

```bash
python3 "actividad/.cursor/skills/pelis/scripts/cartelera.py"
python3 "actividad/.cursor/skills/pelis/scripts/cartelera.py" "Medellín"
```

Ejecútalo desde la raíz del workspace. Si no encuentra el archivo, usa la ruta absoluta de `scripts/cartelera.py` dentro de esta skill.

2. Lee la salida. Cada línea `PELICULA` trae título, marca (`Estreno` o `En cartelera`), detalles y enlace. No inventes títulos, fechas ni clasificaciones.
3. Responde en español con la lista completa, ordenada como viene el script (estreno más reciente primero).

## Formato de respuesta

```markdown
## Cartelera de Cine Colombia — {ciudad}

{total} películas en sala. Fuente: [Cine Colombia](https://www.cinecolombia.com/).

1. **{título}** — {Estreno o En cartelera}
   {fecha} · {duración} · {clasificación} · {géneros}
   [Ver película]({enlace})
```

Si el script imprime `VACIO` o un error, dilo tal cual y no completes la lista de memoria.
