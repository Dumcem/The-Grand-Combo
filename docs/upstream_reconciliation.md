# Evidenze della riconciliazione upstream

Questa pagina conserva le motivazioni e le evidenze riutilizzabili dei checkpoint
chiusi. Il [registro upstream](upstream_delta_register.md) identifica il delta
corrente e il [backlog](rebaseline_backlog.md) contiene le verifiche aperte.
I risultati qui riportati appartengono ai checkpoint indicati.
Il [resoconto e l’inventario storico completi](https://github.com/Dumcem/The-Grand-Combo/blob/bf55d38a233ee6a68acba75412f97ece5154a0df/docs/upstream_reconciliation.md#inventario-del-delta-fissato)
restano disponibili in Git. I riferimenti delle PR #418–427 sono nel
[registro storico delle candidature](https://github.com/Dumcem/The-Grand-Combo/blob/bf55d38a233ee6a68acba75412f97ece5154a0df/docs/upstream_delta_register.md#primo-lotto-pubblicato-task-70b).

## Scelte di integrazione

| Caso | Evidenza da preservare |
| --- | --- |
| Menu indigeno #416 | `837a451a0` ed `e10615c65` conservano opzioni e soglie upstream, usano un flag pendente per paese e lo liberano alla risposta. I rami di riprova lo impostano prima di riaccodare. Le chance AI negano la congiunzione dei requisiti. |
| Svizzera e Anatolia | `837a451a0` limita i core LTU a province SDB effettivamente possedute da SDB, le cessioni svizzere ai proprietari previsti e la spartizione residua a GCF esistente. La cessione anatolica mantiene le esclusioni upstream e applica la relazione con GRE in scope nazionale. |
| Rotterdam | `2f8c75fc4` lega guerra, stanchezza e pace allo stesso belligerante e protegge le proprietà neutrali. L’hunk upstream `3edc1b8a9` rendeva raggiungibile la pace senza queste due garanzie. |
| Salvataggi precedenti | `e10615c65` accetta il vecchio flag nazionale di Osceola insieme a quello globale upstream. Restano i lettori di `WilhelmIV_king` e dei colori dei vassalli, la migrazione del menu 100 e gli ID 180–191 di Temperance. I popup già accodati sono un caso distinto nel backlog. |
| Geografia | Paracatu 2444 rimane nel gruppo Aw per la corrispondenza territoriale. I due gruppi climatici avevano valori identici al confronto. La provincia 2447 conserva Rio de Janeiro. |
| Loader e Performance Addon | La PR #417 fu recepita nel solo overlay Victoria II. Il vecchio addon fu ritirato al checkpoint di chiusura. La coppia residua Steam fu rimossa successivamente. I cataloghi storici restano risolvibili per digest per il recupero. |

## Verifiche mirate dei contributi

- **Scuole di ricerca.** La descrizione navale richiede `ts_naval_desc`. Il fork `9d8de29a6` usa quella chiave al posto del titolo ceco e conserva il duplicato navale. La correzione upstream cambia soltanto la chiave della riga descrittiva. Il confronto byte per byte conserva il resto del CSV Windows-1252.
- **Propaganda.** Il segno del pagamento e la soglia di cassa formano un solo contratto. `0500fc93e` corregge il segno nel fork. La fascia da 250.000 richiede anche il limite superiore di 10 milioni di POP. I controlli statici coprono 420 combinazioni e la selezione esclusiva del pagamento.
- **Fabbriche e Carrington.** Per Alice 1.3.0 occorre leggere il valutatore effettivo dopo il parser. I due predicati statali di fabbrica condividono lo stesso helper e il ciclo paese di un evento può escludere il destinatario. Le condizioni di riesame sono nel [backlog](rebaseline_backlog.md#eventi-decisioni-e-mappa). Nessuna prova in gioco è stata eseguita durante questi controlli.

- **Conversioni LTU, opzione C di 10417.** I blocchi `random_owned` selezionano una provincia di ingresso e applicano poi la conversione a tutte le province LTU con il core richiesto. In Alice, i blocchi che prima saltavano possono avanzare l'indice casuale quando la pulizia avviene dopo la conversione. La verifica dei core finali da sola non copre questa differenza. [Ordine degli effetti Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L21-L31) · [Selettore](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L886-L906)

## Riconciliazione selettiva #428–442

Il 19 novembre 2026 la punta di `master` upstream era `85f173164`. Sono stati confrontati i 15 merge con i rispettivi primi genitori e con il fork a partire da `84c4a635f`. Il [registro](upstream_delta_register.md#pr-428442-riconciliate-per-hunk) riporta ogni hunk recepito o già coperto.

- **#429 e #433.** La concessione finlandese è scritta da SWE e il controllo legge anche SCA, perché la formazione può cambiare identità allo stesso paese. Alice 1.3.0 risolve lo scope per titolare del tag, legge il flag su quel paese e, in `change_tag`, cambia l’identità del paese che esegue l’effetto. Per il Messico, il fork legge entrambe le grafie ma scrive quella minuscola già in uso. Il lettore storico copre il flag prodotto dalla versione anteriore a `850b52cfe` e ancora scritto da upstream. Alice risolve il nome letterale in un ID di flag e legge il bit relativo. Su Victoria II 3.04 l’evidenza statica è la stessa sintassi già usata dai lettori del fork e il riscontro dei produttori e delle condizioni; il comportamento del binario e la rilettura dei salvataggi restano da provare. [Scope Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/triggers.cpp#L1142-L1147) · [Cambio tag](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L1967-L1982) · [Parser del flag](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.hpp#L3089-L3106) · [Lettura del flag](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/triggers.cpp#L2138-L2140)
- **#436–438.** Le modifiche ai defines e ai modificatori sono limitate ai commenti. Il confronto dei contenuti eseguibili conserva anche la data finale distinta della Timeline. Il test del Loader mantiene il confronto byte per byte e riconosce la sola correzione del commento approvata upstream. Le sei righe Direct Immigration conservano chiavi, separatori e colonne oltre all’inglese. La guida Low RAM conserva la formulazione equivalente già presente.
- **#439–442.** L’evento 99797 mantiene entrambi i flag di esclusione e registra la risposta per entrambe le opzioni. Le quattro righe delle scuole navale e ceca coincidono con upstream. La verifica su 441 combinazioni di popolazione e cassa conferma una sola fascia e un solo addebito previsto per fascia. Gli avvisi dell’evento 100 riflettono le soglie del 20% per liberali o socialisti e del 30% per conservatori o reazionari. La correzione di Rio riguarda la chiave `PROV2447`. Le protezioni del menu del fork restano applicate.

Verificati i quattro inventari dei profili, senza pubblicare payload. I due controlli drift hanno 0 FAIL e 0 WARN. Il validator 1966 passa e l’audit restituisce 0 FAIL, 1.828 WARN e 2.972 INFO, in linea con il [checkpoint TEXTILE](rebaseline_backlog.md#textile--merci-industriali-inesistenti). Questi riscontri sono statici. L’avvio, la rigenerazione dello scenario Alice e le prove sui salvataggi restano pendenti. Le cinque correzioni residue recepite erano già upstream, quindi ulteriori PR sarebbero ridondanti.

## Integrazione Git delle PR #428–442

Il Task 7 ha recuperato `master` dall'upstream ufficiale e integrato `85f173164fe2ef635c78eac48880d79fcaa9ebd7` partendo da `a7b1aeb64913291e2d8ec0dbd6b612c52be1c994`. Il merge-base è `8f106a7f0`, già integrato da `124844576`. Il confronto con il primo genitore conferma che tutti i file tracciati al di fuori della documentazione canonica conservano gli stessi blob. L'intervallo upstream comprende 15 merge e 15 commit di contributo, distribuiti su 27 file.

| Risoluzione | Riscontro sul risultato |
| --- | --- |
| Guida Low RAM, #438 | Conservata la formulazione già riconciliata. Entrambe le versioni riportano 500 MB e la possibilità di fino a sei crash nei primi avvii. |
| Bancarotta, #430 | I tre controlli in conflitto hanno lo stesso `relation = { who = FROM value = 100 }`. Conservati anche gli effetti `is_slave` del fork nelle opzioni 70000 e 70001. |
| Sonderbund, #439 | I blocchi eseguibili di `SWIFlavor.txt` coincidono. Conservato il commento che spiega la guardia durante l'attesa della risposta. |
| Localizzazione polacca, #435 | L'unione automatica aggiungeva una seconda copia delle due righe identiche di 203903. Conservata la posizione scelta in `068c8cabf` e lasciate distinte le chiavi di 500007. |

Il confronto delle righe aggiunte e rimosse sui 27 percorsi conferma i contributi upstream, con la formulazione equivalente della guida Low RAM. Il controllo in contesto conserva le guardie finlandesi SWE e SCA, il lettore messicano `protecting_legacy_GCO` e il produttore minuscolo del fork, le guardie del menu indigeno, `PROV2447` Rio de Janeiro e `PROV1203` Osh. Le altre differenze sui file interessati riguardano commenti, codifica, formattazione o comportamenti del fork fuori dagli hunk upstream, tra cui scope di Carrington, esclusioni per Belgio e Brasilia e protezioni messicane e russe. Per le altre esclusioni e gli adattamenti restano validi il [registro](upstream_delta_register.md#eccezioni-di-contenuto-e-condizioni-di-riesame) e i [contratti Loader](deployment/script_extender_profile.md#contratti-dei-consumatori).

La suite generale supera 185 test, comprese 47 regressioni upstream. Nei quattro inventari effettivi sono univoche le 11 chiavi di localizzazione controllate, oltre alla chiave d'opzione 980005 nella composizione Direct Immigration. Il drift in entrambe le direzioni, con base `a7b1aeb64` e `--fail-on-warn`, verifica 18 percorsi con 0 FAIL e 0 WARN. Il validator 1966 verifica 25 aree, 300 occorrenze tecnologiche, localizzazione e struttura. L'intero output dell'audit è identico al pre-merge (0 FAIL, 1.828 WARN, 2.972 INFO). Le differenze di semantica Alice e le soglie di bilanciamento non validate conservano lo stato già documentato.

La suite di deployment simulato su Windows termina con 115 successi su 117 casi, inclusi gli 11 test dei profili e degli overlay. Due casi sono saltati per il privilegio Windows di creazione dei symlink. Il controllo delle junction native e quelli degli hardlink passano.

L'identità dei payload e il controllo dei confini Loader costituiscono evidenza di non regressione statica per Victoria II 3.04 e Project Alice 1.3.0. Le osservazioni in gioco disponibili sono riferite ai checkpoint precedenti. Lo scenario Alice e i salvataggi restano nel perimetro delle [verifiche runtime del backlog](rebaseline_backlog.md#verifiche-runtime). Il merge incorpora contributi già upstream, quindi una nuova PR per questo checkpoint sarebbe ridondante.

## Evidenza runtime e di recupero

- **Steam e Alice a `864c81fe8`.** Il motore originale raggiunse una finestra responsiva per core e Timeline. Alice generò entrambi gli scenari, caricò il core e caricò la Timeline in uno di tre tentativi. Gli altri due terminarono con `0xC0000409` e `IMAGE_REL_AMD64_ADDR32NB relocation requires an ordered section layout`. Il controllo con lo scenario precedente riuscì. Il difetto intermittente è localizzato nella rilocazione JIT Windows, con causa delle allocazioni e correzione ancora aperte. I diagnostici furono 150 errori non fatali e 314 avvisi per core, 195 e 314 per Timeline. I 197 errori Timeline appartengono a un checkpoint anteriore.
- **Recupero Windows.** Un handle esterno aperto ha riprodotto il rifiuto di sostituzione del journal. Dopo il rilascio, il recupero per ID ha ripristinato byte e ownership, conservando i file estranei. L’esperimento dimostra il meccanismo riprodotto. L’origine dell’episodio spontaneo resta indeterminata. La [procedura di recupero](deployment/local_deployment.md#rollback-and-interrupted-publication) è il riferimento operativo.
- **Loader 3.0.0.** La [prova isolata con solo Script Extender](https://github.com/Dumcem/The-Grand-Combo/blob/798eaab6ea10cd879e1517571d72561953bcbe3b/docs/deployment/script_extender_task56.md#risultati-in-partita) osservò cessione volontaria, smembramenti diagnostici, ordini edilizi AI, ricorrenza dell’evento 53 e un caso sintetico post-pace. Il collaudo successivo con entrambi i plugin osservò avvio, editor e riapertura di un salvataggio breve per entrambi i profili in finestra. Due avvii a freddo a schermo intero terminarono con `0xC0000005` all’offset `0x0041AC6B` durante l’inizializzazione della mappa. Il [backlog](rebaseline_backlog.md#verifiche-runtime) distingue questi esiti da quelli del deployment successivo.
