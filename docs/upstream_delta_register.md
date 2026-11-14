# Registro delle differenze upstream

Il Task 71C integra upstream `8f106a7f0ec5690d3fe67429a37986506ad5218b`, con tutte le PR #418–427, a partire dal fork `aa958b0fc` (Task 71B). Le correzioni accettate erano già presenti nella composizione del fork. Il merge conserva le guardie navali Alice, la localizzazione con chiavi univoche, i carrier Timeline, la separazione Loader e la riconciliazione mensile degli addebiti. Le partizioni corrette dalla #427 restano nell'overlay Loader. Motori supportati: Victoria II 3.04 e Project Alice 1.3.0. [Upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/8f106a7f0ec5690d3fe67429a37986506ad5218b)

Restano aperte la ripetibilità delle rinomine di Petrograd (decisione di gameplay), la misura di costo e impatto demografico delle campagne, l'ordine fra firma e chiusura Loader quando si sovrappongono più guerre e il crash a schermo intero. Riaprire il caso Loader con una riproduzione che mostri flag pendenti o una chiusura prima della firma. Riaprire il crash se ricorre in finestra o se lo schermo intero diventa un requisito. Il backlog generale conserva il proprio perimetro.

## Integrazione delle PR #418–438

GitHub conferma i 21 merge. Le #418–427 sono già recepite dal Task 71C. Le #428–438 sono incluse in [`4661c1b5a`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/4661c1b5a7d24f6b658e14caf69245e6043355ee). La verifica parte dal fork `7ae5d59b7`. Il suo ultimo riferimento sincronizzato resta `8f106a7f0`. Le differenze sotto descrivono l’implementazione già presente nel fork prima di qualsiasi futura sincronizzazione.

| PR | Merge upstream | Contributo | Stato nel fork a `7ae5d59b7` |
| --- | --- | --- | --- |
| [#428](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/428) | [`199783291`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/199783291cd3f39eb5d39f42ab3f5cf11324d3ee) | Flag del menu Workplace Events | Già presente. |
| [#429](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/429) | [`4661c1b5a`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/4661c1b5a7d24f6b658e14caf69245e6043355ee) | Concessione svedese e russificazione finlandese | Lettori FIN e guardia SWE presenti. Manca il controllo del flag sotto SCA. |
| [#430](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/430) | [`1223fa769`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/1223fa769d5471a363837f2215d30dd59ac2ecf8) | Relazioni negli eventi di bancarotta | Già presente. |
| [#431](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/431) | [`401afd5e4`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/401afd5e4d251b39721a65f124dfd8b2b0f485b6) | Proprietà di Port-au-Prince | Già presente. |
| [#432](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/432) | [`145c7f73d`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/145c7f73dfee9c348cdbcd74159d935eda692557) | Guardia della decisione confederata su Cuba | Già presente. |
| [#433](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/433) | [`3f836c865`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/3f836c8654edfedd69b3a9d09643f04e4103b9e3) | Flag della decisione messicana | Scrittore e lettore minuscoli. Manca la guardia per lo stato storico con suffisso maiuscolo. |
| [#434](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/434) | [`a79e5b79a`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/a79e5b79ae33ec5992ad0f1c7c26b943f6a2ce5f) | Chiave dell’opzione Direct Immigration 980005 | Già presente. |
| [#435](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/435) | [`6a4fe6f5b`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/6a4fe6f5b70f8cb1c51d3a8a6c034c13ad9803b3) | Localizzazione polacca 203903 | Le due chiavi sono presenti in un’altra posizione del CSV. |
| [#436](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/436) | [`4aa770f9d`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/4aa770f9d71e32de67e5a748225bbb5606c02d29) | Commenti di script e defines | Parziale. Restano differenze puntuali nei commenti, inclusi i tre apostrofi e i defines del core. |
| [#437](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/437) | [`50fcafac8`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/50fcafac81498541f2aaf75fd82022b755c08650) | Localizzazione Direct Immigration | Le sei correzioni del CSV non sono presenti. |
| [#438](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/438) | [`95ba0241f`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/95ba0241faeb1c7dda0ba04d491f107437cfc173) | Guide dei submod | La guida Low RAM contiene correzioni equivalenti. Manca la correzione nella guida Belle Cartographie. |

Le correzioni pubblicate nei due lotti sono chiuse come candidature. Alla prossima sincronizzazione verificare gli hunk residui e i carrier, in particolare i defines della Timeline e le compatibilità dei flag. Le prove runtime del fork restano nel backlog.

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
| Loader | La PR #417 e `cc9d98ca2` introducono hook per provincia, trattati, partizioni, AI e redditi. Il fork rimuove i due `load` dal descrittore comune e recupera nell'overlay i quattro file rimossi dal core. Cessione, trattati, Great War, AI edilizia, redditi e mappa sono nei profili opzionali, con composizione Timeline dichiarata in `723b10694`. [Profili e fonti](deployment/script_extender_profile.md) | Mantenere l'isolamento per Victoria II x86 e i profili comuni per Alice. Avvio breve e riapertura in finestra verificati. Restano crash a schermo intero e prove funzionali. Restano da valutare pace, chiusura e percorso della mappa. I nove ID delle partizioni sono corretti dalla #427. |
| Script condivisi | Menu indigeno 100 (#416), Anatolia, Svizzera, Petrograd e Marocco in `837a451a0` e `e10615c65`. Guardie per Texas tedesco, Velasco, Sonderbund, Haiti e Cracovia. Riferimenti di invenzioni, Moresnet, flag e scope delle fabbriche. Rotterdam (`2f8c75fc4`, upstream `3edc1b8a9`) lega stanchezza e pace allo stesso belligerante e protegge le proprietà neutrali. OOB vuoti SRG, SWA e ZOU soddisfano i riferimenti di storia. [Casi ed evidenze](upstream_reconciliation.md#comportamento-adottato-e-adattamenti) | Conservare le regressioni su scope, proprietà, riferimenti e guardie per entrambi i motori. Candidati upstream per patch isolate. Per gli OOB verificare se sono previste unità effettive prima di proporre gli stub. |
| Salvataggi e stato persistente | Lettori per Osceola, Gold Coast, Wilhelm IV e colori dei vassalli, migrazione del flag del menu 100 e ID 180–191 di Temperance. Gold Rush sopravvive al cambio di proprietario e World Fair ruota l'ultimo ospite. [Flag](upstream_reconciliation.md#task-48--delta-ordinario-residuo) · [Salvataggi](upstream_reconciliation.md#eccezioni-motivate-e-decisioni-aperte) | Conservare finché i salvataggi interessati sono supportati. Valutare le patch generiche singolarmente. Gli eventi già accodati restano da verificare. |
| Personalizzazioni | Ribelli confessionali e catena teocratica (`4381d0243`, `common/rebel_types.txt`, `Revolution_Event_Theocracy.txt`, testi). Paracatu 2444 nel gruppo climatico del fork e Rio de Janeiro 2447. [Geografia e fonti](upstream_reconciliation.md#eccezioni-motivate-e-decisioni-aperte) | Mantenere le scelte del fork. Riesaminare il clima se i due gruppi, oggi equivalenti nei valori, divergono. Verificare la teocrazia su entrambi i motori quando cambiano i meccanismi. |
| Submod opzionali | Apocalypse cambia il conteggio Holy Cities, condizioni di infezione e lettori scout/emergenza. Direct Immigration cambia il collegamento a 4433, l'opzione localizzata e l'ingresso di Genocide. Fantasy Formables e Less Combat RNG hanno pulizia editoriale. Streamer Mode corregge la dipendenza dal nome dichiarato. [Provenienza](upstream_reconciliation.md#inventario-del-delta-fissato) | Proporre i fix di riferimenti riproducibili. Per Holy Cities e Genocide confermare comportamento desiderato e raggiungibilità. La compatibilità combinata dei submod resta aperta. |
| Testi, grafica e documentazione | Recupero di caratteri in CSV, rinomine, endonimi e nomi dei leader. Sprite reclutamento `.dds` (`88219b99d`), commenti e istruzioni, inclusi `Abilities`, `deprecated` e README dei submod. `flags.py` serve alla produzione di risorse. | Trasferibili per famiglie coerenti. Verificare codifica e asset letti dai due motori. Il confronto editoriale basta per commenti e prosa. |
| Deployment e manutenzione | Tool transazionale, cataloghi, test, CI drift/1966, configurazione editor e istruzioni. Il catalogo storico dell'addon ritirato resta risolvibile per digest. [Deployment](deployment/local_deployment.md) | Mantenere come responsabilità del fork. Recupero e ownership valgono indipendentemente dal motore. |
| Eccezioni e residui | Campagne migratorie e BRZ 8502/8503 restano le due esclusioni di contenuto principali. In cleanup `49543a1f3` ripristina la fascia raggiungibile 750.000–999.999 per i pagamenti dei vassalli. | Il fix della fascia è integrato upstream con la #421. Le guardie jugoslave e del golpe sono verificate per esclusione singola; resta il limite di evidenza su Victoria II indicato sopra. |

## Decisioni preparate

- **Migrazione.** `6f9be981d` allinea i lettori ai modificatori nazionali. `da591f8a0` commenta i due lettori, con messaggio «Update pop_types.txt» e senza spiegazione nei metadati pubblici consultati. Il menu 70 conserva l'attivazione e la rimozione di `more_colonial_settlement` e `less_emigration`. Nel fork i due contributi sono +0,1 al calcolo della migrazione coloniale e −0,5 al calcolo dell'emigrazione. L'esito dipende dagli altri fattori e dalle destinazioni ammissibili. L'evento giornaliero 53 conserva per ciascuna campagna `add_tax_relative_income = -0.2` per paesi umani quando è attivo `override_campaigns`, anche nel Loader. Le definizioni dei modificatori lasciano commentato `tax_efficiency`. La localizzazione promette un costo di circa il 10% del massimo gettito mensile. Direct Immigration sostituisce `pop_types.txt` e ora usa gli stessi modificatori del menu. Alice applica i contributi con aggregazione e limiti propri. Mancano misure comparabili su Victoria II e Alice per esborso e impatto demografico. L'ipotesi di bilanciamento o di disattivazione accidentale resta senza prova. Raccomandazione: conservare provvisoriamente il legame menu–effetto. Un ritiro deve coordinare menu, addebiti, salvataggi e overlay. Per rendere definitivo il mantenimento, verificare costi e direzione degli effetti prima di approvare i valori. [Commit upstream](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/da591f8a050da7995d3a57e887c259de58ba0cd5) · [Addebiti nel Loader](deployment/script_extender_task57.md)
- **BRZ 8502/8503.** Nel riferimento fissato esistono solo le due definizioni trigger-only. 8503 ripete due volte la conversione dei medesimi POP e imposta anche lo stato schiavista con un passaggio distinto. Alice accetta `is_slave` come effetto in scope stato e gli eventi originali di Victoria II usano il comando. Raccomandazione: conservare l’esclusione. L’alternativa richiede scegliere un ingresso, quali stati e POP coinvolgere e una sola conversione, con conseguenze sulle riforme e sull’economia del Brasile. Il debug 8500 è distinto e privo di chiamanti nel runtime condiviso. [Esito #416](upstream_reconciliation.md#comportamento-adottato-e-adattamenti)
- **Consumo Alice 1.3.0.** Il codice somma i contributi migratori e limita il risultato del modificatore a un minimo di zero. La riduzione dell'emigrazione può quindi saturare e l'aumento coloniale può essere assorbito da altri contributi. L'addebito moltiplica invece il coefficiente scriptato per la somma dei redditi dei tre strati POP e modifica la tesoreria. Il confronto con il testo sul gettito mensile richiede una misura separata. [Migrazione coloniale ed emigrazione](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/demographics.cpp#L3916-L3951) · [Addebito](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/scripting/effects.cpp#L3067-L3082)
- **Addebiti delle campagne (Task 71B).** L'attivazione dal menu, da Direct Immigration o dagli scout di Apocalypse abilita subito gli addebiti. I reset e le disattivazioni agiscono sul servizio interessato. L'evento 52 ricostruisce il flag globale con un passaggio sui paesi ogni 30 giorni e recupera anche i salvataggi con il flag spento e servizi attivi, entro il prossimo aggiornamento mensile se la catena degli aggiornatori è in corso. L'evento 53 resta l'unico percorso di addebito periodico e continua a verificare il singolo servizio, inclusa la presenza degli edifici per Direct Immigration. L'ultimo servizio disattivato smette subito di produrre costi e il flag si spegne al successivo aggiornamento mensile. Restano da misurare gli importi effettivi e l'impatto demografico sui due motori.
- **Esclusioni strutturali.** Conservare DLL, CB di provincia, termini forzati, partizioni, AI edilizia e curve dei redditi nel profilo opzionale. Conservare le guardie di Rotterdam sulle cessioni neutrali e quelle Alice sui grant finché upstream o il motore coprono gli stessi casi. La rimozione upstream del vecchio Performance Addon è acquisita. [Loader](deployment/script_extender_profile.md) · [Rotterdam](upstream_reconciliation.md#rotterdam)
- **Patch generiche.** Le candidature residue sono elencate sotto. I riferimenti persistenti delle invenzioni e i cambi di contenuto dei submod rimangono soggetti alle verifiche indicate nella tabella del Task 70.
- **Patch editoriali.** La grafia di San Pietroburgo e i testi inclusi nei lotti sono registrati nelle PR integrate. La chiave della campagna anti-emigrazione e il grado di Ryan risultano già corretti upstream. Lo sprite richiede ancora la verifica dell’asset caricato dal core.

Le due esclusioni di contenuto (campagne e BRZ) restano decisioni di progetto. Per BRZ, la prova preliminare consiste nel risolvere il chiamante previsto e il conflitto con le conversioni esistenti. Per le campagne, i casi da confrontare sono attivazione, disattivazione e reset in un paese umano idoneo, con e senza overlay, usando la stessa popolazione e le stesse destinazioni. La verifica deve distinguere movimenti POP e variazione di tesoreria, includendo una campagna senza destinazioni idonee.

## Contributi upstream e candidature residue

### Primo lotto pubblicato (Task 70B)

Il Task 70B ha pubblicato dieci PR normali verso `master`, con un solo commit ciascuna sulla base `14f2e6ff6`. GitHub ha confermato base, repository e commit sorgente, descrizioni e file. Al termine della verifica non risultavano controlli CI. Le verifiche statiche e i riferimenti dei branch sono in `task70-upstream/review70b.md`.

| PR | Contributo |
| --- | --- |
| [#418](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/418) | Commenti e pulizia mirata in Byzantine Expansion |
| [#419](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/419) | Guide Niche Submods e Pastel Map |
| [#420](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/420) | Testi di eventi e toponimi |
| [#421](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/421) | Fascia intermedia dei pagamenti vassalli |
| [#422](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/422) | Flag della scuola industriale di Moresnet |
| [#423](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/423) | Trigger delle fabbriche negli eventi socialisti |
| [#424](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/424) | Solvibilità del compratore a Tangeri |
| [#425](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/425) | Dipendenza di Content Creator Mode |
| [#426](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/426) | Lettori scout ed emergenza di Apocalypse |
| [#427](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/427) | ID di provincia nelle partizioni Loader |

### Candidature residue

- **Sonderbund.** Il fork usa già un invito per paese. La variante locale aggiunge il controllo di una risposta già registrata e mantiene gli ID esistenti. La patch upstream autonoma è pronta per revisione. Si veda il [backlog](rebaseline_backlog.md#residui-della-riconciliazione) per la limitazione dei popup legacy.
- **Script e gameplay.** Restano da isolare e verificare menu indigeno, cessioni svizzere e anatoliche, Rotterdam, Petrograd, propaganda, migrazione, BRZ 8502/8503 e i cambi condizionati dei submod.
- **Compatibilità.** Restano le verifiche su sprite, OOB, chiavi delle invenzioni, chiusura 96021/96094 e workaround navali Alice per singolo meccanismo. Le correzioni dei nove ID delle partizioni sono già integrate con la #427.

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
