# Registro della re-baseline

## Scopo e uso

Durante la re-baseline, i difetti scoperti incidentalmente vengono registrati e classificati. Si interviene immediatamente soltanto quando compromettono il lavoro corrente, l’integrità della baseline o una verifica necessaria per procedere. Gli altri vengono rinviati al workstream appropriato.

La baseline supportata è **Project Alice 1.3.0**, insieme a **Victoria II originale**. «Entrambe» indica il core e il profilo core + Timeline. L’evidenza del triage proviene dal secondo profilo. Per i file core condivisi, il perimetro «entrambe» descrive la presenza dei dati, mentre frequenza ed esiti del core da solo restano da verificare. Per le voci del triage, il comportamento riportato è quello di Alice 1.3.0 e la parità con Victoria II rimane aperta. «Dati» indica una causa nei dati TGC, potenzialmente condivisa dai motori. «Motore» indica un limite verificato di Alice. «Misto» indica un’interazione fra i due.

## Criteri

| Dimensione | Valori e significato |
| --- | --- |
| Gravità | **Alta** se si perde una parte sostanziale del contenuto, si altera una condizione importante o si interrompe una campagna. **Media** per un effetto funzionale circoscritto. **Bassa** per presentazione, diagnostica o conseguenza limitata. **Da stimare** se manca evidenza sull’impatto. |
| Blocco | **Sì** se esiste un’attività corrente o una verifica necessaria già impedita. **Condizionale** se una prova futura specifica può essere impedita. **No** se il lavoro corrente può proseguire. Una gravità alta può avere blocco No. |
| Priorità | **P1** alla prima occasione nel workstream indicato, per impatto provato o verifica necessaria. **P2** al ritorno nel workstream, con dipendenze o rischio da valutare. **P3** opportunistica. Un P1 con blocco No rimane in coda. Il numero di messaggi misura la ricorrenza. |
| Stato | **Aperta**, **Mitigata**, **Rinviata**, **Registrata** per un comportamento informativo accertato, **Chiusa** con evidenza di risoluzione o decisione motivata. |
| Evidenza | **Sorgenti** equivale a SOURCE-LEVEL VERIFIED. **Dati** equivale a STATIC DATA VERIFIED. **Runtime** richiede osservazione riproducibile del comportamento indicato. **Aperta** equivale a UNRESOLVED. |
| Classe Task 37 | **A** perdita funzionale dimostrata, **B** possibile incompatibilità, **C** problema di contenuto, **D** differenza d’implementazione, **E** diagnostico senza impatto ordinario accertato, **F** indeterminato. |

## Indice

| Area | Voci |
| --- | --- |
| [Ordini di battaglia e storia](#ordini-di-battaglia-e-storia) | OOB_NO_POP, OOB_OWNER, OOB_SEARCH, DEAD_OOB, INVALID_HISTORY |
| [Eventi, decisioni e mappa](#eventi-decisioni-e-mappa) | OPTIONS_AID, OPTIONS_CANAL, CANAL_CONTROL, BATTLE_EVENT, EVENT_REF, LITERACY, REG_MOD, SANTA_MOD, EVENT_ORPHAN, EVENT_DEBUG, EVENT_MILITARY, PICTURE, EMPTY_ALLOW, FACTORY_STATE, CARRINGTON_SCHEDULING, CARRINGTON_RECIPIENTS, GREAT_WAR_ALLIANCE, LTU_CORE_CLEANUP |
| [Ricerca, economia e unità](#ricerca-economia-e-unità) | TECH_AI, SCHOOL, TEXTILE, NAV_ORG, BLOCKADE, NAV_ATTR, UNIT_BASKET, UNIT_MORALE, UNIT_REINF, UNIT_STRENGTH, UNIT_WEIGHT, STEAM, ARTILLERY |
| [Workaround navali](#workaround-navali) | SUB_AI_GP, SUB_AI_SP, SUB_FRA, SUB_SWE, SUB_FISH, SUB_BEIYANG, SUB_EIC, SUB_JAP, SUB_RUS |
| [Questioni rinviate](#questioni-rinviate) | NAVAL_AI, NAVAL_TIMING, ALICE_REMAINING, BALANCE, CRASH_1949 |
| [Verifiche runtime](#verifiche-runtime) | Profili installati, JIT Alice, salvataggi, Loader e prestazioni |
| [Manutenzione e chiusura](#manutenzione-e-chiusura) | Regole per aggiornamenti, revisioni del motore e chiusura |

## Provenienza della diagnostica Alice

Il [checkpoint Task 36](https://github.com/Dumcem/The-Grand-Combo/commit/8ccb9326db0bbeef603b17405a9bf84e6e2abe7b) ha generato e caricato fino alla schermata iniziale lo scenario con avvio 1836, profilo core + Timeline. Il Task 37 ha ricondotto **197 errori non fatali e 314 warning**, 466 dal core e 45 dalla Timeline, a **31 gruppi**. Il catalogo locale conserva per ogni occorrenza messaggio, riga del log, file effettivo e ambito. I 197/314 sono storici. La [riconciliazione](upstream_reconciliation.md#evidenza-runtime-e-di-recupero) registra anche i conteggi del successivo checkpoint a `864c81fe8`. Il caricamento costituisce evidenza runtime per lo scenario. Le singole meccaniche conservano il grado di evidenza indicato sotto.

I riferimenti `log` indicano righe fisiche, a partire da 1 e con le intestazioni incluse, di `scenario_errors.txt` del Task 36, SHA-256 `be28104b020207a61e2749cb9038d7e7847020089a0bf1051ff9d6e7b4cc9a9d`. Gli intervalli sono inclusivi. Ogni occorrenza appartiene a una scheda. Una rigenerazione può produrre ordine o numeri diversi. Per confrontarla usare firma, file, ID o ambito della scheda, mantenendo il riferimento al log storico.

Le 31 schede hanno **blocco No per la re-baseline corrente** e sono **Aperte**, salvo indicazione diversa. L’assenza di una guardia documentata indica che la scheda non registra un workaround. Il riscontro di un impedimento concreto impone di registrare l’attività interessata e la prova prima di cambiare il blocco. La mitigazione di un’altra voce non modifica questo criterio.

## Ordini di battaglia e storia

Il caricatore associa un POP soldato a ogni reggimento nazionale. Elimina i reggimenti rimasti senza sorgente prima della serializzazione. OOB_NO_POP e OOB_OWNER costituiscono **135 esclusioni** distinte. OOB_SEARCH registra anche i tentativi falliti di OOB_NO_POP.

### OOB_NO_POP — Reggimenti privi di POP soldato

**A · Alta · P1 · Sorgenti · Misto · Entrambe.** 57 reggimenti senza una sorgente idonea vengono eliminati al caricamento. I 57 warning corrispondenti sono in OOB_SEARCH e rappresentano gli stessi reggimenti.

**Classificazione statica al 1° gennaio 1836.** Le 57 esclusioni sono riprodotte con i dati TGC. Tutte le origini `home` appartengono al paese dell’OOB e contengono POP soldati. Per queste esclusioni la ricostruzione non rileva errori di parsing, POP mancanti o proprietà iniziali incompatibili.

| Gruppo | Reggimenti | Causa |
| --- | ---: | --- |
| A | 37 | Nessun POP soldato nelle province possedute raggiunge individualmente il minimo. |
| B | 8 | I POP soldati dell’origine sono sotto soglia e i posti disponibili altrove sono già occupati. |
| C | 12 | Almeno un POP soldato dell’origine raggiunge il minimo, ma i posti disponibili nell’intero paese sono già occupati. |

Con i parametri TGC, Alice richiede almeno 1.000 soldati per singolo POP. Per un POP idoneo la capacità OOB è `floor(size / 2000) + 1`, al netto dei reggimenti e delle costruzioni già associati. La ricerca d’origine precede quella nelle altre province possedute. [POP del 1836](../TGC/history/pops/1836.1.1) · [Storie provinciali](../TGC/history/provinces) · [Parametri TGC](../TGC/common/defines.lua#L138) · [Ricerca OOB](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military_templates.hpp#L58-L74) · [Capacità](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.cpp#L1264-L1277)

**Confronto Alice.** La baseline resta **1.3.0** e include già la ricerca alternativa e il controllo di capacità della PR #2082. Nel `main` esaminato a `42adaf79c0115e261a87fa5f08e2dff28ad24bc4` persistono soglia, controllo di capacità e rimozione dei reggimenti senza sorgente. Il codice prevede ancora **0/1 per LAN, 0/1 per MNC e 4/6 per BIK**. Le storie nazionali dei tre paesi puntano già ai rispettivi OOB, quindi il caricamento per direttiva introdotto da #2241 seleziona gli stessi file. Il fallimento della ricerca diventa un warning. La riduzione del numero di errori può avvenire senza recuperare alcun reparto. [PR #2082](https://github.com/schombert/Project-Alice/pull/2082/files) · [PR #2241](https://github.com/schombert/Project-Alice/pull/2241/files) · [Associazione in main](https://github.com/schombert/Project-Alice/blob/42adaf79c0115e261a87fa5f08e2dff28ad24bc4/src/parsing/parsers_declarations.cpp#L2581-L2639) · [Rimozione in main](https://github.com/schombert/Project-Alice/blob/42adaf79c0115e261a87fa5f08e2dff28ad24bc4/src/gamestate/system_state.cpp#L3273-L3278)

**Victoria II 3.04 originale, caso Monaco.** L’analisi statica ha usato `v2game.exe`, SHA-256 `62d48c204364dd706584777c2e2b3c7ab3c5f1dd0170872554943575d53d6648`. Il caricatore crea la `Compagnie des Carabiniers` (tipo `guard`, `home = 3251`), applica il minimo e scarta il solo POP soldato disponibile, di dimensione 50. Inserisce comunque il reparto nella lista dell’armata senza sorgente. [OOB Monaco](../TGC/history/units/MNC_oob.txt#L9) · [POP Monaco](../TGC/history/pops/1836.1.1/ANewNation.txt#L18) · [Identificazione del binario 3.04](https://github.com/maxioten/Victoria2-Reverse-Engineering/blob/main/Engine/script-execution-boundaries.md)

Indirizzi virtuali per riprendere la verifica sullo stesso binario, con base `0x00400000`.

- `0x005BE630` cerca il POP sorgente. Il ramo `0x005BE9BA–0x005BEA4F` tratta il fallimento dell’associazione.
- `0x005C6F90` chiama `0x005CB1D0`, che inserisce il reparto nella lista dell’armata.
- `0x00662010` include la finalizzazione delle formazioni. Il ciclo a `0x00662AE9–0x00662B37` percorre la lista dei reggimenti senza leggere il campo sorgente. La richiesta di transizione alla sessione avviene a `0x0066908A`, prima di ulteriori chiamate. [Finalizzazione](https://github.com/maxioten/Victoria2-Reverse-Engineering/blob/main/Engine/loading-initialization.md) · [Confine della sessione giocabile](https://github.com/maxioten/Victoria2-Reverse-Engineering/blob/main/Engine/native-ui-and-frontend.md)
- `0x0068A900` può distaccare e distruggere un reggimento tramite il suo distruttore virtuale. `0x0068AA10` può distaccare e distruggere i reparti durante la distruzione di un’armata. La traccia non collega queste procedure all’assenza di sorgente di Monaco durante l’avvio. Le chiamate indirette irrisolte lasciano aperte cancellazione e riassegnazione.

**Esito e verifica runtime.** La divergenza nell’inizializzazione è accertata. La presenza del reparto nello stato giocabile del 3.04 rimane indeterminata. La verifica automatizzata si è fermata con esito **BLOCKED / NON VERIFICABILE** prima di avviare il gioco. Steam condivide dati utente preesistenti e il registro di deployment indicava `608d1867`, mentre il checkout esaminato era `1956eeeb`. Le due installazioni Loader contenevano profili diversi dal core e l’isolamento delle scritture esterne era da verificare. L’ambiente storico Task 54 era privo di `v2game.exe`. Nessuno snapshot iniziale attendibile è stato acquisito. La scheda resta aperta e l’impedimento riguarda questa verifica. [Procedura di verifica runtime](deployment/local_deployment.md#recording-deployment-evidence)

Acquisire lo stato di Monaco con il 3.04 originale e TGC core di provenienza verificata, dopo l’ingresso nella sessione giocabile e prima dell’avanzamento di data, in un ambiente completamente isolato. Verificare il record del reggimento e il riferimento al POP, se presente. L’attribuzione a un bug di compatibilità Alice o a un difetto dei dati TGC rimane aperta. Sospendere le modifiche ai POP e agli OOB motivate dalle sole esclusioni Alice.

**Archivio locale del progetto.** Il log Task 36 è conservato in `task36-checkpoint/new-scenario-errors.txt` con l’impronta riportata in [Provenienza](#provenienza-della-diagnostica-alice). Il catalogo Task 37 `task37-triage/occorrenze.csv` risolve ciascun caso per file OOB e riga di `home`. In `task45-checkpoint/new-scenario-errors.txt`, al checkpoint `cebfc8c9`, coincidono le firme dei 57 errori OOB_NO_POP, dei 78 warning OOB_OWNER e dei 140 warning OOB_SEARCH.

**Traccia.** 57 errori e 0 warning. Log 145–201. [Ordini di battaglia](../TGC/history/units), 39 file · [AGC_oob.txt](../TGC/history/units/AGC_oob.txt#L7) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2484-L2513) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3510-L3517)

### OOB_OWNER — Provincia d’origine sotto altro proprietario

**A · Alta · P1 · Sorgenti · Misto · Entrambe.** 78 reggimenti distinti da OOB_NO_POP restano senza sorgente e vengono eliminati. Alice salta la ricerca alternativa in questo ramo.

Ordini di battaglia e confini. Riesaminare quando si possono verificare proprietà, data e intenti dello schieramento. Il ripristino richiede di preservare il ruolo storico.

**Sviluppo Alice.** Dopo la 1.3.0, `9e662b23b8e17d016d7f0c3f48df436a8ddf5dca`, integrato con #2241 e presente nel `main` esaminato, aggiunge al ramo con `home` straniera una ricerca nelle province possedute dal paese dell’armata. Il warning di proprietà rimane. Restano da misurare quanti dei 78 reparti siano recuperabili e il guadagno netto, poiché il fallback può occupare posti che altri reparti userebbero in seguito. La scheda resta aperta con baseline 1.3.0. [Commit Alice](https://github.com/schombert/Project-Alice/commit/9e662b23b8e17d016d7f0c3f48df436a8ddf5dca) · [PR #2241](https://github.com/schombert/Project-Alice/pull/2241/files)

**Traccia.** 0 errori e 78 warning. Log 292–296, 300–301, 303, 306, 312–315, 323–324, 329, 334–341, 357, 367, 370–372, 375–376, 378–387, 394–398, 404, 406–411, 413–414, 419, 430–431, 433–436, 439–446, 459–461, 464–466, 487, 509. [Ordini di battaglia](../TGC/history/units), 38 file · [ABA_oob.txt](../TGC/history/units/ABA_oob.txt#L20) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2484-L2499) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3510-L3517)

### OOB_SEARCH — Ricerca in un’altra provincia

**D · Media · P2 · Sorgenti · Motore · Entrambe.** 140 avvisi precedono la ricerca. In 83 casi Alice associa un POP altrove e in 57 ricade in OOB_NO_POP. Il cambio di sorgente può incidere sui rinforzi.

**Confronto dei log.** I 57 fallimenti dei 140 tentativi storici sono già rappresentati in OOB_NO_POP. Dopo la 1.3.0, `9e662b2` emette OOB_SEARCH soltanto dopo un’assegnazione alternativa riuscita nel ramo con `home` posseduta. Per confrontare scenari, abbinare file OOB e identità del reggimento, usando la riga di `home` per il log storico, e verificare presenza e sorgente quando osservabili. La scheda resta aperta. Parità con Victoria II da stabilire. [Diff Alice](https://github.com/schombert/Project-Alice/commit/9e662b23b8e17d016d7f0c3f48df436a8ddf5dca)

**Traccia.** 0 errori e 140 warning. Log 297–299, 302, 304–305, 307–311, 316–322, 325–328, 330–333, 342–356, 358–366, 368–369, 373–374, 377, 388–393, 399–403, 405, 412, 415–418, 420–429, 432, 437–438, 447–458, 462–463, 467–476, 478, 480–486, 488–508, 510–511. [Ordini di battaglia](../TGC/history/units), 70 file · [AFG_oob.txt](../TGC/history/units/AFG_oob.txt#L74) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2495-L2513) · [Alice · military_templates.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military_templates.hpp#L58-L74)

### DEAD_OOB — Ordini di battaglia di tag inattivi

**Corretta e verificata staticamente · Bassa · P3 · Misto · Core e Timeline.** Alice 1.3.0 scansionava i tre OOB prima di caricare le storie nazionali. Le identità SRG, SWA e ZOU erano registrate, ma a quel punto mancavano le istanze nazionali associate. Il caricatore emetteva quindi `dead tag` prima di aprire i file. Il parser della storia nazionale scarta la direttiva `oob`. Il log storico riporta 0 errori e 3 warning, alle righe 477, 479 e 512. [Scansione OOB](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3297-L3348) · [Storia nazionale](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3370-L3411) · [Schema della direttiva](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L1223-L1251)

Il commit del 9 aprile 2026 aveva aggiunto tre file di soli commenti per soddisfare riferimenti già presenti, senza definire unità iniziali. La correzione elimina insieme `history/units/SRG_oob.txt`, `history/units/SWA_oob.txt` e `history/units/ZOU_oob.txt` dal core e le rispettive direttive `oob` dalle storie di Surguja, Swat e Zoutpansberg. La rimozione simultanea evita di ricreare i tre riferimenti pendenti originali. [Commit del 2026](https://github.com/Dumcem/The-Grand-Combo/commit/1724b3d941d135f55caf856590b09e7f45192363) · [Surguja](<../TGC/history/countries/SRG - Surguja.txt>) · [Swat](<../TGC/history/countries/SWA - Swat.txt>) · [Zoutpansberg](<../TGC/history/countries/ZOU - Zoutpansberg.txt>)

**Verifica statica.** L'assemblaggio con le funzioni e i manifest del deployer è riuscito per `core`, `core+1966`, `core+extender` e `core+extender+1966`. In ciascun profilo il confronto delle impronte ha rilevato solo le tre eliminazioni e le tre rimozioni di direttiva. Restano pubblicate le tre storie nazionali, con zero riferimenti pendenti ai tre OOB. Gli altri contenuti e i descrittori coincidono con la base. Le definizioni dei tag, i territori, gli altri OOB, i riferimenti diplomatici e di setup e la comparsa di ZOU tramite l'evento `6022` non dipendono dai file rimossi e non hanno subito modifiche. Il drift in entrambe le direzioni ha restituito 0 FAIL e 0 WARN. [Evento 6022](../TGC/events/SAFFlavor.txt#L1261)

**Runtime pendente.** In Alice 1.3.0 la rimozione dei file elimina la causa dei tre warning. Rigenerare e caricare gli scenari di core e Timeline da un deployment verificato con dati utente isolati e controllare il log per i tre tag e per nuovi errori OOB o di storia. In Victoria II 3.04 è atteso lo stesso stato militare dei segnaposto vuoti, senza richieste esplicite dei tre file. Restano da verificare il caricamento su 3.04 e la comparsa di ZOU con l'evento `6022` su entrambi i motori.

**Candidatura upstream.** Vale la pena preparare le tre sole rimozioni di direttiva dopo il riscontro runtime e la conferma dei dati sul ramo di destinazione. I riferimenti upstream esaminati contengono le direttive e sono già privi dei segnaposto. Il ramo `1815` richiede una verifica sui propri bookmark 1815 e 1836.

### INVALID_HISTORY — Storia paese senza tag definito

**Corretta e verificata staticamente · Bassa · P3 · Dati.** Alice 1.3.0 emetteva sei avvisi perché i file di storia di CIV, UCV, VLP, VNG, VNS e VOP avevano un prefisso privo di identità registrata. Il caricatore li scartava prima di aprirli. Il fork ha rimosso i sei file, recuperabili dalla revisione `e7ef8ca2b`. [File recuperabili](https://github.com/Dumcem/The-Grand-Combo/tree/e7ef8ca2b3cc91c2c2bfa36af44b82765ebf74c2/TGC/history/countries) · [Caricatore Alice 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3386-L3411)

La simulazione iniziale e il confronto ripetuto dopo la rimozione confermano l'esito per `core`, `core+1966`, `core+extender` e `core+extender+1966`. I file di storia nazionale visibili passano da 688 a 682. La regola di Alice seleziona gli stessi 682 file e i warning specifici previsti passano da 6 a 0. Le 683 identità registrate e i riferimenti di gameplay risultano invariati. Il controllo drift fra core e Timeline è passato in entrambe le direzioni, con 0 FAIL e 0 WARN.

Il ramo upstream `1815` registra e usa ancora VLP, VNG, VNS e VOP. I quattro file vanno preservati nella composizione 1815. Il requisito di verifica prima dell'integrazione è nel [registro upstream](upstream_delta_register.md#invalid_history-e-scenario-1815).

**Runtime pendente.** Il log precedente riportava 0 errori e 6 warning per questa voce, alle righe 513–518. La scomparsa degli avvisi resta da osservare rigenerando gli scenari Alice `core` e `core+1966` in un ambiente isolato. La parità su Victoria II originale è attesa dalla composizione statica e resta da confermare in esecuzione. L'installazione Steam condivisa è stata esclusa dalla prova.

## Eventi, decisioni e mappa

Le due schede sulle opzioni condividono la causa nel parser. Restano distinte perché riguardano catene ed effetti diversi.

### OPTIONS_AID — Opzioni di Country Aid oltre il limite

**A · Alta · P1 · Sorgenti · Misto · Entrambe.** Alice conserva otto opzioni e scarta I/J negli eventi 100003, 100005, 100007, 100009 e 100013. Si perdono livelli di aiuto e i relativi effetti.

Eventi e diplomazia economica. Riesaminare alla revisione di Country Aid o se cambia il limite. Ripristino candidato con equivalenza di importi, destinatari, FROM, rifiuto e pesi AI, dopo confronto V2.

**Traccia.** 10 errori e 0 warning. Log 135–144. [CountryAid.txt](../TGC/events/CountryAid.txt#L197) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L3113-L3123) · [Alice · constants.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/common_types/constants.hpp#L581) · [Alice · events.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/events.cpp#L14-L31)

### OPTIONS_CANAL — Opzioni di finanziamento del Chunnel

**A · Alta · P1 · Sorgenti · Misto · Entrambe.** Stesso limite di OPTIONS_AID. Nell’evento 36996 mancano I/J/K, con durate 4745, 5110 e 5475 giorni e pesi AI legati ai fondi.

Eventi infrastrutturali. Riesaminare con la catena di finanziamento o un cambio del limite. Verificare che resti una scelta AI valida e preservare i rami V2.

**Traccia.** 3 errori e 0 warning. Log 132–134. [Canals Construction.txt](../TGC/events/Canals%20Construction.txt#L1771) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L3113-L3123) · [Alice · constants.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/common_types/constants.hpp#L581)

### CANAL_CONTROL — Controllo marittimo degli attraversamenti

**A · Alta · P2 · Sorgenti · Misto · Entrambe.** Alice azzera la provincia di controllo dei canali 12, 13 e 14. Il controllo del blocco non interviene dopo l’apertura. Solo per il 12 è stato trovato un enable attivo.

Mappa e infrastrutture. Riesaminare al ritorno su Chunnel o Alaska o se cambia il consumatore. La semantica di controllo richiede una decisione prima di cambiare il tipo di arco.

**Traccia.** 0 errori e 3 warning. Log 205–207. [adjacencies.csv](../TGC/map/adjacencies.csv#L486) · [Alice · provinces_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/provinces_parsing.cpp#L129-L158) · [Alice · province.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/provinces/province.cpp#L1480-L1509) · [Alice · province.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/provinces/province.cpp#L2238-L2242)

### BATTLE_EVENT — Catena della cattura di Santa Anna

**A · Alta · P1 · Sorgenti · Motore · Entrambe.** Due warning per 44840. on_battle_won registra un evento provinciale e TGC ne definisce uno nazionale. Nei sorgenti 1.3.0 non è stato trovato il dispatch a fine battaglia.

Eventi storici e motore. Riesaminare se il motore implementa l’aggancio o emerge un equivalente verificato. Ripristino subordinato a battaglia, destinatario e ambiti equivalenti.

**Traccia.** 0 errori e 2 warning. Log 252, 290. [on_actions.txt](../TGC/common/on_actions.txt#L9) · [MEXFlavor.txt](../TGC/events/MEXFlavor.txt#L719) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L1909-L1922) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1373-L1407) · [Alice · military.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.cpp#L5783) · [Alice · military.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.cpp#L6005)

### EVENT_REF — Evento oltremare USS mancante

**A · Media · P2 · Sorgenti · Dati · Entrambe.** USSFlavor accoda 4102182 dopo tre giorni. Manca il corpo nazionale e il trasferimento citato nel commento non si esegue.

Eventi storici delle Americhe. Riesaminare quando si ricostruiscono destinatari, territori e ingresso. Ripristino candidato con una definizione coerente su entrambi i motori.

**Traccia.** 0 errori e 1 warning. Log 289. [USSFlavor.txt](../TGC/events/USSFlavor.txt#L1215) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408) · [Alice · events.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/events.cpp#L474-L490)

### LITERACY — Alfabetizzazione nelle riforme cinesi

**A · Media · P2 · Sorgenti · Motore · Entrambe.** Gli eventi 600000 e 600001 perdono rispettivamente +0,01 e +0,02. Alice applica literacy in ambito POP con somma e limite tra 0 e 1.

Eventi storici ed educazione. Riesaminare se cambia lo scope o al ritorno sulla catena. Il ripristino richiede prova dell’equivalenza per popolazione bersaglio e scala V2.

**Traccia.** 2 errori e 0 warning. Log 50–51. [China.txt](../TGC/events/China.txt#L11610) · [Alice · effect_parsing.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/effect_parsing.hpp#L2521-L2530) · [Alice · effects.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L3300-L3305)

### REG_MOD — Rimozione di regency_government

**Corretto nei dati · P3 · Core e Timeline · Verifica runtime pendente.** `regency_government` era la reggenza di HPM e di `Legacy/Test`. TGC lo usò nelle rivoluzioni nel marzo 2020 (`d16334a85`, poi `261d577da`), con un produttore temporaneo in `GovernmentFlavor.txt` eliminato da `084b71992`. Il fork reimportò i lettori dal file teocratico di Test in `7612ca00d`; `978d0ed7e` portò il totale a 20 coppie. La vecchia chiave è priva di definizione e produttore correnti. Il nuovo effetto nazionale rimuove `regency_modifier`, la reggenza effettiva, dopo l’instaurazione della teocrazia.

**Brasile.** `8002` richiede un governo monarchico effettivo e la reggenza, anche quando l’opzione accoda `8003`. `8003` e `8005` verificano di nuovo governo e reggenza quando applicano gli effetti, anche se erano già accodati. `8004` conserva la marcatura anticipata di `pedro_ii_crowned` e la programma solo nel contesto valido. `8006` e `8007` conservano i trigger con reggenza e verificano lo stato corrente se l’opzione era già aperta. `8008` richiede il Brasile monarchico sia nel trigger sia all’applicazione del beneficio, anche con `child_emperor` storico. Le verifiche usano le sei forme monarchiche effettive. La condizione sugli effetti passa dalla capitale posseduta al suo proprietario una sola volta. I flag storici restano disponibili nei salvataggi.

**Traccia e verifiche.** Eliminati 20 dei 40 contenitori `random_owned`, con scomparsa attesa di 40 errori Alice (log storico 52–129, a coppie alterne). La variazione delle estrazioni diplomatiche successive è accettata. Confronto strutturale, validator, drift in entrambe le direzioni, quattro composizioni e 11 test Extender superati. Audit identico a `7796f9a7f` (0 FAIL, 1.828 WARN, 2.972 INFO). Restano la conferma da uno scenario Alice 1.3.0 rigenerato e la verifica in Victoria II 3.04, incluse opzioni già aperte, consegna degli eventi accodati e caricamento di salvataggi precedenti. In Alice la consegna a scadenza è distinta dagli effetti dell’opzione. [Rivoluzioni](../TGC/events/Revolution_Event_Theocracy.txt#L38) · [Brasile](../TGC/events/BRZFlavor.txt#L1) · [Compilazione e ambiti Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/effect_parsing.cpp#L618-L654) · [Coda Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/events.cpp#L474-L493)

### SANTA_MOD — Rimozione di santa_ana_rule

**Corretto nei dati · P3 · Core e Timeline · Verifica runtime pendente.** `santa_ana_rule` era il modificatore del governo di Santa Anna in HPM e `Legacy/Test`, applicato da `44805` e letto dalla cattura texana. Le coppie di rimozione di TGC del marzo 2020 (`d16334a85`, poi `261d577da`) ricomparvero nel fork con l’importazione del file di Test (`7612ca00d`, estesa da `978d0ed7e`). La vecchia chiave è priva di definizione e produttore correnti. Le rivoluzioni teocratiche cancellano `santa_anna_in_charge` solo se il proprietario della capitale selezionata è MEX. La deposizione lascia indipendente `santa_anna_dead`. Le nuove catture richiedono ancora il flag di governo e le rivolte possono usare `fight_the_power`. Le opzioni di una cattura già avviata mantengono la propria logica.

**Traccia e verifiche.** Eliminati gli altri 20 contenitori `random_owned`, con scomparsa attesa di 40 errori Alice (log storico 54–131, a coppie alterne). Il filtro deterministico sulla capitale evita la divergenza di `any_country`, che in un evento Alice può escludere il paese dell’evento. Accettata la conseguente variazione delle estrazioni successive. Si applicano gli esiti statici e le verifiche runtime riportati in REG_MOD. Da verificare anche il caricamento di salvataggi con cattura già aperta o provenienti da una composizione esterna con la vecchia chiave attiva. [Catena messicana](../TGC/events/MEXFlavor.txt#L717) · [Selezione paesi Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L323-L357) · [Flag nazionale Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L2054-L2057)

### EVENT_ORPHAN — Eventi definiti senza ingresso verificato

**F · Da stimare · P3 · Aperta · Misto · Entrambe.** 48 definizioni risultano assegnate ma non elaborate nel registro Alice. Raggiungibilità e intenzione dei singoli ingressi restano aperte.

Eventi per regione. Riesaminare al ritorno su ciascuna catena o dopo cambi di registrazione. Verificare ingressi attivi prima di ripristinarli.

**Traccia.** 0 errori e 48 warning. Log 211–221, 236–251, 253–256, 273–288, 291. [AUSFlavor.txt](../TGC/events/AUSFlavor.txt#L2638) · [Archaeology.txt](../TGC/events/Archaeology.txt#L3349) · [BRZFlavor.txt](../TGC/events/BRZFlavor.txt#L5731) · [CBsAndCores.txt](../TGC/events/CBsAndCores.txt#L1333) · [GEF Events.txt](../TGC/events/GEF%20Events.txt#L3256) · [Germany VS Hungary Events.txt](../TGC/events/Germany%20VS%20Hungary%20Events.txt#L240) · [JANFlavor.txt](../TGC/events/JANFlavor.txt#L3536) · [MEXFlavor.txt](../TGC/events/MEXFlavor.txt#L762) · [POLFlavor.txt](../TGC/events/POLFlavor.txt#L445) · [RUSFlavor.txt](../TGC/events/RUSFlavor.txt#L789) · [SPAFlavor.txt](../TGC/events/SPAFlavor.txt#L4251) · [SlaveryEvents.txt](../TGC/events/SlaveryEvents.txt#L195) · [USA_Minors.txt](../TGC/events/USA_Minors.txt#L2431) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408)

L'evento polacco 500007 condivideva i riferimenti testuali di 203903, corretti separatamente nel fork con `068c8cabf`. La PR #435 copre i testi di 203903. Per 500007, trigger-only, la ricerca ha trovato un solo chiamante commentato. Vale per core e Timeline su entrambi i motori. Riaprire la candidatura quando emerge un ingresso attivo o un riuso deliberato.

### EVENT_DEBUG — Eventi di debug fuori dal flusso ordinario

**E · Bassa · P3 · Dati · Dati · Entrambe.** 14 eventi di test sono a invocazione esplicita. Impatto sul gioco ordinario assente per il perimetro esaminato. Disponibilità da console aperta.

Debug. Riesaminare se si verifica la console o cambia il caricatore. Stato Registrata.

**Traccia.** 0 errori e 14 warning. Log 222–235. [Debug.txt](../TGC/events/Debug.txt#L6) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408)

### EVENT_MILITARY — Circuito di ingaggio di comandanti inattivo

**B · Media · P2 · Dati · Dati · Entrambe.** I 16 eventi 10000105–10000120 si richiamano internamente e l’ingresso identificato è commentato. Un eventuale ripristino riattiverebbe costi e acquisizione di leader.

Leader ed eventi militari. Riesaminare quando si decide se il circuito debba tornare disponibile. Verificare altri ingressi e V2.

**Traccia.** 0 errori e 16 warning. Log 257–272. [Military.txt](../TGC/events/Military.txt#L1518) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408)

### PICTURE — Immagine di form_soviet_union assente

**C · Bassa · P3 · Sorgenti · Dati · Entrambe.** Correzione integrata e verificata staticamente. Verifiche in esecuzione residue. Il commit upstream [`4697a9b03`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/4697a9b03bfa0f20b46ceecbc6e9976452a45564) introdusse la decisione provvisoria con `picture = form_soviet_union` senza aggiungere il file. Il riferimento è ancora presente in upstream `4661c1b5a`. Prima della correzione, nessun omonimo DDS, TGA o PNG era emerso nella cronologia Git disponibile, nel core, nella Timeline, nei submod installati o nell'installazione Steam con A House Divided e Heart of Darkness. La Timeline eredita la decisione e la sua cartella grafica dal core.

Il candidato storico più vicino è `Unused Files/DecisionImages/transition_to_soviet_union.dds` (95 × 95, foto di gruppo con insegna in cirillico). Era in `TGC/gfx/pictures/decisions/` nel 2020, fu spostato fra le immagini inutilizzate nel 2021 e rimosso nel 2023, prima dell'introduzione della decisione nel 2025. Provenienza della foto, diritti di redistribuzione e collegamento con questa decisione restano da accertare. L'altro DDS storico, `soviet_cities.dds` (90 × 90), mostra una scena di propaganda industriale. Nel core, `establish_the_sovnarkom.dds` (95 × 95) coincide byte per byte con l'asset delle espansioni ed è associato alla decisione per il Consiglio dei commissari del popolo.

Cronologia dei DDS storici. [Aggiunta](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/5d4f5c4fab98c6eadd16a87176ae18a955cfd325) · [Spostamento](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/862bd5119719b9a01f9d6cd96b41595bc1e66926) · [Rimozione](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/319e7144d717d9a1c2ae5455a427b0de6a2c38fb)

**Asset adottato.** Stemma ufficiale sovietico approvato il 6 luglio 1923, da una riproduzione attribuita da Wikimedia Commons al Comitato esecutivo centrale dell’URSS con rimando a Rosarchiv. Il ritaglio e ridimensionamento a 95 × 95 px, con conversione in DDS, sono quelli della versione approvata. Il file è stato copiato byte per byte. Commons classifica l’immagine in pubblico dominio come simbolo statale ufficiale sovietico (`PD-RU-exempt`, art. 1259 del codice civile russo). La classificazione documenta la base russa. La situazione nelle altre giurisdizioni e le eventuali restrizioni locali all’uso del simbolo restano da accertare. [Riproduzione e classificazione](https://commons.wikimedia.org/wiki/File:Official_Design_of_the_State_Emblem_of_the_Soviet_Union_%281923-1936%29.jpg)

**Verifiche.** Il [DDS](../TGC/gfx/pictures/decisions/form_soviet_union.dds) misura 95 × 95 px, 36.228 byte, ARGB8888 non compresso con alfa opaco. SHA-256 `5e4c98223a344b80e1d8097304312ac020b05edc7483205956ced8a2384fb45c`. Verificati hash del DDS e del PNG approvati, decodifica e identità dei pixel RGB. Il core risolve il riferimento esistente in `RUS.txt`. Core + Timeline risolve lo stesso file perché la Timeline dipende dal core e non sovrascrive decisione o immagine. Formato uguale a quello di icone esistenti in Victoria II e coerente con il decodificatore DDS di Alice 1.3.0. [RUS.txt](../TGC/decisions/RUS.txt#L1984) · [TGC.mod](../TGC.mod) · [Timeline 1966](../TGC_Timeline_1966.mod) · [Alice · parser](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2339-L2349) · [Alice · decodifica DDS](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/graphics/texture.cpp#L101-L180)

**Verifiche residue.** Il warning precedente è documentato nei log Alice del Task 52, riga 162 per core e 207 per core + Timeline. Resta da confermarne la scomparsa in scenari Alice 1.3.0 rigenerati da un deployment verificato con dati utente isolati. La visualizzazione effettiva in Victoria II originale resta da osservare. Il difetto è condiviso con upstream. Vale la pena proporre una patch limitata all’asset dopo la verifica in esecuzione e la conferma delle condizioni di distribuzione.

### EMPTY_ALLOW — Condizione allow vuota in Russia

**E · Bassa · P3 · Sorgenti · Motore · Entrambe.** La chiave nulla dà la stessa eleggibilità dell’assenza del blocco in Alice. Il warning del Task 32 è slittato alla riga 1991.

Decisioni. Riesaminare se cambia il consumatore di allow. Stato Registrata.

**Traccia.** 0 errori e 1 warning. Log 210. [RUS.txt](../TGC/decisions/RUS.txt#L1991) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2314-L2319) · [Alice · commands.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/commands.cpp#L2118-L2130)

### FACTORY_STATE — Presenza di fabbriche nello stato

**Rinviata · Alice 1.3.0, core e Timeline.** In scope stato, `has_building = factory` e `has_factories = yes` invocano lo stesso helper, che restituisce sempre vero. Le otto sostituzioni in 10150 e 200049 lasciano passare anche gli stati senza fabbriche. Il controllo nazionale segue un altro percorso. Victoria II 3.04 usa entrambe le forme nei dati originali, ma l'equivalenza dei due valutatori resta aperta. Riaprire quando l'helper Alice cambia o quando un confronto su Victoria II con stati equivalenti, con e senza fabbrica, dimostra una differenza utile. [Valutatori Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/triggers.cpp#L3746) · [Helper](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/economy_stats.cpp#L1281-L1289)

### CARRINGTON_SCHEDULING — Accodamento di 21501

**Rinviata · entrambi i motori, core e Timeline.** In Alice `year = 1859` e `month = 8` sono soglie minime e il passaggio AI è giornaliero. La deduplicazione considera anche destinatario e data. Un UTI idoneo può riaccodare l'evento. L'idoneità del tag senza province nello scenario effettivo e la cadenza su Victoria II 3.04 restano da dimostrare. La guardia fork `e3f8162de` può consumare il flag senza destinatari e lascia intatte le istanze già in coda nei salvataggi. Riaprire con riscontro del percorso ordinario di UTI, un caso senza potenze idonee e un salvataggio con 21501 pendente. [Coda Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/events.cpp#L460-L492) · [Serializzazione](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/serialization.cpp#L711)

### CARRINGTON_RECIPIENTS — Destinatario e filtro di 21501

**Bloccata · entrambi i motori, core e Timeline.** In upstream il modificatore segue il ciclo e colpisce il destinatario senza filtro. Nel fork `ed2717251` lo sposta nel ciclo, che per impostazione predefinita in Alice esclude il destinatario anche se idoneo. Gli script originali Victoria II 3.04 supportano la lettura di `THIS` come destinatario nel filtro di esclusione. Riaprire quando un riscontro del motore originale stabilisce come applicare un effetto condizionale al destinatario una sola volta, con casi idoneo, non idoneo e terzo paese idoneo. [Ciclo Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L323-L353) · [Scope Victoria II](https://github.com/maxioten/Victoria2-Reverse-Engineering/blob/4f71b13969fd6de2014491a737189175f7292134/Engine/triggers-and-scopes.md)

### GREAT_WAR_ALLIANCE — Rimosso il filtro obsoleto del 96025

**Risolta a livello statico · verifica runtime pendente.** Il lettore di `great_war_temp_alliance` è attestato almeno dal 2015 e compare nella storia TGC con l'importazione `4e64f2e8f` del 2020. Legacy conserva il lettore. Nei quattro profili supportati e nei dati storici ispezionati non è emerso un produttore attivo. Il core e l'overlay Extender rimuovono il solo controllo nel selettore del 96025 e il manifest registra l'impronta aggiornata. L'upstream ha già applicato la stessa rimozione in `b96f4838c`, perciò una PR sarebbe duplicata. [Attestazione del 2015](https://github.com/vic2mod/ParadoxPlazaMod/blob/24ca8dca9ab3af09e478221ef15c86947f20a4fa/ParadoxPlazaMod/events/GreatWar_Events.txt#L1823) · [Rimozione upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/b96f4838c901c106c525c23aa123100a4b40d9b1)

**Verifiche.** Il confronto statico conferma la stessa selezione a flag assente. Con il flag presente, un candidato che supera tutti gli altri filtri torna selezionabile. Il confronto byte per byte, normalizzati i fine riga, conferma che gli altri filtri, gli scope, gli inviti ripetuti e le assegnazioni e cancellazioni di `enemy_of_my_enemy` e `calling_all_allies` conservano lo stesso script. Superati il validator 1966, il drift in entrambe le direzioni senza FAIL o WARN, gli 11 test Extender e l'assemblaggio delle quattro composizioni con verifica dell'hash. Audit pari alla baseline per esiti e riepiloghi (0 FAIL, 1.828 WARN, 2.972 INFO). Nessuna occorrenza residua nelle sorgenti runtime. La compatibilità del cambio è sostenuta staticamente per Alice 1.3.0 e Victoria II 3.04. La deduplicazione della coda di Alice opera per evento, destinatario e data finché l'evento è in coda. La consegna in Victoria II 3.04 e il comportamento delle istanze pendenti non sono stati verificati in gioco. [Coda Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/events.cpp#L460-L492)

**Runtime pendente.** Restano da verificare il caricamento dei profili, gli inviti già pendenti e la riapertura di salvataggi precedenti della stessa composizione, inclusi eventuali salvataggi o dati esterni che forniscano il flag. Non è stato individuato un ambiente già verificato con isolamento sia dell'installazione sia dei dati utente. Le questioni generali sugli inviti duplicati restano fuori da questa correzione.

### LTU_CORE_CLEANUP — Ordine della pulizia SIC e PAP

**Irrisolta · core e Timeline · Victoria II 3.04 e Alice 1.3.0.** La decisione LTU `question_of_language` chiama 10417. Nell'opzione C, il ramo globale per SIC assente visita le province con core SIC e rimuove invece PAP, anche quando PAP esiste. La variante fork `0500fc93e` rimuove SIC ma lo fa prima del ramo che usa quel core per assegnare un core LTU alle province possedute. Il ramo globale adiacente per PAP assente può già eliminare allo stesso modo l'input della conversione PAP.

Il primo modello statico ha confrontato 24 casi con core solo SIC, solo PAP o sovrapposti, proprietà LTU o di terzi, e ciascun tag presente o assente. La sostituzione fork cambia sette esiti nel modello. Per esempio, con SIC assente una provincia LTU con solo core SIC perde il titolo senza ricevere il core LTU. Su territorio terzo con entrambi i core e PAP presente, upstream toglie PAP mentre la variante fork conserva PAP e toglie SIC. Alice usa identità anche per tag senza terra e copia la lista dei core prima di applicare gli effetti. Gli script originali Victoria II mostrano `all_core` con `remove_core`. Resta da confermare l'esecuzione del ramo con tag senza terra in 3.04. Nessuna prova in gioco è stata eseguita.

Il riesame U8 ha esteso il confronto a 48 casi, includendo l'assenza di una provincia LTU da selezionare e la conservazione di un core estraneo. Sette esiti differiscono tra upstream e fork. La politica approvata per il fork converte i core SIC/PAP sulle province LTU prima della pulizia, conserva la rimozione globale dei core residui dei tag estinti e lascia intatti proprietà, diplomazia e core estranei.

**Correzione sospesa.** Il modello U9 sposta i due blocchi di pulizia subito dopo le rispettive conversioni e ottiene i core previsti in 48 casi. Cinque esiti differiscono dal fork corrente. La selezione casuale serve come ingresso alla conversione dell'intero insieme posseduto. Quando la conversione prima saltava, il riordino può ora consumare uno o due estratti in più: sei casi con uno, uno con due. In Alice 1.3.0 ogni `random_owned` riuscito avanza l'indice casuale degli effetti successivi. Il modello a più province conferma la variazione della traccia anche a parità di core finali. Il riordino resta da verificare su Victoria II 3.04 per l'esecuzione del tag senza terra, la mutazione della lista di core durante `all_core` e l'effetto sulle selezioni successive. Riaprire con riscontro 3.04 su tag presenti e assenti, core sovrapposti, province LTU e terze e confronto della traccia casuale. Valutare un percorso equivalente se il riordino cambia effetti estranei. Core e Timeline ereditano gli stessi script. Nessuna modifica al gameplay o verifica in gioco.

**Alternativa U10 rinviata.** Il filtro `NOT = { owned_by = LTU }` nei due `all_core` lascia i blocchi nella posizione originale. Nei 48 casi modellati riproduce i core finali del riordino U9. Rispetto al fork corrente aggiunge un'estrazione in sei casi e due in uno. La traccia differisce dal riordino in otto casi. In Alice i selettori successivi possono cambiare provincia di ingresso, mentre la conversione modellata raggiunge lo stesso insieme LTU. Su Victoria II 3.04 resta da verificare il percorso con tag SIC/PAP senza terra, filtro di proprietà letterale negato e rimozione durante `all_core`. Entrambe le alternative restano rinviate. Riaprire solo con evidenza nuova e sostanziale sull'esecuzione del motore. [Filtro Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L970-L1015) · [Valutazione proprietà](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/triggers.cpp#L2083-L2086) [Decisione](https://github.com/The-Grand-Combination/The-Grand-Combo/blob/4661c1b5a7d24f6b658e14caf69245e6043355ee/TGC/decisions/FranceExtra.txt#L1264-L1287) · [Evento](https://github.com/The-Grand-Combination/The-Grand-Combo/blob/4661c1b5a7d24f6b658e14caf69245e6043355ee/TGC/events/FRAFlavourExtra.txt#L802-L937) · [Iterazione Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L970-L1015)

## Ricerca, economia e unità

Le schede sui modificatori condividono il controllo dello scope del parser Alice. Conservano firme distinte per consentire verifiche mirate sul consumatore di ciascun campo.

### TECH_AI — Condizione AI nel contesto errato

**Mitigata · Media · P2 · Sorgenti e Dati · Timeline.** Alice 1.3.0 segnala e scarta `is_greater_power = yes` al livello principale di `ai_chance`, dove la grammatica non ammette trigger. In `experimental_radar` la condizione è stata spostata subito dopo `factor = 2` nel primo `modifier`. Il bonus regionale di quel blocco è così riservato alle grandi potenze. Il confronto statico conferma che l'intero `ai_chance` coincide con quello di `advanced_radar_applications` e che gli altri coefficienti e trigger sono preservati. [army_tech.txt](../TGC_Timeline_1966/technologies/army_tech.txt#L4657) · [Grammatica Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L652-L661) · [Compilazione del modifier](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.cpp#L921-L950)

**Compatibilità statica.** Alice 1.3.0 accetta la forma corretta e usa il proprio `ai_weight` per scegliere la ricerca, senza consultare `ai_chance`. Gli script originali di Victoria II 3.04 attestano il trigger dentro un `modifier` tecnologico. L'esecuzione e il trattamento della forma malformata in Victoria II restano non verificati. Validator 1966, audit (0 FAIL, 1.830 WARN, 2.974 INFO) e drift inverso (0 FAIL, 0 WARN) completati. La tecnologia è specifica della Timeline. [Selettore Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/ai/ai_campaign.cpp#L115-L255)

**Verifica residua per la chiusura.** Il log storico, riga 7, riporta un errore e zero warning per questa scheda. L'installazione Alice disponibile è condivisa con Steam e manca un ambiente verificato per isolare gli output utente. Resta da confermare l'assenza della firma nel nuovo log di uno scenario core + Timeline rigenerato con Alice 1.3.0 dopo un deployment verificato. I controlli statici 1966 non coprono il parser di `ai_chance`.

### SCHOOL — Scuola culturale senza definizione

**Corretta e verificata staticamente, runtime pendente.** La scuola `culture_tech_school` esisteva in Victoria II e in TGC. Upstream ha trasferito le specializzazioni ai modificatori nazionali, lasciando lo slot delle scuole ai titoli, e ha sostituito lo stesso trigger con `has_country_modifier = ts_culture` in due invenzioni culturali del core. [Precedente upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/c80d3e98d1cc915f9d8171c1990f5913d070e593)

In `chicago_school`, `modern_primary_education`, `modern_secondary_education` e `professional_educators` la Timeline ora usa `has_country_modifier = ts_culture` con `factor = 1`. Il bonus intenzionale è di +1 punto percentuale per le nazioni idonee con il modificatore culturale. Prima Alice 1.3.0 scartava la condizione sconosciuta e saltava il segmento, con quattro errori di compilazione (log 29–32). Requisiti, base, altri modifier ed effetti restano invariati. [Script Timeline](../TGC_Timeline_1966/inventions/NEW_culture_inventions.txt#L137) · [Scope della probabilità in Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/cultures_parsing.cpp#L568-L571) · [Somma dei fattori](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/triggers.cpp#L5892-L5905)

**Validazione.** Validator strutturale 1966 superato. Audit invariato rispetto a `3d2ea2edd` (0 FAIL, 1.828 WARN, 2.974 INFO). Drift superato nei due sensi con `--fail-on-warn`, con 0 FAIL e 0 WARN in entrambi. Gli inventari di `core` e `core+extender` escludono il file, quelli di `core+1966` e `core+extender+1966` selezionano la sorgente canonica con le quattro sostituzioni. Superati gli 11 test dei profili Extender e `git diff --check`. La ricerca nelle tre sorgenti runtime non trova più il riferimento obsoleto. Restano da rigenerare lo scenario Alice 1.3.0 in un ambiente con dati utente isolati e da verificare le probabilità in Victoria II 3.04, anche con Loader. La patch riguarda soltanto la Timeline del fork.

### TEXTILE — Merci industriali inesistenti

**Corretta tramite scorporo e verificata staticamente · Media · P2 · Dati · Timeline.** La mod storica `Test` aveva una filiera di tappeti e tessili per la casa con le merci `regular_textile` e `luxury_textile`, fabbriche, produzioni artigianali e domanda POP dedicate. Il fork importò nel 2024 `perfected_power_loom` e `mechanized_tufting_machine` con due bonus industriali da +0,05 ciascuna, senza le relative merci e fabbriche. Il file delle invenzioni passò poi alla Timeline 1966. [Importazione 2024](https://github.com/Dumcem/The-Grand-Combo/commit/2d15c2d71fc3f0654983598ade2ebbb6fb14a5a8) · [Split Timeline](https://github.com/Dumcem/The-Grand-Combo/commit/c5ae7219aec87ba5c35388bc51bd9892fa4cb0dd)

La decisione di progetto rinvia l'integrazione della filiera. La Timeline rimuove entrambe le invenzioni e le loro quattro chiavi di localizzazione. La Timeline rimuove anche le due stringhe Bigelow, prive di consumatori. L'archivio storico `Legacy/TestTGCExtension/Test` conserva le invenzioni originali e le loro dipendenze per un eventuale progetto separato, ancora da approvare.

**Verifica statica.** La scansione dei quattro profili non ha trovato consumatori delle invenzioni rimosse. L'assemblaggio conferma che i profili senza Timeline sono identici e che i profili con Timeline perdono solo i due blocchi e le quattro stringhe. Le altre invenzioni sono identiche. In Alice 1.3.0 i quattro errori storici `Invalid commodity` (log 33–36) scendono da 4 a 0 in previsione statica. Validator 1966 superato. Audit da 0 FAIL, 1.828 WARN, 2.974 INFO a 0 FAIL, 1.828 WARN, 2.972 INFO. Drift con `--fail-on-warn` superato in entrambe le direzioni. [Lookup delle merci in Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L1715-L1725)

**Runtime pendente.** Rigenerare lo scenario Timeline in Alice 1.3.0 da un deployment verificato in ambiente isolato e controllare il log. Verificare l'avvio della Timeline su Victoria II 3.04, anche con Loader. Alice salva le invenzioni attive per ID e controlla il checksum dello scenario durante il caricamento. La riapertura di salvataggi precedenti con lo scenario rigenerato, e la gestione delle invenzioni rimosse nei salvataggi Victoria II, restano da verificare.


### NAV_ORG — Organizzazione navale negli effetti unità

**A · Media · P2 · Sorgenti · Motore · Timeline.** Nove naval_organisation in navy_base sono scartati. default_organisation ha una rappresentazione distinta.

Progressione navale. Riesaminare con modifica di schema o consumatore. Ripristino subordinato a equivalenza di campo, scope e valori.

**Traccia.** 9 errori e 0 warning. Log 8, 10–11, 13–18. [navy_tech.txt](../TGC_Timeline_1966/technologies/navy_tech.txt#L3584) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890) · [Alice · culture.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/culture/culture.cpp)

### BLOCKADE — Efficienza del blocco navale ignorata

**A · Media · P2 · Sorgenti · Motore · Timeline.** Sei assegnazioni, tre in scope unità e tre a livello di effetto invenzione, sono scartate da parser distinti.

Logistica navale. Riesaminare se cambia uno dei due parser o il consumatore. Ripristino subordinato a prova per ciascuna forma.

**Traccia.** 6 errori e 0 warning. Log 9, 12, 38, 47–49. [NEW_navy_inventions.txt](../TGC_Timeline_1966/inventions/NEW_navy_inventions.txt#L167) · [navy_tech.txt](../TGC_Timeline_1966/technologies/navy_tech.txt#L3585) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L1791-L1807)

### NAV_ATTR — Attrito navale nell’invenzione ignorato

**A · Media · P2 · Sorgenti · Motore · Timeline.** naval_attrition in navy_base viene scartato e non modifica l’attrito da quella invenzione.

Logistica navale. Riesaminare con supporto nello scope corretto e prova sull’attrito applicato.

**Traccia.** 1 errori e 0 warning. Log 37. [NEW_navy_inventions.txt](../TGC_Timeline_1966/inventions/NEW_navy_inventions.txt#L127) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890)

### UNIT_BASKET — Paniere di rifornimento da invenzione

**A · Media · P2 · Sorgenti · Motore · Timeline.** Quattro supply_cost nei modificatori unità vengono scartati. Alice usa il paniere base e lo scala con supply_consumption, che non cambia il mix di merci.

Logistica militare. Riesaminare se il motore applica panieri da invenzione. Ripristino subordinato alla verifica del mix.

**Traccia.** 4 errori e 0 warning. Log 19–22. [NEW_army_inventions.txt](../TGC_Timeline_1966/inventions/NEW_army_inventions.txt#L216) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L528) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890) · [Alice · economy.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/economy.cpp#L1058-L1066)

### UNIT_MORALE — Morale per unità ignorato

**A · Media · P2 · Sorgenti · Motore · Timeline.** Quattro effetti morale in scope unità non arrivano alle statistiche Alice.

Progressione militare. Riesaminare se il campo raggiunge il consumatore per unità. Conservare ampiezza e semantica originali.

**Traccia.** 4 errori e 0 warning. Log 23, 25–26, 28. [NEW_army_inventions.txt](../TGC_Timeline_1966/inventions/NEW_army_inventions.txt#L1327) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890)

### UNIT_REINF — Rinforzi per unità ignorati

**A · Media · P2 · Sorgenti · Motore · Timeline.** Due reinforce_rate in scope unità sono scartati. Il campo nazionale ha una platea diversa.

Logistica militare. Riesaminare se viene implementato un consumatore per unità. Il ripristino richiede equivalenza dello scope.

**Traccia.** 2 errori e 0 warning. Log 24, 27. [NEW_army_inventions.txt](../TGC_Timeline_1966/inventions/NEW_army_inventions.txt#L1367) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L210-L215) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890)

### UNIT_STRENGTH — Forza massima ignorata

**A · Media · P2 · Sorgenti · Motore · Timeline per gli errori, entrambe per lo scarto silenzioso.** Quattro max_strength in modificatori d’invenzione sono scartati. Nelle definizioni base Alice scarta il campo in silenzio, in 21 unità core e 23 con Timeline.

Unità e combattimento. Riesaminare parser e limite di forza effettivo. Ripristino subordinato a prova senza compensazioni con hull.

**Traccia.** 4 errori e 0 warning. Log 39, 41, 43, 45. [NEW_navy_inventions.txt](../TGC_Timeline_1966/inventions/NEW_navy_inventions.txt#L250) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L542) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890)

### UNIT_WEIGHT — Pesi dichiarati ignorati

**A · Media · P2 · Sorgenti · Motore · Timeline per gli errori, entrambe per lo scarto silenzioso.** Quattro weighted_value in modificatori d’invenzione sono scartati. Nelle definizioni base lo scarto è silenzioso, in 21 unità core e 23 con Timeline.

Unità e AI. Riesaminare se il peso raggiunge un consumatore. Conservare l’intento originale prima di cambiare la selezione.

**Traccia.** 4 errori e 0 warning. Log 40, 42, 44, 46. [NEW_navy_inventions.txt](../TGC_Timeline_1966/inventions/NEW_navy_inventions.txt#L251) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L542) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L869-L890)

### STEAM — Chiave steam nelle definizioni navali

**C · Bassa · P3 · Sorgenti · Motore · Timeline. Corretta e verificata staticamente, runtime pendente.** Eliminate le due direttive `steam = yes` da [aircraftcarrier.txt](../TGC_Timeline_1966/units/aircraftcarrier.txt) e [submarine.txt](../TGC_Timeline_1966/units/submarine.txt). Il confronto con il genitore conserva tutti i 28 campi rimanenti per unità, compresi i blocchi di merci e le classi `big_ship` e `light_ship`. Verificati i riferimenti a modelli, animazioni, suoni e invenzioni di sblocco.

**Alice 1.3.0.** Lo schema delle unità omette `steam`. Il parser segnala la chiave sconosciuta senza assegnare alcun valore alla definizione. La rimozione elimina in previsione statica i due errori storici (log 5–6, zero warning) e conserva i dati usati dal motore. Lo schema separato degli edifici riconosce e scarta la chiave. [Schema unità](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L558) · [Schema edifici](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L271-L285) · [Gestione chiavi sconosciute](https://github.com/schombert/Project-Alice/blob/v1.3.0/ParserGenerator/parser_generator.cpp#L805-L845)

**Victoria II 3.04.** Il binario originale esaminato registra il token generale `steam` (`0x0A5A`). Il controllo mirato non ne ha dimostrato l'uso nel lettore delle unità. Le 21 definizioni vanilla effettive di HoD 3.04, compreso `steam_transport`, funzionano senza la chiave, che compare invece in `common/buildings.txt` per `steamer_shipyard`. La parità per le due unità Timeline è attesa e resta da dimostrare.

**Validazione.** Validator strutturale 1966 superato. Audit sul genitore 0 FAIL, 1.830 WARN, 2.974 INFO. Dopo la correzione 0 FAIL, 1.828 WARN, 2.974 INFO. I due warning rimossi riguardavano `steam`. Drift con `--fail-on-warn` superato in entrambe le direzioni. Gli inventari di `core` e `core+extender` escludono entrambe le unità. `core+1966` e `core+extender+1966` includono le definizioni corrette. Superati gli 11 test dei profili Extender e `git diff --check`.

**Runtime residuo.** Rigenerare lo scenario Alice `core+1966` da un deployment verificato in un ambiente con installazione e dati utente isolati. Confermare l'assenza delle due firme nel log e la registrazione delle unità. Confermare la parità su Victoria II 3.04 con Timeline, anche nel profilo Loader. L'installazione Steam condivisa è stata esclusa dall'esecuzione.

**Upstream.** Nessuna candidatura per queste due rimozioni. Le definizioni interessate appartengono alla Timeline del fork e sono assenti nell'upstream verificato a `4661c1b5a`.

### ARTILLERY — Riconoscimento dell’artiglieria per nome

**E · Bassa · P3 · Sorgenti · Motore · Entrambe.** Il fallback assegna l’ID artillery e unit_type support resta valido. Nessuna perdita funzionale accertata dal fallback.

Unità terrestri. Riesaminare solo se cambia il criterio di selezione o il consumatore. Stato Registrata.

**Traccia.** 0 errori e 1 warning. Log 208. [artillery.txt](../TGC/units/artillery.txt) · [Alice · military_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/military_parsing.cpp#L90-L121) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L2846-L2853)

## Workaround navali

**Stato Mitigata · gravità Alta per pacchetti completi, Media per i soli rami navali · blocco No · P2 · evidenza Sorgenti e Dati.** Area eventi e decisioni navali, entrambe le composizioni. In Alice 1.3.0 i quattro handler di `sub_unit` non creano unità. Le guardie evitano costi o effetti accoppiati a una consegna impossibile. In Victoria II originale, con il flag `project_alice` assente, i percorsi sotto conservano gli effetti e l’ordine originali. Il confronto è statico. Il Task 36 verifica il caricamento dello scenario, mentre la consegna in partita resta da provare.

| ID e percorso | Chiamate | Disponibilità su Alice 1.3.0 | Victoria II e verifica specifica prima del ripristino |
| --- | ---: | --- | --- |
| SUB_AI_GP · `ai_give_warships_steamer` in [3_Clean-Up](../TGC/decisions/3_Clean-Up.txt) | 45 | Pacchetto AI per grandi potenze ed EIC escluso nel `potential`. Addebiti, consegna e cooldown restano accoppiati. | Conservati tutti i rami, la selezione e gli effetti. Verificare requisiti di grande potenza/EIC, costi, cooldown e quantità effettive. |
| SUB_AI_SP · `ai_give_warships_steamer_secondary_power` in [3_Clean-Up](../TGC/decisions/3_Clean-Up.txt) | 14 | Pacchetto AI per potenze secondarie escluso prima degli effetti. | Conservati tutti i rami originali. Verificare requisiti delle potenze secondarie, addebiti, cooldown e consegna. |
| SUB_FRA · `ai_french_west_africa` in [France](../TGC/decisions/France.txt) | 11 | Restano effetti coloniali, flag una tantum e riduzione d’infamia alle condizioni AI originali. La guardia salta i trasporti. | Conservati concessione e ordine originali. Verificare destinatario, porto, infamia ed effetti coloniali una sola volta. |
| SUB_SWE · `svenska_pansarbats_foreningen` in [SWE](../TGC/decisions/SWE.txt) | 1 | Decisione esclusa prima del prelievo dai risparmi dei POP e degli effetti del pacchetto. | Conservati prelievo, condizioni e concessione. Verificare la sorgente dei fondi e la consegna nel porto previsto. |
| SUB_FISH · `conscript_fishermen` in [UncivFlavor](../TGC/decisions/UncivFlavor.txt) | 2 | Decisione esclusa prima dell’addebito di 10.000, delle penalità e del cooldown condiviso di 3.650 giorni. | Conservato il pacchetto. Verificare penalità, flag, costo, cooldown e consegna di entrambe le unità. |
| SUB_BEIYANG · [Decisione](../TGC/decisions/China.txt) ed [eventi 99951–99953](../TGC/events/China.txt) | 7 | Resta la modernizzazione. Il contratto estero, l’accredito di 50.000 al fornitore, l’addebito di 80.000 a Qing e la consegna sono esclusi. Gli eventi già in coda possono mostrare il testo. | Conservati attori, condizioni, province, tempi ed effetti originali. Verificare sia la catena nuova sia ciascuna opzione accodata, con gli stessi soggetti, importi e sette unità. |
| SUB_EIC · evento 9990013 in [EIC](../TGC/events/EIC.txt) | 50 | Restano il trasferimento di Ceylon e gli sviluppi successivi. Il ramo navale a Colombo è escluso. | Conservati trasferimento e flotta. Verificare rilascio e acquisizione territoriale, ordine, porto e consegna delle 50 unità. |
| SUB_JAP · `imperial_japanese_navy` in [JAP](../TGC/decisions/JAP.txt) | 16 | Esclusi pacchetto, costo di 80.000 e benefici. Restano ricerca ordinaria e *Line of Advantage*. | Conservato il pacchetto originale. Verificare ricerca, effetti portuali e diplomatici e concessione, oltre alla decisione indipendente. |
| SUB_RUS · `russian_navy_reforms` in [RUS](../TGC/decisions/RUS.txt) | 20 | Esclusi pacchetto, costi e benefici. Restano ricerca ordinaria e riforma autonoma dell’esercito. | Conservato il pacchetto originale. Verificare rami AI/giocatore, costi di 100.000/150.000, tecnologie, benefici e riforma indipendente. |
| **Totale per composizione** | **166** | **Nove percorsi** | Il profilo Timeline usa gli stessi file core. |

Origine delle guardie nei commit [3dadb6622](https://github.com/Dumcem/The-Grand-Combo/commit/3dadb66229261876b8b5eba463f52d8e21d9d9fe), [7696c503a](https://github.com/Dumcem/The-Grand-Combo/commit/7696c503a9a984aa6e48a6b02ebfa4a8f9418613) e [8ccb9326d](https://github.com/Dumcem/The-Grand-Combo/commit/8ccb9326db0bbeef603b17405a9bf84e6e2abe7b). Il contratto e la distinzione fra guardie d’ingresso e guardie nelle opzioni sono descritti nell’[audit tecnico](../TGC/docs/1966_balance_audit.md#alice-130-naval-construction-and-scripted-grants). [Handler Alice 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L4365-L4380)

**Condizione comune di riesame per ogni percorso.** L’implementazione effettiva di `sub_unit` o di un equivalente può rendere superflua la guardia. Verificare quantità, tipi, provincia, proprietario, scope, fallimenti parziali e comportamento con gli eventi già in coda. Confrontare i rami V2 con i blocchi pre-guardia e ripetere le regressioni dei [Task 34](../tools/tests/test_task34_naval.py) e [Task 35](../tools/tests/test_task35_sub_unit.py) in entrambe le composizioni, con controlli drift e validator/auditor dove richiesti da [AGENTS.md](../AGENTS.md). Dopo deployment controllato, rigenerare lo scenario Alice della baseline adottata e verificare caricamento e semantica dei percorsi. Il ripristino resta candidato e richiede una decisione esplicita per ciascun ramo.

## Questioni rinviate

| ID e area | Gravità, blocco e priorità | Evidenza, decisione aperta e condizione di riesame |
| --- | --- | --- |
| NAVAL_AI · portaerei e selezione AI | Alta condizionata allo scenario di ricerca · No · P2 · Rinviata | **Sorgenti**, Alice 1.3.0, criterio in entrambe le composizioni e concorrenza della portaerei nella Timeline. Per le nuove costruzioni Alice sceglie una classe per categoria usando lo scafo base e poi verifica il porto, senza un secondo candidato. Nello scenario con tutte le classi attive, scafo 65 perde contro 70 e 80 anche con porto 7. Il refit usa criteri diversi. La composizione delle flotte in partita e il confronto V2 restano aperti. Riesaminare nel workstream navale o quando cambia la selezione, con una decisione su varietà delle flotte e ruolo delle categorie. [Diagnostica AI](../TGC/docs/1966_balance_audit.md#alice-naval-ai-selection-diagnostics) |
| NAVAL_TIMING · costruzione e logistica navale | Media · No · P2 · Rinviata | **Sorgenti**, Alice 1.3.0, entrambe. La curva provvisoria conserva il tempo base 90 e porta i tempi nazionali dei trasporti a 45/35 con tutti gli effetti diretti. Questi valori regolano l’approvvigionamento. La consegna dipende anche dalla soglia di 90 giorni dall’accodamento, dalla posizione e dalle merci. Tempi effettivi, capacità produttiva e formula V2 restano aperti. Riesaminare quando si calibra la progressione navale o cambia il consumatore Alice, mantenendo la positività e verificando la coda. [Curva provvisoria](../TGC/docs/1966_balance_audit.md#provisional-transport-production-curve) · [Contratto di costruzione](../TGC/docs/1966_balance_audit.md#alice-130-naval-construction-and-scripted-grants) |
| ALICE_REMAINING · compatibilità residua dei campi | Media · No · P2 · Aperta | **Sorgenti e Dati**, Alice 1.3.0, entrambe. Oltre ai campi già schedati in UNIT_STRENGTH e UNIT_WEIGHT, lo schema scarta silenziosamente `priority` in 21 unità core e 23 con Timeline, e `limit_per_port` in 10 e 12. Altri casi e limiti di rappresentazione sono nell’audit tecnico. Riesaminare durante il workstream unità/AI o quando cambiano parser e consumatori. Verificare l’ambito V2 prima di scegliere equivalenti e collegare qui eventuali nuovi riscontri della stessa causa. [Schema Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L542) · [Contratto applicato](../TGC/docs/1966_balance_audit.md#raw-values-versus-engine-applied-values) |
| BALANCE · bilanciamento 1836–1966 | Da stimare · No · P2 · Rinviata | **Dati**, entrambi i motori e le composizioni. Le soglie legacy sono diagnostiche normative senza validazione. Il workstream deve fondare ruoli, progressione, infrastrutture e logistica e confrontare i valori effettivamente applicati. Riesaminare quando si definiscono obiettivi e misure della progressione. Le violazioni di uno stesso criterio restano raggruppate. [Contratto legacy](../TGC/docs/1966_balance_audit.md#legacy-normative-contract) |
| CRASH_1949 · stabilità di campagna | Alta · Condizionale · P1 · Rinviata | **Aperta**. Il Project Hub registra un crash riproducibile verso fine aprile 1949. Motore, composizione, salvataggio di riferimento e causa restano da accertare nel workstream stabilità. Blocca la verifica di una campagna che lo riproduce e deve superare quella data. Riesaminare quando si recuperano condizioni minime di riproduzione o quando una verifica corrente richiede quel tratto di campagna. Fonte interna del progetto, sezione «Questioni aperte». |

## Verifiche runtime

Il checkpoint documentato dalle ricevute Steam è `608d1867d`, profilo
`core+1966`. I resoconti del medesimo checkpoint attestano la verifica
strutturale delle due installazioni Loader. L’[evidenza storica](upstream_reconciliation.md#evidenza-runtime-e-di-recupero)
copre altri assetti e rimane datata. Le differenze da recepire e le candidature
si seguono nel [registro upstream](upstream_delta_register.md).

| ID | Evidenza disponibile e condizione di riesame |
| --- | --- |
| DEPLOY_STEAM | Ricevuta e manifest del profilo condiviso. Mancano avvio e caricamento di core e Timeline sul checkpoint registrato. Servono un’area utente isolata e controllo osservabile della finestra. |
| DEPLOY_LOADER | In finestra sono documentati avvio, inizializzazione di entrambi i plugin e uso di CB e cache distinti per composizione. Avanzamento, salvataggio e riapertura sono stati osservati in un checkpoint precedente e restano da verificare su quello registrato. Riaprire il crash fullscreen se ricorre in finestra o se lo schermo intero diventa un requisito. |
| DEPLOY_ALICE | Gli otto scenari preesistenti e la diagnostica risultano preservati nel resoconto. Mancano due scenari generati da questo deployment e il loro caricamento. Riprendere quando Documenti, AppData e gli altri output possono essere isolati o recuperati con una procedura verificata. Il guasto intermittente JIT Windows rimane aperto separatamente. |
| TEMPERANCE | Gli ID 180–191 preservano i riferimenti. Servono salvataggi con eventi già pendenti per valutare la compatibilità oltre l’avvio. |
| SONDERBUND | `bf55d38a2` preserva le risposte registrate in aggiunta alla guardia per destinatario. Alice 1.3.0 scrive il flag prima di accodare e ricontrolla il trigger al dispatch. Il singolo popup pendente non è interrogabile dal percorso esaminato. Un popup anteriore alle guardie può ricomparire. Il caso è accettato senza migrazione. Resta la verifica sui due motori. [Dispatch Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/events.cpp#L200-L262) |
| DEPLOY_BILLING | Il payload include la correzione. Verificare servizi concorrenti, ripristino mensile di `override_campaigns`, arresto dopo l’ultimo servizio e assenza di doppi addebiti. Per la migrazione misurare separatamente esborso e movimento POP sui due motori, con e senza Direct Immigration e anche in assenza di destinazioni idonee. |
| LOADER_TREATY | Il caso ottomano isolato produsse 23 clausole e ne applicò 22. L’identità del termine scartato e lo stato prima della sua applicazione non furono registrati. Per attribuire la causa, osservare indice, ordine, cedente, beneficiario e stato, confrontando il termine isolato con quello dopo le mutazioni precedenti. La cessione volontaria osservata lascia aperto il costo dell’obiettivo `acquire_province` rispetto al valore nativo della provincia selezionata. |
| LOADER_PEACE | Verificare la guardia 96021 e la chiusura 96094 dopo pace generale, anche con seconda guerra aperta, più richieste per lo stesso perdente, vincitore umano con firma ritardata e 96021 già in coda. Il criterio è una sola chiusura senza consumo anticipato dei flag o cessioni duplicate. |
| LOADER_ECONOMY | Inizializzazione degli hook, ordini edilizi e ricorrenza di 53 sono osservazioni parziali. Mancano misure dei pagamenti netti per strato su checkpoint abbinati, cumulo nazionale/provinciale, soglia 1990 e isolamento dei singoli effetti di 53 dal tick ordinario. |
| USER_DATA | Il Project Hub riferisce una differenza d’impronta della cartella utente Paradox senza attribuzione. La causa e l’eventuale legame con le sessioni Loader restano indeterminati. Riesaminare con un confronto prima/dopo su un’area utente isolata. |
| PERFORMANCE | L’inizializzazione del Performance Patch è documentata. Un confronto delle prestazioni richiede sessioni comparabili. |

Per le composizioni Loader valgono i [contratti dei consumatori](deployment/script_extender_profile.md#contratti-dei-consumatori).
I [riscontri di progettazione e il piano storico](https://github.com/Dumcem/The-Grand-Combo/blob/11bab1312d7c3351b0abe5e3020596b26527c97a/docs/deployment/script_extender_task57.md#sessione-finale-unica)
conservano i casi di prova dettagliati. Riprendere solo con le condizioni di
osservabilità e isolamento pertinenti. La certificazione funzionale resta parziale.

## Manutenzione e chiusura

1. Cercare la causa prima di assegnare un ID. Accorpare le occorrenze e i sintomi della stessa causa, mantenendo gli ID esistenti e i riferimenti agli eventuali gruppi storici. Conservare nei documenti tecnici la dimostrazione estesa, con un collegamento dal registro.
2. Registrare l’osservazione, la composizione, il motore, le fonti, il grado di evidenza e la condizione di riesame. Indicare il workstream e l’attività concreta impedita quando cambia il blocco. Rivedere la priorità nel workstream alla luce di impatto, evidenza, portata, compatibilità e rischio.
3. Una release stabile di Alice, una modifica del parser o del consumatore o il ritorno al workstream può avviare un riesame. Le versioni in sviluppo possono fornire evidenza, e l’adozione di una nuova baseline resta una decisione esplicita. La versione supportata qui resta quella fissata da [AGENTS.md](../AGENTS.md).
4. Per ritirare un workaround, verificare la nuova implementazione, confrontarla con il comportamento protetto, decidere se il ripristino sia opportuno e rieseguire le regressioni su entrambi i motori. Registrare la decisione e il commit dell’intervento controllato.
5. Chiudere una voce con la prova della risoluzione o la decisione motivata, il perimetro verificato e i riferimenti pertinenti. La mitigazione mantiene la voce aperta al riesame. Un candidato upstream conserva la propria evidenza nel fork e segue la politica di [AGENTS.md](../AGENTS.md).
