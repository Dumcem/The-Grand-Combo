# Registro delle differenze upstream

Upstream `14f2e6ff61e7e1ea07ffef07548560da5bcc47f0`, fork censito `3110dacbc1d6e442c25ac005a06511b70c1c5c1d`. Entrambi verificati su GitHub. L'upstream fissato è antenato del fork. Motori supportati: Victoria II 3.04 e Project Alice 1.3.0. [Upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/14f2e6ff61e7e1ea07ffef07548560da5bcc47f0) · [Fork](https://github.com/Dumcem/The-Grand-Combo/commit/3110dacbc1d6e442c25ac005a06511b70c1c5c1d)

## Copertura storica del Task 68

`git diff --no-renames --name-status 14f2e6ff6 3110dacbc` restituisce **354 percorsi** (180 aggiunte, 170 modifiche, 4 rimozioni). Il prospetto conta ogni percorso una volta. Più voci funzionali possono condividere lo stesso file.

| Area Git | Percorsi | Voci |
| --- | ---: | --- |
| Core, eventi e decisioni | 94 | Alice, Loader, script condivisi, salvataggi, personalizzazioni, eccezioni, testi |
| Core, common | 8 | Loader, migrazione, ribelli confessionali, spaziatura in countries |
| Core, tecnologie, invenzioni e unità | 26 | Alice, rinomina di chiavi e commenti |
| Core, localizzazione, storia, mappa, interfaccia e grafica | 27 | Testi, risorse, fix condivisi, Loader, Paracatu |
| Core, strumenti e documenti 1966 | 15 | Timeline e diagnostica |
| Timeline, directory e descrittore | 115 | Timeline e diagnostica |
| Script Extender, directory e descrittore, più `TGC.mod` | 13 | Loader |
| Submod opzionali e Niche | 19 | Submod, testi e grafica |
| Strumenti, test, documentazione, CI, configurazione e guide alla radice | 37 | Deployment e manutenzione |
| **Totale** | **354** | |

A ogni sincronizzazione confrontare il vecchio upstream con il nuovo, poi il candidato fork direttamente con il nuovo upstream. Controllare gli hunk risolti automaticamente e i file misti. Per ogni voce ricontrollare l'effetto a valle e il profilo che lo carica, ritirare le differenze assorbite e indicare l'evidenza mancante per quelle aperte. L'[inventario storico](upstream_reconciliation.md#inventario-del-delta-fissato) conserva la provenienza degli hunk, il [backlog](rebaseline_backlog.md) le verifiche residue.

## Criterio di allineamento

Valutare le singole modifiche per correttezza, chiarezza, compatibilità e utilità. I conteggi Git servono a orientare il confronto storico.

- **Differenza ingiustificata.** Candidata all’eliminazione quando l’allineamento preserva le garanzie e la qualità del contenuto.
- **Correzione valida trasferibile.** Mantenere nel fork e candidare upstream, comprese le correzioni editoriali e di codifica.
- **Estensione intenzionale.** Mantenere con motivazione, profili interessati e condizioni di riesame.
- **Differenza dubbia.** Conservare provvisoriamente e documentare la verifica mancante.

## Esito della revisione del Task 69

- **Recupero editoriale.** Ripristinati refusi corretti, commenti leggibili, intestazioni delle unità e prosa delle guide. Conservate le codifiche per file: Windows-1252 per gli accenti nei commenti legacy e UTF-8 per `Düsseldorf` in `events/Archaeology.txt`, dove era presente il carattere sostitutivo U+FFFD. Verificati anche `Michoacán`, `Plombières` e l’apostrofo di `We'll`, correggendo le forme imprecise del checkpoint precedente. Il commento di Mameli sul flag di partecipazione resta utile. Il carrier di setup Timeline contiene già la grafia corretta e conserva la soglia 1966.
- **Spaziatura e istruzioni attive.** La riga vuota in countries è stata mantenuta. Temperance ha già le righe interessate prive di spazi finali. In Byzantine Expansion sono state recuperate le sei pulizie precedenti, mantenendo i terminatori originali. Il clear di `election_suffled` in 14005 è un effetto attivo. Era l’unico riferimento già nel commit di introduzione e lo è nei profili correnti. Conserviamo il clear upstream, che ripulisce il flag se presente in uno stato importato. L’esistenza di salvataggi con quel flag resta da dimostrare.
- **Corrette.** Direct Immigration legge ora i due modificatori persistenti già scritti e rimossi dal menu 70, con i coefficienti dell’overlay invariati. La correzione vale anche per una campagna già attiva in un salvataggio caricato con l’overlay. Il core, la Timeline e il Loader condividono i lettori del core. Il Loader conserva la propria copia del menu e dell’addebito. Corretto il testo inglese dell’opzione di arresto.
- **Confermate.** Victoria II e Alice condividono i CB ordinari già adottati. Nel Loader la guardia su 96021 impedisce al percorso ordinario di consumare lo stato richiesto da 96094. Le tabelle di partizione e interessi restano nell’overlay e richiedono ID presenti nella mappa. Per Rotterdam resta la correlazione fra avversario, stanchezza e pace. Per Svizzera e Anatolia restano i limiti di proprietà e gli scope delle cessioni. Per Petrograd i nomi rimangono reversibili e i premi sono una tantum. Per il Marocco il filtro di solvibilità precede il trasferimento. La riforma militare segue già upstream: costo e attivazione tecnologica sono indipendenti dalla possibilità di costruire il forte. Il ripristino della fortificazione reintrodurrebbe la dipendenza rimossa oppure richiederebbe un disegno diverso.
- **Guardie condivise.** Il comando di disabilitazione delle unioni come vassallo è una scelta esplicita del menu. Ogni esclusione della formazione jugoslava come vassallo e ogni esclusione del golpe 152009873 blocca il rispettivo ingresso. Alice 1.3.0 compila già il `NOT` upstream con più figli come negazione di una disgiunzione, quindi i raggruppamenti sono equivalenti su Alice. In Victoria II si conserva la forma esplicita e verificabile staticamente; la parità con il raggruppamento upstream resta da dimostrare sul motore originale. Le annessioni jugoslave ai soli paesi AI, i costi dell’uscita dalla neutralità e i pesi AI già adottati coincidono con upstream. [Negazione Alice](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.cpp#L760-L827)
- **Fuori perimetro.** Bilanciamento generale Timeline, JIT Alice su Windows, prestazioni del Loader, interazioni tra submod opzionali e diagnosi dei salvataggi con eventi già in coda rimangono nel backlog. I risultati statici non misurano le frequenze o gli esiti in partita.

## Differenze correnti

| Gruppo | Delta, origine ed evidenza | Motori, decisione e trasferibilità |
| --- | --- | --- |
| Alice | Sette percorsi di grant navali scriptati (`3dadb6622`, `7696c503a`, `8ccb9326d`), guardie su banche e università, rami cinesi e unità EIC. Fallback navali in tecnologie e invenzioni e vincoli sui tempi di costruzione. [Consumatori Alice e regressioni](rebaseline_backlog.md#workaround-navali) | Mantenere i percorsi Victoria II e le guardie Alice. Riesaminare quando cambia il consumatore. Proponibili patch di compatibilità per singolo meccanismo. |
| Timeline e diagnostica | Estensione a 1966 e separazione del profilo (`25ec425d3`, `0583e338f`). Limiti temporali, ricerca, edifici, sottomarini e portaerei, interfaccia, asset e testi. Parser, composizione, validatore, audit e drift seguono la stessa responsabilità. [Manifest e carrier](../TGC_Timeline_1966/docs/manifest_1966_timeline.md) | Mantenere il profilo. Entrambi i motori caricano dati con divergenze documentate. JIT Windows di Alice e bilanciamento restano nella re-baseline. Strumenti generici separabili dai contenuti. |
| Loader | La PR #417 e `cc9d98ca2` introducono hook per provincia, trattati, partizioni, AI e redditi. Il fork rimuove i due `load` dal descrittore comune e recupera nell'overlay i quattro file rimossi dal core. Cessione, trattati, Great War, AI edilizia, redditi e mappa sono nei profili opzionali, con composizione Timeline dichiarata in `723b10694`. [Profili e fonti](deployment/script_extender_profile.md) | Mantenere l'isolamento per Victoria II x86 e i profili comuni per Alice. Avvio breve e riapertura in finestra verificati. Restano crash a schermo intero e prove funzionali. Proponibili le guardie su pace, chiusura, partizioni e percorso della mappa. |
| Script condivisi | Menu indigeno 100 (#416), Anatolia, Svizzera, Petrograd e Marocco in `837a451a0` e `e10615c65`. Guardie per Texas tedesco, Velasco, Sonderbund, Haiti e Cracovia. Riferimenti di invenzioni, Moresnet, flag e scope delle fabbriche. Rotterdam (`2f8c75fc4`, upstream `3edc1b8a9`) lega stanchezza e pace allo stesso belligerante e protegge le proprietà neutrali. OOB vuoti SRG, SWA e ZOU soddisfano i riferimenti di storia. [Casi ed evidenze](upstream_reconciliation.md#comportamento-adottato-e-adattamenti) | Conservare le regressioni su scope, proprietà, riferimenti e guardie per entrambi i motori. Candidati upstream per patch isolate. Per gli OOB verificare se sono previste unità effettive prima di proporre gli stub. |
| Salvataggi e stato persistente | Lettori per Osceola, Gold Coast, Wilhelm IV e colori dei vassalli, migrazione del flag del menu 100 e ID 180–191 di Temperance. Gold Rush sopravvive al cambio di proprietario e World Fair ruota l'ultimo ospite. [Flag](upstream_reconciliation.md#task-48--delta-ordinario-residuo) · [Salvataggi](upstream_reconciliation.md#eccezioni-motivate-e-decisioni-aperte) | Conservare finché i salvataggi interessati sono supportati. Valutare le patch generiche singolarmente. Gli eventi già accodati restano da verificare. |
| Personalizzazioni | Ribelli confessionali e catena teocratica (`4381d0243`, `common/rebel_types.txt`, `Revolution_Event_Theocracy.txt`, testi). Paracatu 2444 nel gruppo climatico del fork e Rio de Janeiro 2447. [Geografia e fonti](upstream_reconciliation.md#eccezioni-motivate-e-decisioni-aperte) | Mantenere le scelte del fork. Riesaminare il clima se i due gruppi, oggi equivalenti nei valori, divergono. Verificare la teocrazia su entrambi i motori quando cambiano i meccanismi. |
| Submod opzionali | Apocalypse cambia il conteggio Holy Cities, condizioni di infezione e lettori scout/emergenza. Direct Immigration cambia il collegamento a 4433, l'opzione localizzata e l'ingresso di Genocide. Fantasy Formables e Less Combat RNG hanno pulizia editoriale. Streamer Mode corregge la dipendenza dal nome dichiarato. [Provenienza](upstream_reconciliation.md#inventario-del-delta-fissato) | Proporre i fix di riferimenti riproducibili. Per Holy Cities e Genocide confermare comportamento desiderato e raggiungibilità. La compatibilità combinata dei submod resta aperta. |
| Testi, grafica e documentazione | Recupero di caratteri in CSV, rinomine, endonimi e nomi dei leader. Sprite reclutamento `.dds` (`88219b99d`), commenti e istruzioni, inclusi `Abilities`, `deprecated` e README dei submod. `flags.py` serve alla produzione di risorse. | Trasferibili per famiglie coerenti. Verificare codifica e asset letti dai due motori. Il confronto editoriale basta per commenti e prosa. |
| Deployment e manutenzione | Tool transazionale, cataloghi, test, CI drift/1966, configurazione editor e istruzioni. Il catalogo storico dell'addon ritirato resta risolvibile per digest. [Deployment](deployment/local_deployment.md) | Mantenere come responsabilità del fork. Recupero e ownership valgono indipendentemente dal motore. |
| Eccezioni e residui | Campagne migratorie e BRZ 8502/8503 restano le due esclusioni di contenuto principali. In cleanup `49543a1f3` ripristina la fascia raggiungibile 750.000–999.999 per i pagamenti dei vassalli. | Il fix della fascia è candidato upstream. Le guardie jugoslave e del golpe sono verificate per esclusione singola; resta il limite di evidenza su Victoria II indicato sopra. |

## Decisioni preparate

- **Migrazione.** `6f9be981d` allinea i lettori ai modificatori nazionali. `da591f8a0` commenta i due lettori, con messaggio «Update pop_types.txt» e senza spiegazione nei metadati pubblici consultati. Il menu 70 conserva l'attivazione e la rimozione di `more_colonial_settlement` e `less_emigration`. Nel fork i due contributi sono +0,1 al calcolo della migrazione coloniale e −0,5 al calcolo dell'emigrazione. L'esito dipende dagli altri fattori e dalle destinazioni ammissibili. L'evento giornaliero 53 conserva per ciascuna campagna `add_tax_relative_income = -0.2` per paesi umani quando è attivo `override_campaigns`, anche nel Loader. Le definizioni dei modificatori lasciano commentato `tax_efficiency`. La localizzazione promette un costo di circa il 10% del massimo gettito mensile. Direct Immigration sostituisce `pop_types.txt` e ora usa gli stessi modificatori del menu. Alice applica i contributi con aggregazione e limiti propri. Mancano misure comparabili su Victoria II e Alice per esborso e impatto demografico. L'ipotesi di bilanciamento o di disattivazione accidentale resta senza prova. Raccomandazione: conservare provvisoriamente il legame menu–effetto. Un ritiro deve coordinare menu, addebiti, salvataggi e overlay. Per rendere definitivo il mantenimento, verificare costi e direzione degli effetti prima di approvare i valori. [Commit upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/da591f8a050da7995d3a57e887c259de58ba0cd5) · [Addebiti nel Loader](deployment/script_extender_task57.md)
- **BRZ 8502/8503.** Nel riferimento fissato esistono solo le due definizioni trigger-only. 8503 ripete due volte la conversione dei medesimi POP e imposta anche lo stato schiavista con un passaggio distinto. Alice accetta `is_slave` come effetto in scope stato e gli eventi originali di Victoria II usano il comando. Raccomandazione: conservare l’esclusione. L’alternativa richiede scegliere un ingresso, quali stati e POP coinvolgere e una sola conversione, con conseguenze sulle riforme e sull’economia del Brasile. Il debug 8500 è distinto e privo di chiamanti nel runtime condiviso. [Esito #416](upstream_reconciliation.md#comportamento-adottato-e-adattamenti)
- **Consumo Alice 1.3.0.** Il codice somma i contributi migratori e limita il risultato del modificatore a un minimo di zero. La riduzione dell'emigrazione può quindi saturare e l'aumento coloniale può essere assorbito da altri contributi. L'addebito moltiplica invece il coefficiente scriptato per la somma dei redditi dei tre strati POP e modifica la tesoreria. Il confronto con il testo sul gettito mensile richiede una misura separata. [Migrazione coloniale ed emigrazione](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/demographics.cpp#L3916-L3951) · [Addebito](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L3067-L3082)
- **Esclusioni strutturali.** Conservare DLL, CB di provincia, termini forzati, partizioni, AI edilizia e curve dei redditi nel profilo opzionale. Conservare le guardie di Rotterdam sulle cessioni neutrali e quelle Alice sui grant finché upstream o il motore coprono gli stessi casi. La rimozione upstream del vecchio Performance Addon è acquisita. [Loader](deployment/script_extender_profile.md) · [Rotterdam](upstream_reconciliation.md#rotterdam)
- **Patch generiche.** Le unità di modifica e i casi da riprodurre sono elencati sotto. I riferimenti persistenti delle invenzioni e i cambi di contenuto dei submod rimangono soggetti alle verifiche indicate nella tabella del Task 70.
- **Patch editoriali.** Correggere il grado di Ryan `10000111`, `St. Peterburg`, la chiave `override_less_emigration_remove_title` (già corretta nel fork), caratteri corrotti e refusi nei commenti e nei README. Lo sprite reclutamento è un fix di riferimento verificabile con l'esistenza dell'asset. [Notifiche](rebaseline_backlog.md#residui-della-riconciliazione)

Le due esclusioni di contenuto (campagne e BRZ) restano decisioni di progetto. Per BRZ, la prova preliminare consiste nel risolvere il chiamante previsto e il conflitto con le conversioni esistenti. Per le campagne, i casi da confrontare sono attivazione, disattivazione e reset in un paese umano idoneo, con e senza overlay, usando la stessa popolazione e le stesse destinazioni. La verifica deve distinguere movimenti POP e variazione di tesoreria, includendo una campagna senza destinazioni idonee.

## Candidati upstream

### Proposte del Task 70

Pronte per revisione locale sulla punta effettiva upstream `14f2e6ff6`, con patch indipendenti e descrizioni in inglese. I nomi corrispondono ai materiali nella cartella di consegna `task70-upstream`.

| Stato | Contributi |
| --- | --- |
| Pronti · 01–04 | Commenti, guide, rimozione degli spazi finali in Byzantine Expansion, testo/codifica e riferimento allo sprite. In Temperance upstream ha già le righe pulite. In countries la riga vuota è impaginazione senza effetto e resta com’è. |
| Pronti · 05–07 | Pagamenti dei vassalli, segno del costo di propaganda, flag Moresnet e trigger delle fabbriche; cessioni in Anatolia e Svizzera e selettore marocchino; menu indigeno e sua eleggibilità AI. |
| Pronti · 08–09 | Dipendenza di Content Creator Mode, lettori scout/emergenza di Apocalypse e nove ID assenti dalla mappa nel file partizioni. Il file interessi AI è già valido rispetto a questa verifica. |
| Condizionati a una scelta | Migrazione, incluso il collegamento Direct Immigration, e BRZ 8502/8503. Per Petrograd decidere tra bloccare la decisione dopo il primo uso e consentire cambi di nome senza ripetere i premi. Per Rotterdam confermare proprietà, core e pace in caso di più belligeranti idonei. Per Holy Cities, infezione, genocidio e OOB vuoti confermare l’intento. |
| Verifiche da completare | Prima di proporre la guardia su 96021, verificare la chiusura dei trattati per i paesi esclusi da 96094 upstream, che applica filtri propri. Verificare la compatibilità dei salvataggi prima di rinominare chiavi delle invenzioni e la semantica Victoria II prima di proporre i raggruppamenti militare e jugoslavo. I workaround Alice richiedono un controllo dei consumatori e del percorso Victoria II per ciascun grant. |
| Fuori perimetro | Timeline 1966, personalizzazioni, struttura dei profili del fork e strumenti di deployment. |

### Commenti, istruzioni e localizzazione

| Gruppo | Perimetro trasferibile |
| --- | --- |
| Commenti di script e GUI | Ortografia e grammatica nei commenti delle decisioni, degli eventi, delle unità, di Direct Immigration e di Screenshot Mode. Conservare gli identificatori scriptati, compreso `agressive_tag`. |
| Guide dei submod | Correzioni di prosa nelle istruzioni dei Niche Submods, di Low Ram e di Pastel Map. Le indicazioni operative e i valori riportati restano quelli delle guide di partenza. |
| Accenti e codifica | Sostituire U+FFFD in `events/Archaeology.txt` e correggere `Michoacán`, `Plombières` e l’apostrofo di `We'll` nei rispettivi commenti. Gli altri accenti esaminati erano già leggibili come Windows-1252 nel riferimento fissato e restano nei byte originali. Verificare la codifica del file di destinazione prima di applicare gli hunk. |
| Testi localizzati | Refuso della chiave `override_less_emigration_remove_title`, grado di Ryan e grafia di San Pietroburgo. Trasferire le sole righe interessate. |

### Difetti funzionali

| Caso da riprodurre | Modifica minima trasferibile |
| --- | --- |
| Direct Immigration legge flag assenti durante una campagna attiva | Sostituire i due lettori in `TGCDirectImmigration/common/pop_types.txt` con `has_country_modifier`. Conservare coefficienti, menu e addebiti. Coordinare con la decisione upstream sulle campagne del core. |
| La fascia 750.000–999.999 POP è impossibile nei due selettori dei pagamenti vassalli | Portare a 1.000.000 il limite superiore esclusivo in entrambi i selettori di `3_Clean-Up.txt`. |
| Menu indigeno riaperto con una risposta pendente o AI che accetta requisiti parziali | Nel percorso dell’evento 100 impostare e liberare il blocco per paese a ogni ingresso e uscita. Negare con un `AND` esplicito l’intero gruppo di requisiti quando si azzera la chance AI. |
| La cessione svizzera include una provincia estranea alla sequenza di trasferimento | Nell’evento 10426 filtrare per il proprietario previsto in ciascun ramo, prima di modificare core e proprietà. |
| Il ramo anatolico senza Bosforo applica la relazione in scope errato | Spostare la relazione con GRE nello scope nazionale e applicare le esclusioni di provincia nel selettore delle cessioni. |
| Alternare i nomi di Petrograd riassegna prestigio, militanza o stanchezza | Usare un flag di premio per decisione e paese, lasciando reversibile il flag del nome. |
| Un compratore non solvibile può essere selezionato per il Tangier Protocol | Applicare il requisito di tesoreria nel selettore dell’effetto che sceglie il compratore. |
| Rotterdam usa la stanchezza di un paese diverso dall’avversario o cede proprietà neutrali | Vincolare stanchezza e pace allo stesso belligerante e filtrare cessioni e core per il proprietario previsto. |
| Nel Loader la notifica di pace ordinaria anticipa la chiusura di un trattato forzato | Escludere da 96021 i paesi con `se_treaty_dismantled`, così 96094 può consumare lo stato di chiusura. Per le tabelle, eliminare soltanto gli ID assenti dalla mappa del riferimento. |

## Regressioni da mantenere

| Suite | Contratto |
| --- | --- |
| 1966, navale e `sub_unit` | Fixture di parser, composizione e semantica, contratti di validazione e proiezione, consumatori e guardie di costruzione e grant. |
| Upstream 41–44 e 50 | Catene diplomatiche, proprietà, beneficiari, salvataggi, mappa e carrier. Consolidato il controllo di ereditarietà di `GEF Events.txt`. |
| Upstream 46–49 | Produttori e lettori, applicabilità delle riforme, unicità, menu e rotazione. Il menu 100 verifica l'unicità nella composizione effettiva. Le campagne verificano opzione, effetto e segno. Rimosso l'oracolo sugli effetti interni del debug 8500. |
| Deploy e profili Extender | Integrazione dei quattro profili, dipendenze, confini motore, composizione, compatibilità storica, recupero e interruzioni simulate. |

Aggiungere un test quando si può indicare il difetto che fallirebbe, la garanzia che deve durare e il profilo o motore interessato. Estendere il test pertinente prima di creare un file per numero di task. Usare valori esatti per interfacce persistenti, soglie approvate e configurazioni obbligatorie. Per decisioni aperte verificare proprietà come direzione, raggiungibilità e collegamento tra attivazione, effetto e costo. Per correzioni editoriali basta il diff, salvo chiavi, codifica e riferimenti consumati a runtime.

Verifica del Task 68 con `unittest discover` nelle due directory. `tools/tests` passa con 181 test. `tools/deploy/tests` passa con 111 test e 6 skip previsti dalle fixture. Le modifiche riguardano documenti e test di riconciliazione. Il validator e l'audit di bilanciamento 1966 restano fuori dal perimetro di questa verifica.

## Milestone 68–71

| Milestone | Criterio verificabile | Stato |
| --- | --- | --- |
| 68 | Delta Git riconciliato, oracoli rivisti, documentazione aggiornata ed esiti delle suite registrati | Conclusa |
| 69 / 69R | Correzione Direct Immigration, recupero editoriale e candidature separate per tipo di intervento | Verifica statica, decisioni di progetto aperte |
| 70 | Patch indipendenti sulla base upstream effettiva, con descrizioni, verifiche mirate e condizioni di pubblicazione | Materiali pronti localmente |
| 71 | Registro e backlog aggiornati al checkpoint finale, verifiche applicabili concluse e condizioni di riesame esplicite | Da avviare |
