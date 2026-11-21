# ==============================================================================
# Dockerfile per FS25 Mod Manager
# Immagine snella ed efficiente basata su Python 3.12 Alpine
# ==============================================================================
FROM python:3.12-alpine

WORKDIR /app

# Installa dipendenze minime di sistema per SQLite e utilità
RUN apk add --no-cache bash curl tzdata

# Copia codice dell'applicazione e asset
COPY server.py scan_mods.py curated.py enrich_modhub.py backup_mods.py index.html ./
COPY assets/ ./assets/
COPY icons/ ./icons/

# Crea directory dati persistenti e punti di mount
RUN mkdir -p /app/data /mods /backup_mods /scraper

# Esponi porta 8025
EXPOSE 8025

# Variabili d'ambiente predefinite
ENV PORT=8025 \
    FS25_MODS_DIR=/mods \
    FS25_ARCHIVE_DIR=/backup_mods \
    FS25_KINGMODS_DB=/scraper/kingmods_fs25.db \
    PYTHONUNBUFFERED=1

# Healthcheck di sicurezza
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD curl -f http://127.0.0.1:8025/api/status || exit 1

# Comando di avvio server
CMD ["python3", "server.py", "8025"]
