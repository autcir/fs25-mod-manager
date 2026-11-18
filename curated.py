# -*- coding: utf-8 -*-
"""
Knowledge base italiana per MOD MANAGER FS25.
Ogni scheda viene agganciata alla mod tramite la chiave del nome file
(es. FS25_Courseplay.zip -> "courseplay").

Campi:
  short   -> una frase: cosa fa
  details -> spiegazione pratica
  tier    -> S/A/B/C/D/E/F/G/H (importanza, dalla classifica in DOCS/)
  role    -> etichetta funzionale
  tip     -> consiglio d'uso
"""


def c(short, details="", tier="", role="", tip=""):
    return {"short": short, "details": details, "tier": tier, "role": role, "tip": tip}


CURATED = {
    # ------------------------------------------------------------------ S
    "universalautoload": c(
        "Carica e fissa automaticamente bancali, balle e casse sul rimorchio.",
        "Aggiunge l'autoload ai rimorchi del gioco e a quelli compatibili: apri il menu del veicolo, scegli il tipo di carico e premi il tasto di caricamento. È la mod che elimina il carrello elevatore manuale.",
        "S", "Logistica",
        "Attivala sempre: è la regina delle quality-of-life. Controlla il tasto assegnato nelle impostazioni.",
    ),
    "courseplay": c(
        "L'operaio AI che genera percorsi, svolte e lavorazioni per i campi.",
        "Calcola le capezzagne, evita gli ostacoli, gestisce più mezzi sullo stesso campo, raccolta e scarico. Si integra con AutoDrive per la logistica.",
        "S", "Automazione",
        "Per iniziare usa un campo semplice e la modalità 'Field Work'; impara prima le basi, poi passa a più veicoli.",
    ),
    "gpsplus": c(
        "Guida assistita GPS con linee AB, sterzata automatica e svolte a fine campo.",
        "Mostra le linee guida a terra, mantiene la corsia, regola la larghezza dell'attrezzo e registra le curve. Si comanda con Alt+W.",
        "S", "Guida",
        "Attivala appena inizi a guidare: righe dritte = meno passaggi e meno carburante.",
    ),
    "togglesuperstrength": c(
        "Super forza attivabile con un tasto: sollevi trattori e attrezzi pesanti.",
        "Permette di raddrizzare mezzi capovolti, spostare oggetti e recuperare situazioni bloccate. Funziona anche in multiplayer, con attivazione individuale.",
        "S", "Qualità della vita",
        "Tienila sempre attiva: è l'assicurazione contro i mezzi ribaltati nei fossi.",
    ),
    "lumberjack": c(
        "Migliora la motosega: abbatte alberi, distrugge ceppi e regola velocità e portata.",
        "Aggiunge super forza, taglio ovunque, rimozione ceppi e un menu impostazioni. Mantiene comunque il guadagno dalla vendita del legno.",
        "S", "Forestale",
        "Usa 'cut anywhere' solo quando serve: è comodissima ma poco realistica.",
    ),
    "storedeliveries": c(
        "Fa consegnare gli acquisti del negozio direttamente in fattoria.",
        "Imposta il punto di consegna dove ti trovi e paga una piccola percentuale sul prezzo. Evita i viaggi al concessionario per mezzi e materiali.",
        "S", "Logistica",
        "Prima di comprare un mezzo grande, posizionati dove vuoi che arrivi.",
    ),
    "additionalfieldinfo": c(
        "Mostra ettari, resa potenziale e stato del campo quando ci cammini sopra.",
        "Estende il pannello informazioni con area del campo, area del terreno, prezzo per ettaro e dati agronomici utili prima di comprare o seminare.",
        "S", "Informazioni",
        "Guardalo prima di acquistare un campo: il prezzo per ettaro racconta molto.",
    ),
    "easydevcontrols": c(
        "Menu di sviluppo (F11): soldi, meteo, teletrasporto e strumenti di test.",
        "Pensato per modder e mapper, ma comodissimo per sbloccare bug, cambiare ora/neve e fare prove senza rovinare la carriera.",
        "S", "Utility",
        "Usalo con moderazione: i soldi facili tolgono il gusto della progressione.",
    ),
    "powertools": c(
        "Menu rapido (F12) per rifornire mezzi, volare e usare comandi di qualità della vita.",
        "Riempie diesel, semi e concime, attiva il volo libero e altre scorciatoie. Pensato per test e content creator.",
        "S", "Utility",
        "Ottimo per testare attrezzi nuovi senza perdere mezz'ora di viaggi.",
    ),
    "asm_cannabisdlcpack": c(
        "La filiera cannabis completa: coltivazione, serre, lavorazione e prodotti.",
        "Pacchetto FS22 riportato su FS25 con nuovi fill type, serre di crescita, essiccazione, rifinitura, estrazione e negozi. Include veicoli e attrezzature dedicate.",
        "S", "Produzione",
        "È il cuore del progetto cannabis su Flat Map: seguila con la guida DOCS/03.",
    ),

    # ------------------------------------------------------------------ A
    "autodrive": c(
        "Rete di percorsi per far guidare i veicoli da soli tra campi, silos e vendita.",
        "Configuri una volta le strade e i punti di interesse; poi i mezzi viaggiano in autonomia. Si sposa con Courseplay per la logistica completa.",
        "A", "Automazione",
        "Configura prima i punti di scarico e vendita, poi lascia che Courseplay gestisca il campo.",
    ),
    "precisionfarming": c(
        "Agronomia avanzata: campioni di suolo, azoto variabile, sensori e resa.",
        "Precision Farming 3.0 aggiunge analisi del terreno, mappe di prescrizione, sostenibilità e dati di resa. È un potenziatore realistico, non una scorciatoia.",
        "A", "Agronomia",
        "Attivala dopo aver capito il gioco base: introduce molte più variabili da gestire.",
    ),
    "hirepurchasing": c(
        "Acquisto di macchinari a rate con acconto e piano mensile.",
        "Permette di avviare l'azienda con mezzi costosi senza pagare tutto subito. Scegli acconto, durata e rata; il finanziamento pesa sul bilancio.",
        "A", "Economia",
        "Leggi bene la rata mensile: un mezzo grande può strozzare i primi raccolti.",
    ),
    "followme": c(
        "Crea convogli: un veicolo segue un altro in fila.",
        "Il mezzo che segue mantiene distanza e direzione. Perfetto per portare più rimorchi o accompagnare la mietitrebbia.",
        "A", "Logistica",
        "Solo singleplayer/PC: non usarla su server multiplayer.",
    ),
    "courseplayplayerunload": c(
        "Add-on di Courseplay: gli scaricatori AI raggiungono la mietitrebbia guidata da te.",
        "I trattoristi di Courseplay si avvicinano, seguono e scaricano automaticamente mietitrebbie e trince guidate dal giocatore.",
        "A", "Automazione",
        "Attivala insieme a Courseplay; imposta bene il punto di scarico del rimorchio.",
    ),
    "fieldcreatorplus": c(
        "Crea, unisce ed espande campi dal menu costruzione.",
        "Disegni il contorno, confermi e il gioco crea il campo. Puoi collegare più appezzamenti o allargarne uno esistente senza ore di aratura.",
        "A", "Costruzione",
        "Usa Shift+P per aprire il menu; salva prima di modifiche grosse ai confini.",
    ),
    "simpleinspector": c(
        "HUD con lo stato di tutti i veicoli: lavoro, carburante, riempimento.",
        "Mostra una panoramica compatta dei mezzi senza aprire la mappa: chi sta lavorando, quanto carburante resta e cosa trasportano.",
        "A", "Informazioni",
        "Tienilo aperto durante i lavori grossi per capire subito chi è fermo.",
    ),
    "smalltenderpack": c(
        "Carretti e cisterne compatti per rifornire semi e concime a bordo campo.",
        "Include ST2031, rimorchio fertilizzante e cisterna: pensati per essere trainati da pickup o trattori piccoli, riducono i viaggi al silos.",
        "A", "Logistica",
        "Ottimo con fattorie piccole: non serve un trattorone per ogni rifornimento.",
    ),
    "greenhouseautomaticwatering": c(
        "Riempie automaticamente d'acqua le serre.",
        "Aggiunge l'opzione 'Irrigazione Automatica' nel menu di produzione della serra: una volta attiva, l'acqua viene fornita da sola senza riempimenti manuali.",
        "B", "Acqua",
        "Attivala su tutte le serre: elimina una delle micromanager più noiose del gioco.",
    ),
    "automaticwater_animals_greenhouses": c(
        "Pompa che rifornisce automaticamente stalle e serre vicine.",
        "Piazzi la pompa vicino a una stalla o serra e collega le utenze: l'acqua non si esaurisce più. Sono inclusi due modelli.",
        "A", "Acqua",
        "Piazzala prima di riempire le stalle: spostarla dopo è scomodo.",
    ),
    "waterpump": c(
        "Pompa a vento che distribuisce acqua alle produzioni.",
        "Genera e distribuisce acqua; il costo dipende dalla distanza. Ha una modalità 'Distributing' per collegare più utenze.",
        "A", "Acqua",
        "Abbinala alla pompa automatica per stalle/serre e togliersi il pensiero.",
    ),
    "waterfree": c(
        "Serbatoio d'acqua gratuito e infinito per la fattoria.",
        "Piazzabile economico (500 $) che produce acqua senza costi giornalieri. Comodissimo per avviare produzioni e abbeveratoi.",
        "A", "Acqua",
        "Mettici accanto un punto di carico: riempirai cisterne in pochi secondi.",
    ),
    "moveplaceablesadvanced": c(
        "Sposta e ruota gli oggetti già piazzati, senza demolire.",
        "Permette di traslare su X/Y/Z e ruotare sui tre assi. Corregge errori di posizionamento di capannoni, serre e decorazioni.",
        "A", "Costruzione",
        "Salva prima di spostare edifici grandi: se il terreno non regge, puoi tornare indietro.",
    ),
    "bunkersilopack": c(
        "Pacchetto di bunker silos per insilato di mais e erba.",
        "Include silos di dimensioni diverse e la copertura. È il metodo più redditizio per conservare foraggio e trasformarlo in silage.",
        "A", "Stoccaggio",
        "Compatta bene il trinciato e copri: l'insilato di qualità vale molto di più.",
    ),
    "smallconcretebunkersilo": c(
        "Bunker silo in cemento compatto, ideale per iniziare.",
        "Circa 300.000 litri di capacità per bunker: poco spazio, costo contenuto. Perfetto nelle prime partite.",
        "A", "Stoccaggio",
        "Costruiscilo vicino all'area animali per ridurre i viaggi.",
    ),
    "bunkersilolarge18x90m": c(
        "Bunker silo gigante 18×90 m per produzioni di insilato su larga scala.",
        "Enorme capacità, pensato per aziende grandi e molti capi di bestiame. Richiede spazio e mezzi adeguati per compattare.",
        "A", "Stoccaggio",
        "Non serve nelle prime ore: occupa molto terreno e va riempito in fretta.",
    ),
    "silosfs": c(
        "Pacchetto di silos multiprodotto compatibili crossplay.",
        "Silos con colori configurabili, auger e blower nascondibili, pensati per stoccare mais, grano e altri prodotti.",
        "A", "Stoccaggio",
        "Controlla la compatibilità crossplay se giochi con amici su console.",
    ),
    "smallfarmproduction": c(
        "Piccole produzioni da fattoria per trasformare le colture in prodotti finiti.",
        "Due edifici compatti con ricette per dare valore aggiunto al raccolto, senza costruire un impero industriale.",
        "A", "Produzione",
        "Guarda le ricette prima di seminare: produci ciò che l'edificio richiede.",
    ),
    "greenhousetree": c(
        "Serra grande e vivaio: ortaggi, fiori, bamboo, aloe e alberelli.",
        "Include un punto vendita e più serre con produzioni continue che richiedono soprattutto acqua. Ottima per reddito costante.",
        "A", "Produzione",
        "Abbinala a un serbatoio d'acqua gratuito: la produzione non si ferma mai.",
    ),
    "windmill": c(
        "Mulino che produce farina, zucchero e oli da mais, grano e colture.",
        "Due piazzabili: mulino (50.000 $) e generatore (30.000 $, reddito passivo). Trasforma cereali e barbabietole in prodotti più remunerativi.",
        "A", "Produzione",
        "Il generatore è un piccolo reddito passivo: utile nei periodi di magra.",
    ),

    # ------------------------------------------------------------------ B
    "roadbuilder": c(
        "Costruisci strade asfaltate o sterrate direttamente in gioco.",
        "Disegni il percorso e il gioco crea la strada. Perfetto per collegare capannoni, campi e punti vendita (Alt+R).",
        "B", "Costruzione",
        "Progetta prima la viabilità: rifare le strade dopo è più costoso.",
    ),
    "roadkit": c(
        "Pezzi pre-fabbricati per strade, parcheggi e piazzali.",
        "Alternativa rapida al Road Builder: piazzi moduli già pronti e li combini. Ogni pezzo costa circa 10 €.",
        "B", "Costruzione",
        "Ottimo per piccoli piazzali; per strade lunghe Road Builder è più comodo.",
    ),
    "perfectedge": c(
        "Blocca un asse durante pittura e terraforming per bordi perfettamente dritti.",
        "Tieni premuto Shift mentre disegni: il tratto resta allineato a X o Z. Ideale per campi, vialetti e piazzali.",
        "B", "Costruzione",
        "Usalo insieme a PlaceTerraformPaintAnywhere per rifiniture precise.",
    ),
    "freeterraformingandpainting": c(
        "Terraforming e pittura del terreno gratuiti.",
        "Rimuove il costo di scavo, riempimento e pittura. Utile per costruire la fattoria dei sogni senza bruciare il capitale.",
        "B", "Costruzione",
        "Salva spesso: con i lavori gratuiti è facile esagerare e deformare la mappa.",
    ),
    "placeterraformpaintanywhere": c(
        "Piazza edifici e modella il terreno in qualsiasi punto della mappa.",
        "Elimina i vincoli di costruzione: puoi costruire ovunque, anche fuori dalle aree acquistabili, e terraformare senza limiti.",
        "B", "Costruzione",
        "Perfetta per il progetto cannabis su Flat Map, ma tienila disattivata se vuoi realismo.",
    ),
    "unlimitedcolorconfigurations": c(
        "Sblocca tutti i colori per ogni configurazione in officina.",
        "Permette di scegliere qualsiasi colore su mezzi e attrezzi, non solo quelli previsti dalla mod. Pura personalizzazione estetica.",
        "B", "Personalizzazione",
        "Ottima per rendere uniforme la flotta aziendale.",
    ),
    "infodisplayextension": c(
        "Estende le barre informative a schermo con più dati.",
        "Aggiunge indicatori e dettagli alle informazioni già mostrate dal gioco. Utile per chi vuole tutto sotto controllo.",
        "B", "Informazioni",
        "Se il (HUD) diventa troppo pieno, disattivala: è solo informativa.",
    ),

    # ------------------------------------------------------------------ C
    "johndeereseries7810": c(
        "Trattore John Deere 7810 da 175 CV, versatile e potente.",
        "Prezzo 68.000 $, velocità 40 km/h. Tira attrezzi pesanti e resta maneggevole nei campi medi.",
        "C", "Trattore",
        "Buon primo trattore 'grande' se hai campi sopra i 5 ettari.",
    ),
    "johndeeret560pack": c(
        "Mietitrebbia John Deere T560 con barra e carrello.",
        "387 CV, serbatoio 10.000 L, 285.000 $. È l'evoluzione naturale della TX32 per aziende in crescita.",
        "C", "Mietitrebbia",
        "Prendila quando i campi superano ciò che la TX32 riesce a gestire.",
    ),
    "newhollandtx32": c(
        "Mietitrebbia economica e agile per i primi campi.",
        "55.000 $, 155 CV, serbatoio 5.600 L. Include barra e carrello per il trasporto.",
        "C", "Mietitrebbia",
        "La scelta intelligente per i primi 2-3 campi: costa poco e si muove bene.",
    ),
    "johndeereplanter1775nt": c(
        "Seminatrice John Deere 1775NT a 12 file, larga 17,75 m.",
        "234.500 $, richiede 360 CV. Semina veloce su grandi superfici, con tramoggia da 3.524 L.",
        "C", "Semina",
        "Serve un trattore molto potente: non comprarla prima del mezzo adatto.",
    ),
    "grimmeks5400": c(
        "Preparatore Grimme KS 5400 per patate e colture da radice.",
        "Larghezza 6 m, richiede 107 CV, 23.000 $. Prepara il letto di semina per patate.",
        "C", "Colture speciali",
        "Utile solo se coltivi patate o rape: altrimenti resta in archivio.",
    ),
    "degelmanprotill": c(
        "Coltivatore verticale pesante Degelman Pro-Till 40 ft.",
        "Lavora il terreno in modo aggressivo, interrando residui e preparando il letto di semina. Richiede trattori robusti.",
        "C", "Lavorazione suolo",
        "Non usarlo su terreni già perfetti: consuma molto e serve potenza.",
    ),
    "poettingersynkro3030": c(
        "Coltivatore portato Pöttinger SYNKRO 3030 NOVA da 3 m.",
        "Leggero e compatto, adatto a piccole e medie aziende. Lavora bene su terreni sciolti.",
        "C", "Lavorazione suolo",
        "Buon compromesso tra larghezza e potenza richiesta.",
    ),
    "namysloopti": c(
        "Coltivatore leggero Namyslo Opti 560H per lavorazione superficiale.",
        "Progettato per lavorare a bassa profondità senza seppellire troppo i residui. Ideale per preparazioni rapide.",
        "C", "Lavorazione suolo",
        "Usalo dopo la raccolta per rimescolare la paglia senza arare.",
    ),
    "rauspiram_3m": c(
        "Erpice RAU SPIRAM 3 m, leggero e trainabile da trattori piccoli.",
        "2.500 $, 90 CV, velocità 13 km/h. Prepara il terreno in modo semplice ed economico.",
        "C", "Lavorazione suolo",
        "Perfetto per iniziare: costa poco e quasi tutti i trattori lo tirano.",
    ),
    "claasdiscopack": c(
        "Pacchetto falciatrici CLAAS DISCO per erba e foraggio.",
        "Include più modelli con larghezze diverse. Uno dei tre pacchetti falci dell'archivio: scegli la marca che preferisci.",
        "C", "Fienagione",
        "Non attivare insieme agli altri pacchetti falci: sono sovrapposti.",
    ),
    "poettingermowerpack": c(
        "Pöttinger Novacat A10 Cross Flow + 301 AM ED Pro.",
        "Falciatrice e andanatore di alta qualità, con larghezze da 3 m. Pensato per fienagione professionale.",
        "C", "Fienagione",
        "Scegli questo oppure il Claas/Kuhn: tenerli tutti non serve.",
    ),
    "fd_kuhn_mower_pack": c(
        "Pacchetto falciatrici Kuhn con versioni John Deere e suoni reali.",
        "Tre modelli, larghezze diverse e suoni registrati dal vero. È il terzo pacchetto falci dell'archivio.",
        "C", "Fienagione",
        "Se tieni questo, archivia gli altri due per risparmiare spazio e confusione.",
    ),
    "fiatseries180_90jt": c(
        "Fiatagri Serie 90 JT: trattore storico robusto e affidabile.",
        "Trattore vintage con buona potenza e configurazioni. Adatto a chi ama il parco macchine italiano.",
        "C", "Trattore",
        "Abbinalo alle zavorre Fiat per lavorare in sicurezza con attrezzi pesanti.",
    ),
    "fiat_480": c(
        "Fiat 480 del 1973, trattorino vintage economico (48 CV).",
        "Prezzo 6.900 $, 48 CV, 23 km/h. Piccolo, affidabile e perfetto per lavori leggeri.",
        "C", "Trattore",
        "Ottimo per iniziare o per le piccole produzioni vicino casa.",
    ),
    "mf11": c(
        "Spandiletame Massey Ferguson 11 degli anni '70.",
        "4.800 $, capacità 500 L, larghezza 42 m. Configurazioni di colore per corpo e telo.",
        "C", "Letame",
        "Utile solo se hai animali: senza letame resta un attrezzo decorativo.",
    ),
    "lizard_t25": c(
        "Trattore Lizard T-25 leggero e low-cost (30 CV).",
        "12.500 $, 26 km/h, molte configurazioni. Ideale per piccoli campi e lavori di cortile.",
        "C", "Trattore",
        "Buon secondo trattore per attrezzi leggeri, non per arature pesanti.",
    ),
    "lizardlh_10": c(
        "Lizard LH 10: aratro portato per piccoli trattori.",
        "Attrezzo a tre punti per rivoltare il terreno. Lavoro lento ma efficace su appezzamenti piccoli.",
        "C", "Lavorazione suolo",
        "Usalo se parti con un trattore sotto i 100 CV.",
    ),
    "lizardkastrnka": c(
        "Trattorino vintage Lizard Kastrnka, semplice e compatto.",
        "Mod leggero con poche pretese, pensato per piccole aziende e collezionisti. Ottimo per girare la fattoria.",
        "C", "Trattore",
        "Non aspettarti prestazioni da campo grande: è un mezzo da cortile.",
    ),
    "lizardhs400": c(
        "Irroratrice trainata Lizard HS-400 per piccoli agricoltori.",
        "Vecchio progetto economico, capace di trattare piccole superfici. Si riempie facilmente.",
        "C", "Irrigazione",
        "Controlla la capacità: per campi grandi dovrai fare più viaggi.",
    ),
    "johnderre45": c(
        "Mietitrebbia John Deere 45 d'epoca, più da collezione che da lavoro.",
        "20.500 $, 50 CV, serbatoio 1.800 L. Molto lenta e con poca capacità.",
        "C", "Mietitrebbia",
        "Prendila per il gusto del vintage, non per l'efficienza.",
    ),
    "lizard_z609": c(
        "Mietitrebbia trainata vintage Lizard Z-609 per patate.",
        "Due file, scava e dispone le patate in un mucchio largo 0,8 m. Adatta a terreni leggeri.",
        "C", "Raccolta",
        "Uso molto limitato: serve solo se coltivi patate e vuoi il gusto retrò.",
    ),
    "flatbed_trailer": c(
        "Pianale semplice e indispensabile per pallet, balle e tronchi.",
        "15.500 $, configurazioni di colore per telaio, cerchi e gomme. Carica di tutto e si aggancia facilmente.",
        "C", "Rimorchio",
        "Con Universal Autoload diventa uno dei mezzi più utili dell'azienda.",
    ),
    "utilitrailer": c(
        "Rimorchi Lizard Utili 1, 2 e 3 per trasportare attrezzature.",
        "Tre modelli con dimensioni diverse, pensati per la logistica quotidiana in fattoria.",
        "C", "Rimorchio",
        "Tienine uno per ogni trattore: riduci i tempi morti.",
    ),
    "lizarddragontrailerkit": c(
        "Kit rimorchio Lizard Dragon TK 35/76, configurabile.",
        "Si aggancia a veicoli con attacco basso o auto. Utile per trasporti leggeri e versatili.",
        "C", "Rimorchio",
        "Controlla l'attacco del trattore prima dell'acquisto.",
    ),
    "trailer_carretinha_br": c(
        "Carretinha brasiliana artigianale in legno e acciaio.",
        "Rimorchietto semplice e rustico per piccoli trasporti. Costa poco e si adatta a qualsiasi fattoria.",
        "C", "Rimorchio",
        "Perfetta per le prime partite o per un look vintage.",
    ),
    "two_wheel_trailer": c(
        "Rimorchio a due ruote da 2.000 L, anche per animali.",
        "1.000-1.500 $, capacità 2.000 L; può trasportare 1 mucca, 4 maiali o 2 pecore. Molto maneggevole.",
        "C", "Rimorchio",
        "Buon jolly per piccoli spostamenti di bestiame.",
    ),
    "doubleweightfiat": c(
        "Zavorre per i Fiat, da 600 a 1.220 kg.",
        "Evita impennate e migliora la trazione con attrezzi pesanti. Prezzi da 600 a 1.220 $.",
        "C", "Zavorra",
        "Obbligatorie se usi aratri o attrezzi pesanti con i Fiat vintage.",
    ),
    "smalltoolspackdf": c(
        "Piccolo pacchetto di attrezzi da suolo, tra cui aratro SALEK.",
        "Aratro PN 2-300 da 0,5 m e altri utensili economici per piccoli trattori.",
        "C", "Lavorazione suolo",
        "Buon set di partenza per appezzamenti minuscoli.",
    ),
    "handbalingtools": c(
        "Ballerina manuale e forcone per fare balle con pochi soldi.",
        "Lizard Hand Baler 2000: piccola, economica e manuale. Perfetta per fattorie ruspanti o sfide a budget zero.",
        "C", "Fienagione",
        "Lenta ma soddisfacente: usala nelle prime ore o per roleplay.",
    ),
    "handpushabletoolspack": c(
        "38 attrezzi manuali per tutte le fasi, dalla preparazione alla raccolta.",
        "Carriole, attrezzi spingibili, aratri e accessori a mano. Copre i lavori di piccolissima scala.",
        "C", "Strumenti",
        "Divertente per una fattoria a misura d'uomo, poco efficiente su larga scala.",
    ),
    "homemade_manurespreader": c(
        "Spandiletame artigianale economico per piccole stalle.",
        "4.500 $, 25 CV, larghezza 2,5 m. Semplicissimo ma funzionale.",
        "C", "Letame",
        "Abbinalo a un piccolo allevamento: costa meno di un modello industriale.",
    ),
    "manureevacuator": c(
        "Aspirapore letame con ricetta di produzione del letame.",
        "8.000 $, manutenzione 25 $/mese. Trasforma il letame in un prodotto gestibile.",
        "C", "Letame",
        "Utile solo con stalle piene: altrimenti è un costo fisso.",
    ),
    "old_manure_heap": c(
        "Letamaio old-style da 1.500.000 L.",
        "10.000 $, manutenzione 10 $/giorno, configurazione sinistra/destra. Deposito enorme per letame.",
        "C", "Letame",
        "Costruiscilo lontano dalle case: è grande e non profuma.",
    ),
    "forestryhelper": c(
        "Informazioni su tronchi, lunghezze e peso per il taglio forestale.",
        "Mostra dati utili durante il taglio e aiuta a ottenere pezzi della misura desiderata. Pensato per chi lavora il bosco.",
        "C", "Forestale",
        "Utile se vendi legno; trascurabile se non tagli alberi.",
    ),

    # ------------------------------------------------------------------ D
    "average_wooden_shelter": c(
        "Capannone in legno medio, con varianti muro in cemento, legno o mattoni.",
        "Pacchetto di 3 tettoie medie per coprire mezzi e attrezzi. Funzionale e bellissimo da vedere.",
        "D", "Costruzione",
        "Piazzalo vicino all'officina per avere i mezzi al coperto.",
    ),
    "smallwoodenshed": c(
        "Piccola tettoia in legno per riporre macchinari.",
        "Economica e compatta, ideale per i primi attrezzi o per un angolo del cortile.",
        "D", "Costruzione",
        "Perfetta nelle prime partite quando lo spazio è poco.",
    ),
    "smallrusticbaleshed": c(
        "Capanno rustico autocostruito per balle di fieno.",
        "Estetica da vecchia fattoria, pensato per proteggere le balle dalla pioggia.",
        "D", "Costruzione",
        "Abbinalo a un campo di fieno per un angolo molto naturale.",
    ),
    "shed_vologne": c(
        "Capanno Vologne: 22.000 $, manutenzione 8 $/mese.",
        "Edificio piazzabile di medie dimensioni, adatto a mezzi e attrezzature.",
        "D", "Costruzione",
        "Buon rapporto qualità/prezzo se ti serve spazio coperto.",
    ),
    "old_structure_pack": c(
        "Pacchetto di vecchie strutture e tettoie rurali.",
        "Tre edifici dal sapore antico per decorare la fattoria e coprire piccoli attrezzi.",
        "D", "Decorazione",
        "Usali per creare un borgo agricolo attorno alla casa.",
    ),

    # ------------------------------------------------------------------ E
    "raisinproductionpack": c(
        "Filiera dell'uva: succo, uva da tavola e uvetta.",
        "Aggiunge linee di produzione legate alla viticoltura, con nuovi prodotti e semi. Serve se coltivi uva.",
        "E", "Produzione",
        "Attivala solo se hai vigneti: altrimenti occupa slot mod senza utilità.",
    ),
    "olives": c(
        "Olivi andalusi e raccoglitore a ombrello per la filiera dell'olio.",
        "Alberi grandi e attrezzo specifico: l'uso corretto dell'idraulica aumenta la produzione. Richiede oliveti.",
        "E", "Produzione",
        "Abbinala a una produzione di olio per chiudere la filiera.",
    ),

    # ------------------------------------------------------------------ F (mappe)
    "monteriggioni": c(
        "Mappa italiana in Toscana: colline, cipressi e campagna autentica.",
        "Ambientazione curatissima, ottima per una carriera classica. È la mappa consigliata per iniziare.",
        "F", "Mappa",
        "Copiala in mods/ e attivala nella schermata MOD del salvataggio.",
    ),
    "newfrontier": c(
        "Mappa americana con campi larghi e strade ampie.",
        "Paesaggio aperto, mercato agricolo e segheria; le altre produzioni le costruisci tu. Partenza senza stress.",
        "F", "Mappa",
        "Ideale se vuoi usare trattori grandi e fare tanti ettari.",
    ),
    "calmsden": c(
        "Oak Bridge Farm: mappa inglese con siepi e strade strette.",
        "Un piccolo capolavoro paesaggistico, ma difficile da percorrere con mezzi grandi. Richiede pazienza.",
        "F", "Mappa",
        "Perfetta per un gameplay lento e curato; sconsigliata ai principianti.",
    ),
    "papenburger_map_v2_4k": c(
        "Mappa tedesca in 4K, dettagliatissima ma pesante.",
        "Texture ad alta risoluzione e grande attenzione ai dettagli. Richiede un PC potente.",
        "F", "Mappa",
        "Se il gioco scatta, abbassa la qualità o scegli una mappa meno pesante.",
    ),
    "abandonedtaiga_4x": c(
        "Mappa russa 4× in taiga: enorme, selvaggia e impegnativa.",
        "Ambientazione unica e spazi sterminati, ma è pesantissima. Pensata per esperti e PC di fascia alta.",
        "F", "Mappa",
        "Evitala nelle prime partite: rischia di trasformare il gioco in una passeggiata infinita.",
    ),
    "flat_map": c(
        "Mappa piatta vuota: la base perfetta per costruire da zero.",
        "Non è una mappa di gioco tradizionale: serve per testare mod, costruzioni e il progetto cannabis. Include configurazioni base.",
        "F", "Mappa",
        "Usala con Road Builder e PlaceTerraformPaintAnywhere per la fattoria dei sogni.",
    ),
    "homestead": c(
        "Mappa stile 'No Man's Land': bosco, acqua sotto tutta la mappa e 67 appezzamenti.",
        "Partenza rustica con allevamento, vendita e una fattoria preesistente. Tanto spazio per costruire.",
        "F", "Mappa",
        "Ottima se ti piace partire da zero e sviluppare la fattoria.",
    ),
    "farmlands": c(
        "Mappa con pianure sterminate e campi enormi.",
        "Pensata per mezzi grandi e lavorazioni su larga scala. Include sistema ferroviario.",
        "F", "Mappa",
        "Serve un PC robusto e molta pazienza per i primi investimenti.",
    ),
    "panhandle_caprock": c(
        "Mappa del Texas panhandle, tra altopiani e terre aperte.",
        "Paesaggio americano con il Canadian River, campi larghi e vedute infinite. Adatta a grandi aziende.",
        "F", "Mappa",
        "Preparati a lunghe distanze tra campi e punti vendita.",
    ),
    "ronidaisland4x": c(
        "Isola 4× tra agricoltura e silvicoltura.",
        "Mappa grande con storia introduttiva, spazi per allevamento e boschi. Richiede tempo e un buon PC.",
        "F", "Mappa",
        "Parti con obiettivi piccoli: la mappa è enorme.",
    ),
    "lonehills": c(
        "Mappa ispirata a No Man's Land con fattoria iniziale e campo pronto.",
        "Puoi partire con poco e ampliare tutto: campi, boschi e costruzioni. Versione sistemata con modDesc in radice.",
        "F", "Mappa",
        "Copiala dall'archivio solo quando vuoi giocarla: pesa circa 197 MB.",
    ),

    # ------------------------------------------------------------------ G
    "th_defaulttypes": c(
        "Carica i tipi di prodotto di default dalla mappa [TH] TerraLife.",
        "Mod di compatibilità: serve solo con mappe TerraLife. Con le mappe normali non fa praticamente nulla.",
        "G", "Compatibilità",
        "Tienila archiviata: non aggiunge nulla alle tue mappe attuali.",
    ),
    "johndeere_330_lawntractor": c(
        "Rasaerba John Deere 330: divertente per l'ordine intorno casa.",
        "Piccolo trattorino da prato, capace di piccoli lavori con attrezzi leggeri. Zero produzioni.",
        "G", "Veicolo",
        "Attivala solo per roleplay o per tenere ordinati i prati.",
    ),
    "bunkersilolarge18x90m_feld_grassilage": c(
        "Variante 'grassilage da campo' del bunker 18×90 m.",
        "È un doppione del bunker grande: cambia solo la destinazione d'uso dell'erba. Non serve tenerli entrambi.",
        "G", "Stoccaggio",
        "Scegli questo oppure il bunker standard, non tutti e due.",
    ),

    # ------------------------------------------------------------------ nuovi attivi
    "afs_z211": c(
        "Andanatore/voltafieno Agromet Z-211/2 per erba, erba medica e trifoglio.",
        "Ideale per girare il fieno e formare andane regolari prima della pressa. Larghezza di lavoro contenuta.",
        "C", "Fienagione",
        "Usalo dopo la falciatura, quando l'erba è asciutta al punto giusto.",
    ),
    "axe": c(
        "Ascia economica che abbatte alberi, più lenta della motosega.",
        "Costa 50 $ e taglia tronchi fino a 1,1 m di diametro. Perfetta per iniziare senza motosega.",
        "C", "Strumenti",
        "Ottima nelle prime ore, poi passa alla motosega per fare sul serio.",
    ),
    "chickencoopeuropean": c(
        "Pollaio europeo moderno con allevamento di galline.",
        "85.000 $, manutenzione 40 $/mese. Include tre oggetti: pollaio, letame e distributore.",
        "B", "Animali",
        "Abbinalo a un piccolo orto: le galline danno uova e letame.",
    ),
    "dryer": c(
        "Fermentatore per paglia e essiccatore per fieno, erba e insilato.",
        "Può essere piazzato in mezzo al campo senza deformare il terreno. Conserva i prodotti deperibili e li trasforma.",
        "B", "Produzione",
        "Piazzalo vicino al silos per ridurre i viaggi durante la raccolta.",
    ),
    "foragepickup": c(
        "Raccoglitore LIZARD FP-2M che carica materiale dal terreno nel rimorchio.",
        "Nato per svuotare i silos a trincea, raccoglie anche erba, insilato e altri materiali. Larghezza di lavoro maggiorata.",
        "B", "Raccolta",
        "Utile per pulire i bordi dei silos senza pala meccanica.",
    ),
    "guettlermatador610s": c(
        "Erpice a dischi Güttler Matador 610S da 6 m.",
        "15.000 $, richiede 80 CV. Lavorazione superficiale veloce per preparare il letto di semina.",
        "C", "Lavorazione suolo",
        "Buon compromesso tra larghezza e potenza: adatto a trattori medi.",
    ),
    "harrows_pack": c(
        "Pacchetto di erpici da 3-5 m per preparazione del terreno.",
        "Prezzi 550-800 $, richiede 22-31 CV, velocità 15 km/h. Leggerissimi e adatti ai trattori piccoli.",
        "C", "Lavorazione suolo",
        "Perfetti per iniziare: costano poco e non richiedono potenza.",
    ),
    "husqvarna_ts146xk": c(
        "Rasaerba Husqvarna TS146XK per prati e piccoli lavori.",
        "Taglio preciso, sedile comodo e sterzo ergonomico. Non è un mezzo agricolo: serve per l'ordine intorno casa.",
        "D", "Veicolo",
        "Usalo se tieni molto all'estetica della fattoria.",
    ),
    "increasedworkareasforpickups": c(
        "Aumenta l'area di lavoro dei raccoglitori per prendere meglio le andane.",
        "Soprattutto in curva, i pickup raccolgono più materiale senza lasciare strisce. Piccola mod, grande differenza.",
        "B", "Raccolta",
        "Attivala insieme a forage pickup e presse per ridurre i residui a terra.",
    ),
    "internationalih_70": c(
        "Trattorino International IH 70 con attrezzi da giardino.",
        "Include trattore, falciatrice e coltivatore. Pensato per piccoli lavori, orti e giardinaggio.",
        "C", "Trattore",
        "Set completo per una mini-fattoria: costa poco ed è divertente.",
    ),
    "johndeere2410": c(
        "Aratro John Deere 2410 per lavorazioni profonde.",
        "Aratro reversibile robusto, pensato per campi medio-grandi e terreni difficili. Richiede potenza.",
        "C", "Lavorazione suolo",
        "Non usarlo su tutti i campi: l'aratura profonda costa e compatta il terreno.",
    ),
    "landstal_pack": c(
        "Pacchetto di 11 macchine LandStal: rulli, disc harrow, coltivatori e weeders.",
        "Copre quasi tutta la preparazione del letto di semina. Ottimo rapporto qualità/prezzo per aziende medie.",
        "C", "Lavorazione suolo",
        "Con 11 attrezzi hai solo l'imbarazzo della scelta: prendi quelli adatti ai tuoi ettari.",
    ),
    "lemken_juwel8_pack": c(
        "Aratro reversibile Lemken Juwel 8 per campi medio-grandi.",
        "Struttura robusta e lavorazione precisa su diversi tipi di terreno. Disponibile in più larghezze.",
        "C", "Lavorazione suolo",
        "Serve un trattore pesante: controlla la potenza prima di comprarlo.",
    ),
    "lippfermentingsilo": c(
        "Silos a torre Lipp per insilato, stile anni '70.",
        "Costruzione in acciaio con tecnologia a doppia cucitura. Ideale per stoccare foraggio fermentato in verticale.",
        "B", "Stoccaggio",
        "Piazzalo vicino alla stalla: il trasporto verticale è comodo ma serve spazio in altezza.",
    ),
    "lizard_duplex_627": c(
        "Falciatrice laterale Lizard DupleX 627 per erba e foraggio.",
        "Falcia a destra, adatta a trattori con sollevatore idraulico. Larghezza contenuta per piccoli appezzamenti.",
        "C", "Fienagione",
        "Buona per bordi e campi stretti; per grandi superfici meglio una falciatrice più larga.",
    ),
    "lizardhls15m": c(
        "Spandiconcime Lizard HLS 15M da 400 L, larghezza 15 m.",
        "Distribuisce concime o semi. Economico e semplice, ideale per piccole superfici.",
        "C", "Semina",
        "Non aspettarti precisione industriale: va benissimo per iniziare.",
    ),
    "mobileworkshop": c(
        "Configura i veicoli ovunque, senza officina.",
        "Vai vicino al mezzo e premi N: si apre la finestra officina standard. Cambi colore, gomme e configurazioni.",
        "B", "Utility",
        "Comodissimo quando sei lontano dalla fattoria: evita viaggi inutili.",
    ),
    "objectbalestorage": c(
        "Deposito per balle ai bordi del campo o in cortile.",
        "Tre capacità (150, 350, 800 balle) con modello 3D dedicato. Protegge le balle e libera spazio.",
        "C", "Stoccaggio",
        "Mettilo vicino al campo dove pressi: riduci i viaggi.",
    ),
    "oldlogshedspack": c(
        "Vecchie tettoie in legno per mezzi e attrezzature.",
        "Sei piazzabili tra fienili e capannoni, con estetica vissuta. Perfette per un look rustico.",
        "D", "Costruzione",
        "Usale per coprire i mezzi senza spendere troppo.",
    ),
    "oldsheepfold": c(
        "Ovile per 250 pecore e capre, con fienile e acqua manuale.",
        "Include illuminazione e un soppalco per le balle. Adatto a un allevamento medio-grande.",
        "C", "Animali",
        "Controlla la capacità del tuo allevamento prima di comprarlo.",
    ),
    "oldwoodenwagon": c(
        "Carro in legno multifunzione, categoria rimorchi.",
        "Vecchio stile ma capiente e versatile per piccoli trasporti in fattoria.",
        "C", "Rimorchio",
        "Perfetto per un'ambientazione vintage.",
    ),
    "placeablewalllights": c(
        "22 lampade da parete per decorare case e capannoni.",
        "Lampadine, LED, neon e lanterne a gas. Si trovano nella categoria Decorazioni.",
        "D", "Decorazione",
        "Usale per illuminare i vialetti e rendere la fattoria viva di sera.",
    ),
    "production_points_pack": c(
        "Riporta su FS25 le fabbriche di produzione di FS22.",
        "Panetteria, caseificio, mulino, spinnery e altro: punti di produzione pronti da piazzare e collegare alla filiera.",
        "B", "Produzione",
        "Controlla le ricette e i punti vendita prima di costruire la filiera.",
    ),
    "rauunisemms_pack": c(
        "Seminatrici Rau Unisem MS4 e MS6 per mais e colture a file.",
        "Interfila 75 cm, velocità 12 km/h, possibilità di concimare durante la semina. Due larghezze.",
        "C", "Semina",
        "Perfette per il mais: l'interfila stretta richiede appezzamenti ben preparati.",
    ),
    "scythe": c(
        "Falce a mano per tagliare erba e piccoli campi.",
        "30 $, lenta e faticosa ma autentica. Si usa per giardinaggio e roleplay.",
        "G", "Strumenti",
        "Divertente per una fattoria tradizionale, inutile su larga scala.",
    ),
    "seeds_addon": c(
        "Aggiunge varietà di semi specifiche per ogni coltura.",
        "I semi si usano solo con le seminatrici del pacchetto o con quelle compatibili. Aggiunge profondità alla scelta delle colture.",
        "B", "Semina",
        "Controlla la compatibilità delle tue seminatrici prima di attivarla.",
    ),
    "selleverything": c(
        "Tre punti vendita che accettano praticamente tutto.",
        "Vendi colture, balle, tronchi, prodotti, animali, semi e concime. Il primo è una stazione semplice, gli altri due sono più completi.",
        "B", "Economia",
        "Ottimo per smaltire scorte accumulate e chiudere filiere senza cercare il compratore giusto.",
    ),
    "shovelhand": c(
        "Pala a mano per spostare materiali, con capacità 200 o 800 L.",
        "26 $, si usa per piccoli lavori e per caricare materiale sfuso. Leggera e sempre disponibile.",
        "C", "Strumenti",
        "Utile nelle prime ore o per piccoli spostamenti in cortile.",
    ),
    "smallhouse": c(
        "Piccola casa colonica con luci, letto e armadio.",
        "10.000 $, manutenzione 50 $/giorno. Include trigger per dormire e cambiare abito.",
        "D", "Costruzione",
        "Perfetta per iniziare la fattoria con un tocco personale.",
    ),
    "smallproduction": c(
        "Mini produzione con composter, legna da ardere e deposito legna.",
        "Cinque oggetti: compostiera, sacchi di substrato, falegnameria, legna e liquame. Trasforma scarti in prodotti utili.",
        "B", "Produzione",
        "Ottima per smaltire letame e residui senza grandi investimenti.",
    ),
    "specialoffers": c(
        "Controlla le offerte del concessionario e ti avvisa delle nuove occasioni.",
        "Monitora regolarmente gli sconti su veicoli e attrezzi. Ti permette di comprare a meno senza controllare ogni giorno.",
        "B", "Economia",
        "Attivala se compri spesso usato: le offerte buone spariscono in fretta.",
    ),
    "waterfree": c(
        "Serbatoio d'acqua gratuito e infinito.",
        "500 $, manutenzione zero, produzione di acqua continua. Perfetto per serre, stalle e produzioni.",
        "A", "Acqua",
        "Piazzalo al centro della fattoria e collega le utenze vicine.",
    ),
    "wheelbarrow": c(
        "Carriole per trasportare materiali sfusi e oggetti.",
        "Due modelli (200 $ e 150 $) con capacità diverse. Piccole, leggere e sempre utili in cortile.",
        "C", "Strumenti",
        "Ottime per i primi lavori manuali, poi diventano decorative.",
    ),
    "wood_autoload": c(
        "Due rimorchi legno con autoload per tronchi e alberi.",
        "Caricano e scaricano automaticamente il legno, anche su pallet. Include due depositi per lo stoccaggio.",
        "B", "Forestale",
        "Abbinala a LumberJack: dalla motosega alla vendita senza movimenti manuali.",
    ),
    "z034_osa": c(
        "Falciatrice laterale Lizard Z034 'Osa 2' per erba e foraggio.",
        "Si monta su trattori con sollevatore idraulico. Leggera e adatta a piccoli appezzamenti.",
        "C", "Fienagione",
        "Buona per bordi e campi stretti, non per grandi superfici.",
    ),
}
