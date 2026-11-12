# Task 57 · Consolidamento e piano di collaudo finale

**Pronto al collaudo finale.** Il profilo resta facoltativo per Victoria II
3.04 x86. Le misure nel motore e l'identità della clausola ottomana richiedono
la sessione descritta sotto. Nessuna modifica ai dati di gioco nel Task 57.
Per il collaudo generale già eseguito, vedere il [Task 56](script_extender_task56.md).
Il sorgente ufficiale esaminato è quello del bundle 3.0.0 al commit
`e911c9537a32495469c94c078613981a85f62acc`.

## Mappa

`fabb6434a` discende dal riferimento pubblico `9f88e7585`. La mappa estesa
differisce dal `default.map` condiviso soltanto per il percorso relativo di
`definition.csv`. Da `map/`, `../mod/TGCScriptExtender/map/definition.csv`
risolve nella coppia pubblicata dal catalogo dedicato, che include `map`
tra le radici di runtime e eredita il CSV dal core. Nessuna dipendenza da
lettera di unità o cartella utente. La regressione confronta l'intero file
con il core dopo la sola sostituzione attesa e controlla destinazione e CSV.
L'avvio e il salvataggio del Task 56 forniscono la verifica nel motore per
la mappa adottata. Core, Timeline e percorso di Project Alice 1.3.0 restano
fuori dal profilo e non richiedono rigenerazione di scenario.

## Clausola ottomana

La prova era `dismantle TUR RUS gw` con Francia giocante, RUS vincitore AI,
TUR destinatario, 496 punti su 500, 23 clausole e 22 applicate. Il
rapporto conserva le liberazioni di Bulgaria, Romania e Albania e le cessioni
di 859 e 885 a RUS. Indice, CB, beneficiario eventuale, provincia/Stato e
ordine delle singole clausole non sono stati conservati. Gli hash di log e
salvataggi permettono un confronto con eventuali copie, senza ricostruirne
il contenuto. Il Task 56 ha verificato la rimozione dei file originali.

Il sorgente 3.0.0 aggiunge prima le clausole gratuite valide senza selezione
territoriale o di paese terzo, nell'ordine dei CB caricati. Poi l'IA aggiunge
in coda le scelte valide, in ordine di valore per punto e, a parità, di
costo più alto. Nel bundle l'ordine delle clausole gratuite candidate è
`treaty_pay_tributes`, `treaty_dismantle_forts`, `treaty_humiliate`.
La posizione effettiva dipende dalla validità iniziale di ciascuna. Il plugin
verifica l'intero trattato nello stato iniziale,
poi rivalida ogni termine per indice a partire da zero, dopo aver eseguito
quelli precedenti. `SE_TREATY_TERM_INVALID` indica CB assente o privo del
marcatore trattato, oppure fallimento di `goal_valid_scoped`. Senza terzo
paese si usa la validità del motore. Con terzo paese si verificano esistenza
del cedente, condizioni `allowed_countries`, appartenenza alla partizione
quando applicabile e, se configurati, Stati validi, ancora posseduti dal
cedente e conformi a `allowed_states`. Altri controlli (parti, capitale,
ultimo Stato, proprietario e occupante) hanno chiavi distinte quando
raggiunti. [CB ufficiali](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/mod/script_extender/common/se_treaty_cbs.txt#L305-L424) · [Composizione IA](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty_ai_dismantle.cpp#L420-L552) · [Validazione](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty.cpp#L810-L918) · [Applicazione](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty.cpp#L1301-L1351)

Il controllo iniziale riuscito rende plausibile che una clausola precedente
abbia cambiato lo Stato richiesto dal termine scartato. La stessa evidenza
è compatibile con una composizione IA che sceglie termini incompatibili o
con un controllo che respinge uno Stato ancora valido. La causa precisa è
indeterminata. Nessun difetto TGC dimostrato e nessuna modifica proposta al
plugin. La prova OTT sotto distingue i quattro casi con dati osservabili.

## Redditi e trasferimenti

Le sei definizioni coincidono strutturalmente con il merge upstream
`9a24bd649`. Le tecnologie sono nella stessa catena culturale. Ogni curva precedente è
spenta dalla tecnologia immediatamente successiva. La coppia `the_police_state`
si esclude tramite `year = 1990` e la sua negazione. Con progressione ordinaria
è attiva al massimo una curva. Una fixture con tecnologie saltate potrebbe
attivarne più di una e va esclusa dal confronto principale.

| Ultima tecnologia della catena | Guardia aggiuntiva | Bonus poveri/medi/ricchi | Output per 100 netti per strato |
| --- | --- | --- | --- |
| Nessuna | Controllo | 0 / 0 / 0 | 100 / 100 / 100 |
| `state_n_government` | Senza `nationalism_n_imperialism` | 5% / 2,5% / 1% | 105 / 102,5 / 101 |
| `nationalism_n_imperialism` | Senza `revolution_n_counterrevolution` | 10% / 5% / 2,5% | 110 / 105 / 102,5 |
| `revolution_n_counterrevolution` | Senza `mass_politics` | 15% / 10% / 5% | 115 / 110 / 105 |
| `mass_politics` | Senza `the_police_state` | 25% / 15% / 10% | 125 / 115 / 110 |
| `the_police_state` | Fino al 31 dicembre 1989 | 40% / 25% / 15% | 140 / 125 / 115 |
| `the_police_state` | Dal 1º gennaio 1990 | 50% / 40% / 25% | 150 / 140 / 125 |

Il plugin usa l'importo netto positivo in unità fisse da 1/32768. Per ogni
pagamento supportato moltiplica per `max(0, 1000 + provincia + paese) / 1000`
con troncamento intero, leggendo gli offset del solo strato del POP. Usa il
paese proprietario della provincia. Lascia invariati importi non positivi e
chiamate estranee ai sette siti di reddito (vendite artigiane, fabbriche,
RGO, pensioni e disoccupazione). Il fondo per gli input artigiani ha fattore
uno. I modificatori preesistenti si sommano negli stessi accumulatori di
provincia e paese. Esempio con `state_n_government` e
`international_zone_modifier` nazionale (5/10/25%) e nessun contributo
provinciale: 100 netti diventano 110 / 112,5 / 126. Con un ulteriore +10%
provinciale ai poveri diventano 120 / 112,5 / 126. [Sorgente redditi](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/income_modifiers.cpp#L10-L76)

Il Task 56 ha osservato la ricorrenza di 53. Il confronto strutturale mostra
la rimozione dei sei blocchi `any_country` di trasferimento POP. Restano
il richiamo a un giorno e il ramo `override_campaigns`, che agisce sulla
tesoreria nazionale tramite `add_tax_relative_income`. La rimozione evita
di sommare i vecchi trasferimenti ai nuovi pagamenti. Le spese condizionali
delle campagne vanno misurate a parte.

## CB ed eventi di chiusura

`acquire_province` conserva la definizione del commit upstream `cc9d98ca2`.
È `is_triggered_only`, richiede un bersaglio con Stato non coloniale senza
capitale e applica le guardie upstream su civiltà, vicinanza/porti/guerra,
relazioni e politiche dell'IA. `allowed_states` esclude capitali e core del
richiedente e contiene le eccezioni coloniali e i filtri territoriali e
diplomatici dell'IA. Il plugin presenta una voce per provincia e applica la
validità del motore. La scelta memorizza l'ID, che viene usato da costo e
trasferimento. Con `peace_cost_factor = 1` il contributo territoriale atteso
è il valore nativo di quella sola provincia, con la scala e gli arrotondamenti
del motore. Se due province valgono rispettivamente 12 e 7 punti nativi,
il termine deve usare 12 o 7 secondo l'ID scelto, mentre il contributo
territoriale del corrispondente termine per l'intero Stato è 19. Con
`badboy_factor = 1.0` la base è `INFAMY_DEMAND_STATE = 5`
prima degli aggiustamenti situazionali. I 14 punti del trattato volontario
del Task 56 non stabiliscono il numero mostrato per l'obiettivo di guerra.
[Selettore e costo](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/demand_province.cpp) · [Calcolo nativo](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/docs/re/systems/casus-belli.md#peace-cost-wargoal_peacecost-0x00951920-c)

All'aggiunta dell'obiettivo, `dismantle_cb` e `dismantle_cb_add` marcano
il bersaglio con `dismantle_declared`. Il primo avvia 96000 direttamente,
mentre il secondo lo avvia nel ramo fuori da una grande guerra. Il flag
impedisce di riaggiungere `dismantle_cb_add` tramite le condizioni ordinarie.
All'accettazione entrambi i CB impostano i due
flag sul perdente e invocano il vincitore con `dismantled_by` o la variante
`_gw`. `great_war_penalty_cb` mantiene riparazioni e usa il ramo Extender
nel caso `rank = 16` oppure colonia, tramite provincia posseduta. Il plugin
accoda per perdente, trattiene il primo vincitore e alza il budget al
massimo tra le richieste ancora in coda. Dopo la pace bilaterale presenta
l'editor al vincitore umano o applica il trattato dell'IA. La chiusura script
96094 richiede invece che il perdente sia fuori da **ogni** guerra e abbia
entrambi i flag. Con i due flag 96021 e gli altri dieci eventi legacy
guardati sono inibiti. 96094 pulisce entrambi i flag, gli altri flag/modificatori
di guerra e applica esaurimento, infamia e prestigio. Non effettua ulteriori
cessioni. Dopo la pulizia entrambi gli eventi perdono le loro condizioni,
salvo nuovo conflitto o nuovi flag. Con `se_treaty_dismantled` assente,
`ultimatum_accepted` oppure `dismantling_treaty` può attivare 96021 con
le sue guardie di tag, rango, colonia e pace. 96021 consuma i flag della
catena legacy e può applicare effetti punitivi e invocare 96030. La sola
`se_treaty_dismantled` blocca 96021 senza rendere eleggibile 96094. I produttori
controllati impostano entrambi i flag nello stesso ramo. Con un vincitore
umano è da misurare anche l'ordine tra editor, firma e 96094, perché 96094
controlla la pace e i flag, senza consultare lo stato dell'editor.
[Coda delle richieste](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/script_extender/src/features/treaty.cpp#L1939-L1958)

Per la concorrenza controllare anche una pace con più effetti di
smembramento per lo stesso perdente e un caso in cui 96021 era già
eleggibile prima che fossero impostati i flag Extender. Se il motore ha già
accodato l'evento, registrare se rivaluta il trigger prima di offrirlo o
eseguirlo. Le guardie statiche dimostrano l'esclusione al momento della
valutazione, mentre il comportamento di una coda preesistente è aperto.
Nelle prove legacy usare separatamente i due flag alternativi e ripetere
con un tag escluso o con una guerra ancora aperta come controllo negativo.

## Sessione finale unica

Alla successiva autorizzazione, preparare una sola copia isolata come nel
Task 56, verificare hash, destinazioni utente e piano di deployment. Usare
un salvataggio base 1836 e checkpoint indipendenti per prova, all'interno
della stessa directory. Tenere attivi i log diagnostici necessari e copiare
le righe decisive nel rapporto prima del rollback. Per i casi con fixture
registrare le modifiche, il diff dei campi e gli hash dei checkpoint.
Eseguire prima OTT, CB e GW con l'INI del profilo. Per i confronti ECO
riavviare il processo dalla stessa copia dopo il cambio di `income_modifiers`.
Usare infine il checkpoint economico di controllo per E53.

| Prova | Setup e azione | Evidenza e criterio |
| --- | --- | --- |
| OTT | Francia 1836, ricreare il checkpoint dell'11 gennaio dopo Dunkerque, poi imporre la partizione di Ceylon a ENG prima della prova ottomana. Attivare `treaty_dismantle_log` e invocare `dismantle TUR RUS gw` in pausa. Registrare versione, data, rango, capitale, occupazione, core e Stati prima dell'invocazione. | Conservare indice dello scarto a partire da zero, ordine delle clausole gratuite e righe accettate del selettore IA con CB, cedente, beneficiario, provincia e Stati. Verificare 23/496/500 e 22 applicate prima di attribuire il risultato alla stessa prova. Se si discosta, confrontare i due assetti e registrare la riproduzione come differente. |
| OTT, attribuzione | Dallo stesso checkpoint, ricostruire nell'ordine i termini osservati. Con una fixture di prova isolata riprodurre il termine da solo e dopo le clausole precedenti, verificando la validità dopo ciascuna mutazione di proprietà, capitale, core o soggetto. Se il log non basta, usare osservazioni diagnostiche in sola lettura. | Termine valido da solo e invalido dopo una mutazione pertinente indica rifiuto coerente. Se il selettore ha abbinato due richieste incompatibili, annotare anche il problema di composizione. Un riferimento TGC errato è un difetto di contenuto solo con riscontro nella mappa e nelle condizioni. Se i requisiti effettivi sono ancora soddisfatti, conservare il caso minimo come possibile difetto del plugin. Senza indice e stato prima del termine, attribuzione inconclusiva. Dipende da OTT. |
| CB | Da un checkpoint con CB concesso via fixture e attaccante umano, scegliere uno Stato multi-provincia con almeno due bersagli leciti. Provare ciascuna scelta dallo stesso salvataggio, più un controllo con capitale/core e uno con `acquire_state`. Concludere la pace sul bersaglio selezionato. | Salvare righe UI, ID del goal, costo e infamia prima/dopo, più diff proprietari. PASS con filtri rispettati, valore nativo della sola provincia, base infamia 5 a parità di condizioni e cambio del solo ID scelto. Confrontare con il valore nativo per singola provincia o una fixture equivalente di Stato a singola provincia. Il solo confronto col trattato volontario è insufficiente. |
| GW | Preparare una guerra con CB di smembramento, un perdente idoneo a 96021 e un vincitore prima AI, poi umano. Accettare e rilevare flag e coda prima e dopo la pace. Eseguire anche il ramo della penalità GW con un perdente idoneo e uno escluso, una pace bilaterale con seconda guerra ancora aperta, il caso legacy con solo ultimatum e il caso con un solo flag Extender. | Registrare log, trattato, proprietari, flag e contatori di occorrenza su più giorni. PASS se una richiesta ancora in coda per perdente produce un solo trattato, 96094 chiude una sola volta dopo la pace generale, il legacy non consuma i flag durante lo smembramento e non ci sono cessioni duplicate. Per l'umano ritardare la firma di alcuni giorni e registrare se 96094 precede la firma e con quali effetti. Per i rami negativi verificare assenza del trigger previsto, senza dedurla dal solo mancato evento casuale. |
| ECO | Caricare copie abbinate di un checkpoint con POP campione povero/medio/ricco e pagamenti positivi. Usare le sei configurazioni tecnologiche e il controllo della tabella. Misurare il pagamento netto per categoria con opzione disattivata/attivata a stato iniziale identico. Provare cumulo paese/provincia e attraversare il 31 dicembre 1989. La fixture tardiva deve neutralizzare esplicitamente la fine partita dell'evento 55, in modo locale e documentato. | Conservare tipo, proprietario, saldo pre/post, categoria, netto di controllo e modificatori aggregati per ciascun POP. PASS se il pagamento scala con la formula entro la granularità fissa, i non positivi e i trasferimenti estranei restano uguali e dopo il ricalcolo del 1990 si applica soltanto l'ultima curva. Se si dispone soltanto dei saldi giornalieri aggregati, la misura puntuale resta inconclusiva. |
| E53 | Stesso checkpoint economico. Confrontare `override_campaigns` spento e acceso. Provare ogni campagna singolarmente su un paese umano e un controllo AI o senza requisito. Per `direct_immigration` usare una sola provincia per edificio e poi entrambi. | Registrare base del gettito e delta di tesoreria attribuibile all'evento, isolando il tick normale. PASS se i rami applicabili producono i coefficienti `−0,4/−0,8` (infamia), `−0,2` (colonizzazione, turismo, emigrazione, ricerca), `−0,2/−0,3/−0,4` (natalità), `−0,3` (scout), `−0,02/−0,01` per gli edifici e se i controlli danno zero. Verificare il richiamo già osservato mentre si misura il tick. Dipende dai controlli economici di base. |

Al termine verificare rollback e assenza di transazioni pendenti, registrare
le evidenze e rimuovere la sola directory autorizzata dopo verifica dei
percorsi protetti, come nel Task 56.

## Regressioni

Le verifiche statiche controllano l'override della mappa, il CB, i due flag,
i trigger e i valori delle sei curve, e il richiamo di 53 con ID e ritardo
esatti. Il confronto con il riferimento pubblico conferma che `TGC`,
Timeline 1966, descrittore e catalogo condivisi sono invariati. Nessuna
correzione di contenuto candidata a upstream. I validatori 1966 non sono
pertinenti a questo perimetro.

Il primo avvio della suite completa dalla cartella temporanea predefinita
ha evidenziato un problema della fixture Windows. In un test riprodotto,
la destinazione nel record aveva `OpenAI.Codex` mentre il percorso passato
dalla fixture aveva `openai.codex`. Il confronto esatto della destinazione
ha quindi lasciato la transazione simulata in elenco. Nella directory
temporanea dedicata nel progetto, la suite completa ha registrato 103 test
riusciti e 5 saltati per indisponibilità di collegamenti o junction su
Windows. Gli 8 test mirati Extender sono tutti riusciti, anche separatamente.

La verifica finale ha confermato l'assenza della directory delle fixture
nel progetto e di fixture residue nella cartella temporanea predefinita.
La copia del Task 56 è tuttora assente. Nessuna installazione, DLL o
transazione di deployment reale è stata creata per il Task 57.
