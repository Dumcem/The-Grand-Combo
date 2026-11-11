# Riconciliazione upstream TGC

La revisione upstream fissata è [14f2e6ff61e7e1ea07ffef07548560da5bcc47f0](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/14f2e6ff61e7e1ea07ffef07548560da5bcc47f0). Il Task 39 ha inventariato 63 commit esclusivi upstream e 243 file nel [delta dalla base comune ea0392ff](https://github.com/The-Grand-Combination/The-Grand-Combo/compare/ea0392ff668851c916cd86688452e99f406ed861...14f2e6ff61e7e1ea07ffef07548560da5bcc47f0). Il fork era a `7441a4189253183dca61d6d71efb610fd4184e03` prima del primo lotto.

## Esiti registrati

| Upstream | Esito nel fork | Commit locale o evidenza |
| --- | --- | --- |
| [`b93eb2da7`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/b93eb2da7) | **Parziale.** Rimossi la chiamata USS senza destinatario `4102182` e quattro duplicati territoriali, con appartenenze preservate. Il testo in `00_decisions.csv` resta da valutare. Il trasferimento oltremare USA resta incompiuto. | `598a2fa77a561e22f847e7eebb8e0fbbdc61bf84` |
| [`90106a7bf`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/90106a7bf) | **In parte equivalente, in parte sospeso.** Il nome del modificatore `vernacular_chinese` è già corretto. Per i due effetti `literacy` in ambito POP manca evidenza sufficiente su scala e destinatari in Victoria II originale. | Task 40, nessuna modifica a `China.txt` |
| [`ff837623f`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/ff837623f) | **Riconciliato con adattamento.** Evento e testi `99797`, con invito una volta per paese tramite flag all'apertura. Alice 1.3.0 memorizza `fire_only_once` sull'evento libero, quindi il primo destinatario bloccherebbe il secondo. Il flag di risposta resta legato alla scelta. | `7005ab14da7dc2b37560adebfa85aa274b1d3b58` |
| [`2fd86782f`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/2fd86782f) | **Parziale.** Recepite le condizioni di `99800` per attendere solo i paesi esistenti. Comandanti, movimenti nazionalisti e relative localizzazioni esclusi dal lotto e ancora da valutare nel loro contesto. | `7005ab14da7dc2b37560adebfa85aa274b1d3b58` |
| [`5934144d3`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/5934144d3) | **Riconciliato nel contenuto.** `44842` registra la pace di Velasco e `99960` accetta il flag in alternativa alla tregua. I rami di cessate il fuoco e prosecuzione restano distinti. La raggiungibilità dall'aggancio di battaglia Alice resta la voce [BATTLE_EVENT](rebaseline_backlog.md#battle_event--catena-della-cattura-di-santa-anna). | `7005ab14da7dc2b37560adebfa85aa274b1d3b58` |
| [`8912b304f`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/8912b304f) | **Equivalente.** Patch dei testi Temperance League già presente secondo il confronto Task 39. L'anticipo degli eventi in `e4e92b60c` resta da valutare. | Fork a `7441a4189` |
| [`14f2e6ff6`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/14f2e6ff6) | **Esito finale già soddisfatto.** I file di prova dello Script Extender, aggiunti e poi rimossi upstream, sono assenti. Esclusa la loro introduzione temporanea. | Fork a `7441a4189` |

I controlli del Task 41 sono statici. Entrambi i profili ereditano gli stessi eventi. Le verifiche del comportamento nei motori restano da eseguire al checkpoint autorizzato. Le equivalenze parziali del Task 39 per flag Chunnel e Taiwan e per file o hunk dei commit misti vanno riutilizzate quando si riconciliano i rispettivi gruppi.

## Task 42

Modifiche e regressioni nel commit locale `730d3fd4696bfd9a78eee5f0b7c581242a9c7ccd`.

| Gruppo | Esito e dipendenze |
| --- | --- |
| Texas tedesco e GEF | **Adattato.** I due flag di [`cc5f562d7`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/cc5f562d7) riattivano `800000`, i destinatari GEF e le rinomine texane esistenti. L'evento richiede un promotore ancora attivo e l'annessione USA richiede che ADV esista. Velasco è indipendente. Gli hunk AI texani di [`6741d7e73`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/6741d7e73) sono equivalenti nel comportamento perché le quattro decisioni escludono l'AI. [`28e31bd58`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/28e31bd58) riguarda la Grande Germania, i Paesi Bassi e le colonie. Resta da valutare in quel gruppo. |
| Rivolte polacche | **Adattato.** [`cc5f562d7`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/cc5f562d7) ripristina il segnale di vittoria consumato da Cracovia e dagli eventi polacchi. Recepite la correzione di scope da [`e5fcf7bc3`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/e5fcf7bc3) e la verifica dell'esistenza di CPL nel ramo di Cracovia. Il diff russo di `cc5f562d7` e i suoi testi riguardano la crisi orientale e restano fuori dal lotto. |
| Ridenominazioni | **Parziale.** Da [`3c16e7a2b`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/3c16e7a2b) recepiti i requisiti territoriali dell'Alsazia e la rimozione dei flag senza produttore per Bismarck e Sakhalin. Il blocco vuoto del Raj è già equivalente negli effetti. Il flag francese cambia la frequenza della ribellione algerina e resta nel gruppo Algeria. Sospese le decisioni Petrograd: il ripristino del nome rimuove il flag e può riaprire la decisione con nuovi bonus se le condizioni coesistono. [`a027796c0`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/a027796c0) e [`0e398e8a8`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/0e398e8a8) riconciliati nel risultato cumulativo, con 19 rinomine per data e tre per Iron Range. |
| Haiti e USA | **Adattato.** [`d988356d8`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/d988356d8) sposta il modificatore da South Georgia a Port-au-Prince, applicandolo solo quando Haiti possiede la provincia. [`73504b7f`](https://github.com/The-Grand-Combination/The-Grand-Combo/commit/73504b7f) consente l'offerta per Môle Saint-Nicolas fuori dalla sfera del proponente e impedisce di chiedere aiuto al leader di sfera quando è un belligerante avversario. Il ramo di cessione dopo la guerra conserva i suoi requisiti. Il seguito `530011` conserva il CB separato indirizzato specificamente a USA. |

I tre lotti coprono rimozione USS, deduplicazione territoriale, Sonderbund, Velasco e le parti indicate dei quattro gruppi del Task 42. Sei commit sorgente sono riconciliati nel contenuto e altri due hanno un risultato già presente. I commit misti sono contabilizzati per hunk. I controlli dei due profili e dei due motori restano statici fino al checkpoint runtime.

## Blocchi pendenti

- **Catene storiche ed eventi comuni.** Restano Grande Germania e Paesi Bassi, crisi orientale, Algeria, Temperance League, le altre rinomine del delta e le catene regionali ancora da valutare. Petrograd e alfabetizzazione cinese restano sospese per le ragioni indicate sopra.
- **Mappa e storia.** Opzioni indigene [#416](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/416), rimozione di tag, storie provinciali e terreni. Verificare selettori e riferimenti attivi.
- **Setup, riforme, POP e progressione.** Valutare scelte di gameplay e carrier `00_Setup.txt` della Timeline.
- **Diplomazia e CB ordinari.** Trattato di Londra, CB precedenti all'Extender, neutralità e formazione jugoslava.
- **Localizzazione, UI, GFX e submod opzionali.** Verificare codifica, chiavi, asset indipendenti e perimetro dei submod. La rimozione di `TGCPerformanceAddon` resta sospesa perché il deployment lo gestisce ancora.
- **Script Extender e Performance Patch.** [#417](https://github.com/The-Grand-Combination/The-Grand-Combo/pull/417) resta sospesa come gruppo. Prima di un'eventuale adozione servono una decisione sul supporto dei due runtime e verifica del comportamento sostitutivo di CB, redditi e costruzione AI.

## Checkpoint di chiusura

Gli SHA in tabella identificano la provenienza e gli esiti sul contenuto. I tre lotti sono commit locali senza acquisizione dell'ascendenza upstream. Per chiudere il ciclo, assegnare un esito a tutto il delta fissato, approvare le esclusioni e verificare il risultato nei due profili e nei due motori secondo il perimetro. Solo dopo autorizzazione, creare il merge reale di riconciliazione e marcare il checkpoint verificato con lo SHA upstream. Usare quel riferimento per il delta del ciclo successivo. L'aggiornamento della mod live passa da deployment verificato con rollback disponibile.
