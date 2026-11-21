# ==============================================================================
# MOD MANAGER FS25 — Makefile Centralizzato
# ==============================================================================

SHELL := /bin/bash
PORT  ?= 8025
URL   := http://127.0.0.1:$(PORT)

.DEFAULT_GOAL := help

.PHONY: help run start stop restart status scan scan-fast scan-force test backup logs docker-build docker-run docker-stop docker-logs

help: ## Mostra questa guida con tutti i comandi disponibili
	@echo ""
	@echo "🌾 MOD MANAGER FS25 — Pannello di Controllo"
	@echo "--------------------------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""

run: start ## Avvia il server e apre la dashboard nel browser
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open "$(URL)" >/dev/null 2>&1 & \
		echo "🌾 Dashboard aperta nel browser: $(URL)"; \
	else \
		echo "Apri questo indirizzo nel tuo browser: $(URL)"; \
	fi

start: ## Avvia il server in background sulla porta 8025 se non attivo
	@if curl -s "$(URL)/api/status" >/dev/null 2>&1; then \
		echo "✔ Server Mod Manager già attivo su $(URL)"; \
	else \
		if [ ! -f "data/mods.js" ]; then \
			echo "Scansione iniziale delle mod in corso..."; \
			./aggiorna.sh --fast; \
		fi; \
		mkdir -p data; \
		nohup python3 server.py $(PORT) > data/server.log 2>&1 & disown; \
		sleep 0.8; \
		if curl -s "$(URL)/api/status" >/dev/null 2>&1; then \
			echo "✔ Server Mod Manager avviato con successo su $(URL)"; \
		else \
			echo "❌ Errore nell'avvio del server. Controlla data/server.log"; \
			exit 1; \
		fi \
	fi

stop: ## Ferma il server Mod Manager
	@PID=$$(pgrep -f "python3 server.py $(PORT)" || true); \
	if [ -n "$$PID" ]; then \
		kill $$PID && echo "✔ Server fermato (PID $$PID)"; \
	else \
		echo "Nessun server attivo sulla porta $(PORT)"; \
	fi

restart: stop start ## Riavvia il server locale

status: ## Mostra lo stato del server, numero mod e stato del gioco FS25
	@echo "--------------------------------------------------------"
	@echo "Stato Mod Manager FS25"
	@echo "--------------------------------------------------------"
	@if curl -s "$(URL)/api/status" >/dev/null 2>&1; then \
		echo -e "Server Web:   \033[32mATTIVO\033[0m ($(URL))"; \
		curl -s "$(URL)/api/status" | python3 -c 'import sys, json; d=json.load(sys.stdin); print("Mod nel set: ", d.get("active_count", 0)); print("Archivio:   ", d.get("archive_count", 0), "mod")'; \
	else \
		echo -e "Server Web:   \033[31mSPENTO\033[0m (avvialo con: make run)"; \
	fi
	@if pgrep -f "FarmingSimulator2025Game.exe" >/dev/null 2>&1; then \
		echo -e "FS25 Gioco:   \033[33mIN ESECUZIONE\033[0m (modifiche bloccate per sicurezza)"; \
	else \
		echo -e "FS25 Gioco:   CHIUSO (modifiche consentite)"; \
	fi
	@if [ -d "/run/media/autcir/EROSBACKUP" ]; then \
		echo -e "EROSBACKUP:   \033[32mCOLLEGATO\033[0m (/run/media/autcir/EROSBACKUP)"; \
	else \
		echo -e "EROSBACKUP:   NON COLLEGATO"; \
	fi
	@echo "--------------------------------------------------------"

scan: ## Scansione completa delle mod (compreso ModHub ufficiale)
	./aggiorna.sh

scan-fast: ## Scansione veloce locale (solo modDesc e icone, no scraping)
	./aggiorna.sh --fast

scan-force: ## Scansione forzata (ignora la cache)
	./aggiorna.sh --force

test: ## Esegue l'intera suite di sicurezza e integrità (52 test)
	TMPDIR=/tmp python3 -m unittest test_sicurezza -v

backup: ## Copia di sicurezza sul disco EROSBACKUP (se montato)
	@if [ -d "/run/media/autcir/EROSBACKUP" ]; then \
		nice -n 19 ionice -c3 python3 backup_mods.py --dest /run/media/autcir/EROSBACKUP/fs25-mods; \
	else \
		echo "❌ Disco EROSBACKUP non montato in /run/media/autcir/EROSBACKUP"; \
		exit 1; \
	fi

logs: ## Segue i log del server in tempo reale
	@touch data/server.log
	tail -f data/server.log

docker-build: ## Costruisce l'immagine Docker locale del Mod Manager
	docker compose build

docker-run: ## Avvia il Mod Manager in background con Docker Compose
	docker compose up -d
	@echo "✔ Mod Manager attivo su http://127.0.0.1:$(PORT) via Docker"

docker-stop: ## Ferma il container Docker
	docker compose down
	@echo "✔ Container Mod Manager fermato"

docker-logs: ## Segue i log del container Docker
	docker compose logs -f
