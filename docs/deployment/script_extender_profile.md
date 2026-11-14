# Profilo Victoria II con The Grand Loader

`core+extender` prepara i contenuti della [PR #417](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/417)
che dipendono da Script Extender. Il profilo è destinato a **Victoria II 3.04
Windows x86**. La [guida di deployment](local_deployment.md#profiles-and-runtime-policy)
definisce la matrice dei profili e i requisiti di isolamento. Usare una radice
dedicata per ciascuna composizione Loader.

## Composizione e caricamento

| Profilo | Coppia runtime sotto `mod/` | Selezione in launcher | `user_dir` |
| --- | --- | --- | --- |
| `core+extender` | `TGCScriptExtender` e `TGCScriptExtender.mod` | **TGC - Script Extender** | `TGCScriptExtender` |
| `core+extender+1966` | `TGCScriptExtender1966` e `TGCScriptExtender1966.mod` | **TGC - Script Extender + Timeline 1966** | `TGCScriptExtender1966` |

Entrambi usano gli stessi file tracciati ed esclusioni di `core`. L'overlay
Extender aggiunge cinque file e ne sostituisce sei. `extender_overlay.json` elenca i percorsi ammessi
e gli SHA-256 dei sei originali, calcolati normalizzando CRLF a LF.
Aggiornare consapevolmente ciascun override e il relativo hash se cambia la
base. Il piano e lo staging verificano i byte effettivi da pubblicare. Il
manifest delle sorgenti è distinto dal catalogo delle transazioni, così una
revisione degli override consente ancora il rollback di un deployment precedente.

Nel profilo 1966 il deployer usa la Timeline canonica. Il manifest
`extender_1966_overrides.json` elenca i 18 percorsi in cui la Timeline
sostituisce il core. L'assemblaggio richiede una decisione esplicita su ogni
nuova collisione fra Timeline ed Extender. Oggi i due overlay hanno percorsi
distinti. Il file Timeline `common/buildings.txt` conserva le definizioni di
banca e università usate da `buildings_ai.txt` e porta forti, basi navali e
ferrovie al livello 8. Gli altri override Timeline conservano orizzonte,
setup, interfaccia e contenuti estesi. I file Extender per CB, eventi, redditi,
localizzazioni, partizioni e interessi IA restano quelli del profilo base.
Il deployer genera il descrittore 1966 dal modello Extender e riscrive
`map/default.map` per il `definition.csv` della coppia assemblata. I byte
generati entrano nelle impronte di piano, staging e verifica come gli altri file.

Il descrittore riprende i `replace_path` di TGC. Selezionare soltanto la
voce del profilo desiderato. Il Loader legge le direttive `load` dai descrittori
passati con `-mod=` e carica nell'ordine Script Extender e Performance Patch,
come nel descrittore TGC upstream fissato a `14f2e6ff`. Entrambi i percorsi
sono relativi a `mod/`. L'Extender cerca `cb_types.txt`, `buildings_ai.txt`,
`se_partitions.txt` e `ai_interests.txt` nel primo percorso di mod che
fornisce ciascun file. Con un solo descrittore TGC, il lettore del plugin e
quello del gioco ricevono gli stessi contenuti senza fare affidamento sulla
precedenza fra descrittori. L'Extender legge i propri CB di trattato, l'interfaccia,
le risorse grafiche e le localizzazioni dalla cartella ufficiale del plugin.
Il plugin genera `common/se_cb_types.generated.txt` nella propria cartella
unendo i CB del mod e i suoi CB. Ciascun profilo Loader richiede una cartella
di gioco separata, con una copia privata e scrivibile della cartella
`mod/script_extender`. Il deployment rifiuta una cartella di gioco che
contiene l'altro profilo o un alias del file generato. Rollback e recovery
operano sulla coppia gestita e lasciano il file generato al plugin.
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
e il tool consegnano solo contenuti TGC. Il bootstrapper `dinput8.dll` accanto
a `v2game.exe` e le cartelle esterne `mod/script_extender` e
`mod/performance_patch` sono prerequisiti per l'avvio dedicato. Il descrittore
TGC contiene entrambe le direttive, quindi basta selezionare quel descrittore.
[Release ufficiale](https://github.com/The-Grand-Combination/The-Grand-Loader/releases/tag/3.0.0) ·
[Sorgenti e configurazione](https://github.com/The-Grand-Combination/The-Grand-Loader/tree/3.0.0)

Usare entrambi gli INI completi del bundle accanto alle rispettive DLL. Per
aggiornare un ambiente di prova precedente, ripristinare i due INI originali
per recuperare anche i valori diagnostici e i parametri dei trattati. Il
[file di opzioni](script_extender_options.ini) elenca gli interruttori
attivi dello Script Extender come riferimento. Il bundle imposta
`treaty_dismantle_gp = 250`, mentre il README riporta 200. Conservare
`oos_log = 1` del Performance Patch e lasciare spenti i profiler,
`oos_test_button`, `network_log`, `buildings_ai_log` e
`treaty_dismantle_log`.

| Funzione | Input nel profilo | Dipendenza e differenza rispetto al condiviso |
| --- | --- | --- |
| Cessione singola | `common/cb_types.txt`, quattro chiavi in `localisation/00_se_acquire_province.csv` | `demand_province` implementa selezione, costo e cessione della provincia. Restano anche i CB di stato. `acquire_province` conserva `is_triggered_only` e le condizioni upstream. Il percorso per la cessione negoziata è anche offerto dal termine del plugin. |
| Trattati volontari | Termini, editor, testi e risorse della distribuzione esterna | `treaty` carica i termini da `common/se_treaty_cbs.txt` del plugin. Cessione singola e cessione all'alleato richiedono anche `demand_province`. |
| Trattati forzati | Tre CB in `common/cb_types.txt`, guardie e chiusura 96094 in `events/Great War.txt` | `treaty` legge `dismantled_by` e `dismantled_by_gw`. Restano le riparazioni della penalità obbligatoria Great War. Per i due CB di smantellamento valgono i termini upstream. L'evento 96094 chiude la pace senza rifare le cessioni scriptate. |
| Partizioni e interessi AI | `common/se_partitions.txt`, `common/ai_interests.txt` | Il termine `treaty_partition` del plugin usa regioni, province e tag della mappa TGC. Le priorità AI assegnano territorio al vincitore o agli alleati secondo le regole del trattato. |
| Costruzione AI | `common/buildings_ai.txt`, `events/BanksAndUniversities.txt` | `buildings_ai` programma la costruzione di banche e università con chance, soglia di tesoreria e peso provinciale. Gli eventi 6200 e 6201 diventano solo invocabili, mentre 6202 e 6203 restano attivi alle condizioni del core. |
| Reddito per strato | `common/triggered_modifiers.txt`, `localisation/00_poor_income.csv`, `events/JANFlavor.txt` | `income_modifiers` applica le sei curve ai redditi dei POP, compreso il livello dal 1990. L'evento 53 perde i sei trasferimenti diretti e mantiene il proprio richiamo giornaliero e gli altri effetti. Il profilo eredita la rimozione delle 15 assegnazioni legacy di `e5fcf7bc3` dal core condiviso. Le misure dei pagamenti effettivi e della transizione del 1990 restano nel collaudo funzionale. |

Sono conservati i percorsi di migrazione del fork. La PR #417 sostituisce
i trasferimenti di reddito dell'evento 53. Non introduce un sostituto per
le politiche migratorie di TGC. Le decisioni diagnostiche `SE_Test` sono
assenti come nella revisione upstream `14f2e6ff6`. Le funzioni generiche
del plugin per mappa, costruzione del giocatore, sfondi, flag provinciali e
colori dei vassalli sono attive in entrambi i profili Loader.
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

Il Performance Patch del Loader usa i valori del bundle nel profilo
dedicato. Per il ritiro del vecchio addon e le verifiche su configurazioni
precedenti, vedere le [evidenze storiche](../upstream_reconciliation.md).
[Opzioni del Performance Patch](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/docs/README.md)

Il profilo condiviso continua a usare `core` o `core+1966` su Victoria II
originale o Project Alice 1.3.0. Per tornare al condiviso, chiudere la sessione
dedicata, avviare dall'installazione condivisa senza Loader e selezionare
TGC con la Timeline solo se desiderata. Aprire un salvataggio del profilo
condiviso. Trattati, indici dei CB, modifiche territoriali, stato economico e
flag possono rendere incompatibile un salvataggio passato per l'Extender.

## Contratti dei consumatori

- **Mappa.** Il profilo deve risolvere `definition.csv` nella propria coppia
  pubblicata sotto `mod/`. Il core fornisce il CSV. L’override dedicato evita
  che il Loader cerchi il percorso della coppia condivisa. I test verificano il
  percorso effettivo per ciascuna composizione.
- **Cessione.** `acquire_province` è `is_triggered_only` e il selettore conserva
  l’ID della singola provincia. Con `peace_cost_factor = 1` il contributo
  territoriale atteso usa il valore nativo di quell’ID. `badboy_factor = 1.0`
  usa la base 5 prima dei correttivi. Il costo osservato nell’editor del
  trattato volontario vale per quel percorso. [Selettore e costo](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/demand_province.cpp)
- **Smembramento.** La coda del plugin aggrega per perdente, trattiene il primo
  vincitore e alza il budget al massimo delle richieste pendenti. L’editor o il
  trattato AI intervengono dopo la pace bilaterale. Il 96094 richiede invece
  pace generale e i due flag. Pulisce i flag e applica gli effetti di chiusura
  senza cessioni. `se_treaty_dismantled` inibisce il 96021 anche da solo,
  mentre occorre anche `dismantling_treaty` per il 96094. La catena legacy
  conserva le proprie condizioni. Il plugin rivalida i termini dopo ciascuna
  mutazione precedente, quindi l’esito della convalida iniziale può cambiare.
  [Coda](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty.cpp#L1939-L1958) ·
  [Applicazione](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty.cpp#L1301-L1351)
- **Reddito.** Nella progressione culturale ordinaria ogni curva lascia il
  posto alla successiva. Le ultime due si escludono alla soglia del 1990.
  Per i pagamenti supportati il plugin moltiplica il netto positivo dello
  strato per `max(0, 1000 + provincia + paese) / 1000` in unità fisse da
  1/32768 con troncamento intero. Il paese è il proprietario della provincia.
  Gli importi non positivi, il fondo per gli input artigiani e le chiamate
  estranee ai sette siti restano invariati. L’evento 53 conserva il richiamo a
  un giorno e le spese nazionali delle campagne sotto `override_campaigns`.
  I sei trasferimenti POP diretti sono rimossi nella composizione Loader.
  [Sorgente redditi](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/income_modifiers.cpp#L10-L76)

## Avvio in finestra e isolamento

Avviare Victoria II con `fullScreen=no` e `borderless=no`. Controllare il
`settings.txt` della copia di gioco, della radice utente indicata da
`userdir.txt` e della sottocartella del profilo. È il workaround osservato
per il crash a schermo intero durante l’inizializzazione della mappa.

Usare il bundle ufficiale verificato, gli INI completi e un’area di
salvataggi di prova isolata. Pubblicare e recuperare la coppia gestita
seguendo la [guida di deployment](local_deployment.md). Le ricevute
riguardano i contenuti TGC. Il bundle e i salvataggi hanno un ciclo separato.
Verificare il log dei plugin e la separazione dei file generati. Per il
multiplayer allineare build, contenuti e INI dei partecipanti.

Il [backlog](../rebaseline_backlog.md#verifiche-runtime) indica che cosa è
stato osservato e quali comportamenti richiedono ancora una verifica.
