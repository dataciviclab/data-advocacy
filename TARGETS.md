# Target pronti da inviare

Qui ci sono i target **già preparati** — Issue aperta, difetto documentato con data e URL — per
cui **nessuno ha ancora inviato la PEC**. Chiunque abbia una casella certificata può prenderne
uno.

Fonte viva: [board FOIA Layer 2](https://github.com/orgs/dataciviclab/projects/8) — colonna
**Da inviare**. Questo file è uno snapshot, aggiornato quando cambia la colonna.

## Come si prende un target

1. Scegli una riga e scrivilo come commento nella Issue.
2. Genera la bozza: `python bozza.py <nota-richiesta.md>`.
3. Invia la PEC dal tuo client, come persona fisica.
4. Registra l'invio: `python registro.py nuova <target> --issue <N>`.

Se non hai una PEC puoi comunque contribuire: proponi un nuovo target, verifica un difetto,
scrivi la richiesta. **Un'altra persona la invierà.** Vedi `CONTRIBUTING.md`.

## Disponibili (snapshot 2026-11-10)

| Issue | Ente | Dataset | Difetto |
|---|---|---|---|
| [#21](https://github.com/dataciviclab/data-advocacy/issues/21) | Ministero della Salute | Posti letto per regione e disciplina | aggiornamento e link |
| [#22](https://github.com/dataciviclab/data-advocacy/issues/22) | MIT | Passeggeri trasportati dal TPL | dato assente (la domanda, non l'offerta) |
| [#23](https://github.com/dataciviclab/data-advocacy/issues/23) | MIT | TPL in formato aperto | formato chiuso (6 XLSX, metadati 2022) |
| [#25](https://github.com/dataciviclab/data-advocacy/issues/25) | MIT | Incidentalità stradale | serie ferma al 2018 |
| [#26](https://github.com/dataciviclab/data-advocacy/issues/26) | MEF / OpenCivitas | Metadati servizi_totali (TOT) 2018 | catalogo, metadati assenti |

> Nota: MIT ha già due richieste in attesa (#20 no, #24 sì). Chi prende uno dei target MIT
> valuti se inviare subito o scaglionare, per non concentrare le richieste sullo stesso ente.

## In corso

Le richieste già inviate e il loro stato sono nel [REGISTRO](REGISTRO.md). Non serve fare nulla:
si aspetta la risposta entro i termini e, se arriva, si registra.
