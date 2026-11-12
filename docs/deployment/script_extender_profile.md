# Profilo facoltativo TGC con Script Extender

`core+extender` prepara i contenuti della [PR #417](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/417)
che dipendono da Script Extender. Il profilo è destinato a **Victoria II 3.04
Windows x86** in una seconda installazione, fuori da `steamapps`. Il Task 55
verifica contenuti e deployment staticamente e su installazioni simulate.
Il [rapporto del Task 56](script_extender_task56.md) documenta le prove in partita
su Victoria II 3.04. Il [Task 57](script_extender_task57.md) ricostruisce i
controlli del plugin e definisce la sessione per le prove residue.

## Composizione e caricamento

Il tool di deployment usa il catalogo dedicato `components_extender.json` per
assemblare una sola coppia `mod/TGCScriptExtender` e `mod/TGCScriptExtender.mod`.
La base usa gli stessi file tracciati ed esclusioni di `core`. L'overlay aggiunge
cinque file e ne sostituisce sei. L'override di `map/default.map` fa puntare
Victoria II al `definition.csv` della coppia installata in
`mod/TGCScriptExtender`. `extender_overlay.json` elenca i percorsi ammessi
e gli SHA-256 dei sei originali, calcolati normalizzando CRLF a LF.
Aggiornare consapevolmente ciascun override e il relativo hash se cambia la
base. Il piano e lo staging verificano i byte effettivi da pubblicare. Il
manifest delle sorgenti è distinto dal catalogo delle transazioni, così una
revisione degli override consente ancora il rollback di un deployment precedente.

Il descrittore riprende i `replace_path` di TGC e usa `user_dir = "TGCScriptExtender"`
per salvataggi e dati utente separati. La selezione prevista è il solo
**TGC - Script Extender**. Il Loader legge le direttive `load` dai descrittori
passati con `-mod=`. L'Extender cerca `cb_types.txt`, `buildings_ai.txt`,
`se_partitions.txt` e `ai_interests.txt` nel primo percorso di mod che
fornisce ciascun file. Con un solo descrittore TGC, il lettore del plugin e
quello del gioco ricevono gli stessi contenuti senza fare affidamento sulla
precedenza fra descrittori. L'Extender legge i propri CB di trattato, l'interfaccia,
le risorse grafiche e le localizzazioni dalla cartella ufficiale del plugin.
Il plugin genera `common/se_cb_types.generated.txt` nella propria cartella
unendo i CB del mod e i suoi CB. La cartella deve quindi essere scrivibile.
Verificare al primo avvio il percorso registrato per i CB, i file ausiliari e
l'effettiva separazione di salvataggi e cache.
[Selezione dei plugin](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/launcher/README.md) ·
[Ricerca dei file](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/game/localisation.cpp) ·
[Integrazione dei CB](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty_ui.cpp)

## Dipendenze e contenuti

Usare l'asset ufficiale `TGL.+.Vic2.Perfomance.Patch.+.SE.3.0.0.zip` della
release 3.0.0, associata a `e911c9537a32495469c94c078613981a85f62acc`.
Il digest pubblicato da GitHub è
`e5ca3b29c9d17870ca2235eacc9ca1759251467827c39e82ece1045d3c59dfba` (SHA-256).
Confrontarlo con l'asset effettivo prima di un test autorizzato. Il sorgente
del bundle dichiara Script Extender 0.1.0 e Performance Patch 1.0.0. Il tag
consultato non fornisce una licenza di ridistribuzione per le DLL. Il repository
e il tool consegnano solo contenuti TGC. Il bootstrapper `dinput8.dll` e
l'intera cartella esterna `mod/script_extender` sono prerequisiti per l'avvio
dedicato. La direttiva del profilo carica già il plugin.
[Release ufficiale](https://github.com/The-Grand-Combination/The-Grand-Loader/releases/tag/3.0.0) ·
[Sorgenti e configurazione](https://github.com/The-Grand-Combination/The-Grand-Loader/tree/3.0.0)

Applicare le chiavi del [file di opzioni](script_extender_options.ini)
all'INI **ufficiale** accanto alla DLL nel solo ambiente dedicato. Conservare
gli altri valori del bundle. I valori pubblicati nel file INI fanno fede per
il test, anche dove il README elenca default diversi.

| Funzione | Input nel profilo | Dipendenza e differenza rispetto al condiviso |
| --- | --- | --- |
| Cessione singola | `common/cb_types.txt`, quattro chiavi in `localisation/00_se_acquire_province.csv` | `demand_province` implementa selezione, costo e cessione della provincia. Restano anche i CB di stato. `acquire_province` conserva `is_triggered_only` e le condizioni upstream. Il percorso per la cessione negoziata è anche offerto dal termine del plugin. |
| Trattati volontari | Termini, editor, testi e risorse della distribuzione esterna | `treaty` carica i termini da `common/se_treaty_cbs.txt` del plugin. Cessione singola e cessione all'alleato richiedono anche `demand_province`. |
| Trattati forzati | Tre CB in `common/cb_types.txt`, guardie e chiusura 96094 in `events/Great War.txt` | `treaty` legge `dismantled_by` e `dismantled_by_gw`. Restano le riparazioni della penalità obbligatoria Great War. Per i due CB di smantellamento valgono i termini upstream. L'evento 96094 chiude la pace senza rifare le cessioni scriptate. |
| Partizioni e interessi AI | `common/se_partitions.txt`, `common/ai_interests.txt` | Il termine `treaty_partition` del plugin usa regioni, province e tag della mappa TGC. Le priorità AI assegnano territorio al vincitore o agli alleati secondo le regole del trattato. |
| Costruzione AI | `common/buildings_ai.txt`, `events/BanksAndUniversities.txt` | `buildings_ai` programma la costruzione di banche e università con chance, soglia di tesoreria e peso provinciale. Gli eventi 6200 e 6201 diventano solo invocabili, mentre 6202 e 6203 restano attivi alle condizioni del core. |
| Reddito per strato | `common/triggered_modifiers.txt`, `localisation/00_poor_income.csv`, `events/JANFlavor.txt` | `income_modifiers` applica le sei curve ai redditi dei POP, compreso il livello dal 1990. L'evento 53 perde i sei trasferimenti diretti e mantiene il proprio richiamo giornaliero e gli altri effetti. I modificatori legacy ereditati possono avere effetti diversi con il nuovo consumatore. |

Sono conservati i percorsi di migrazione del fork. La PR #417 sostituisce
i trasferimenti di reddito dell'evento 53. Non introduce un sostituto per
le politiche migratorie di TGC. Le decisioni diagnostiche `SE_Test` sono
assenti come nella revisione upstream `14f2e6ff6`. Le funzioni generiche
del plugin per mappa, costruzione del giocatore, sfondi e flag provinciali
restano disattivate nel primo profilo di verifica.
[Documentazione funzionale del plugin](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/README.md)

Gli adattamenti alla PR sono circoscritti. La chiusura 96094 si basa sui due
flag di accettazione e sul ritorno alla pace. Una nuova verifica di rango,
colonie o tag escluderebbe alcuni bersagli ammessi dai CB, ad esempio
paesi con possedimenti oltremare, e potrebbe escludere un paese che perde
rango nel trattato. Anche 96021 deve rispettare il flag Extender, perché
potrebbe consumare `dismantling_treaty` prima di 96094. Dalla tabella
delle partizioni sono rimossi 20 riferimenti agli ID assenti dalla mappa
del core `3603`, `3605`, `3649–3652`, `3661`, `4018`, `4019`.
Gli altri riferimenti sono conservati.

## Ritorno al profilo condiviso

Il Task 58 ha ritirato il vecchio addon, che modificava decisioni di
rinomina e contenuti di giornale. Il Performance Patch del Loader interviene
su percorsi del motore e rimane disattivato nel profilo collaudato. Un
eventuale confronto delle prestazioni richiede una prova separata.
[Opzioni del Performance Patch](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/docs/README.md)

Il profilo condiviso continua a usare `core` o `core+1966` su Victoria II
originale o Project Alice 1.3.0. Per tornare al condiviso, chiudere la sessione
dedicata, avviare dall'installazione condivisa senza Loader e selezionare
TGC con la Timeline solo se desiderata. Aprire un salvataggio del profilo
condiviso. Trattati, indici dei CB, modifiche territoriali, stato economico e
flag possono rendere incompatibile un salvataggio passato per l'Extender.

## Condizioni per un test runtime separato

1. Autorizzare esplicitamente il percorso della seconda installazione e l'uso
   del bundle ufficiale verificato. Confermare Victoria II 3.04 Windows x86,
   isolare la cartella di gioco e partire da salvataggi di prova.
2. Esaminare il piano pulito e usare il ciclo `plan → apply → verify` della
   [procedura di deployment](local_deployment.md), con
   `--profile core+extender` su ogni comando. Verificare ownership, SHA del
   commit e contenuto della coppia. Per annullare la transazione usare
   `rollback` con lo stesso profilo e l'ID registrato. Il rollback gestisce
   i file TGC pubblicati, mentre bundle e salvataggi restano separati.
3. Avviare col solo descrittore TGC esteso e con le quattro opzioni richieste.
   Controllare log del Loader, inizializzazione delle funzioni, origine dei
   CB e delle tabelle, interfaccia dei trattati e `user_dir` distinto.
4. Verificare una cessione di singola provincia e il costo in pace, un trattato
   volontario e uno forzato con vincitori umano e AI, una partizione, la
   chiusura 96094 e i flag, i costi di costruzione di entrambe le strutture e
   i redditi per strato. Ripetere caricamento e salvataggio nel solo profilo
   dedicato. Per un eventuale test multiplayer allineare build, contenuti
   e INI di tutti i partecipanti.
