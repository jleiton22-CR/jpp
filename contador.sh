#!/bin/zsh
# Cuántas veces se ha descargado cada instalador del sitio (los cuenta GitHub en cada Release).
#   ./contador.sh
set -e
REPO="jleiton22-CR/jpp"
gh api "repos/$REPO/releases" --paginate --jq '.[] | .tag_name as $t | .assets[] | [$t, .name, .download_count] | @tsv' \
| awk -F'\t' 'BEGIN{printf "%-14s %-26s %s\n","Release","Archivo","Descargas"} {printf "%-14s %-26s %d\n",$1,$2,$3; total+=$3} END{printf "\nTotal: %d descargas\n", total}'
