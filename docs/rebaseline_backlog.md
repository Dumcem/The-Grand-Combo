# Registro della re-baseline

## Scopo e uso

Durante la re-baseline, i difetti scoperti incidentalmente vengono registrati e classificati. Si interviene immediatamente soltanto quando compromettono il lavoro corrente, l’integrità della baseline o una verifica necessaria per procedere. Gli altri vengono rinviati al workstream appropriato.

La baseline supportata è **Project Alice 1.3.0**, insieme a **Victoria II originale**. «Entrambe» indica il core e il profilo core + Timeline. L’evidenza del Task 37 proviene dal secondo profilo. Per i file core condivisi, il perimetro «entrambe» descrive la presenza dei dati, mentre frequenza ed esiti del core da solo restano da verificare. Per le voci del triage, il comportamento riportato è quello di Alice 1.3.0 e la parità con Victoria II rimane aperta. «Dati» indica una causa nei dati TGC, potenzialmente condivisa dai motori. «Motore» indica un limite verificato di Alice. «Misto» indica un’interazione fra i due.

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
| [Eventi, decisioni e mappa](#eventi-decisioni-e-mappa) | OPTIONS_AID, OPTIONS_CANAL, CANAL_CONTROL, BATTLE_EVENT, EVENT_REF, LITERACY, REG_MOD, SANTA_MOD, EVENT_ORPHAN, EVENT_DEBUG, EVENT_MILITARY, PICTURE, EMPTY_ALLOW |
| [Ricerca, economia e unità](#ricerca-economia-e-unità) | TECH_AI, SCHOOL, TEXTILE, NAV_ORG, BLOCKADE, NAV_ATTR, UNIT_BASKET, UNIT_MORALE, UNIT_REINF, UNIT_STRENGTH, UNIT_WEIGHT, STEAM, ARTILLERY |
| [Workaround navali](#workaround-navali) | SUB_AI_GP, SUB_AI_SP, SUB_FRA, SUB_SWE, SUB_FISH, SUB_BEIYANG, SUB_EIC, SUB_JAP, SUB_RUS |
| [Questioni rinviate](#questioni-rinviate) | NAVAL_AI, NAVAL_TIMING, ALICE_REMAINING, BALANCE, CRASH_1949 |
| [Residui della riconciliazione](#residui-della-riconciliazione) | Candidati upstream, simulazione condivisa, JIT Alice, Loader e prestazioni |
| [Manutenzione e chiusura](#manutenzione-e-chiusura) | Regole per aggiornamenti, revisioni del motore e chiusura |

## Provenienza del Task 37

Il [checkpoint Task 36](https://github.com/Dumcem/The-Grand-Combo/commit/8ccb9326db0bbeef603b17405a9bf84e6e2abe7b) ha generato e caricato fino alla schermata iniziale lo scenario con avvio 1836, profilo core + Timeline. Il Task 37 ha ricondotto **197 errori non fatali e 314 warning**, 466 dal core e 45 dalla Timeline, a **31 gruppi**. Il confronto con il Task 32 ha confermato tre soli spostamenti di riga, due per `literacy` in Cina e uno per `allow` vuoto in Russia. Il caricamento costituisce evidenza runtime per lo scenario. Le singole meccaniche conservano il grado di evidenza indicato sotto.

I riferimenti `log` indicano righe fisiche, a partire da 1 e con le intestazioni incluse, di `scenario_errors.txt` del Task 36, SHA-256 `be28104b020207a61e2749cb9038d7e7847020089a0bf1051ff9d6e7b4cc9a9d`. Gli intervalli sono inclusivi. Ogni occorrenza appartiene a una scheda. Una rigenerazione può produrre ordine o numeri diversi. Per confrontarla usare firma, file, ID o ambito della scheda, mantenendo il riferimento al log storico.

Le 31 schede hanno **blocco No per la re-baseline corrente** e sono **Aperte**, salvo indicazione diversa. L’assenza di una guardia documentata indica che la scheda non registra un workaround. Il riscontro di un impedimento concreto impone di registrare l’attività interessata e la prova prima di cambiare il blocco. La mitigazione di un’altra voce non modifica questo criterio.

## Ordini di battaglia e storia

Il caricatore associa un POP soldato a ogni reggimento nazionale. Elimina i reggimenti rimasti senza sorgente prima della serializzazione. OOB_NO_POP e OOB_OWNER costituiscono **135 esclusioni** distinte. OOB_SEARCH registra anche i tentativi falliti di OOB_NO_POP.

### OOB_NO_POP — Reggimenti privi di POP soldato

**A · Alta · P1 · Sorgenti · Misto · Entrambe.** 57 reggimenti senza una sorgente idonea vengono eliminati al caricamento. I 57 warning corrispondenti sono in OOB_SEARCH e rappresentano gli stessi reggimenti.

Ordini di battaglia e popolazione iniziale. Riesaminare con le fonti storiche e confrontare province, POP e composizione iniziale in entrambi i motori. Un ripristino richiede una sorgente coerente.

**Traccia.** 57 errori e 0 warning. Log 145–201. [Ordini di battaglia](../TGC/history/units), 39 file · [AGC_oob.txt](../TGC/history/units/AGC_oob.txt#L7) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2484-L2513) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3510-L3517)

### OOB_OWNER — Provincia d’origine sotto altro proprietario

**A · Alta · P1 · Sorgenti · Misto · Entrambe.** 78 reggimenti distinti da OOB_NO_POP restano senza sorgente e vengono eliminati. Alice salta la ricerca alternativa in questo ramo.

Ordini di battaglia e confini. Riesaminare quando si possono verificare proprietà, data e intenti dello schieramento. Il ripristino richiede di preservare il ruolo storico.

**Traccia.** 0 errori e 78 warning. Log 292–296, 300–301, 303, 306, 312–315, 323–324, 329, 334–341, 357, 367, 370–372, 375–376, 378–387, 394–398, 404, 406–411, 413–414, 419, 430–431, 433–436, 439–446, 459–461, 464–466, 487, 509. [Ordini di battaglia](../TGC/history/units), 38 file · [ABA_oob.txt](../TGC/history/units/ABA_oob.txt#L20) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2484-L2499) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3510-L3517)

### OOB_SEARCH — Ricerca in un’altra provincia

**D · Media · P2 · Sorgenti · Motore · Entrambe.** 140 avvisi precedono la ricerca. In 83 casi Alice associa un POP altrove e in 57 ricade in OOB_NO_POP. Il cambio di sorgente può incidere sui rinforzi.

Ordini di battaglia. Riesaminare se cambia l’algoritmo o durante il confronto delle sorgenti dei reggimenti. Parità V2 da stabilire.

**Traccia.** 0 errori e 140 warning. Log 297–299, 302, 304–305, 307–311, 316–322, 325–328, 330–333, 342–356, 358–366, 368–369, 373–374, 377, 388–393, 399–403, 405, 412, 415–418, 420–429, 432, 437–438, 447–458, 462–463, 467–476, 478, 480–486, 488–508, 510–511. [Ordini di battaglia](../TGC/history/units), 70 file · [AFG_oob.txt](../TGC/history/units/AFG_oob.txt#L74) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2495-L2513) · [Alice · military.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.cpp#L9800-L9818)

### DEAD_OOB — Ordini di battaglia di tag inattivi

**B · Bassa · P3 · Sorgenti · Misto · Entrambe.** Alice salta gli OOB di SRG, SWA e ZOU al bookmark. L’eventuale necessità di tali unità dopo la comparsa del tag resta aperta.

Storia iniziale e attivazione dei paesi. Riesaminare con date, territori e regole di attivazione o dopo una modifica del caricatore.

**Traccia.** 0 errori e 3 warning. Log 477, 479, 512. [SRG_oob.txt](../TGC/history/units/SRG_oob.txt) · [SWA_oob.txt](../TGC/history/units/SWA_oob.txt) · [ZOU_oob.txt](../TGC/history/units/ZOU_oob.txt) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3314-L3346)

### INVALID_HISTORY — Storia paese senza tag definito

**C · Bassa · P3 · Dati · Dati · Entrambe.** I file di CIV, UCV, VLP, VNG, VNS e VOP esistono senza una voce attiva nella tabella paesi. Alice li salta.

Storia e paesi. Verificare la disattivazione storica dei tag prima di recuperare o archiviare le definizioni.

**Traccia.** 0 errori e 6 warning. Log 513–518. [Storia paesi](../TGC/history/countries) · [countries.txt](../TGC/common/countries.txt) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L3386-L3411)

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

**C · Bassa · P3 · Sorgenti · Dati · Entrambe.** 20 coppie condizione/rimozione in eventi di rivoluzione puntano a un modificatore senza definizione. Alice omette entrambe. Impatto di una reggenza attiva da stabilire.

Governi e rivoluzioni. Riesaminare quando si trova una definizione storica e il relativo produttore o si rivedono i rami teocratici.

**Traccia.** 40 errori e 0 warning. Log 52–53, 56–57, 60–61, 64–65, 68–69, 72–73, 76–77, 80–81, 84–85, 88–89, 92–93, 96–97, 100–101, 104–105, 108–109, 112–113, 116–117, 120–121, 124–125, 128–129. [Revolution_Event_Theocracy.txt](../TGC/events/Revolution_Event_Theocracy.txt#L41) · [Alice · trigger_parsing.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.hpp#L3478-L3498) · [Alice · effect_parsing.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/effect_parsing.hpp#L1999-L2015)

### SANTA_MOD — Rimozione di santa_ana_rule

**C · Bassa · P3 · Sorgenti · Dati · Entrambe.** 20 coppie condizione/rimozione puntano a un modificatore senza definizione. Il flag messicano ha semantica distinta da questo modificatore e da BATTLE_EVENT.

Governi e rivoluzioni. Riesaminare se emerge la definizione o l’intento originale della pulizia.

**Traccia.** 40 errori e 0 warning. Log 54–55, 58–59, 62–63, 66–67, 70–71, 74–75, 78–79, 82–83, 86–87, 90–91, 94–95, 98–99, 102–103, 106–107, 110–111, 114–115, 118–119, 122–123, 126–127, 130–131. [Revolution_Event_Theocracy.txt](../TGC/events/Revolution_Event_Theocracy.txt#L52) · [Alice · trigger_parsing.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.hpp#L3478-L3498) · [Alice · effect_parsing.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/effect_parsing.hpp#L1999-L2015)

### EVENT_ORPHAN — Eventi definiti senza ingresso verificato

**F · Da stimare · P3 · Aperta · Misto · Entrambe.** 48 definizioni risultano assegnate ma non elaborate nel registro Alice. Raggiungibilità e intenzione dei singoli ingressi restano aperte.

Eventi per regione. Riesaminare al ritorno su ciascuna catena o dopo cambi di registrazione. Verificare ingressi attivi prima di ripristinarli.

**Traccia.** 0 errori e 48 warning. Log 211–221, 236–251, 253–256, 273–288, 291. [AUSFlavor.txt](../TGC/events/AUSFlavor.txt#L2638) · [Archaeology.txt](../TGC/events/Archaeology.txt#L3349) · [BRZFlavor.txt](../TGC/events/BRZFlavor.txt#L5731) · [CBsAndCores.txt](../TGC/events/CBsAndCores.txt#L1333) · [GEF Events.txt](../TGC/events/GEF%20Events.txt#L3256) · [Germany VS Hungary Events.txt](../TGC/events/Germany%20VS%20Hungary%20Events.txt#L240) · [JANFlavor.txt](../TGC/events/JANFlavor.txt#L3536) · [MEXFlavor.txt](../TGC/events/MEXFlavor.txt#L762) · [POLFlavor.txt](../TGC/events/POLFlavor.txt#L445) · [RUSFlavor.txt](../TGC/events/RUSFlavor.txt#L789) · [SPAFlavor.txt](../TGC/events/SPAFlavor.txt#L4251) · [SlaveryEvents.txt](../TGC/events/SlaveryEvents.txt#L195) · [USA_Minors.txt](../TGC/events/USA_Minors.txt#L2431) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408)

### EVENT_DEBUG — Eventi di debug fuori dal flusso ordinario

**E · Bassa · P3 · Dati · Dati · Entrambe.** 14 eventi di test sono a invocazione esplicita. Impatto sul gioco ordinario assente per il perimetro esaminato. Disponibilità da console aperta.

Debug. Riesaminare se si verifica la console o cambia il caricatore. Stato Registrata.

**Traccia.** 0 errori e 14 warning. Log 222–235. [Debug.txt](../TGC/events/Debug.txt#L6) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408)

### EVENT_MILITARY — Circuito di ingaggio di comandanti inattivo

**B · Media · P2 · Dati · Dati · Entrambe.** I 16 eventi 10000105–10000120 si richiamano internamente e l’ingresso identificato è commentato. Un eventuale ripristino riattiverebbe costi e acquisizione di leader.

Leader ed eventi militari. Riesaminare quando si decide se il circuito debba tornare disponibile. Verificare altri ingressi e V2.

**Traccia.** 0 errori e 16 warning. Log 257–272. [Military.txt](../TGC/events/Military.txt#L1518) · [Alice · nations_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/nations_parsing.cpp#L1391-L1408)

### PICTURE — Immagine di form_soviet_union assente

**C · Bassa · P3 · Sorgenti · Dati · Entrambe.** Il parser cerca DDS, TGA e PNG e omette la risorsa assente. Il problema osservato è di presentazione.

GUI e asset. Riesaminare alla revisione della decisione o se viene ritrovata la risorsa. Ripristino candidato con asset verificato.

**Traccia.** 0 errori e 1 warning. Log 209. [RUS.txt](../TGC/decisions/RUS.txt#L1984) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2339-L2349)

### EMPTY_ALLOW — Condizione allow vuota in Russia

**E · Bassa · P3 · Sorgenti · Motore · Entrambe.** La chiave nulla dà la stessa eleggibilità dell’assenza del blocco in Alice. Il warning del Task 32 è slittato alla riga 1991.

Decisioni. Riesaminare se cambia il consumatore di allow. Stato Registrata.

**Traccia.** 0 errori e 1 warning. Log 210. [RUS.txt](../TGC/decisions/RUS.txt#L1991) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L2314-L2319) · [Alice · commands.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/commands.cpp#L2118-L2130)

## Ricerca, economia e unità

Le schede sui modificatori condividono il controllo dello scope del parser Alice. Conservano firme distinte per consentire verifiche mirate sul consumatore di ciascun campo.

### TECH_AI — Condizione AI nel contesto errato

**B · Media · P2 · Sorgenti · Misto · Timeline.** is_greater_power direttamente dentro ai_chance di experimental_radar viene scartato. L’intento di filtro o di peso resta aperto.

Ricerca e AI. Riesaminare se cambia la grammatica o quando si ricostruisce l’intento. Conservare i modifier validi e verificare V2.

**Traccia.** 1 errori e 0 warning. Log 7. [army_tech.txt](../TGC_Timeline_1966/technologies/army_tech.txt#L4670) · [Alice · cultures_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/cultures_parsing.cpp#L550-L553) · [Alice · trigger_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.cpp#L921-L950) · [Alice · parsers.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers.hpp#L64-L77)

### SCHOOL — Scuola culturale senza definizione

**A · Media · P2 · Sorgenti · Dati · Timeline.** In quattro invenzioni la condizione culture_tech_school non produce un trigger. Il relativo bonus di probabilità +1 manca.

Invenzioni culturali. Riesaminare quando si identifica la scuola prevista. Il ripristino dipende da un riferimento valido con la stessa platea.

**Traccia.** 4 errori e 0 warning. Log 29–32. [NEW_culture_inventions.txt](../TGC_Timeline_1966/inventions/NEW_culture_inventions.txt#L137) · [Alice · trigger_parsing.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.hpp#L1774-L1791) · [Alice · trigger_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.cpp#L921-L936) · [Alice · system_state.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp#L1978-L1986) · [Alice · triggers.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/triggers.cpp#L5865-L5878)

### TEXTILE — Merci industriali inesistenti

**A · Media · P2 · Sorgenti · Dati · Timeline.** perfected_power_loom e mechanized_tufting_machine perdono quattro bonus +0,05 per regular_textile e luxury_textile. Il consumatore funziona con merci valide.

Economia e invenzioni. Riesaminare con fonti su tappeti e produzione tessile. Ripristino candidato solo dopo aver identificato i beni voluti.

**Traccia.** 4 errori e 0 warning. Log 33–36. [NEW_industry_inventions.txt](../TGC_Timeline_1966/inventions/NEW_industry_inventions.txt#L91) · [Alice · parsers_declarations.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers_declarations.cpp#L1715-L1725) · [Alice · culture.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/culture/culture.cpp#L655-L659) · [Alice · economy_production.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/economy_production.cpp#L890-L898)

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

**C · Bassa · P3 · Sorgenti · Motore · Timeline.** Due chiavi steam non appartengono allo schema Alice delle unità. Classi navali e merci restano disponibili. Il ruolo di steam in V2 è da accertare.

Unità navali. Riesaminare a fronte di un cambiamento di schema o di evidenza sulla meccanica V2.

**Traccia.** 2 errori e 0 warning. Log 5–6. [aircraftcarrier.txt](../TGC_Timeline_1966/units/aircraftcarrier.txt#L5) · [submarine.txt](../TGC_Timeline_1966/units/submarine.txt#L5) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L272-L285) · [Alice · parser_defs.txt](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L554)

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

Origine delle guardie nei commit [3dadb6622](https://github.com/Dumcem/The-Grand-Combo/commit/3dadb66229261876b8b5eba463f52d8e21d9d9fe), [7696c503a](https://github.com/Dumcem/The-Grand-Combo/commit/7696c503a9a984aa6e48a6b02ebfa4a8f9418613) e [8ccb9326d](https://github.com/Dumcem/The-Grand-Combo/commit/8ccb9326db0bbeef603b17405a9bf84e6e2abe7b). Il contratto e la distinzione fra guardie d’ingresso e guardie nelle opzioni sono descritti nell’[audit tecnico](../TGC/docs/1966_balance_audit.md#task-34-alice-130-naval-construction-and-scripted-grants). [Handler Alice 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L4365-L4380)

**Condizione comune di riesame per ogni percorso.** L’implementazione effettiva di `sub_unit` o di un equivalente può rendere superflua la guardia. Verificare quantità, tipi, provincia, proprietario, scope, fallimenti parziali e comportamento con gli eventi già in coda. Confrontare i rami V2 con i blocchi pre-guardia e ripetere le regressioni dei [Task 34](../tools/tests/test_task34_naval.py) e [Task 35](../tools/tests/test_task35_sub_unit.py) in entrambe le composizioni, con controlli drift e validator/auditor dove richiesti da [AGENTS.md](../AGENTS.md). Dopo deployment controllato, rigenerare lo scenario Alice della baseline adottata e verificare caricamento e semantica dei percorsi. Il ripristino resta candidato e richiede una decisione esplicita per ciascun ramo.

## Questioni rinviate

| ID e area | Gravità, blocco e priorità | Evidenza, decisione aperta e condizione di riesame |
| --- | --- | --- |
| NAVAL_AI · portaerei e selezione AI | Alta condizionata allo scenario di ricerca · No · P2 · Rinviata | **Sorgenti**, Alice 1.3.0, criterio in entrambe le composizioni e concorrenza della portaerei nella Timeline. Per le nuove costruzioni Alice sceglie una classe per categoria usando lo scafo base e poi verifica il porto, senza un secondo candidato. Nello scenario con tutte le classi attive, scafo 65 perde contro 70 e 80 anche con porto 7. Il refit usa criteri diversi. La composizione delle flotte in partita e il confronto V2 restano aperti. Riesaminare nel workstream navale o quando cambia la selezione, con una decisione su varietà delle flotte e ruolo delle categorie. [Diagnostica AI](../TGC/docs/1966_balance_audit.md#alice-naval-ai-selection-diagnostics) |
| NAVAL_TIMING · costruzione e logistica navale | Media · No · P2 · Rinviata | **Sorgenti**, Alice 1.3.0, entrambe. La curva provvisoria conserva il tempo base 90 e porta i tempi nazionali dei trasporti a 45/35 con tutti gli effetti diretti. Questi valori regolano l’approvvigionamento. La consegna dipende anche dalla soglia di 90 giorni dall’accodamento, dalla posizione e dalle merci. Tempi effettivi, capacità produttiva e formula V2 restano aperti. Riesaminare quando si calibra la progressione navale o cambia il consumatore Alice, mantenendo la positività e verificando la coda. [Curva provvisoria](../TGC/docs/1966_balance_audit.md#provisional-transport-production-curve) · [Contratto di costruzione](../TGC/docs/1966_balance_audit.md#task-34-alice-130-naval-construction-and-scripted-grants) |
| ALICE_REMAINING · compatibilità residua dei campi | Media · No · P2 · Aperta | **Sorgenti e Dati**, Alice 1.3.0, entrambe. Oltre ai campi già schedati in UNIT_STRENGTH e UNIT_WEIGHT, lo schema scarta silenziosamente `priority` in 21 unità core e 23 con Timeline, e `limit_per_port` in 10 e 12. Altri casi e limiti di rappresentazione sono nell’audit tecnico. Riesaminare durante il workstream unità/AI o quando cambiano parser e consumatori. Verificare l’ambito V2 prima di scegliere equivalenti e collegare qui eventuali nuovi riscontri della stessa causa. [Schema Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt#L512-L542) · [Contratto applicato](../TGC/docs/1966_balance_audit.md#raw-values-versus-engine-applied-values) |
| BALANCE · bilanciamento 1836–1966 | Da stimare · No · P2 · Rinviata | **Dati**, entrambi i motori e le composizioni. Le soglie legacy sono diagnostiche normative senza validazione. Il workstream deve fondare ruoli, progressione, infrastrutture e logistica e confrontare i valori effettivamente applicati. Riesaminare quando si definiscono obiettivi e misure della progressione. Le violazioni di uno stesso criterio restano raggruppate. [Contratto legacy](../TGC/docs/1966_balance_audit.md#legacy-normative-contract) |
| CRASH_1949 · stabilità di campagna | Alta · Condizionale · P1 · Rinviata | **Aperta**. Il Project Hub registra un crash riproducibile verso fine aprile 1949. Motore, composizione, salvataggio di riferimento e causa restano da accertare nel workstream stabilità. Blocca la verifica di una campagna che lo riproduce e deve superare quella data. Riesaminare quando si recuperano condizioni minime di riproduzione o quando una verifica corrente richiede quel tratto di campagna. Fonte interna del progetto, sezione «Questioni aperte». |

## Residui della riconciliazione

**Blocco di allineamento da sottoporre a decisione.** In `TGC/localisation/00_events_10000000.csv` le 15 descrizioni `EVTDESC10000106`–`EVTDESC10000120` della revisione fissata identificano per nome l'ufficiale e distinguono l'ammiraglio Jane. Il fork mostra lo stesso testo generico per tutti. I nomi rimangono nelle definizioni degli ufficiali in `TGC/events/Military.txt`, ma l'informazione è assente dalle notifiche. Il registro spiega che i testi preesistenti del fork furono conservati. La scelta va riesaminata prima della certificazione. La descrizione upstream di `10000111` chiama Ryan generale, mentre l'evento crea un ammiraglio in entrambi gli alberi. [Descrizioni upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/blob/14f2e6ff61e7e1ea07ffef07548560da5bcc47f0/TGC/localisation/00_events_10000000.csv)

Le voci della tabella seguono i rispettivi workstream senza bloccare il checkpoint upstream fissato.

| Classe Task 58 | Area e provenienza | Questione e riferimento |
| --- | --- | --- |
| B | Upstream TGC | I CB ordinari di `88604963d` e `b865278ff` e la rimozione del ramo Bhutan in `great_game_cb` sono recepiti nel core e in Extender. Restano da isolare le patch candidate sulle guardie di pace e sulle partizioni, preservandone le evidenze. [Candidati e motivazioni](upstream_reconciliation.md#task-55--preparazione-del-profilo-script-extender) |
| B | Fork e percorso condiviso | Simulazione oltre l'avvio e salvataggi con eventi Temperance pendenti ancora da verificare. [Task 52](upstream_reconciliation.md#task-52--checkpoint-runtime) |
| B | Deployment Windows | Un handle esterno persistente può impedire la sostituzione del journal. Conservare le ricevute e applicare il recupero per ID se si presenta il caso. [Procedura di recupero](deployment/local_deployment.md#rollback-and-interrupted-publication) |
| B | Alice | Guasto intermittente JIT Windows osservato anche prima del merge. La diagnosi e la prova prolungata restano nel workstream Alice 1.3.0. [Task 53](upstream_reconciliation.md#task-53--diagnosi-del-crash-alice) |
| B | Loader e integrazione Extender | Identità e causa della clausola ottomana aperte. Pagamenti POP e 1990, costo di guerra, 96021/96094 e singoli effetti dell'evento 53 richiedono il collaudo mirato. [Task 57](deployment/script_extender_task57.md) |
| C | Bilanciamento e prestazioni | La re-baseline normativa prosegue come in BALANCE. Un confronto del Performance Patch richiede una prova dedicata. [Profilo Extender](deployment/script_extender_profile.md) |

## Manutenzione e chiusura

1. Cercare la causa prima di assegnare un ID. Accorpare le occorrenze e i sintomi della stessa causa, mantenendo gli ID esistenti e i riferimenti agli eventuali gruppi storici. Conservare nei documenti tecnici la dimostrazione estesa, con un collegamento dal registro.
2. Registrare l’osservazione, la composizione, il motore, le fonti, il grado di evidenza e la condizione di riesame. Indicare il workstream e l’attività concreta impedita quando cambia il blocco. Rivedere la priorità nel workstream alla luce di impatto, evidenza, portata, compatibilità e rischio.
3. Una release stabile di Alice, una modifica del parser o del consumatore o il ritorno al workstream può avviare un riesame. Le versioni in sviluppo possono fornire evidenza, e l’adozione di una nuova baseline resta una decisione esplicita. La versione supportata qui resta quella fissata da [AGENTS.md](../AGENTS.md).
4. Per ritirare un workaround, verificare la nuova implementazione, confrontarla con il comportamento protetto, decidere se il ripristino sia opportuno e rieseguire le regressioni su entrambi i motori. Registrare la decisione e il commit dell’intervento controllato.
5. Chiudere una voce con la prova della risoluzione o la decisione motivata, il perimetro verificato e i riferimenti pertinenti. La mitigazione mantiene la voce aperta al riesame. Un candidato upstream conserva la propria evidenza nel fork e segue la politica di [AGENTS.md](../AGENTS.md).
