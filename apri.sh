#!/usr/bin/env bash
# Apre la dashboard nel browser predefinito collegata al server locale.
set -euo pipefail

cd "$(dirname "$0")"

PORT=8025
URL="http://127.0.0.1:${PORT}"

# Verifica che i dati siano presenti
if [ ! -f "data/mods.js" ]; then
  echo "Dati mancanti: eseguo prima la scansione..."
  ./aggiorna.sh --fast
fi

# Controlla se il server Python è già attivo sulla porta 8025
if ! curl -s "${URL}/api/status" >/dev/null 2>&1; then
  echo "Avvio server Mod Manager in background su ${URL}..."
  mkdir -p data
  nohup python3 server.py "${PORT}" >data/server.log 2>&1 &
  sleep 0.8
fi

# Apri nel browser
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 &
  echo "🌾 Mod Manager aperto: ${URL}"
else
  echo "Apri questo indirizzo nel tuo browser:"
  echo "  ${URL}"
fi
