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

## Evidenza runtime e di recupero

- **Steam e Alice a `864c81fe8`.** Il motore originale raggiunse una finestra responsiva per core e Timeline. Alice generò entrambi gli scenari, caricò il core e caricò la Timeline in uno di tre tentativi. Gli altri due terminarono con `0xC0000409` e `IMAGE_REL_AMD64_ADDR32NB relocation requires an ordered section layout`. Il controllo con lo scenario precedente riuscì. Il difetto intermittente è localizzato nella rilocazione JIT Windows, con causa delle allocazioni e correzione ancora aperte. I diagnostici furono 150 errori non fatali e 314 avvisi per core, 195 e 314 per Timeline. I 197 errori Timeline appartengono a un checkpoint anteriore.
- **Recupero Windows.** Un handle esterno aperto ha riprodotto il rifiuto di sostituzione del journal. Dopo il rilascio, il recupero per ID ha ripristinato byte e ownership, conservando i file estranei. L’esperimento dimostra il meccanismo riprodotto. L’origine dell’episodio spontaneo resta indeterminata. La [procedura di recupero](deployment/local_deployment.md#rollback-and-interrupted-publication) è il riferimento operativo.
- **Loader 3.0.0.** La [prova isolata con solo Script Extender](https://github.com/Dumcem/The-Grand-Combo/blob/798eaab6ea10cd879e1517571d72561953bcbe3b/docs/deployment/script_extender_task56.md#risultati-in-partita) osservò cessione volontaria, smembramenti diagnostici, ordini edilizi AI, ricorrenza dell’evento 53 e un caso sintetico post-pace. Il collaudo successivo con entrambi i plugin osservò avvio, editor e riapertura di un salvataggio breve per entrambi i profili in finestra. Due avvii a freddo a schermo intero terminarono con `0xC0000005` all’offset `0x0041AC6B` durante l’inizializzazione della mappa. Il [backlog](rebaseline_backlog.md#verifiche-runtime) distingue questi esiti da quelli del deployment successivo.
