# Laboratorio runtime Windows

Il laboratorio usa una VM Windows dedicata con checkpoint a VM spenta, profilo
locale standard e dischi del guest compresi nel checkpoint. Una sola VM può
ospitare i due motori e tutti i profili. Il deployer resta l'unico strumento di
pubblicazione dei contenuti TGC. La [matrice runtime](runtime_lab_matrix.md)
collega fixture, osservazioni e criteri di chiusura al backlog.

## Confine di isolamento

| Soluzione | Condizioni e limiti |
| --- | --- |
| VM Windows con checkpoint | Preferita per ripristinare insieme filesystem, profilo e registro del guest. Console grafica osservabile, accelerazione richiesta dai motori da verificare. Prestazioni e capacità CPU/GPU del guest possono differire dall'host. |
| Account Windows standard dedicato | Ripiego se esiste già ed è accessibile. Richiede sessione interattiva, Documenti e AppData indipendenti e prova che il token non possa scrivere nelle destinazioni personali né nelle copie di gioco esistenti. Condivide servizi, registro di macchina e aree pubbliche scrivibili. Il ripristino deve includere tutte le scritture nel profilo e nelle radici rilevate. |
| Windows Sandbox | Valutabile se già attiva. Ripristino ricostruendo la sessione da input immutabili, con rete e condivisioni disabilitate. La compatibilità grafica, quella dei prerequisiti e il trasferimento delle evidenze vanno dimostrati. [Requisiti e configurazione](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-overview) |
| `userdir.txt`, variabili d'ambiente, `-outputScenario`, VSS | Utili per singoli percorsi, nomi o recupero. L'isolamento richiede un confine verificabile per tutte le scritture. VSS sul volume host con dati personali non offre un ripristino mirato del laboratorio. |

Durante le prove tenere il guest offline, senza cartelle host mappate, dischi
host, clipboard condivisa, redirect RDP o account cloud. Usare un supporto
di ingresso dedicato di sola lettura e scollegarlo prima dell'avvio dei motori.
Esportare le evidenze a sessione conclusa mediante un supporto dedicato ai soli
artefatti del laboratorio. Tenere separati gli input immutabili e il disco
sacrificabile. L'host conserva i propri log di sistema, i file della VM, le
risorse condivise di calcolo e gli export deliberati. I checkpoint riguardano
i dischi del guest inclusi e vanno conservati secondo la politica locale.
[Checkpoint Windows](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints)

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
   poi un ripristino del checkpoint su questi dati. Prima di avviare un motore
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
   Con tutti i motori chiusi, partire dal checkpoint pulito e verificarne le
   impronte. Usare una copia della fixture associata a motore, profilo e
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
   dopo aver verificato il mask per l'ordine dei descrittori di quella radice.
   Usare un nome nuovo per ciascun profilo e conservare subito
   `scenario_errors.txt` per ciascuna build. Registrare percorso, dimensione,
   SHA-256 e checksum mostrato al caricamento. Ripetere per core e Timeline.
   La CLI headless è utile quando osservabile entro un tempo definito.
   Menu, avanzamento e ricarica richiedono osservazioni coerenti con il caso.
4. Eseguire le azioni della [matrice](runtime_lab_matrix.md) e raccogliere
   prova visiva, log, differenze di stato, errori e codici d'uscita. Registrare
   almeno data UTC, operatore, commit, Windows guest, versione e SHA-256
   del binario effettivamente eseguito, hash di launcher, plugin e INI se
   pertinenti, profilo e descrittori, ID della transazione, scenario e
   checksum, fixture e sua impronta, azione, esito e riferimenti ai file.
   Usare `pass`, `fail`, `blocked` o `not-run` per ciascuna prova.
5. Confrontare l'host e il guest con le rispettive baseline. Esportare
   l'evidenza, fermare la VM e ripristinare il checkpoint pulito oppure
   conservare deliberatamente il checkpoint della prova con il suo ID.
   Verificare il ripristino con sentinelle modificate, aggiunte e rimosse.
   Il rollback del deployer riguarda le coppie gestite. Il checkpoint
   recupera anche profilo, cache, output plugin e altri dati del guest.

Binari di gioco, DLL esterne, scenari, salvataggi, log e configurazioni
locali restano fuori dal repository.
