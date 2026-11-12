# Task 56 · Collaudo isolato di `core+extender`

Esito **parziale** su Victoria II 3.04 Windows x86 (Steam build 4904558,
`v2game.exe` SHA-256 `62d48c204364dd706584777c2e2b3c7ab3c5f1dd0170872554943575d53d6648`).
Avvio diretto dell'eseguibile originale dalla copia dedicata con
`-mod=mod/TGCScriptExtender.mod` e la libreria Steam originale.

## Bundle e deployment

Il [bundle ufficiale 3.0.0](https://github.com/The-Grand-Combination/The-Grand-Loader/releases/expanded_assets/3.0.0)
ha SHA-256 `e5ca3b29c9d17870ca2235eacc9ca1759251467827c39e82ece1045d3c59dfba`.
Il log riporta The Grand Loader 1.1.0 e un solo plugin, Script Extender 0.1.0.
Le quattro opzioni previste dal profilo erano attive. Le cinque funzioni
facoltative e il Performance Patch erano disattivati. I log diagnostici di
edilizia e smembramento erano attivi nell'ultima sessione.

| Tentativo | Transazione | SHA-256 del manifest | Esito |
| --- | --- | --- | --- |
| Iniziale | `bdce2840c1c84d6499d9d9d80560dde6` | `7a60c57dc7ca3d225d2d38c19f8d2ad5bff5756dc5a7ee9cb635b1ba75b74088` | Plan, apply e verify riusciti. All'avvio il Loader si inizializzava, poi il gioco usciva con codice 3 cercando `mod/TGC/map/definition.csv`. |
| Corretto | `cabd43c74f774665b6fe6a830744c608` | `0a4c39ecb18bbe39f52ee1db38015158a22c88e5c00e518d1cc6681290bc464a` | Plan, apply e verify riusciti. Il profilo ha avviato la partita del 1836. |

Il commit locale `fabb6434a430f0266a24c750ffa7fd5ef7b71008` corregge
il percorso in un override di `map/default.map` dedicato all'Extender e
aggiunge una verifica di regressione. Suite di deployment: 108 test, 106
riusciti e 2 saltati. La correzione riguarda soltanto il profilo facoltativo.

## Risultati in partita

| Meccanica | Osservazione | Limite |
| --- | --- | --- |
| CB, interfaccia e salvataggio | Il plugin ha combinato `cb_types.txt` del profilo con `se_treaty_cbs.txt`. L'editor localizzato ha mostrato Belfast a 9 punti e Dunkerque a 14. L'IA britannica ha accettato la cessione di Dunkerque (punteggio di accettazione nel log 529). Nel salvataggio la provincia 400 passa da FRA a ENG e la partita dell'11 gennaio 1836 si riapre con il nuovo proprietario. | Provato il costo della clausola di trattato. Da provare il costo di `acquire_province` come obiettivo di guerra. |
| Smembramento | `dismantle ENG` come Francia ha selezionato British Ceylon. Il salvataggio conferma il passaggio di 1321–1324 da ENG a SRI e 1325 rimane MLD. `dismantle TUR RUS gw` ha selezionato 23 clausole per 496 punti, ne ha applicate 22 e ne ha scartata una in fase di convalida con `SE_TREATY_TERM_INVALID`. Bulgaria, Romania e Albania sono diventate indipendenti. | Invocazioni diagnostiche. Resta aperta la causa dello scarto e resta da riprodurre l'intera sequenza da dichiarazione di guerra a pace. |
| Interessi territoriali dell'IA | Il plugin ha caricato 32 liste. In `dismantle PER RUS gw` la provincia 1113 era `of interest`, costava 21 punti ed è passata da PER a RUS. Il log registra nove clausole applicate. | Singolo caso diagnostico. |
| Edilizia dell'IA | Il plugin ha letto dal profilo università (probabilità 0,10, soglia monetaria ×3) e banca (0,15, ×2). La Spagna ha ordinato entrambe in provincia 474 e il Liechtenstein una banca in provincia 3253. Il riepilogo a 30 giorni riporta 1 università e 6 banche ordinate. | Verificati gli ordini. |
| Eventi 96021 e 96094 | In una copia del salvataggio, il Belgio in pace è stato predisposto con entrambi i flag. Il log del 3 febbraio registra `The Treaty of Bruxelles`. Nel salvataggio successivo entrambi i flag sono assenti e le province belghe sono identiche. | Caso post-pace sintetico. L'esito dell'intera catena in una guerra giocata resta da verificare. |
| Evento 53 | `Daily Updater` osservato giornalmente in Jan Mayen fino al 3 febbraio. Nel salvataggio `event=53` è in coda per il giorno successivo. | Non sono stati isolati in partita i singoli effetti condizionali. |
| Sei curve di reddito | Il log conferma l'inizializzazione di sette hook di pagamento POP. | Importi delle sei curve e transizione del 1990 da verificare con misure controllate. |

SHA-256 delle evidenze principali:

- CB combinati `e14b5e51bdafd0e00f109aeaf49427380314b926aa0cb654127ddae2a935231b`.
- Salvataggio dell'11 gennaio dopo la cessione `5b4805a2bc1578cb9d8d4114451f3010aee29002631cc1f059c0543966b5d8fb`.
- Salvataggio diagnostico del 3 febbraio `2918bb1135cd3c752b8909404c96ab6028cdc57dfc6e1e2a423c22f372d7bc83`.
- Log Loader dell'ultima sessione `c5fa8ea289d67a484c8b4a474f7869129ae6f2bc0039ac1894d3591f059b1643`.
- Log di gioco dell'ultima sessione `5fc9e75e19e2d1bc5ef4098b6a8ffc1fd8b39a095741fbaa614ec777b5e45b7c`.

## Isolamento e verifica dei percorsi protetti

La directory temporanea autorizzata `TGC-Task56-isolated` comprendeva le copie
del gioco, archivio ed estratti del Loader, DLL, configurazioni, cache,
salvataggi, log, backup, ricevute, metadati di deployment e file di controllo.
Prima dell'avvio `userdir.txt` indicava un percorso assoluto interno e il
descrittore usava `user_dir = "TGCScriptExtender"`. Durante le sessioni i dati
utente sono comparsi in quel percorso e log del Loader e CB generati nella
copia del gioco. L'ultima sessione si è chiusa con codice 0 e i log di errore
di Victoria II erano vuoti.

Il confronto prima/dopo ha restituito la stessa impronta per le 144.970 voci
di Steam (installazione e manifest), dati Paradox e deployment condiviso
(`ca37313ac50d954a3e4dcef8d5afd73250749bc8721a8efa569ca0766ffd4ef2`).
Anche l'impronta separata degli 8 file degli scenari Alice coincide
(`570a2f4241fc6cc53be2cf4d19a68cff752c97e7803fe4e7a0c104bd87803606`).

## Chiusura e pulizia

Entrambi i deployment sono stati annullati tramite il tool ufficiale. Prima
della rimozione, la verifica finale ha confermato l'assenza della coppia
gestita, di componenti ancora in ownership e di transazioni pendenti in
entrambi gli stati. Backup, ricevute e metadati sono rimasti disponibili fino
alla chiusura verificata.

Rimossa `C:\Users\thoma\.codex\.chatgpt-projects\g-p-6825a7a014648191916975de34a36f0d\TGC-Task56-isolated`
dopo aver verificato percorso risolto, data di creazione e assenza di punti
di reparse. La rimozione ha incluso `game`, `retry`, `bundle`, `user-data`,
`deployment-state`, `evidence`, `scratch` e i file di controllo nella radice.
La copia iniziale di `game/assets` era già stata rimossa durante la preparazione,
sempre all'interno della stessa directory. Alla rimozione finale c'erano
51.632 file per 3.395.007.507 byte logici. La verifica successiva ha trovato
la directory assente e nessun residuo nella cartella padre, per 0 byte di
artefatti temporanei rimasti. La documentazione e la correzione restano nel
repository locale. Nessun push.
