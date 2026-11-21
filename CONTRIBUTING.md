# Guida per i Contributori — AgroDeck FS25

Ti ringraziamo per l'interesse a contribuire ad **AgroDeck FS25**!

## 🛡️ Regola d'Oro: Sicurezza e Integrità Assoluta

AgroDeck è progettato per gestire le mod senza mai rischiare la perdita di file fisici o la corruzione dei salvataggi. Qualsiasi modifica al codice deve rispettare queste linee guida:

1. **Mai cancellare file veri nell'archivio**: le operazioni di rimozione o disattivazione devono manipolare esclusivamente i collegamenti simbolici (*symlink*).
2. **Validazione Percorsi**: ogni operazione su filesystem deve rifiutare tentativi di directory traversal (`../`).
3. **Protezione dei Salvataggi**: le modifiche ai savegame devono sempre passare per la verifica dello stato del gioco (blocco se il gioco è aperto) e chiedere conferma in caso di slot occupati.
4. **52 Test di Sicurezza**: prima di inviare una PR, esegui:
   ```bash
   make test
   ```
   Tutti i 52 test devono terminare con esito positivo (`OK`).

## 🛠️ Flusso di Sviluppo Locale

1. Forka il repository e crea un branch dedicato:
   ```bash
   git checkout -b feature/nuova-funzionalita
   ```
2. Avvia la dashboard locale:
   ```bash
   make run
   ```
3. Effettua le modifiche rispettando la coerenza visiva dark e i principi di accessibilità (cifre tabulari per i numeri, contrasto WCAG, assenza di gradienti casuali o slop).
4. Verifica la sintassi JS e Python:
   ```bash
   node -c assets/app.js
   python3 -m py_compile server.py scan_mods.py backup_mods.py
   ```
5. Esegui la suite di test:
   ```bash
   make test
   ```
