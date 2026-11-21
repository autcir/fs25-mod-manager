# PRODUCT.md — Mod Manager FS25

## A cosa serve
Strumento locale di Ciro (canale AutCir) per Farming Simulator 25 su Linux/Proton:

1. **Inventario delle mod**: tutte le mod in `mods/`, `BACKUP_MODS/` e `mods-bck/`, con scheda in
   italiano, dati ModHub, doppioni e criticità. Solo lettura.
2. **Mod attive nel gioco**: link simbolici nella cartella mod del gioco per la serie scelta.
3. **Partita nuova**: crea `careerSavegame.xml`, `farms.xml` ed `environment.xml` nel profilo Wine del
   gioco, sulla mappa scelta tra quelle dell'archivio, con soldi, prestito e regole scelte; poi può
   avviare `run.sh` e OBS.
4. **Rimetti i link di prima**: torna a un elenco di mod attive salvato in `data/link_salvati/`.
5. **Ricerca KingMods**: cerca nel database SQLite locale (`scraper/kingmods_fs25.db`).

## Piattaforma
- Server Python 3 della libreria standard (`server.py`), solo `127.0.0.1:8025`.
- JavaScript, CSS e HTML senza librerie esterne né CDN.

## Vincoli che non si toccano
- Mai cancellare file veri: mod, salvataggi, backup, csv. Si tolgono solo link simbolici; un salvataggio
  esistente si sposta in `BACKUP_SAVEGAMES/` dopo conferma esplicita (vedi README, «Sicurezza»).
- Mai scrivere nell'archivio `mods/`.
- Nessuna dipendenza nuova senza il sì di Ciro.
- Interfaccia in italiano semplice, testi leggibili, nessuna promessa che il codice non mantiene.
