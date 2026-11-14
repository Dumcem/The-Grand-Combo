# Documentazione tecnica del fork TGC

Questo indice raccoglie i riferimenti tecnici di `Dumcem/The-Grand-Combo` e della Timeline 1966. Il repository è la fonte canonica per l’implementazione e la documentazione tecnica. Il [Project Hub](https://docs.google.com/document/d/1Emgb7R5rbDqzZiqAtLA0v5lsDwHwfasDcOpZUfH6TUU/edit) è il punto di ingresso per orientamento, decisioni e stato del progetto. Le [istruzioni operative](../AGENTS.md) si applicano al lavoro nel repository.

## Struttura del fork e Timeline 1966

- [Manifest della Timeline 1966](../TGC_Timeline_1966/docs/manifest_1966_timeline.md) — composizione del submod, dipendenza dal core e inventario dei file condivisi o sovrascritti.

## Validazione e audit

- [Perimetro delle verifiche](../TGC/docs/1966_extension_audit.md) — differenze tra controlli strutturali, bilanciamento e compatibilità runtime.
- [Validator statico e controlli di drift](../TGC/docs/1966_extension_validator.md) — perimetro dei controlli, comandi e integrazione CI.
- [Auditor di bilanciamento](../TGC/docs/1966_balance_audit.md) — fonti, criteri diagnostici e limiti dell’evidenza per motore.

## Deployment e profili Loader

- [Deployment locale](deployment/local_deployment.md) — profili supportati, pubblicazione, verifica e recupero.
- [Profilo The Grand Loader](deployment/script_extender_profile.md) — composizione, dipendenze e limiti dei profili con Script Extender.

## Re-baseline e questioni aperte

- [Registro della re-baseline](rebaseline_backlog.md) — questioni tecniche, stato delle verifiche e condizioni di riesame.

## Sincronizzazione upstream

- [Registro delle differenze upstream](upstream_delta_register.md) — riferimento sincronizzato, differenze del fork, regressioni da preservare e contributi candidati.

## Storico e provenienza delle evidenze

- [Riconciliazione upstream](upstream_reconciliation.md) — motivazioni degli adattamenti e riscontri dei checkpoint precedenti.
