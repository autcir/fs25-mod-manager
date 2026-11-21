# Politica di Sicurezza — AgroDeck FS25

## 🔒 Principi di Isolamento e Garanzie

AgroDeck FS25 adotta una politica rigorosa per garantire che l'esecuzione del manager non possa in nessun caso danneggiare l'installazione del gioco o causare perdita di file:

- **Operazioni Atomiche sui File**: i salvataggi e i file di configurazione sono scritti in modo atomico.
- **Divieto di Cancellazione Ricorsiva**: il server locale non possiede funzioni di cancellazione ricorsiva sul disco.
- **Isolamento dell'Archivio Mod**: l'archivio delle mod (`mods/`) e le cartelle di backup sono trattati in sola lettura durante le normali sessioni di gioco.
- **Controllo Concorrenza**: ogni richiesta di scrittura o attivazione verifica preventivamente che il processo di Farming Simulator 25 non sia in esecuzione (`pgrep FarmingSimulator2025Game.exe`).

## 🚨 Segnalazione Vulnerabilità

Se riscontri un potenziale rischio per la sicurezza o un comportamento inatteso sui file:
- Apri un'issue contrassegnata come security, oppure contatta direttamente i maintainer del progetto.
- Risponderemo entro 24 ore con un fix prioritario.
