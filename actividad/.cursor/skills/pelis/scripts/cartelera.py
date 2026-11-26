#!/usr/bin/env python3
"""Lista las películas en cartelera de Cine Colombia, de la más reciente a la más antigua."""

import json
import subprocess
import sys
import unicodedata
import urllib.parse

API = "https://www.cinecolombia.com/api/v1/films"
SITES = "https://www.cinecolombia.com/api/v1/sites"
PAGE_URL = "https://www.cinecolombia.com/peliculas/{slug}"
MESES = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)

# Slugs que usa la API. El nombre visible se resuelve también contra /api/v1/sites.
CIUDADES = {
    "bogota": "bogota",
    "bogotá": "bogota",
    "medellin": "medellin",
    "medellín": "medellin",
    "cali": "cali",
    "bucaramanga": "bucaramanga",
    "cartagena": "cartagena",
    "barranquilla": "barranquilla",
    "monteria": "monteria",
    "montería": "monteria",
    "fusagasuga": "fusagasuga",
    "fusagasugá": "fusagasuga",
    "manizales": "manizales",
    "ibague": "ibague",
    "ibagué": "ibague",
    "armenia": "armenia",
    "popayan": "popayan",
    "popayán": "popayan",
    "pereira": "pereira",
    "villavicencio": "villavicencio",
    "chia": "bogota",
    "chía": "bogota",
    "soacha": "bogota",
}


def fold(text):
    normalized = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def fetch_json(url):
    result = subprocess.run(
        [
            "curl",
            "-fsS",
            "--max-time",
            "30",
            "-A",
            "Mozilla/5.0 (compatible; pelis-skill/1.0)",
            "-H",
            "Accept: application/json",
            url,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detalle = (result.stderr or result.stdout or "curl falló").strip()
        raise SystemExit(f"No pude consultar Cine Colombia: {detalle}")
    return json.loads(result.stdout)


def resolver_ciudad(argumento):
    if not argumento:
        return "bogota", "Bogotá"
    clave = fold(argumento)
    if clave in {fold(k): v for k, v in CIUDADES.items()}:
        slug = {fold(k): v for k, v in CIUDADES.items()}[clave]
        return slug, argumento.strip()
    data = fetch_json(SITES)
    vistos = {}
    for site in data.get("sites") or []:
        slug = site.get("city_slug")
        if not slug:
            continue
        vistos.setdefault(slug, site.get("municipality") or site.get("city") or slug)
        if fold(slug) == clave or fold(site.get("municipality") or "") == clave:
            return slug, site.get("municipality") or slug
    conocidos = ", ".join(sorted(vistos))
    raise SystemExit(
        f"No reconocí la ciudad '{argumento}'. Slugs disponibles: {conocidos}"
    )


def cargar_cartelera(slug):
    peliculas = []
    generos = {}
    pagina = 1
    total = None
    while total is None or len(peliculas) < total:
        query = urllib.parse.urlencode(
            {
                "city": slug,
                "state": "live",
                "programming": "normal",
                "per_page": 100,
                "page": pagina,
            }
        )
        data = fetch_json(f"{API}?{query}")
        for genero in (data.get("related_data") or {}).get("genres") or []:
            generos[genero.get("id")] = genero.get("name")
        lote = data.get("films") or []
        if not lote:
            break
        peliculas.extend(lote)
        total = (data.get("meta") or {}).get("total", len(peliculas))
        pagina += 1
        if pagina > 20:
            break
    return peliculas, generos


def en_sala(film):
    return film.get("is_upcoming") is False and film.get("content_type") == "cartelera"


def fecha_texto(iso):
    if not iso or len(iso) < 10:
        return "sin fecha"
    anio, mes, dia = iso[:10].split("-")
    return f"{int(dia)} {MESES[int(mes) - 1]} {anio}"


def duracion_texto(minutos):
    if not isinstance(minutos, int) or minutos <= 0:
        return ""
    horas, resto = divmod(minutos, 60)
    if horas and resto:
        return f"{horas}h {resto}m"
    if horas:
        return f"{horas}h"
    return f"{resto}m"


def formatear(film, generos):
    titulo = (film.get("title_es") or film.get("title") or "Sin título").strip()
    original = (film.get("title") or "").strip()
    if original and fold(original) != fold(titulo):
        titulo = f"{titulo} ({original})"
    clasificacion = ((film.get("censor_rating") or {}).get("classification") or "").strip()
    nombres = [
        generos[gid]
        for gid in film.get("genre_ids") or []
        if generos.get(gid)
    ]
    detalles = [
        fecha_texto(film.get("premiere_date") or film.get("release_date")),
        duracion_texto(film.get("duration_minutes")),
        clasificacion,
        ", ".join(nombres),
    ]
    detalles = [parte for parte in detalles if parte]
    marca = "Estreno" if film.get("is_estreno") else "En cartelera"
    slug = film.get("slug") or ""
    enlace = PAGE_URL.format(slug=urllib.parse.quote(slug)) if slug else "https://www.cinecolombia.com/"
    return titulo, marca, " · ".join(detalles), enlace


def main():
    argumento = " ".join(sys.argv[1:]).strip()
    slug, nombre = resolver_ciudad(argumento)
    peliculas, generos = cargar_cartelera(slug)

    en_cartelera = [film for film in peliculas if en_sala(film)]
    en_cartelera.sort(
        key=lambda film: film.get("premiere_date") or film.get("release_date") or "",
        reverse=True,
    )

    print(f"CIUDAD\t{nombre}\t{slug}")
    print(f"TOTAL\t{len(en_cartelera)}")
    print(f"FUENTE\thttps://www.cinecolombia.com/")
    if not en_cartelera:
        print("VACIO\tNo hay películas en cartelera para esta ciudad.")
        return
    for film in en_cartelera:
        titulo, marca, detalles, enlace = formatear(film, generos)
        print(f"PELICULA\t{titulo}\t{marca}\t{detalles}\t{enlace}")


if __name__ == "__main__":
    main()
