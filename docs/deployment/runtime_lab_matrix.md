# Matrice delle verifiche runtime

[Procedura del laboratorio](runtime_lab.md) · [Qualifica Victoria II 3.04](runtime_lab_operations.md#task-14--victoria-ii-304-x86) · [Backlog](../rebaseline_backlog.md#verifiche-runtime)

## Fixture condivise

| Fixture | Preparazione e riuso |
| --- | --- |
| Nuova partita | Inizio 1836 in pausa. Una base per motore e profilo, con scenario Alice rigenerato dopo il deploy. Riferimento per confronti che richiedono una nuova partita. |
| Victoria II 3.04, Task 14 | Salvataggi sintetici dell'Impero russo separati per composizione e riaperti nel motore originale. I manifest delle fixture fissano eseguibile, revisione, profilo e hash del salvataggio. [Procedura e prove](runtime_lab_operations.md#task-14--victoria-ii-304-x86) |
| Grand Loader 3.0.0, Task 15 | Fixture distinte `t15-loader-core-01` (`AKGB`) e `t15-loader-1966-01` (`FNKX`). Entrambe riaperte in Russia al 3 gennaio 1836, ciascuna con il proprio profilo. [Procedura e prove](runtime_lab_operations.md#task-15--qualifica-dei-profili-grand-loader) |
| Eventi pendenti | Derivazioni dalla base con un evento realmente accodato o un popup aperto nel punto richiesto. Conservare una copia prima dell'accodamento, una in attesa e una dopo la risposta. Usare per Temperance, Sonderbund e Gold Rush. Una prova forzata da console può diagnosticare gli effetti di una scelta, mentre la prova di dispatch richiede il percorso effettivo. |
| Territorio e diplomazia | Derivazioni dalla base con proprietà divisa, soggetti e sfere controllabili, mappa e tag annotati. Serve per Yinxu, Petrograd, Gold Rush e Anatolia, con condizioni specifiche per ciascun caso. |
| Guerra e pace | Base con due guerre e registrazione di belligeranti, leader, province e pace bilaterale/generale. Derivare una battaglia TEX/MEX e copie per USS e Loader senza condividere flag già consumati. |
| Economia | Checkpoint gemelli a parità di POP, cassa, data, prezzi, velocità e servizi attivi. Riutilizzabili tra ingaggio e Loader con le rispettive condizioni. |

Per un esperimento autorizzato, riusare una fixture compatibile o prepararla nel laboratorio. Conservare motore, profilo, revisione,
checksum e SHA-256 assieme alla ricetta. Le copie diagnostiche di vecchi
salvataggi sono facoltative e richiedono provenienza e scenario compatibile
documentati. Il risultato storico vale per la fixture effettivamente provata.

## Criterio di necessità delle prove live

Una prova live è eccezionale. È giustificata solo se una domanda tecnica concreta resta irrisolta dopo l'analisi del codice, della documentazione, dei sorgenti disponibili dei motori e dei test deterministici. Completezza, prudenza, copertura sistematica e conferma generica sono motivi insufficienti.

Prima di autorizzarla, registrare:

1. La domanda concreta ancora senza risposta.
2. Le verifiche statiche e deterministiche già esaurite e il loro esito.
3. Perché solo l'esecuzione del motore può rispondere.
4. La decisione tecnica che dipende dall'esito.
5. L'esperimento minimo sufficiente, con il solo motore, profilo e stato iniziale pertinenti.

Se manca uno di questi elementi, la prova resta sospesa e si esplicita il limite dell'evidenza. Una voce aperta indica una questione da riesaminare. Le ricette storiche documentano le condizioni delle osservazioni, senza creare una coda di esecuzioni. Restano applicabili i controlli statici, la validazione di scenario, i validator, gli audit e le regressioni deterministiche previsti da [AGENTS.md](../../AGENTS.md).

## Qualifiche completate

V2 indica Victoria II 3.04 x86. La baseline Alice è 1.3.0. Le qualifiche valgono per le revisioni e le composizioni documentate.

| Caso | Motore e profilo | Evidenza |
| --- | --- | --- |
| DEPLOY_STEAM | V2, `core` e `core+1966`, copia autorizzata fuori da `steamapps` | Task 14 a `3c3be0d63`. Riapertura dell'Impero russo al 3 gennaio in entrambi i profili con rendering WARP. Log, schermate e fixture separate. [Riscontro](runtime_lab_operations.md#task-14--victoria-ii-304-x86) |
| DEPLOY_LOADER | V2, `core+extender` e `core+extender+1966` | Task 15 completato a `3c3be0d63`. Avvio in finestra, inizializzazione dei plugin, avanzamento, salvataggio e riapertura verificati per entrambi. Cache e CB privati, 105 ambiti host invariati per profilo. [Risultati](runtime_lab_operations.md#task-15--qualifica-dei-profili-grand-loader) |
| DEPLOY_ALICE | Alice, `core` e `core+1966` | Task 13 ha riaperto la fixture `core` del Task 12 e un nuovo salvataggio. Ha generato `core+1966`, aperto e avanzato la partita al secondo tentativo e riaperto il salvataggio. Il blocco del primo ingresso Timeline resta con causa indeterminata. [Riscontro](runtime_lab_operations.md#riscontro-del-task-13) |
| [EVENT_ORPHAN](../event_orphan_review.md#confronto-diagnostico-alice-130) | Alice, due profili condivisi | Confronto Task 13 completato in entrambi i profili. Stesse 45 firme storiche e sole assenze Yinxu nella coorte. Confermate 16 firme EVENT_MILITARY, due firme 44840 e assenza della firma USS. |

## Casi per cui basta il lavoro statico o deterministico

| Caso | Riesame ed evidenza |
| --- | --- |
| [Yinxu](../event_orphan_review.md#yinxu--esito-del-task-16) | Riesame statico concluso. Alice core conferma concessione e persistenza, con richiesta del ramo B accodata al destinatario corretto. La copertura runtime resta parziale. Nessuna ulteriore prova è necessaria o autorizzata. La domanda residua su `FROM` nel 3.04 è conservata nel riesame. |
| TEMPERANCE | Confrontare registrazione e conservazione degli ID 180–191 e usare fixture già disponibili per leggere ID, scadenza, destinatario e checksum, se pertinenti. Il comportamento di eventi già accodati in salvataggi storici resta non osservato. Vale il best effort per quei salvataggi. |
| SONDERBUND | Tracciare guardie e risposte per destinatario nel codice e nella coda Alice. La possibile ricomparsa di un popup anteriore alle guardie è accettata senza migrazione. La parità di dispatch nei due motori rimane non osservata. |
| [PETROGRAD](../upstream_delta_register.md#petrograd--decisioni-e-rinomine-della-provincia-994) | Tracciare i due primi usi di 994, i beneficiari, le guardie e le rinomine periodiche per proprietà, vassallaggio e flag. La persistenza in partita resta non osservata. |
| [USS_VICTORY_SCOPE](../rebaseline_backlog.md#uss_victory_scope--destinatario-dello-smembramento-dopo-la-vittoria-uss) | L'incoerenza di scope è aperta e documentata nei dati. Tracciare il destinatario di `3755286` e i suoi effetti. Valutare il CB speciale separatamente dalla decisione. |
| [MILITARY_HIRE_PAYMENT](../rebaseline_backlog.md#military_hire_payment--addebito-e-idoneità-nel-reclutamento-attivo) | L'ordine addebito–convalida è verificabile nel codice. Usare casi deterministici per soglie di cassa, seed, cambio di proprietario e cooldown. Il comportamento in partita resta non misurato. |

## Incertezze potenzialmente dipendenti dal motore

Questi casi restano sospesi per la parte live. Le domande indicano dove cercare evidenza prima di applicare il criterio di necessità.

| Caso | Domanda residua e verifica preliminare |
| --- | --- |
| [BATTLE_EVENT / Santa Anna](../event_orphan_review.md#prove-runtime-da-riprendere) | Il gancio battaglia originale di 3.04 consegna `44840` con gli scope richiesti? Esaurire prima ricerca sul binario e riferimenti tecnici utili. In Alice 1.3.0 manca il consumo del gancio e il riferimento è provinciale, con corpo nazionale. |
| GOLD RUSH | Il cambio di proprietario di 104 tra accodamento e scelta altera lo scope effettivo di `99903` in 3.04? Prima confrontare sorgenti, guardie, flag e storico di esecuzione con casi deterministici, usando le fixture disponibili se pertinenti. |
| [ANATOLIA](../rebaseline_backlog.md#anatolia--perimetro-di-500291-e-verifiche-runtime) | Il 3.04 aggiorna l'esistenza di GRE durante `500291` in tempo per il filtro AI e il vassallaggio? Prima esaminare ordine delle cessioni, filtri, capitale e conseguenze con la matrice statica. |
| LOADER_TREATY | Quale clausola è rimasta inapplicata nel caso ottomano e quale stato la rende inapplicabile? Confrontare prima codice del consumatore e tracce archiviate. Resta separata la domanda sul costo effettivo di `acquire_province`. |
| LOADER_ECONOMY | Un hook applica il valore netto per strato previsto quando si sommano modificatori nazionali e provinciali, anche alla soglia 1990? Tracciare prima formule e hook. Isolare staticamente gli effetti di 53 da quelli del tick ordinario. |
| LOADER_PEACE | Una firma ritardata o una seconda guerra cambia la consegna di `96021` o fa ripetere `96094`? Prima esaminare coda, ordine delle firme, guardie e consumo dei flag con transizioni deterministiche. |
| PERFORMANCE / JIT Alice | Per il JIT, esaminare prima log, dump disponibili, binario, variante CPU e dipendenze per attribuire la rilocazione. Per le prestazioni, un confronto sarà valutabile solo se serve a una decisione concreta e le misure esistenti sono insufficienti. [Evidenza storica](../upstream_reconciliation.md#evidenza-runtime-e-di-recupero) |
