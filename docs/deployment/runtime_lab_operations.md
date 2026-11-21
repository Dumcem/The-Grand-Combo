# Operazioni e archivio del laboratorio

[Ammissione e confine di isolamento](runtime_lab.md) · [Matrice delle verifiche](runtime_lab_matrix.md)

## Punto di ingresso locale

Dalla working copy canonica, in una sessione Windows ordinaria con Git e
Python 3.11+ raggiungibili. Sulla macchina del Task 11 l'archivio è
`%LOCALAPPDATA%\TGC-Runtime-Lab`, sul disco locale. In AppContainer risolvere
prima il vero percorso dell'host o usare un percorso assoluto già verificato.

```powershell
$lab = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TGC-Runtime-Lab'
$tool = 'tools/deploy/runtime_lab.py'
Get-Content "$lab\baselines\index.json", "$lab\sessions\task10\summary.json"
python -B $tool rebuild-smoke --lab-root $lab --run infra-20261120-01
```

`rebuild-smoke` è il gruppo infrastrutturale locale. Riusa la fixture
`sentinels-v1`, crea, modifica ed elimina file sintetici in una copia
sacrificabile, ricostruisce una seconda copia e confronta le due baseline.
Registra i percorsi host variati, se presenti. Ogni esecuzione usa un ID nuovo.
Lo stdout è un oggetto JSON breve. Il codice di uscita è 0 per un passo
riuscito, 1 per un arresto o errore e 2 per un cache miss.

| Directory | Contenuto |
| --- | --- |
| `baselines/` | `index.json` per trovare installazioni inventariate e stato delle dipendenze, catalogo locale dei percorsi da proteggere, input verificati per ID e cache scenari. |
| `fixtures/` | Dati sintetici immutabili con ricetta e checksum. I salvataggi richiedono una provenienza identificata e una copia ammessa al laboratorio. |
| `sessions/<id>/` | Riepiloghi JSON, controlli prima/dopo, manifest e log grezzi in `raw/`. Per `task10`, preservare le ricevute storiche con i percorsi originali. |
| `transfer/<id>/` | Richiesta e uscita dedicata per una singola sessione Sandbox. |
| `scratch/` | Copie sacrificabili create dagli strumenti. I checkpoint di VM sono facoltativi e ammessi solo con una VM già autorizzata. |

Per inizializzare un nuovo archivio, creare queste directory su un volume
locale fuori da checkout, Steam, directory temporanee, profili di gioco e
cartelle sincronizzate. In `baselines/host-protected-paths.json` conservare
un oggetto JSON con etichette e percorsi assoluti, rilevati secondo la
[guida di ammissione](runtime_lab.md#ammissione-al-primo-avvio). Includere
i rami di stato e le radici dei journal attivi. Rivedere il catalogo quando
si spostano Steam, i profili o i target. Su inventari storici distinguere
alberi completi da percorsi espliciti selezionati.

## Preparazione gratuita di Windows Sandbox

La funzionalità `Containers-DisposableClientVM` è inclusa in Windows 11 Pro.
L'abilitazione richiede autorizzazione amministrativa e può richiedere
riavvio. Dopo l'abilitazione verificare la presenza dell'app o di `wsb.exe`
e la console interattiva. L'hypervisor attivo da solo non dichiara operativa
la Sandbox o disponibile un guest Hyper-V autorizzato.
[Installazione Microsoft](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install) · [CLI Microsoft](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli)

1. Generare la configurazione per la sola fixture di ammissione.

   ```powershell
   python -B $tool sandbox-config --lab-root $lab --run admission-01 `
       --baseline admission-v1 --commit HEAD --engine alice --profile core
   python -B $tool host-check --lab-root $lab --run admission-01 --phase before
   ```

2. Esaminare `sessions/admission-01/session.wsb`. La funzione genera XML
   con rete, clipboard, stampanti, microfono e videocamera disabilitati,
   Protected Client attivo e vGPU disattivata per la prima ammissione.
   L'input e la richiesta sono mappati in lettura. L'unica cartella
   scrivibile è un outbox inizialmente vuoto, sotto `transfer/<id>/`.
   Conservare host e guest in condizioni quiete. Avviare la configurazione
   solo quando la funzionalità è operativa e la console osservabile.
   [Configurazione Microsoft](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file)
3. Nel guest provare creazione, modifica e rimozione di sentinelle in
   `C:\TGCInput` e `C:\TGCRequest`, verificando il rifiuto di tutte le
   scritture e l'identità dei file sull'host. Provare una scrittura in
   `C:\TGCOutbox` e verificarne il solo effetto atteso sull'host. Verificare
   che i percorsi personali e il resto dell'archivio siano irraggiungibili
   dalla Sandbox. Creare, modificare e rimuovere altre sentinelle sotto
   `C:\TGC-Lab` e nelle Known Folders del guest. Conservare i comandi, i
   loro output e una prova osservabile della console.
4. Chiudere completamente l'istanza. Avviare una seconda sessione con un
   nuovo ID e gli stessi input. Verificare che le modifiche guest siano
   sparite, le sentinelle di ingresso coincidano e il nuovo outbox sia
   vuoto. Eseguire `host-check --phase after` per le due sessioni dopo la
   rispettiva chiusura. Il comando confronta anche i mount dichiarati in
   sola lettura. Una differenza richiede diagnosi prima di proseguire.
   Un test del solo XML o del filesystem host non qualifica i mount guest.

## Preparazione di una baseline motore

Creare `baselines/<id>/input/` con **copie dedicate** di materiale
legittimamente utilizzabile nel guest e verificato offline. La baseline
di ammissione contiene solo sentinelle. Preparare la baseline di motore
dopo la qualifica sintetica.

- `checkout.bundle` contiene la cronologia necessaria alla revisione.
  Crearlo con `git bundle create <nuovo-percorso-assoluto> <ref>` usando un
  ref contenente il commit scelto. Riutilizzarlo finché contiene i commit di
  prova. Il bootstrap clona localmente e imposta l'origin canonico prima
  del deploy.
- `games/Shared` contiene Victoria II 3.04 e, per i profili Alice, i file
  Alice 1.3.0 accanto agli asset base. `games/Loader` e `games/Loader1966`
  contengono copie distinte dei plugin e degli INI. Basta inserire le
  radici che la baseline supporta. Escludere salvataggi personali,
  dati Steam utente, cache, payload TGC precedenti e stati di deployment.
  Annotare provenienza, release, SHA-256 e condizioni per l'avvio offline.
  La licenza dell'host non concede automaticamente una seconda
  installazione Windows per una VM alternativa. Usare soltanto un sistema
  guest per cui i diritti siano già documentati. Per Steam non trasferire
  credenziali né aggirare requisiti di avvio. [Profili](runtime_lab.md#radici-e-prerequisiti)
- Fornire nel guest Git e Python da distribuzioni offline attendibili e
  autorizzate. Conservare versione e impronte. Stagiare il set
  `runtime_lab.py`, `deploy_tgc.py`, `snapshot_runtime_paths.py` sotto
  `input/tools` dalla revisione di tooling scelta. Serve anche per testare
  revisioni TGC anteriori al Task 11. Il deploy effettivo richiama
  `deploy_tgc.py` dal checkout selezionato.
- Le cartelle mappate devono essere dedicate, con file ordinari e prive
  di link. Il generatore controlla l'input e registra il suo digest. Tenere
  l'input fermo dalla generazione del file `.wsb` alla chiusura del guest.
  Una baseline incompleta resta bloccata anche se la configurazione XML
  è stata prodotta.

## Sessione motore e riuso

1. Eseguire `sandbox-config` con l'ID baseline di motore, il commit,
   `--engine alice|victoria2` e il profilo della [matrice](runtime_lab_matrix.md).
   Passare `--cache-key` per una voce Alice disponibile. La voce viene
   esposta da sola e in lettura come `C:\TGCScenarioEntry`. Aggiungere
   `--vgpu` soltanto dopo aver qualificato anche quella
   configurazione. Eseguire `host-check --phase before`, aprire la Sandbox
   e ripetere i controlli applicabili alla sessione. Provare i prerequisiti
   grafici e l'avvio legittimo offline nei passaggi di ammissione.
2. Dopo avere osservato il confine, creare nel guest
   `C:\TGC-Lab\admission.json` con `status: "pass"`,
   `request_sha256` dal riepilogo della configurazione e i riferimenti
   alle prove osservate. Il file è una ricevuta della verifica svolta.
   Eseguire dalla console guest con Python e Git disponibili:

   ```powershell
   $tool = 'C:\TGCInput\tools\runtime_lab.py'
   python -B $tool guest-deploy
   ```

   Il comando verifica il digest degli input, crea checkout e copia gioco
   nel guest, seleziona il profilo e richiama `plan → apply → verify`. Il
   controllo automatico del piano confronta commit, profilo e percorsi e
   si ferma per blocker o adozione. Per Loader imposta `userdir.txt` della
   copia guest su una cartella privata del profilo. Il riepilogo e gli output per ogni fase
   finiscono in `C:\TGC-Lab\Evidence`.
3. Per Alice verificare per prima la cache. Preparare un breve
   `identity.json` con `engine_version`, `engine_sha256` della variante
   effettivamente qualificata, `profile`, `manifest_sha256` dal deploy,
   `baseline_sha256`, `scenario_parameters` e `scenario_checksum` già
   osservato. I digest sono SHA-256 esadecimali minuscoli. La cache
   confronta l'intero record, verifica le impronte del contenuto e copia
   soltanto in una destinazione nuova.

   ```powershell
   python -B $tool scenario-reuse --identity $identity --entry C:\TGCScenarioEntry --payload $newFolder
   # Su cache miss (exit 2) o al primo build senza un checksum storico:
   python -B $tool guest-alice-build
   ```

   La cache è un input dedicato di sola lettura nel guest, mantenuto
   separato dal bundle e dalle radici usate per il digest della baseline.
   In un hit collocare gli output nella Known Folder del guest
   come indicato dalla ricetta originaria. In una nuova build preservare
   anche i file bookmark generati prima della partita, quando presenti.
   Usare `scenario-store --identity <file> --cache <radice> --payload <cartella>` dopo aver osservato il
   checksum effettivo e trasferito il payload in host. Per una cache
   corrotta il comando si ferma con errore. Conservare la ricevuta per
   diagnosi e ricostruire in un nuovo percorso.
4. `guest-alice-build` usa il launcher e la selezione dal profilo verificato.
   Registra exit code, hash, scenario e diagnostica. L'esito `generated`
   indica un file presente, con caricamento ancora da riscontrare.
   Per il primo smoke aprire lo scenario dal launcher Alice, osservare
   profilo, finestra e checksum, avanzare e salvare un dato sintetico, se
   praticabile. Per Victoria II usare la composizione esatta della matrice,
   inclusa la radice dedicata e l'avvio in finestra per Loader. Registrare
   le osservazioni e le evidenze richieste per il singolo caso. Fermarsi
   se l'esecuzione offline richiede una dipendenza non disponibile o se il
   profilo risulta incompatibile nel guest. I casi di gioco in matrice
   richiedono ancora osservazioni e fixture specifiche.
5. Chiudere i motori e raccogliere in `Evidence` output scelti, log e
   osservazioni. Usare `python -B $tool guest-export` e attendere la
   ricevuta SHA-256 nell'outbox prima di chiudere la Sandbox. Per la
   chiusura da CLI seguire la verifica qui sotto. Poi eseguire sull'host
   `host-check --phase after` e `archive-export` con lo stesso `--lab-root`
   e `--run`. Il trasferimento archiviato viene confrontato con la ricevuta
   e pubblicato in `sessions/<id>/raw`. Conservare un drop non verificato
   per diagnosi. Ricostruire una nuova sessione dagli stessi input e
   verificare le sentinelle.

### Verifica della chiusura da CLI

Usare l'ID conservato in `sandbox-start.json` per `wsb stop --id <id>`.
Conservare l'ora UTC, l'esito di `stop` e l'output di `wsb list --raw`.
Richiedere esito zero da entrambi i comandi e un oggetto JSON con
`WindowsSandboxEnvironments` di tipo array. Verificare che l'ID della
sessione sia assente. Nelle ricette che partono senza altri guest attendere
un array vuoto. Il controllo con il solo `.Count` nelle ricette locali
dei Task 14 e 15 accetta anche un campo assente o nullo. Se la lista è
assente o invalida, conservare il drop e trattare la chiusura come non
verificata. [CLI Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli#stop)

`stop` termina il guest e chiude la finestra del desktop. `list` riguarda le
sessioni dell'utente corrente. Un dialogo di disconnessione richiede un
riscontro temporale separato con il client e lo stato del guest.
[Evidenza storica e condizione di riesame](../rebaseline_backlog.md#verifiche-runtime)

## Manutenzione

- Aggiornare il checkout da Git, risolvere il commit, verificare bundle e
  stato pulito. Registrare commit, motore e variante, profilo, fixture,
  scenario e checksum, data UTC, esito e riferimenti ai dati grezzi.
  Confrontare sessioni tramite i riepiloghi prima di leggere i log.
- Per aggiornare una dipendenza o baseline, creare un nuovo ID,
  documentare la compatibilità e conservare l'input precedente finché
  uno scenario, una fixture o un risultato vi si riferisce. Verificare
  periodicamente la presenza e l'integrità degli input e l'accesso offline.
  Una release del motore si adotta dopo audit, secondo `AGENTS.md`.
- Aggiungere casi alla matrice con input, osservazione e criterio di
  chiusura. Riutilizzare fixture e scenari solo quando identità e impronte
  corrispondono. Per ampliare il laboratorio estendere questi comandi e
  gli stessi schemi di evidenza.
- Conservare i riscontri di riferimento, i manifest, i log di fallimento
  e le ricette delle fixture. Dopo una verifica d'integrità, rivedere
  periodicamente doppioni, drop già importati e cache obsolete. Prima
  di una rimozione verificare il percorso assoluto, i riferimenti e la
  riproducibilità. La pulizia dei dati durevoli è una decisione esplicita.
  `rebuild-smoke` elimina soltanto le cartelle scratch univoche che crea.

## Riscontro del Task 11

Il checkpoint iniziale locale e remoto era
`d003e53e3272f97ba60766a961d21591801f5ad6`. Su Windows 11 Pro,
`Win32_OptionalFeature` indicava stato 2 (disabilitato) per
`Containers-DisposableClientVM` e `Microsoft-Hyper-V-All`. Era disponibile
Virtual Machine Platform e l'hypervisor risultava attivo. Mancavano un
launcher Sandbox e un guest autorizzato utilizzabile. Gli account
ausiliari esaminati erano account Codex, senza una sessione di prova.
Resta necessaria l'autorizzazione amministrativa ad abilitare la
funzionalità inclusa, seguita dalla qualifica sintetica dei mount e dal
riscontro grafico e offline. Nessuna nuova spesa.
[Stati di Win32_OptionalFeature](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-optionalfeature)

Il Task 10 è archiviato in `sessions/task10`. Copia integrale verificata con
SHA-256 su **16.574 file, 110 directory e 393.701.734 byte**. Gli originali in
TEMP sono stati preservati. Il gruppo `rebuild-smoke` ha verificato
creazione, modifica, cancellazione e ricostruzione di sentinelle. I 103
percorsi protetti sono risultati identici nell'archiviazione e nella prova
locale. La configurazione `.wsb` sintetica è stata generata e l'XML
validato. I permessi dei mount e gli avvii dei motori restano da verificare
nel guest.

La prova nativa `sessions/t11-orchestration` ha collaudato il checkout da
bundle, la selezione del profilo `core`, la preparazione della radice
sintetica e i tre comandi del deployer. Gli exit code `plan`, `apply` e
`verify` sono tutti 0. I 103 percorsi protetti coincidono e la copia
sacrificabile è stata rimossa. Cinque test locali passano per
ricostruzione, mapping XML, ricezione delle evidenze e riuso cache.

## Riscontro del Task 12

Il 20 novembre 2026 `Containers-DisposableClientVM` risultava abilitata
su Windows 11 Pro, con il launcher presente e senza segnali di riavvio
pendente nei controlli di servicing. Il launcher ha completato la
predisposizione iniziale del client Microsoft Windows Sandbox 0.8.114.0.
La revisione usata nelle prove è `3c3be0d63138e3c9ddaef5ca3d2d04a40d3e98c3`.
Sono stati verificati anche gli otto hash delle ricevute di riferimento del Task 10.

Le sessioni `t12-ammissione-01` e `t12-ammissione-02` hanno usato la
stessa baseline sintetica `admission-t12-v1`, con rete, clipboard e
periferiche disabilitate, Protected Client richiesto e outbox separate.
Il Task 14 ha chiarito il limite della [direttiva vGPU storica](#controllo-della-configurazione-grafica).
In entrambe il guest ha creato, modificato ed eliminato sentinelle. Le
scritture sui due mount in sola lettura sono state negate. Nella seconda
sessione, con un nuovo ID Sandbox, erano assenti le sentinelle lasciate
nella prima sotto la radice di prova, Documenti, AppData locale e roaming e
TEMP. Il desktop del secondo guest è stato osservato direttamente. Gli
inventari prima/dopo coincidono per le 103 voci host protette e i due
mount di ingresso. Entrambi gli export sono stati verificati con
`archive-export`.

La sonda ha registrato cinque esiti `false` per sessione a causa del modo
in cui PowerShell avvolge `UnauthorizedAccessException`. Le cinque
operazioni hanno restituito esplicitamente accesso negato. Il riesame ha
confermato anche gli hash invariati e ha conservato intatti i registri
grezzi. L'esito rivisto è in
`sessions/t12-ammissione-02/admission-summary.json`. La traccia disponibile
è il registro delle operazioni sintetiche, con percorso, orario ed esito.

Per ripetere l'ammissione usare `sandbox-config --baseline admission-t12-v1`
con un ID nuovo per ciascuna sessione. Nella configurazione generata,
impostare il comando di accesso sulla sonda archiviata
`C:\TGCInput\probe.ps1`, come negli esempi `.wsb` delle due sessioni.
Usare `host-check` prima e dopo. Chiudere e verificare l'ID con
`wsb.exe list --raw` e `wsb.exe stop --id <id>`. Conservare i risultati
dell'outbox con `archive-export`.

### Smoke Alice 1.3.0 core

`t12-alice-core` ha completato `plan → apply → verify` nel guest con la
revisione `3c3be0d63` e lo stesso profilo di isolamento. Il manifest TGC
ha digest `1dcfee2f661923abf19472c315dc4c4767d5fa8f4759578db806be16ec30ce94`.
Al primo avvio `launch_alice.exe` è uscito con `0xC0000135`. Nel guest
mancavano `MSVCP140.dll`, `VCRUNTIME140.dll` e `VCRUNTIME140_1.dll`,
dipendenze di `LLVM-C.dll`. Le tre copie x64 già presenti sull'host,
firmate da Microsoft, sono state verificate per SHA-256 e affiancate
all'eseguibile nella radice guest. Il mount aggiuntivo ha rifiutato
la scrittura e la verifica del deploy TGC è passata di nuovo.
[Distribuzione locale delle librerie Visual C++](https://learn.microsoft.com/en-us/cpp/windows/deployment-in-visual-cpp)

Il launcher ha generato `tgc-lab-core.bin` e ha avviato `Alice.exe`
(variante AVX2) con quel file. Sono stati osservati il globo del 1836,
l'ingresso in partita con l'Impero russo al 1º gennaio 1836 e il ritorno
al launcher con «Save and Exit». Il salvataggio sintetico è stato
verificato su disco. Il checksum interno Alice nelle intestazioni dello
scenario e del salvataggio coincide. SHA-256 dello scenario:
`dc348af50328d761edc85d78f64c98cbe3611ab0abe0a1634aa85badf31b2ed8`.
La sessione è stata distrutta e le 105 voci inventariate sono
risultate invariate, come l'ingresso ausiliario. L'export di 23 file
comprende `scenario_errors.txt` separato, scenario, salvataggio, manifest,
registro dell'errore iniziale e hash dell'eseguibile. Il riepilogo e
l'identità riutilizzabile sono in `sessions/t12-alice-core/`.
Un ripristino locale dalla cache con `scenario-reuse` ha restituito lo
stesso SHA-256 senza avviare o ricompilare lo scenario.
[Formato delle intestazioni Alice 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/serialization.hpp#L174-L193)

Per preparare una nuova sessione core con cache, dalla sessione Windows
ordinaria usare l'ID della baseline e la chiave registrata.

```powershell
$key = (Get-Content "$lab\sessions\t12-alice-core\runtime-summary.json" -Raw | ConvertFrom-Json).cache_key
python -B $tool sandbox-config --lab-root $lab --run alice-core-02 `
    --baseline alice-130-t12 --commit 3c3be0d63138e3c9ddaef5ca3d2d04a40d3e98c3 `
    --engine alice --profile core --cache-key $key
```

La baseline ausiliaria `alice-130-t12-vc-runtime` contiene le tre DLL e
il loro manifest. Esporre quell'ingresso in sola lettura e verificare
hash e permessi. Copiare le tre DLL solo nella radice di gioco guest
prima di avviare Alice. Nel guest, dopo `guest-deploy`, confrontare
`scenario-identity.json` con la variante usata, il digest del nuovo
manifest e gli hash delle DLL. Usare `scenario-reuse` dalla voce montata
e collocare `scenarios/tgc-lab-core.bin` nella cartella scenari del
guest. Il launcher con il solo descrittore TGC selezionato riconosce lo
scenario. Conservare il controllo host e l'export per il nuovo ID.

## Riscontro del Task 13

Il checkpoint Git iniziale era `ca008ec0b9b4d431cd5a8d1335b43c90a4033166`.
Le prove riusano il bundle `alice-130-t12` a
`3c3be0d63138e3c9ddaef5ca3d2d04a40d3e98c3`. Il delta fino al checkpoint
contiene soltanto documentazione. Si riusano inoltre `alice-130-t12-vc-runtime`,
la configurazione Sandbox storica con Protected Client richiesto e il
client Project Alice 1.3.0 AVX2 con SHA-256
`b1a2d4d664add6f5187d6c4fd92e259930cb1944cdc3636c36ef58e993318c95`.
SHA-256 della baseline di input
`9cfcaec59df040ad0dd709d4551805677fc1e01d517840a6a136c8686e0973eb`.

### Riapertura core

`t13-alice-core` ha completato `plan → apply → verify` nel guest
e ripristinato `tgc-lab-core.bin` tramite `scenario-reuse`. Il
manifest coincide con quello del Task 12
(`1dcfee2f661923abf19472c315dc4c4767d5fa8f4759578db806be16ec30ce94`).
La cache ha chiave
`af6ea133dbbeb22a2fc76c22209fcc0e405c30db850bdad58e19ef71854ae92e`.
Il motore ha riaperto il salvataggio del Task 12 in partita, con l'Impero
russo in pausa al 1º gennaio 1836. Dopo cinque giorni di simulazione
sono stati eseguiti «Save and Exit» e un nuovo avvio di Alice. Il nuovo
salvataggio ha riportato alla partita in pausa al 6 gennaio 1836 con
lo stato osservato prima dell'uscita. I file sono in `raw/synthetic-saves/`
e le immagini in `screens/`.

| Artefatto `core` | Impronta |
| --- | --- |
| SHA-256 dello scenario | `dc348af50328d761edc85d78f64c98cbe3611ab0abe0a1634aa85badf31b2ed8` |
| Checksum Alice dello scenario e dei due salvataggi | `8db62b55a969b9194c823224decd040ff00634670d99c6b6ec7151655b8d944e374c5c5d33f187a7b655e8fae42bead5af2e1bac07ecceaff9d639d5a2ec7815` |
| SHA-256 della fixture RUS del 1º gennaio | `bc2fd6624c8f0fc5f546407893017a3b0e4ff36a2de5d3f71eab1c9d1d5ec096` |
| SHA-256 del nuovo salvataggio RUS del 6 gennaio | `78ca27a008663dfe9ae6b361b1c25586fa92bb2d9170f848eda0a77337edd42b` |

La diagnostica `core` proviene dalla build Task 12 dello stesso scenario,
con 70 errori e 301 warning. Le tre firme di errore con riga diversa
rispetto al Task 36 sono OPTIONS_CANAL. Il limite di opzioni in 36996
ricompare quattro righe prima dopo la rimozione di quattro assegnazioni
a flag provinciali nel file. Il [confronto per ID](../event_orphan_review.md#confronto-diagnostico-alice-130)
riporta 45 firme della coorte EVENT_ORPHAN.

L'export ha verificato 23 file. Al termine `wsb list --raw` non
elencava guest. `host-check` ha attestato 106 ambiti invariati, inclusi
input, richiesta e voce cache. Gli hash dell'input Visual C++ montato
separatamente coincidono nelle due ricevute ausiliarie.

### Qualificazione core+1966

`t13-alice-1966` ha completato `plan → apply → verify` con il manifest
`11b4e5b23edd78dce306b2275cf81aad4052693f83740dc6033d4753d08590ed`.
Il launcher è uscito con codice 0. La maschera `TGC Timeline 1966`
ha selezionato il descrittore Timeline e la sua dipendenza core. Lo
scenario `tgc-lab-core-1966.bin` registra le radici nell'ordine
gioco base, TGC, Timeline. Il deploy verificato conserva gli override
della Timeline, inclusi `common/defines.lua` e `technologies/army_tech.txt`.

Al primo tentativo, Alice ha smesso di rispondere nella transizione
dalla schermata iniziale. Il processo è
stato chiuso e rilanciato con lo stesso scenario. Al secondo tentativo,
selezionando esplicitamente «New Game» e l'Impero russo, la partita
era responsiva e in pausa al 1º gennaio 1836. Dopo sette giorni di
simulazione, «Save and Exit» e un nuovo avvio hanno permesso di
riaprire la partita in pausa all'8 gennaio con lo stato salvato.
La causa del primo blocco rimane indeterminata. Le evidenze del
tentativo sono in `raw/first-entry-stall.json` e `screens/`.

| Artefatto `core+1966` | Impronta |
| --- | --- |
| SHA-256 dello scenario | `e7759c161303653fb86cc47751fca0ec56255c4973852005283b1c05eb59e682` |
| Checksum Alice dello scenario e del salvataggio | `a58c7830726f91b616c8aa4affcc7d02f39e3d67111e00d41dced44834398fc65ca2ee8ade2f8ffb6afa1b208b73025073ab34fe89151d844c6d1227147c14c3` |
| SHA-256 del salvataggio RUS dell'8 gennaio | `5994a55ad7ee296c3d7e9994d4cdf3d64911fc9e31ef32ed710c26253fb3935b` |
| Chiave cache | `0fc64b376b1cdf45eb824da36d723ab8234570c5a4253046c7f473b903ceaa28` |

La build ha riportato 104 errori non fatali e 301 warning. I 34
errori aggiuntivi rispetto a `core` riguardano i campi e riferimenti
storici di tecnologie e invenzioni Timeline. Tutte le firme di errore
coincidono con il Task 36, tenuto conto dello spostamento delle tre
righe OPTIONS_CANAL. I due profili hanno le stesse 301 firme di
warning, con le stesse molteplicità. [Diagnostica storica](../rebaseline_backlog.md#provenienza-della-diagnostica-alice)

`scenario-store` ha conservato lo scenario archiviato. Una prova
separata di `scenario-reuse` ha restituito lo stesso SHA-256.
L'export ha verificato 27 file. Il guest è stato distrutto e la lista
di Sandbox è risultata vuota. I 105 ambiti protetti e gli hash
dell'input Visual C++ coincidono con le impronte iniziali. Le fixture
riutilizzabili sono in `fixtures/alice-130-core-t13` e
`fixtures/alice-130-1966-t13`, con ricetta, impronte e identità dello
scenario.

### Controlli tecnici 1966

- Il validator strutturale è passato su 25 aree, 300 tecnologie e 230
  invenzioni nel perimetro. Ha segnalato 53 limiti semantici Alice come
  diagnostica.
- L'audit ha registrato 0 FAIL, 1.828 WARN e 2.972 INFO. I risultati sulle
  soglie sono calcolati sui valori grezzi degli script con base normativa
  da validare. Le proiezioni motore seguono il perimetro dichiarato
  dall'audit. [Contratto dell'audit](../../TGC/docs/1966_balance_audit.md)
- **PRIORITY SUMMARY.** Undici gruppi di semantica motore, due di
  disponibilità, uno di design e 120 lacune di evidenza. Zero gruppi
  nelle categorie integrità, perimetro sorgenti, invarianti tecniche e
  meccaniche.
- **RECOMMENDED PLAYTEST FOCUS.** L'audit elenca cinque proprietà di
  `aircraftcarrier`: `build_time` (8), `default_organisation` (9),
  `gun_power` (2), `maximum_speed` (2) e `supply_consumption` (8).
  I conteggi derivano dalle regole diagnostiche sui valori grezzi.
- 122 casi del deployer e del laboratorio (6 saltati), 124 casi
  delle suite 1966 e due regressioni Yinxu, tutti con uscita 0.

I log dei due controlli 1966 sono in
`%LOCALAPPDATA%\TGC-Runtime-Lab\sessions\task13\raw`.

### Ripetizione delle prove

Preparare una sessione per volta dalla working copy e assegnarle un ID
nuovo. Usare lo stesso commit del bundle per riprodurre queste prove.
Usare l'identità e la chiave della fixture scelta.

```powershell
$lab = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TGC-Runtime-Lab'
$py = "$lab\baselines\alice-130-t12\input\tools\Python\python.exe"
$tool = 'tools/deploy/runtime_lab.py'
$ref = '3c3be0d63138e3c9ddaef5ca3d2d04a40d3e98c3'
$run = 'alice-core-replay-01'
$fixture = Get-Content "$lab\fixtures\alice-130-core-t13\fixture.json" -Raw | ConvertFrom-Json
# Per core+1966 scegliere alice-130-1966-t13 e un altro ID.
& $py -B $tool sandbox-config --lab-root $lab --run $run --baseline alice-130-t12 --commit $ref --engine alice --profile $fixture.profile --cache-key $fixture.cache_key
```

Replicare il mount in sola lettura delle DLL ausiliarie dal
`session.wsb` della prova. Collocare l'identità, il manifest e la
fixture scelta nella richiesta prima di acquisire
`host-check --phase before`. Avviare con `wsb start --config`
passando il contenuto di `session.wsb` e aprire la console con
`wsb connect --id <id>`. Nel guest usare la procedura di
ammissione e `guest-deploy`, confrontare il manifest e gli hash
effettivi, quindi eseguire `scenario-reuse` con la ricetta sotto
`C:\TGCScenarioEntry`. Collocare lo scenario in
`Documents\Project Alice\scenarios` e il salvataggio in
`Documents\Project Alice\saved games` nelle cartelle utente del guest.
Avviare Alice, selezionare il salvataggio, premere «Play» e controllare
nazione, data e stato. Salvare, chiudere Alice, riavviarlo e ripetere
la selezione con il nuovo salvataggio.

Per ripetere una nuova build Timeline, usare `--profile core+1966` e
omettere `--cache-key`. Dopo `guest-deploy` e il controllo delle
librerie eseguire `guest-alice-build`. Per entrambi i profili, usare
`guest-export` a motore chiuso, poi `wsb stop --id <id>`,
`wsb list --raw`, `host-check --phase after` e `archive-export`.
I controlli host prendono `--lab-root $lab --run $run`.

## Task 14 · Victoria II 3.04 x86

Checkpoint iniziale `8eca8278d73fd78dbd084c89b94c2469d8f18087`,
con `origin/master` a `ca008ec0b9b4d431cd5a8d1335b43c90a4033166`.
Il bundle permanente termina a `3c3be0d63138e3c9ddaef5ca3d2d04a40d3e98c3`.
La differenza rispetto a HEAD riguarda la documentazione. Il Task 13
è attestato dalle ricevute dell'archivio in `sessions/task13`.

La baseline Victoria II riusa `alice-130-t12/input` per i dati
Heart of Darkness, il bundle e gli strumenti. Il binario archiviato
`v2game.exe` è un PE x86 (`0x014c`), identico alla copia Steam
locale per dimensione e SHA-256
`62d48c204364dd706584777c2e2b3c7ab3c5f1dd0170872554943575d53d6648`.
L'identità della base resta
`9cfcaec59df040ad0dd709d4551805677fc1e01d517840a6a136c8686e0973eb`.

Il supplemento `baselines/victoria2-304-x86` contiene 51 file e
134.431.648 byte. Aggiunge gli asset originali mancanti e le librerie
Lua e Steam del gioco. Lo snapshot del supplemento ha SHA-256
`ca0df368d6b50da9a0ffa7e812dc50265ac1060904c32a3b4f207141d03c5c65`.
Il manifest elenca le impronte dei singoli file. L'inventario PE
indica `d3d9.dll`, `d3dx9_41.dll`, Lua, TBB e Steam API.
Lua importa VC80 e TBB importa VC100. Il supplemento conserva il CAB
DirectX x86 distribuito con il gioco e i redistributable Visual C++
2005 e 2010 x86 di Steamworks, tutti con firma Microsoft valida.
L'estrazione DirectX e l'installazione dei redistributable sono eseguite
nella Sandbox. [Requisiti Heart of Darkness](https://store.steampowered.com/app/215001/Victoria_II_Heart_of_Darkness/) · [Deployment Microsoft C++](https://learn.microsoft.com/en-us/cpp/windows/deployment-in-visual-cpp)

### Dipendenza del frontend e avvio offline

Il primo avvio `core` ha caricato TGC, creato il dispositivo
Direct3D 9 e scritto il checksum 3.04 `EPTI`. Prima del menu il
processo è terminato con `0xC0000005` in `v2game.exe+0x005EE877`.
La stessa firma è riapparsa al riavvio con cache e in un controllo
senza mod. Il log ricolloca il problema dopo l'inizializzazione
della mappa. I due installer Visual C++ x86 erano usciti con codice 0.

Il binario contiene un riferimento dinamico a `ggcoins.dll`.
Aggiungendo nella sola copia guest la DLL originale appartenente alla
distribuzione Steam, il motore ha raggiunto il menu e aperto partite
offline in finestra. La DLL è conservata in
`baselines/victoria2-304-x86-frontend`, con SHA-256
`3e29a9501e1dec6fc728eefd4a4390261471b14cac9f7f95277ab46ab47a0305`.
Snapshot del secondo supplemento
`aa2759530f9ea1c1e2cf32f3a99fee476096201dfb91164e8b4f5d5dfd85f6a6`.
Il mount era in sola lettura, come verificato nel guest. Il caso riguarda
la completezza della copia del motore. I file `.wsb` richiedono
Protected Client attivo e la disattivazione di rete e vGPU.

### Profilo core

`t14-v2-core` ha superato `plan → apply → verify` con il solo
descrittore `TGC.mod` e il manifest
`1dcfee2f661923abf19472c315dc4c4767d5fa8f4759578db806be16ec30ce94`.
In finestra è stata osservata la partita russa in pausa al 1º gennaio
1836. All'avanzamento fino al 3 gennaio sono seguiti salvataggio,
uscita e riapertura in un nuovo processo. La partita in pausa mostrava
la stessa data, nazione e situazione sulla mappa. Il log del nuovo
processo riporta 3.04 e il checksum di inizializzazione `GBPA`.
La scrittura e la riapertura sono attestate separatamente.
Il log registra 35 tecnologie in ciascuno dei cinque file di ramo.

La fixture `fixtures/v2-304-core-t14/Russian_Empire1836_01_03.v2`
ha SHA-256
`fd03d99b70bf8b08c769622497c2e357b3a70e85578e94d64800bf3f1ebc40e9`.
L'intestazione indica `RUS`, partenza il 1º gennaio e data salvata
il 3 gennaio. L'archivio verificato contiene 98 file, incluse tre
schermate native F11 e i log dei tentativi. Dopo la distruzione del
guest i 105 ambiti host e le impronte dei due supplementi coincidono.

### Profilo core+1966

`t14-v2-1966` ha superato `plan → apply → verify` in un nuovo
guest con `TGC.mod` seguito da `TGC_Timeline_1966.mod` e manifest
`11b4e5b23edd78dce306b2275cf81aad4052693f83740dc6033d4753d08590ed`.
Gli hash di descrittori, `defines.lua` e del file militare Timeline
corrispondono alla revisione del bundle. Il log del motore registra
60 tecnologie per file di ramo contro le 35 del core, confermando il
caricamento degli override. Il checksum di inizializzazione è `GFVE`.

Il primo processo ha mostrato «Failed to create a graphics device»
con la console disconnessa. Nel log falliscono la creazione Direct3D
con elaborazione vertici hardware e il tentativo software. Riavviato
una volta con la console connessa, il motore ha creato il dispositivo
senza modificare il deployment o la configurazione del guest.
L'associazione con lo stato della console è osservata in questa
sessione. La causa del guasto grafico non è stata isolata.

La Grand Campaign russa è partita in pausa il 1º gennaio 1836 ed è
avanzata fino al 4 gennaio. Il salvataggio era presente a motore chiuso
e si è riaperto nel nuovo processo con data, nazione e stato attesi.
La fixture `fixtures/v2-304-1966-t14/Russian_Empire1836_01_04.v2`
ha SHA-256
`fd3d4b115c4f9505945cb86d68a3b88194b9824d70d4a389422686b380ec5197`.
L'archivio verificato contiene 60 file, incluse tre schermate native
e i log del primo tentativo. Dopo la distruzione del guest i 105
ambiti host e le impronte dei supplementi coincidono.

Le ricevute `runtime-summary.json` in `sessions/t14-v2-core` e
`sessions/t14-v2-1966` identificano archivi, fixture e schermate.
`sessions/task14/summary.json` collega i due esiti, l'identità degli
input e la ricetta. Nei guest il motore è stato osservato in partita
senza un processo Steam attivo.

### Controllo della configurazione grafica

I due log del motore riportano l'adattatore NVIDIA. Due prove
sintetiche senza file di gioco, registrate in
`sessions/task14/isolation-probe` e
`sessions/task14/isolation-probe-vgpu-case`, hanno riprodotto
la differenza. Con `<VGpu>Disable</VGpu>` il guest esponeva
NVIDIA e l'adattatore remoto Microsoft. Con
`<vGPU>Disable</vGPU>` esponeva solo l'adattatore remoto.
In entrambi i casi risultavano soltanto gli indirizzi loopback,
senza schede di rete abilitate né route predefinite.

Il generatore ora usa il nome `vGPU` della specifica. I risultati
dei primi due guest attestano il funzionamento offline con la
GPU esposta. Per le configurazioni storiche fa fede il riscontro
effettivo nel guest. [Configurazione Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file#vgpu)

La correzione interessa il generatore del laboratorio di questo fork.
Il file è assente dal riferimento upstream e una PR al mod originale
non è pertinente.

In `t14-v2-warp-core` il manifest è identico al primo core. A gioco
riaperto il guest esponeva solo l'adattatore remoto Microsoft, senza
schede di rete abilitate né route predefinite. Direct3D ha indicato
Microsoft Basic Render Driver e `d3d10warp.dll`. Il motore ha
caricato la partita russa al 1º gennaio, scritto il salvataggio al 3
gennaio e riaperto lo stesso stato in un nuovo processo. Checksum
`GBPA`, tre schermate e 105 ambiti host senza differenze.
La fixture del profilo corretto è `fixtures/v2-304-warp-core-t14`.
Il salvataggio ha SHA-256
`c14033e75311e7c33bc4733d219766b5b637fdabac992166e3bd463e85ac400a`.

`t14-v2-warp-1966` ha usato lo stesso manifest del primo ciclo
Timeline, il renderer WARP e i due descrittori nello stesso ordine.
Il log conferma 60 tecnologie per ramo e il checksum `GFVE`.
Dopo una disconnessione, il primo processo mostrava il menu ma i
clic non attivavano i pulsanti. Un riavvio a console connessa ha
ripristinato i comandi. La partita russa è avanzata dal 1º al 3
gennaio 1836. Il file è stato verificato a gioco chiuso e la partita
è stata riaperta in pausa al 3 gennaio in un nuovo processo.
Il guest vedeva soltanto l'adattatore remoto Microsoft e non aveva
schede di rete abilitate o route predefinite.
La fixture corrispondente è `fixtures/v2-304-warp-1966-t14`.
Il salvataggio ha SHA-256
`dff3ac436d820572e6b14a0ca7dc9986b3998fd8de32b2c59eef771d6d522979`.

### Ripetizione locale

La ricetta del checkpoint è in `sessions/task14/recipe` nell'archivio
permanente. Usare PowerShell 7 dalla radice di questo repository, con
Windows Sandbox disponibile e nessun guest attivo. Conservare la base
`alice-130-t12` e i due supplementi con i rispettivi manifest. Eseguire
prima un profilo completo e poi l'altro in un guest nuovo, con un ID
nuovo per ogni prova. La configurazione corretta disattiva la vGPU.

```powershell
$lab = "$env:LOCALAPPDATA\TGC-Runtime-Lab"
$recipe = "$lab\sessions\task14\recipe"
$run = 't14-v2-replay-core-01'
& "$recipe\t14-v2-start-local.ps1" -Profile core -Run $run
while (!(Test-Path "$lab\transfer\$run\outbox\progress.log")) {
    Start-Sleep -Seconds 2
}
Get-Content "$lab\transfer\$run\outbox\progress.log" -Wait
```

Attendere l'avvio del motore e interrompere la sola lettura del log con
Ctrl+C. La ricetta usa `sandbox-config`, `host-check` e `guest-deploy`
con `plan → apply → verify`. Il processo nativo usa
`v2game.exe -mod=mod/TGC.mod`. Per `core+1966` aggiunge
`-mod=mod/TGC_Timeline_1966.mod` in coda. Se compare il messaggio
facoltativo sull'associazione `ms-gamingoverlay`, chiuderlo dal guest.
In caso di disconnessione della console, usare «Riconnetti» oppure
`wsb connect --id <id>` con l'ID nel `sandbox-start.json` della
sessione. La console può perdere la connessione durante un comando
di controllo mentre il guest continua l'esecuzione.
Se si verifica l'errore grafico documentato o il menu perde l'input
dopo una disconnessione, chiudere il gioco e lanciare una volta
`& "$recipe\t14-v2-retry-graphics-local.ps1" -Run $run`.
La ricetta conserva i log e attende 40 secondi prima di riavviare.
Assicurarsi che la console sia connessa durante l'attesa.

In «Single Player» scegliere l'Impero russo e avviare la Grand
Campaign. Acquisire una schermata nativa con F11 al 1º gennaio 1836.
Avanzare di alcuni giorni, mettere in pausa, annotare la data,
premere F11 e salvare col nome proposto. Uscire dal gioco e rilevare
il file sul disco del guest prima di riavviare.

```powershell
& "$recipe\t14-v2-control-local.ps1" -Run $run -Action inspect
Get-Content "$lab\transfer\$run\outbox\inspect.json"
& "$recipe\t14-v2-control-local.ps1" -Run $run -Action restart
```

Nel nuovo processo usare «Single Player», scegliere il proprio
salvataggio e premere «PLAY». Verificare nazione, data e stato in
partita. Premere F11 e rilevare il processo responsivo prima di
uscire dal gioco.

```powershell
& "$recipe\t14-v2-control-local.ps1" -Run $run -Action inspect
# Uscire dal gioco dopo il riscontro.
& "$recipe\t14-v2-close-local.ps1" -Run $run
$py = "$lab\baselines\alice-130-t12\input\tools\Python\python.exe"
# Sostituire 1836.1.3 con la data effettivamente osservata, se diversa.
& $py -B "$recipe\t14-v2-receipt-local.py" $lab $run '1836.1.3'
```

La chiusura esporta e verifica l'archivio, distrugge il guest e
confronta gli ambiti host e i supplementi prima e dopo. La ricevuta
controlla anche l'intestazione del salvataggio, l'ordine dei
descrittori, gli hash di file rappresentativi rispetto al commit e
il manifest dopo il runtime. Per la seconda prova usare un altro ID
e `-Profile 'core+1966'`. Tenere separate le fixture.

### Condizioni per i due profili Loader

Usare la baseline nativa qualificata e l'asset ufficiale Grand Loader
3.0.0 con Script Extender e Performance Patch, verificando gli hash
di DLL e INI e l'inizializzazione di entrambi i plugin. Preparare
radici distinte `C:\TGC-Lab\Games\Loader` e
`C:\TGC-Lab\Games\Loader1966`, con `userdir.txt`, cache, log,
salvataggi e CB generato privati per ciascuna. Avviare in finestra
con il singolo descrittore previsto per ciascuna composizione.
Ripetere avanzamento, salvataggio e riapertura in guest separati e
conservare le ricevute dei controlli di isolamento. [Contratto Extender](script_extender_profile.md)

Le suite mirate del laboratorio e del deployment Extender hanno
superato rispettivamente 5 e 11 test dopo la correzione del generatore.
La qualifica ha esercitato il caricamento delle due composizioni.
Validatore e audit 1966 sono
stati saltati perché il task non modifica o valuta validità o
bilanciamento dell'estensione.

## Task 15 · Qualifica dei profili Grand Loader

Le due prove hanno usato Victoria II 3.04 x86, la baseline nativa del
Task 14 con i relativi supplementi e il bundle Git a `3c3be0d63`.
Al momento della prova il checkout e `origin/master` erano a
`246231fc5`. I contenuti dei due profili e `deploy_tgc.py`
coincidono fra le due revisioni. Il riepilogo permanente è `sessions/task15/summary.json`
sotto `%LOCALAPPDATA%\TGC-Runtime-Lab`.

Lo ZIP ufficiale Grand Loader 3.0.0 è conservato in
`sessions/task15/grand-loader-3.0.0.zip`. Il suo SHA-256 coincide con
quello pubblicato,
`e5ca3b29c9d17870ca2235eacc9ca1759251467827c39e82ece1045d3c59dfba`.
Il manifest `baselines/victoria2-loader-300-t15/manifest.json` contiene
gli hash delle DLL, dei due INI completi e delle risorse impiegate,
oltre agli import x86 e al digest degli input. Lo ZIP conserva il CB
pregenerato di distribuzione. Il laboratorio lo esclude dall'input
dei guest e verifica che il plugin lo generi durante ogni prova.
[Asset ufficiale](https://github.com/The-Grand-Combination/The-Grand-Loader/releases/expanded_assets/3.0.0)

### Risultati Loader

| Profilo | Descrittore selezionato | Checksum | Fixture nell'archivio |
| --- | --- | --- | --- |
| `core+extender` | `TGCScriptExtender.mod` | `AKGB` | `fixtures/t15-loader-core-01` |
| `core+extender+1966` | `TGCScriptExtender1966.mod` | `FNKX` | `fixtures/t15-loader-1966-01` |

Entrambe le prove hanno superato `plan → apply → verify` e la verifica
dopo il runtime. In ciascuna, l'Impero russo è partito il 1º gennaio
1836, è avanzato fino al 3 gennaio ed è stato riaperto in pausa a
quella data in un nuovo processo. Le due fixture contengono salvataggi
distinti con i rispettivi SHA-256 in `fixture.json`. Le ricevute
`runtime-summary.json` nelle sessioni `t15-loader-core-01` e
`t15-loader-1966-01` collegano manifest, schermate, log e salvataggio.

Nei log di avvio e riapertura, al banner storico 1.1.0 del
bootstrapper seguono Script Extender 0.1.0 e Performance Patch 1.0.0.
I log mostrano i valori letti dagli INI, fra cui
`treaty_dismantle_gp=250` e `oos_log=1`, con i profiler disattivati.
I file del bundle hanno gli stessi hash prima e dopo le due sessioni.

Le radici dei giochi, dei dati utente e dello stato transazionale
sono distinte sotto `C:\TGC-Lab\Games`, `C:\TGC-Lab\UserData` e
`C:\TGC-Lab\State`, con le rispettive sottocartelle `Loader` e
`Loader1966`. Il log attribuisce i CB alla coppia selezionata più
`common/se_treaty_cbs.txt`. Ogni guest ha generato
`mod\script_extender\common\se_cb_types.generated.txt` nella propria
radice e creato la cache della mappa sotto il proprio `user_dir`.
Per la Timeline, `default.map` risolve `definition.csv` dalla coppia
`TGCScriptExtender1966` e il file pubblicato coincide con il blob
atteso. Il log motore registra 60 tecnologie per ramo nella Timeline
e 35 nel core.

I guest hanno usato WARP con vGPU disattivata, senza schede di rete
abilitate o route predefinite. Il controllo finale confronta 105
ambiti host per sessione. Entrambi i confronti sono passati e
l'elenco finale delle Sandbox era vuoto.

### Diagnosi e ripetizione

Il primo processo core si è chiuso prima del menu con `CFileException`.
Il generatore scriveva `userdir.txt` con CRLF su Windows. Dopo aver
conservato file e log, la ricetta ha riscritto lo stesso percorso
privato senza fine riga. Nello stesso guest il ciclo core è riuscito.
Il generatore ora scrive direttamente i byte ASCII del percorso, senza
terminatore. La ricetta archiviata riusa una versione precedente dello
strumento nel bundle del guest e conserva quel passaggio per
compatibilità con l'input storico. La correzione riguarda lo strumento
di questo fork.

Il controllo finale dell'esportazione core è riuscito dopo aver
corretto nella ricetta locale il percorso dello stato transazionale.
Durante la prova è comparso un avviso Bitdefender su una riga di
comando PowerShell. L'origine precisa resta indeterminata e le
protezioni sono rimaste attive. La qualifica copre l'avvio in
finestra. Il crash storico a schermo intero e le prove funzionali
di trattati, partizioni, redditi POP e bilanciamento restano fuori
da questo esito.

La procedura completa è in `sessions/task15/ricetta.md`. Per ripetere
la prova, avviare PowerShell 7 dalla radice del repository e usare
un ID nuovo per ciascun profilo.

```powershell
$lab = "$env:LOCALAPPDATA\TGC-Runtime-Lab"
$recipe = "$lab\sessions\task15\recipe"
$run = 't15-loader-replay-core-01'
& "$recipe\t15-loader-start-local.ps1" -Run $run -Profile 'core+extender'
```

Seguire il log di avanzamento in `transfer/<id>/outbox/progress.log`,
poi creare e salvare una partita nella console. A gioco chiuso
usare `t15-loader-control-local.ps1` con `-Action inspect` e
`-Action restart`. Dopo la riapertura eseguire `inspect` mentre il
motore risponde, uscire e usare `t15-loader-close-local.ps1` per
esportare, chiudere il guest e controllare l'host. Concludere con
`t15-loader-receipt-local.py` passando la data effettiva. Per la
seconda prova usare `core+extender+1966` e un altro ID. Le istruzioni
archiviate includono la raccolta dei log in caso di errore al primo
avvio e la riconnessione della console.
