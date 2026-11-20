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
   osservazioni. Usare `python -B $tool guest-export`; il comando copia
   nell'outbox e lascia una ricevuta SHA-256. Chiudere la Sandbox, poi in
   host eseguire `host-check --phase after` e `archive-export` con lo
   stesso `--lab-root` e `--run`. Il trasferimento archiviato viene
   confrontato con la ricevuta e pubblicato in `sessions/<id>/raw`.
   Conservare un drop non verificato per diagnosi. Ricostruire una nuova
   sessione dagli stessi input e verificare le sentinelle.

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
