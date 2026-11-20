# Laboratorio runtime Windows

Il laboratorio conserva su disco locale procedure, input ed evidenze. Windows
Sandbox è il primo ambiente di esecuzione da qualificare su Windows 11 Pro.
Ogni sessione può essere chiusa e ricostruita dagli input verificati. Il
deployer resta l'unico strumento di pubblicazione dei contenuti TGC.
[Comandi e archivio permanente](runtime_lab_operations.md) · [Matrice runtime](runtime_lab_matrix.md)

## Confine di isolamento

| Soluzione | Condizioni e limiti |
| --- | --- |
| Windows Sandbox | Inclusa in Windows 11 Pro. Ricostruzione da input immutabili. Rete e reindirizzamenti disabilitati, con cartelle dedicate per input in sola lettura e uscita. Occorrono verifica effettiva dei mount, avvio legittimo offline e prova grafica per ciascun motore. [Requisiti](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install) |
| VM Windows con checkpoint | Ripiego se esiste già un guest autorizzato a tempo indeterminato con risorse disponibili. Il checkpoint ripristina filesystem, profilo e registro del guest. Verificare console, grafica e diritti d'uso del guest. [Checkpoint Windows](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints) |
| Account Windows standard dedicato | Ripiego se già autorizzato e accessibile. Richiede sessione interattiva, Documenti e AppData indipendenti e prova che il token non possa scrivere nelle destinazioni personali né nelle copie di gioco esistenti. Condivide servizi, registro di macchina e aree pubbliche scrivibili. Il ripristino deve includere tutte le scritture nel profilo e nelle radici rilevate. |
| `userdir.txt`, variabili d'ambiente, `-outputScenario`, VSS | Utili per singoli percorsi, nomi o recupero. L'isolamento richiede un confine verificabile per tutte le scritture. VSS sul volume host con dati personali non offre un ripristino mirato del laboratorio. |

Durante le prove tenere il guest offline, senza dischi host, clipboard
condivisa, reindirizzamenti delle periferiche o account cloud. La Sandbox
espone soltanto gli input dedicati in lettura e una cartella di uscita
esclusiva della sessione. Qualificare entrambe le modalità prima di esporre
una baseline di motore. Per una VM con checkpoint usare supporti dedicati
agli input e alle evidenze e scollegarli durante la prova. L'host conserva
log di sistema, file di virtualizzazione, risorse condivise di calcolo ed
export deliberati. L'archivio deve rimanere ricostruibile con risorse già
disponibili e senza licenze aggiuntive o versioni di valutazione.

## Radici e prerequisiti

Usare un checkout Git canonico pulito nel guest, con Python 3.11+ e Git. Le
radici di gioco, del checkout e di stato devono essere disgiunte. Lavorare fuori
da `steamapps`. Preparare copie ordinarie da componenti legittimamente
disponibili e autorizzati, prive di salvataggi, profili, cache, stati o
collegamenti alle installazioni esistenti. Se mancano guest Windows, diritti
d'uso, runtime di sistema, supporto grafico o un avvio legittimo offline,
registrare il blocco del profilo interessato. L'installazione di prerequisiti
o la modifica di Steam richiedono le rispettive autorizzazioni.

| Radice nel guest | Profili | Materiale richiesto |
| --- | --- | --- |
| `C:\TGC-Lab\Games\Shared` | `core`, `core+1966` | Victoria II 3.04 x86 e dati base Heart of Darkness. Per Alice 1.3.0, launcher, varianti CPU, DLL e `assets` della release accanto a `v2game.exe`. [Release](https://github.com/schombert/Project-Alice/releases/tag/v1.3.0) · [Istruzioni 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/docs/user_guide.md) |
| `C:\TGC-Lab\Games\Loader` | `core+extender` | 3.04 x86, bundle Loader 3.0.0 verificato con entrambi i plugin, due INI completi e copia scrivibile dei plugin in quella radice. |
| `C:\TGC-Lab\Games\Loader1966` | `core+extender+1966` | Stessi prerequisiti e copie indipendenti dei plugin. [Bundle 3.0.0](https://github.com/The-Grand-Combination/The-Grand-Loader/releases/tag/3.0.0) · [Configurazione Loader](script_extender_profile.md#dipendenze-e-contenuti) |

Assegnare a ciascuna radice il proprio `--state-root`, ad esempio
`C:\TGC-Lab\State\Shared`. Il deployer usa sia
`--state-root\targets\<id>` sia `<game-root>\.tgc-deploy`. Aprire uno
stato nuovo. Le ricevute precedenti sono vincolate alla loro radice e
appartengono al contesto in cui sono state create. Conservare risultati e
manifest in `C:\TGC-Lab\Runs\<id>`, fuori dagli alberi sotto osservazione.
Ricostruire la sessione o ripartire dal checkpoint pulito tra i profili
condivisi, che possono scrivere negli stessi percorsi utente nel guest.

## Ammissione al primo avvio

1. Registrare identità e SID della sessione, Documenti, AppData Roaming e Local,
   cartella temporanea, directory corrente, volumi visibili e reindirizzamenti.
   Nel guest verificare che le destinazioni personali host siano irraggiungibili.
   Con il ripiego ad account verificare in sola lettura le ACL effettive,
   comprese aree pubbliche, cartelle padre e destinazioni raggiungibili per alias.
   Se il confine rimane incerto, sospendere l'avvio.
2. Con strumenti già autorizzati, eseguire una prova di scrittura sintetica nel
   guest e osservare i percorsi assoluti. Provare creazione, rename e rimozione
   sotto Documenti, AppData, TEMP, gioco, dati utente, plugin e stato. Verificare
   poi una ricostruzione della Sandbox o un ripristino del checkpoint su questi dati. Prima di avviare un motore
   confermare il desktop osservabile e un tracciamento di filesystem, registro
   e processi figli (per esempio Process Monitor nel guest). Registrare
   eventuali limiti della cattura. [Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)
3. Inventariare prima e dopo le destinazioni protette dell'host. Includere
   libreria e manifest Steam del gioco, radici Loader, profili Paradox e Alice
   sotto Documenti, AppData e VirtualStore pertinenti, dati del deployer e
   eventuali radici reindirizzate. Per il confronto delle directory esplicite
   usare, da host, il comando di sola lettura riportato sotto. Conservare
   eventuali eventi di scrittura e i due inventari fuori dagli alberi
   controllati. Confrontare anche le scritture transitorie e il registro
   tramite tracciamento quando pertinenti.
4. Durante il primo avvio autorizzato tracciare launcher, motore e figli,
   partendo prima della creazione dei processi e finendo dopo la loro uscita.
   Annotare per file riusciti e tentati identità, processo, operazione e
   destinazione risolta. Controllare salvataggi e impostazioni di Victoria II
   sotto Documenti o `userdir.txt` e le sottocartelle dei descrittori. Cercare
   `map/cache`, `gfx/flags`, `logs`, `settings.txt`, screenshot, crash dump,
   VirtualStore e TEMP. Per Alice controllare `Documents\Project Alice`
   (in particolare `scenarios`, `saved games`, impostazioni e dump) e Local
   AppData `Project Alice\scenario_errors.txt`. Per Loader verificare
   `the_grand_loader.log`, `mod\script_extender\common\se_cb_types.generated.txt`,
   INI e output di entrambi i plugin per ogni radice. Aggiungere al perimetro
   le scritture scoperte e interrompere la prova se viola il confine.
   [Known Folder nel sorgente Alice 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/filesystem/simple_fs_win.cpp#L422-L531)

Il confronto dei file copre percorsi, assenze, directory vuote, dimensioni
e SHA-256 dei file ordinari. Il comando si ferma su reparse point, errori di
lettura e collisioni di nomi. Per reindirizzamenti legittimi inventariare
la destinazione effettiva come radice esplicita e registrare la relazione.
Questa lettura non certifica ACL, timestamp, stream NTFS alternativi,
registro o scritture transitorie e non è atomica. Servono sessioni quiete,
stesso elenco di percorsi e tracciamento per l'attribuzione.

```powershell
$observed = @(
    '--path', 'alice-documents', (Join-Path $personalDocuments 'Project Alice'),
    '--path', 'deployment-state', $personalDeploymentState
)
python -B tools/deploy/snapshot_runtime_paths.py @observed > "$evidence\host-before.json"
if ($LASTEXITCODE) { throw 'Baseline incompleta' }
# Ripetere dopo la sessione con gli stessi argomenti, salvando host-after.json.
if ((Get-FileHash "$evidence\host-before.json").Hash -ne
    (Get-FileHash "$evidence\host-after.json").Hash) { throw 'Impronte host diverse' }
```

## Ciclo per una sessione

1. Scegliere revisione Git, profilo, motore, fixture e un ID di sessione.
   Con tutti i motori chiusi, partire dagli input immutabili verificati o dal
   checkpoint pulito. Usare una copia della fixture associata a motore, profilo e
   checksum. Tenere l'originale della fixture immutabile.
2. Eseguire i comandi seguenti nel guest. Rivedere il piano e il suo target
   prima di `apply`. Registrare ciascun exit code e fermarsi al primo errore.
   Per recovery seguire la [guida del deployer](local_deployment.md).

   ```powershell
   $target = @('--game-root', $game, '--state-root', $state, '--profile', $profile)
   python -B tools/deploy/deploy_tgc.py plan @target |
       Set-Content -LiteralPath "$evidence\plan.json" -Encoding utf8
   # Dopo aver esaminato il piano e controllato eventuali blocker.
   python -B tools/deploy/deploy_tgc.py apply @target --plan-file "$evidence\plan.json" > "$evidence\apply.json"
   python -B tools/deploy/deploy_tgc.py verify @target > "$evidence\verify.json"
   ```

3. Preparare la fixture. Per Alice rigenerare dal deployment verificato, nel
   working directory della copia di gioco. Usare una selezione osservata nel
   launcher oppure `-modsMask <mask> -outputScenario <nome.bin> -autoBuild`
   dopo aver verificato i nomi dei descrittori di quella radice. Alice 1.3.0
   cerca una sottostringa sensibile alle maiuscole nel nome e include le
   dipendenze. Con la composizione canonica, verificare che
   `TGC - The Grand Combination` selezioni soltanto il core e che
   `TGC Timeline 1966` selezioni la Timeline con il core caricato prima.
   Usare un nome scenario nuovo per ciascun profilo. Archiviare ogni
   `scenario_errors.txt` del laboratorio prima della build successiva,
   affinché l'assenza di diagnostica nuova sia osservabile. Il launcher può
   aprire un editor come processo figlio in presenza di errori. Registrare
   percorso, dimensione, SHA-256 e checksum mostrato al caricamento.
   La CLI headless è utile quando osservabile entro un tempo definito.
   Menu, avanzamento e ricarica richiedono osservazioni coerenti con il caso.
   [Selezione e generazione nel launcher 1.3.0](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/launcher/launcher_main_win.cpp#L1147-L1184) · [Scrittura scenario e diagnostica](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/launcher/launcher_main_win.cpp#L122-L173)
4. Eseguire le azioni della [matrice](runtime_lab_matrix.md) e raccogliere
   prova visiva, log, differenze di stato, errori e codici d'uscita. Registrare
   almeno data UTC, operatore, commit, Windows guest, versione e SHA-256
   del binario effettivamente eseguito, hash di launcher, plugin e INI se
   pertinenti, profilo e descrittori, ID della transazione, scenario e
   checksum, fixture e sua impronta, azione, esito e riferimenti ai file.
   Usare `pass`, `fail`, `blocked` o `not-run` per ciascuna prova.
5. Confrontare l'host e il guest con le rispettive baseline. Esportare
   l'evidenza e chiudere la Sandbox, oppure fermare la VM e ripristinare il
   checkpoint pulito. Conservare il checkpoint della prova solo quando serve.
   Verificare il ripristino con sentinelle modificate, aggiunte e rimosse.
   Il rollback del deployer riguarda le coppie gestite. Il checkpoint
   recupera anche profilo, cache, output plugin e altri dati del guest.

Binari di gioco, DLL esterne, scenari, salvataggi, log e configurazioni
locali restano fuori dal repository.

## Riscontro del Task 10

Il 20 novembre 2026, `origin/master` e la working copy di partenza
corrispondevano a `37000ca00a535f69c443a4916a89ab1bcd213cb9`.
L'host esaminato era Windows 11 Pro x64, build 26300.9974, con 28 processori
logici, circa 64 GiB di RAM e 376 GiB liberi sul volume di lavoro.
L'hypervisor era rilevato e i servizi `vmcompute` e `hns` erano attivi.
La sessione non esponeva una VM Windows con checkpoint o Windows Sandbox
utilizzabile. I due account candidati appartenevano a Codex, con profili
presenti e senza sessione attiva. L'enumerazione della GUI host era
disponibile. Mancavano una console guest e una traccia di scrittura del guest.

L'inventario ha identificato la radice Steam condivisa di Victoria II e
Alice, due radici Loader con `userdir.txt`, DLL e INI distinti per radice,
otto scenari Alice esistenti, diagnostica Alice in Local AppData e tre
target nello stato locale del deployer. Il file di rilascio locale dichiara
Alice 1.3.0. Gli eseguibili e i plugin sono stati identificati con SHA-256.
Gli archivi originali non sono stati individuati nei percorsi esaminati.
Il banner storico Loader `1.1.0` coincide con il bootstrapper del tag del
bundle `3.0.0`. Nei log compaiono Script Extender `0.1.0` e Performance
Patch `1.0.0`. In AppContainer il percorso Local AppData appariva
reindirizzato, mentre il profilo Windows ordinario risolveva Documenti e
AppData nelle proprie cartelle. Le impronte dei percorsi personali sono
state calcolate sul profilo ordinario. In AppContainer anche l'enumerazione
`tasklist` falliva e l'area TEMP della prima prova è stata dismessa alla
chiusura della sessione. Il ciclo completo ha usato una radice TEMP
persistente nella sessione ordinaria, con il controllo `tasklist` nativo.
[Bootstrapper](https://github.com/The-Grand-Combination/The-Grand-Loader/blob/3.0.0/launcher/CMakeLists.txt#L1-L4) · [Asset Loader](https://github.com/The-Grand-Combination/The-Grand-Loader/releases/expanded_assets/3.0.0) · [Asset Alice](https://github.com/schombert/Project-Alice/releases/expanded_assets/v1.3.0)

| Verifica | Esito |
| --- | --- |
| Pubblicazione sacrificabile | `plan → apply → verify` con deployer invariato, profilo `core+1966`, sorgente `18bbd5bb819d9ef1ae5c997f3c88c6f48a70510f`, sentinella sintetica come marker di installazione. 16.539 file verificati. Transazione `ac2262c3d1c5441f815008b9d5948375`, digest manifest `7ca39341ae76303482df594366427047d60da27456ccf211e7057cec06a5c47b`. |
| Ripristino sacrificabile | `rolled-back` con ripristino della coppia TGC preesistente nella fixture, rimozione della coppia Timeline aggiunta e conservazione del file estraneo. Un secondo confronto ha confermato il ripristino del salvataggio sintetico e la scomparsa della cache aggiunta. Impronta della baseline della fixture: `ACC06D444CFCED1160F4927ABC9A483EB974016465E8C6F4317F363A3457E2E3`. |
| Percorsi personali | Prima e dopo la prova, inventari identici su 103 percorsi etichettati e 10.704 record di file, comprese le cartelle dati Paradox e Alice, le copie dei plugin, le cache selezionate e i metadati locali del deployer. Il confronto di contenuto vale per i percorsi osservati. |
| Tooling | Suite del deployer 117 eseguiti, 6 saltati, nessun errore. Ripetizione in sessione ordinaria dei sei casi saltati. Quattro passati (hardlink e junction), due saltati per assenza del privilegio symlink. Il controllo delle impronte rileva una sostituzione a parità di dimensione, registra directory vuote e assenze, e rifiuta etichette duplicate. |
| Motori | Bloccato prima dell'avvio. Servono un guest Windows autorizzato e ripristinabile, oppure un account di prova già autorizzato con confine dimostrabile, e strumenti di osservazione nella relativa sessione. Il materiale legittimo per quel guest, eventuali prerequisiti e l'avvio offline vanno verificati prima di avviare ciascun profilo. |

Le prove infrastrutturali sono attribuite alla fixture sintetica. Gli otto
scenari esistenti sono stati osservati durante l'inventario. La rigenerazione
di core e Timeline, il confronto delle 48 firme, Yinxu, Temperance e
Sonderbund attendono un ambiente ammesso alla prova.
