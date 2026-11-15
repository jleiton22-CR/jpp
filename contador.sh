#!/bin/zsh
# Cuántas veces se ha descargado cada instalador del sitio (los cuenta GitHub en cada Release).
#   ./contador.sh
# Solo usa curl y python3, que vienen con el Mac. No hace falta instalar nada ni iniciar sesión.
REPO="jleiton22-CR/jpp"
JSON=$(curl -fsS "https://api.github.com/repos/$REPO/releases?per_page=100") || { echo "No se pudo leer GitHub (¿sin internet?). No hay contador que mostrar."; exit 1; }
print -r -- "$JSON" | python3 -c '
import sys, json
try:
    releases = json.load(sys.stdin)
    assert isinstance(releases, list)
except Exception:
    sys.exit("GitHub no devolvió los datos esperados (puede haber un límite de consultas por hora). Inténtalo más tarde.")
print("%-14s %-26s %s" % ("Release", "Archivo", "Descargas"))
total = 0
for r in releases:
    for a in r["assets"]:
        print("%-14s %-26s %d" % (r["tag_name"], a["name"], a["download_count"]))
        total += a["download_count"]
print("\nTotal: %d descargas" % total)
'
