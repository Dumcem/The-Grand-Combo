# 1966 Extension Audit (updated: 2026-04-03)

## Stato attuale (rivalutazione)

- `end_date` confermata a **1966.1.1**.
- Copertura tech top-level:
  - Army: max 1956 (5 tech con anno >=1950)
  - Commerce: max 1956 (5 tech con anno >=1950)
  - Navy: max 1966 (3 tech con anno >=1950)
  - Industry: max 1966 (3 tech con anno >=1950)
  - Culture: max 1966 (3 tech con anno >=1950)
- Copertura invenzioni: nessuna tech `>=1950` risulta senza invention-link.
- Localizzazione late-tech: `key` + `key_desc` ora completa per tutte le tech `>=1950`.

## Stato obiettivi

### Obiettivo A — Estendere la campagna al 01/01/1966
- **Raggiunto**.

### Obiettivo B — Aggiungere tecnologie/invenzioni per il periodo esteso
- **Raggiunto (baseline contenutistica)**.
- Nota: la parità quantitativa tra alberi è migliorata, ma army/commerce restano più densi.

### Obiettivo C — Stabilizzazione per rilascio
- **Non ancora completato**.
- Blocco principale residuo: validazione gameplay (bilanciamento/AI/economia) con run lunghi.

## Piano finale verso completamento

## Fase 4 — Test funzionali (obbligatoria)
Eseguire almeno 3 campagne smoke-test fino al 1960+:
1. GP industriale
2. GP navale
3. Nazione media

Metriche da registrare:
- ritmo ricerca e accesso AI alle tech tarde,
- letalità/attrito nel late-war,
- stabilità economica (produzione, domanda, prezzi, liquidità).

## Fase 5 — Tuning finale (se necessario)
Solo dopo i test, intervenire su:
- valori numerici (bonus/costi/AI chance),
- eventuali micro-gap di progressione osservati in partita,
- rifiniture localizzazione testuale.
