# 🌾 FS25 Mod Manager & Discovery Hub

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Tests](https://img.shields.io/badge/security%20tests-52%2F52%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()
[![FS25](https://img.shields.io/badge/Farming%20Simulator-25-green.svg)]()

Un gestionale locale moderno, veloce e sicuro per le mod di **Farming Simulator 25**, con **hub di scoperta collegato a oltre 22.000 mod indicizzate**, console di gestione attiva a due colonne e architettura non distruttiva a collegamenti simbolici (*symlinks*).

---

## ⚡ Caratteristiche Principali

### 1. 🎛️ Console di Gestione a Due Colonne
* **Colonna Sinistra (Nel Gioco)**: visualizza esattamente le mod attive nel tuo set corrente di FS25.
* **Colonna Destra (Archivio / Riserva)**: catalogo completo delle tue mod salvate e collezionate nel tempo.
* **Azioni Rapide a 1-Click**: sposta le mod tra gioco e archivio con un click (`+ Aggiungi` / `✕ Rimuovi`), senza mai rischiare di cancellare file fisici.
* **Barra di Sincronizzazione Sticky**: anteprima delle modifiche e applicazione immediata con ripristino automatico dello stato precedente in caso di errore.

### 2. 🔍 Hub di Ricerca & Scoperta KingMods (22.645 Mod)
* **Catalogo Locale Indicizzato**: ricerca istantanea (1 ms) tra oltre 22.000 mod FS25 con statistiche reali di download e valutazioni community.
* **Cross-Check con il tuo Archivio**:
  * <span style="color:#4ade80;">**🟢 Nel Gioco**</span>: mod già presente e attiva nel set di gioco.
  * <span style="color:#38bdf8;">**✓ In Archivio**</span>: mod presente nel tuo archivio locale.
  * <span style="color:#a6b8a4;">**⭐ Nuova**</span>: mod non ancora presente, scaricabile con link diretto alla scheda ufficiale.
* **Preset Tematici Rapidi**:
  * 🇮🇹 *Made in Italy & Mediterraneo*: Fiat, Fiatagri, Laverda, Same, Landini, Antonio Carraro, Alpego e mappe storiche (*Etruria*, *Polesine*).
  * ⚙️ *Script & Realismo Indispensabili*: Universal Autoload, Courseplay, AutoDrive, TerraFarm, fisica avanzata e suolo.
  * 🏆 *Top Download di Sempre*: le mod più scaricate dalla community globale.
  * 🚜 *Trattori Iconici*: compatti, medi e grandi mezzi da lavoro.
  * 🏭 *Produzioni & Fabbriche*: serre, capannoni, cantine e magazzini automatici.
  * 🗺️ *Mappe Europee*: scenari collinari e campagne aperte.
* **102 Categorie FS25 Reali**: filtro dropdown con conteggio in tempo reale per ogni categoria.

### 3. 🛡️ Sicurezza Assoluta (Zero Perdita Dati)
* **52 Test di Integrità Automatizzati** (`make test`).
* Non cancella mai file ZIP veri: lavora esclusivamente con collegamenti simbolici.
* Blocco automatico di qualsiasi operazione mentre il gioco FS25 è aperto.
* Controllo copie esatte, rilevamento conflitti di versione e sanitizzazione nomi file.
* Backup con versioning incrementale: le mod aggiornate non sovrascrivono quelle vecchie ma creano copie storiche (`.vecchio-<data>`).

### 4. 🚀 Career & Game Architect
* Crea nuove partite da zero scegliendo mappa, capitale iniziale, debito, difficoltà economica (EASY / NORMAL / HARD) e giorni per mese.
* Protegge i salvataggi esistenti segnalando gli slot occupati e chiedendo conferma esplicita per evitare sovrascritture accidentali.

---

## 🚀 Avvio Rapido

### Metodo 1: Makefile (Consigliato su Linux)

```bash
# Avvia il server locale e apre automaticamente la dashboard
make run
```

Visualizza lo stato e i comandi disponibili:
```bash
make help
make status
```

### Metodo 2: Script Diretto

```bash
./apri.sh
```
La dashboard si aprirà automaticamente nel tuo browser su `http://127.0.0.1:8025`.

### Metodo 3: Docker (Universale su Windows / Linux / macOS)

Se preferisci eseguire il Mod Manager in un container isolato senza installare dipendenze sul sistema:

```bash
# Avvia il container in background
docker compose up -d

# Oppure tramite Makefile
make docker-run
```

Per fermarlo:
```bash
docker compose down
# oppure
make docker-stop
```

---

## ⚙️ Configurazione dei Percorsi

Il Mod Manager rileva automaticamente i percorsi standard di FS25 su Linux (Wine/Proton/Steam) e su Windows.

Se utilizzi percorsi personalizzati, puoi configurarli in due modi:

### Opzione A: File `data/config.json`
Copia il file di esempio e personalizza le directory:
```bash
cp data/config.example.json data/config.json
```
```json
{
  "active_game_dir": "/percorso/alle/tue/mod",
  "wine_game_root": "/percorso/ai/tuoi/salvataggi/FarmingSimulator2025",
  "game_launcher": "/percorso/al/tuo/run.sh",
  "archive_dir": "/percorso/al/tuo/archivio/mods",
  "kingmods_db": "/percorso/a/kingmods_fs25.db",
  "backup_disco": "/percorso/al/disco/di/backup"
}
```

### Opzione B: Variabili d'Ambiente
```bash
export FS25_MODS_DIR="/percorso/alle/tue/mod"
export FS25_ARCHIVE_DIR="/percorso/all/archivio"
export FS25_KINGMODS_DB="/percorso/a/kingmods_fs25.db"
make run
```

---

## 🧪 Test di Sicurezza & Qualità

Per verificare l'integrità del sistema e accertarsi che nessuna operazione tocchi file non autorizzati:

```bash
make test
```
Esegue i 52 test unitari che convalidano:
* Protezione dell'archivio e divieto di cancellazione file fisici.
* Rifiuto di percorsi traversali (`../`) e sanitizzazione input.
* Convalida transazioni di salvataggio e protezione slot occupati.
* Policy di sicurezza su formati esterni e link salvati.

---

## 📦 Struttura del Progetto

```text
MOD_MANAGER/
├── assets/
│   ├── app.js             # Logica applicativa, reattività e routing viste
│   └── style.css          # Design system dark ad alto contrasto (Impeccable / No AI Slop)
├── data/
│   ├── config.example.json# Template di configurazione percorsi
│   ├── mods.js            # Cache metadati mod scansionate
│   └── profili.json       # Abbinamenti salvataggi e set di mod
├── Dockerfile             # Immagine Docker leggera basata su Python 3.12 Alpine
├── docker-compose.yml     # Configurazione Docker Compose con volumi montati
├── Makefile               # Pannello di controllo centralizzato con comandi rapidi
├── server.py              # Server locale con API REST sicure e query SQLite
├── scan_mods.py           # Scanner modDesc.xml e generatore manifest
└── test_sicurezza.py      # Suite di 52 test automatizzati
```

---

## 📄 Licenza

Rilasciato sotto licenza [MIT](LICENSE). Libero per la community di Farming Simulator 25.
