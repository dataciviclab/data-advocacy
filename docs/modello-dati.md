# Modello dei dati

Tre entità, una sola fonte di verità.

| Entità | Dove vive | Chi la scrive |
|---|---|---|
| **Target** — dataset + evidenza del difetto | Issue GitHub (`foia-request.yml`) | chiunque |
| **Richiesta** — una PEC inviata | `richieste/<target>/<data>_<richiedente>.json` | `registro.py` |
| **Registro** — tabella pubblica | `REGISTRO.md` | `registro.py` (generato) |

## La richiesta

Un file JSON per ogni PEC inviata. Append-only: non si riscrive il record altrui, si aggiunge il
proprio.

```json
{
  "target": "art_d15",
  "issue": 19,
  "richiedente": "01",
  "data_invio": "2026-11-03",
  "scadenza": "2026-12-03",
  "protocollo": null,
  "data_risposta": null,
  "esito": null,
  "escalation": "none",
  "note": "",
  "norma": ["art7_formato_aperto"],
  "tipo_risposta": null,
  "verificato_il": null
}
```

### Campi

- `target` — slug del dataset richiesto, corrisponde alla cartella.
- `issue` — numero della Issue che descrive il target.
- `richiedente` — etichetta anonima (`01`, `02`, …). L'identità vera resta in `richiedente.json`,
  che non è versionato.
- `data_invio` / `scadenza` — la scadenza è `data_invio + 30 giorni`, calcolata in automatico.
- `protocollo` — numero assegnato dall'ente alla ricezione.
- `esito` — `null` (in attesa) · `ok` · `parziale` · `rifiutata` · `ignorata`.
- `escalation` — `none` · `rpct` · `anac`.
- `norma` — id degli obblighi applicati, da `obblighi/obblighi.yaml`.
- `tipo_risposta` — `null` · `nessuna` · `interlocutoria` · `negativa_motivata` ·
  `documentazione` · `impegno`. È un asse **ortogonale** all'esito: dice cosa è arrivato, non
  cosa ha risolto.
- `verificato_il` — data in cui la correzione è stata verificata **sul dato**.

**Correzione verificata** = `esito: ok` **e** `verificato_il` valorizzato. Un "ok" senza verifica
sul dato non conta.

## Escalation

La scadenza si calcola da sola. Passati i 30 giorni senza esito:

1. **Riesame al RPCT** (art. 5 co. 7 D.Lgs. 33/2013) — `registro.py escalation <target>/<file> rpct`
2. **Segnalazione ANAC** se il riesame resta senza risposta — `... anac`

## Il registro

`REGISTRO.md` è generato da `registro.py build` e non va editato a mano. La CI verifica che sia
allineato ai record: se una PR modifica `richieste/` senza rigenerarlo, i test falliscono.

## Gli obblighi

`obblighi/` chiude la catena norma → ente → fonte → obbligo. Ogni obbligo è ancorato a `urn`,
`articolo`, `comma` e a un frammento di testo (`testo_ancora`), così la citazione è verificabile
e non editoriale. Dettagli in [`obblighi/README.md`](../obblighi/README.md).
