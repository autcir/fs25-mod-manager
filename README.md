# fs25-mod-manager

A local mod manager for **Farming Simulator 25 on Linux (Proton)**. A small Python server plus a web page that runs
only on your PC (`127.0.0.1`).

[English](#english) · [Italiano](#italiano)

> The interface is in Italian. The code is plain Python 3 (standard library only) and plain HTML/JS, no external
> libraries, no CDN, no telemetry.

---

## English

### What it does

- **Mod inventory**: reads every `.zip` in your mod library, takes title, version, author, shop category, price,
  power, working width and dependencies from `modDesc.xml`, and shows them in a searchable dashboard.
- **Duplicates and problems**: byte-identical copies (SHA-256), the same mod in several folders, version conflicts,
  broken zips, missing `modDesc.xml`.
- **ModHub data** (optional, needs internet): rating, votes, release date and official page of each mod.
- **Activate mods in the game**: puts **symbolic links** to the chosen mods in the folder the game reads.
- **Mods of a savegame**: reads `careerSavegame.xml`, tells you which mods that savegame uses, which are missing
  (with a link to the ModHub page) and links the ones you have.
- **New savegame**: writes `careerSavegame.xml`, `farms.xml` and `environment.xml` in the game profile, on a map
  found in your library.
- **Backup** (optional): copies your mod files to a backup drive with `backup_mods.py`.

### Safety: what it never does

Written after a real loss of 96 mods caused by an older version, and covered by `test_sicurezza.py` (52 tests, all
in temporary folders).

- It **never deletes real files**. In the game mod folder it only adds or removes symbolic links. Real `.zip`
  files that are not selected stay there and the dashboard lists them.
- Before removing links it saves their list in `data/link_salvati/`; **"Rimetti i link di prima"** puts them back.
- It **stops** if the game mod folder and the library are the same folder (or one is inside the other).
- It **never deletes a savegame**: if the slot is used it asks you to type the slot number, then **moves** the old
  savegame into `BACKUP_SAVEGAMES/` next to it.
- The backup copies only; a changed file keeps the old copy as `<name>.vecchio-<date>`.
- The server listens only on `127.0.0.1` and refuses requests from other hosts and other websites.
- Only plain `.zip` file names are accepted (no folders, no `..`).
- Close the game before activating mods ("mods of a savegame" refuses to run while the game is open).

### Platform

- **Tested** on Arch Linux with FS25 running under Proton (umu-launcher), Python 3.14.
- **Default paths** for Steam + Proton (native Steam, Flatpak Steam, Steam Deck desktop mode) are included but
  **not tested yet** on those setups: check them with `python3 config.py` and set the variables below if needed.
- Windows is not supported (it uses symbolic links and `pgrep`).

### Install

```bash
git clone https://github.com/autcir/fs25-mod-manager.git
cd fs25-mod-manager
python3 config.py      # shows the paths it will use
```

Requirements: Python 3.10+, a browser. Optional: ImageMagick (`magick` or `convert`) to turn DDS icons into PNG.

### Configuration

Every path comes from an environment variable or from `~/.config/fs25-mod-manager/config.json`
(same key names; environment variables win).

| Variable | What it is | Default |
| --- | --- | --- |
| `FS25_PROFILE_DIR` | game profile `.../My Games/FarmingSimulator2025` | first existing one under `~/.local/share/Steam`, `~/.steam/steam`, Flatpak Steam (`compatdata/2300320`) |
| `FS25_GAME_MODS_DIR` | folder the game reads mods from | `$FS25_PROFILE_DIR/mods` |
| `FS25_LIBRARY_DIR` | your library: `mods/` (archive), optional `BACKUP_MODS/` and `mods-bck/` | `$XDG_DATA_HOME/fs25-mod-manager/library` |
| `FS25_LAUNCHER` | optional script that starts the game | not set: no launch button |
| `FS25_BACKUP_DIR` | optional backup drive or folder | not set: backup off |
| `FS25_KINGMODS_DB` | optional local SQLite database for the search tab (not included) | `$FS25_LIBRARY_DIR/scraper/kingmods_fs25.db` |
| `FS25_NICKNAME` | player name in a new savegame | `Player` |
| `FS25_FARM_NAME` | farm name in a new savegame | `My Farm` |

Example `~/.config/fs25-mod-manager/config.json`:

```json
{
  "FS25_LIBRARY_DIR": "~/fs25-library",
  "FS25_BACKUP_DIR": "/run/media/me/BACKUP"
}
```

The archive (`$FS25_LIBRARY_DIR/mods`) **must be a different folder** from the game mod folder: the game folder gets
links that point into the archive.

**Mod sets (optional).** If `FS25_LAUNCHER` points to a shell script with lines like `SET_MOD="mods"` and
`name) SET_MOD="mods-other" ;;`, each of those folders (next to the script) becomes a "set" you can pick for a
savegame, and the launch button runs `script name`. Without a launcher there is one set: the game mod folder.

### Use

```bash
./aggiorna.sh          # scan the library (add --fast to skip ModHub, --force for a full rescan)
./apri.sh              # start the local server on 127.0.0.1:8025 and open the dashboard
```

Run the safety tests (they only use temporary folders):

```bash
TMPDIR=/some/folder/on/disk python3 -m unittest test_sicurezza -v
```

### What stays on your PC

Scans, caches, icons, saved link lists and logs are written in `data/` and `icons/` inside this folder (ignored by
git). Nothing is sent anywhere except the ModHub lookups (`enrich_modhub.py`) and the optional mod download, which
go to `farming-simulator.com` / the GIANTS CDN.

### License

MIT, see `LICENSE`. Farming Simulator and ModHub belong to GIANTS Software; this project is not affiliated with them
and does not contain or distribute any mod.

---

## Italiano

### Cosa fa

- **Inventario delle mod**: legge ogni `.zip` della tua libreria, prende da `modDesc.xml` titolo, versione, autore,
  categoria, prezzo, potenza, larghezza di lavoro e dipendenze, e li mostra in una pagina con ricerca e filtri.
- **Doppioni e problemi**: copie identiche (SHA-256), stessa mod in più cartelle, versioni in conflitto, zip rotti,
  `modDesc.xml` mancante.
- **Dati ModHub** (facoltativo, serve internet): voto, numero di voti, data e pagina ufficiale di ogni mod.
- **Attiva le mod nel gioco**: mette **link simbolici** alle mod scelte nella cartella che il gioco legge.
- **Mod di un salvataggio**: legge `careerSavegame.xml`, dice quali mod usa quel salvataggio, quali mancano (con il
  link alla pagina ModHub) e collega quelle che hai.
- **Partita nuova**: scrive `careerSavegame.xml`, `farms.xml` ed `environment.xml` nel profilo del gioco, su una
  mappa trovata nella tua libreria.
- **Copia di sicurezza** (facoltativa): copia i file delle mod su un disco di backup con `backup_mods.py`.

### Sicurezza: cosa non fa mai

Regole scritte dopo una perdita vera di 96 mod causata da una versione vecchia, e provate da `test_sicurezza.py`
(52 test, tutti in cartelle temporanee).

- **Non cancella mai file veri.** Nella cartella mod del gioco aggiunge o toglie solo link simbolici. I `.zip` veri
  non scelti restano lì e la pagina te li elenca.
- Prima di togliere i link ne salva l'elenco in `data/link_salvati/`; **«Rimetti i link di prima»** li rimette.
- **Si ferma** se la cartella mod del gioco e la libreria sono la stessa cartella (o una sta dentro l'altra).
- **Non cancella mai un salvataggio**: se lo slot è usato chiede di scrivere il numero dello slot, poi **sposta** il
  salvataggio vecchio in `BACKUP_SAVEGAMES/` accanto.
- La copia di sicurezza copia e basta; un file cambiato tiene la copia vecchia come `<nome>.vecchio-<data>`.
- Il server ascolta solo su `127.0.0.1` e rifiuta richieste da altri host e da altri siti.
- Accetta solo nomi di file `.zip` semplici (niente cartelle, niente `..`).
- Chiudi il gioco prima di attivare le mod («mod di un salvataggio» con il gioco aperto rifiuta).

### Piattaforma

- **Provato** su Arch Linux con FS25 sotto Proton (umu-launcher), Python 3.14.
- I **percorsi predefiniti** per Steam + Proton (Steam normale, Steam Flatpak, Steam Deck in modalità desktop) ci
  sono ma **non sono ancora stati provati** su quelle installazioni: controllali con `python3 config.py` e, se serve,
  imposta le variabili della tabella sopra.
- Windows non è supportato (usa link simbolici e `pgrep`).

### Installazione e uso

```bash
git clone https://github.com/autcir/fs25-mod-manager.git
cd fs25-mod-manager
python3 config.py      # mostra i percorsi che userà
./aggiorna.sh          # scansiona la libreria (--fast senza ModHub, --force da capo)
./apri.sh              # avvia il server su 127.0.0.1:8025 e apre la pagina
```

Serve Python 3.10 o più recente e un browser. Facoltativo: ImageMagick per le icone DDS.

La configurazione (variabili `FS25_*` o `~/.config/fs25-mod-manager/config.json`) è spiegata nella tabella della
parte inglese. L'archivio (`$FS25_LIBRARY_DIR/mods`) **deve essere una cartella diversa** da quella mod del gioco.

### Cosa resta sul tuo PC

Scansioni, cache, icone, elenchi dei link e log stanno in `data/` e `icons/` dentro questa cartella (fuori da git).
Niente viene inviato altrove, tranne le ricerche sul ModHub (`enrich_modhub.py`) e lo scaricamento facoltativo di
una mod, che vanno su `farming-simulator.com` e sul CDN di GIANTS.

### Licenza

MIT, vedi `LICENSE`. Farming Simulator e ModHub sono di GIANTS Software; questo progetto non è collegato a loro e non
contiene né distribuisce mod.
