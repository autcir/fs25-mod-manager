#!/usr/bin/env bash
# Rigenera i dati della dashboard leggendo mods/ e BACKUP_MODS/.
# Non modifica, sposta o cancella alcuna mod.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Errore: python3 non trovato. Installalo e riprova." >&2
  exit 1
fi

ENRICH_ARGS=()
SECOND_ARGS=()
SCAN_ARGS=()
RUN_ENRICH=1
for arg in "$@"; do
  case "$arg" in
    --force)
      ENRICH_ARGS+=(--refresh)
      SCAN_ARGS+=(--force)
      ;;
    --no-icons)
      SECOND_ARGS+=(--no-icons)
      SCAN_ARGS+=(--no-icons)
      ;;
    --fast|--no-modhub)
      RUN_ENRICH=0
      ;;
    *)
      SCAN_ARGS+=("$arg")
      SECOND_ARGS+=("$arg")
      ;;
  esac
done

echo "Scansione delle mod in corso..."
python3 scan_mods.py --quiet "${SCAN_ARGS[@]}"

if [ -f data/mods.json ] && [ "$RUN_ENRICH" -eq 1 ]; then
  echo
  echo "Controllo dei dati ufficiali sul ModHub..."
  if ! python3 enrich_modhub.py "${ENRICH_ARGS[@]}"; then
    echo "Avviso: dati ModHub non aggiornati, la dashboard usa quelli già in cache." >&2
  fi
  echo
  echo "Aggiornamento della dashboard..."
  python3 scan_mods.py "${SECOND_ARGS[@]}"
else
  # Ristampa il riassunto a video se abbiamo saltato enrich
  python3 scan_mods.py "${SECOND_ARGS[@]}"
fi

echo
echo "Fatto. Apri la dashboard con: ./apri.sh"
