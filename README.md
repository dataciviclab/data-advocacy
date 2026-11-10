# data-advocacy

Campagna civica per richiedere i dati pubblici alle PA, con FOIA (accesso
civico generalizzato, art. 5 D.Lgs. 33/2013).

Il repo copre due fasi.

- **Layer 2 (campagna corrente)** — richieste mirate su **un singolo dataset
  individuato**, con un difetto documentato (portale irraggiungibile, formato
  chiuso, serie storica mancante, contraddizione pubblica). È la strada che
  regge: una richiesta puntuale ottiene risposta, un censimento no.
- **Layer 1 (archiviato)** — la campagna 2026 che chiedeva il catalogo completo
  del patrimonio informativo a 29 enti. Tooling e tracker storici restano in
  `foia.py` e `data/archivio/`.

---

## Modello Layer 2

| Entità | Dove vive | Chi la scrive |
|---|---|---|
| **Target** — dataset + evidenza del difetto | Issue GitHub (`foia-request.yml`) | chiunque |
| **Richiesta** — una PEC inviata | `richieste/<target>/<data>_<richiedente>.json` | `registro.py` |
| **Registro** — tabella pubblica | `REGISTRO.md` | `registro.py` (generato) |

Una sola fonte di verità: i file in `richieste/`. Il registro è **derivato**,
mai editato a mano. L'identità e la PEC del richiedente restano **locali**
(`richiedente.json`, non versionato): nel log pubblico compare solo un'etichetta
anonima (`01`, `02`, …). Più persone possono inviare verso lo stesso target:
ognuna crea il proprio file, senza conflitti.

### Forma del record

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

- `esito`: `null` (in attesa) · `ok` · `parziale` · `rifiutata` · `ignorata`.
- `escalation`: `none` · `rpct` · `anac`.
- `norma`: id degli obblighi applicati, da `obblighi/obblighi.yaml` (lista, può essere vuota).
- `tipo_risposta`: `null` · `nessuna` · `interlocutoria` · `negativa_motivata` · `documentazione` · `impegno`
  (asse ortogonale all'esito: cosa è arrivato, non cosa ha risolto).
- `verificato_il`: data (`AAAA-MM-GG`) della verifica sul dato.
  **Correzione verificata** = `esito: ok` **+** `verificato_il` valorizzato.

`norma`, `tipo_risposta` e `verificato_il` sono opzionali nei record più vecchi (retro-compatibili).

---

## Come partecipare

Quattro ruoli. Non serve farli tutti: il punto è che si possono **separare**.

| Ruolo | Cosa fa | Serve la PEC? |
|---|---|---|
| **Segnalatore** | trova il dataset e il difetto, apre la Issue con l'evidenza | no |
| **Richiedente** | invia la PEC come persona fisica | sì |
| **Revisore** | controlla che l'evidenza sia datata e riproducibile prima dell'invio | no |
| **Manutentore** | merge, registro, coerenza del board | no |

I target già pronti e non ancora inviati sono in [`TARGETS.md`](TARGETS.md). Chi non ha una PEC
può comunque proporre un target, verificarlo e scrivere la richiesta: **un'altra persona la
invierà**.

- Regole di convivenza: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- Cosa pubblichiamo e cosa no, diritto di replica: [`DISCLAIMER.md`](DISCLAIMER.md)
- Come si contribuisce nel dettaglio: [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## Ciclo

```
SO segnala un dataset con difetto
  → apri Issue (target)                              [GitHub]
  → scrivi la richiesta in una nota (skill target-selection)
  → python bozza.py <nota.md>                        [genera la bozza .eml]
  → invia la PEC dal client                          [ricevute PEC]
  → python registro.py nuova <target> --issue N --norma <id>   [crea il record]
  → risposta         → python registro.py risposta <target>/<file> --esito ... --tipo ...
  → verifica sul dato → python registro.py verifica <target>/<file> --verificato-il AAAA-MM-GG
  → silenzio/rigetto → python registro.py escalation <target>/<file> rpct|anac
  → python registro.py build                         [aggiorna REGISTRO.md]
```

**Ladder di escalation**: 30gg senza risposta → riesame al RPCT (art. 5 co. 7) →
ricorso/segnalazione ANAC. La scadenza si calcola da sola (data invio + 30gg).

---

## Strumenti

| File | Cosa fa |
|---|---|
| `registro.py` | log condiviso delle richieste (record, scadenze, registro) |
| `bozza.py` | genera la bozza `.eml` (testo+HTML+allegati) da una nota-richiesta |
| `portal_scan.py` | confronta il portale diretto di un ente col catalogo nazionale |
| `foia.py` | Layer 1 (archiviato): bozze dal template catalogo |

### `bozza.py`

Legge una nota con blocchi PEC (`TO`/`CC`/`SUBJECT`/`ATTACH`/`FILE` + corpo delimitato) e
produce un `.eml` per richiesta. I placeholder (`[NOME COGNOME]`, `[DATA]`, …) sono compilati
da `richiedente.json`; `[DATA]` è la data odierna.

```bash
python bozza.py <nota.md>            # tutte le richieste della nota
python bozza.py <nota.md> --id m1    # una sola
```

### `portal_scan.py`

Elenca i dataset di un portale dal suo sitemap e li confronta col catalogo nazionale
(`dati.gov.it`), che è spesso un harvest parziale e non aggiornato.

```bash
python portal_scan.py <sitemap-index> --catalog <org-dati.gov.it>
python portal_scan.py <sitemap-index> --match <tema>
```

---

## Comandi

```bash
python registro.py nuova <target> [--issue N] [--data AAAA-MM-GG] [--richiedente 01] [--norma ID]
python registro.py risposta <target>/<file> --esito ok|parziale|rifiutata|ignorata \
    [--tipo ...] [--verificato-il AAAA-MM-GG] [--data-risposta AAAA-MM-GG] [--protocollo ...]
python registro.py verifica <target>/<file> [--tipo ...] [--verificato-il AAAA-MM-GG] [--data-risposta AAAA-MM-GG]
python registro.py escalation <target>/<file> rpct|anac
python registro.py nota <target>/<file> "testo" [--append]
python registro.py norma <target>/<file> --norma <id> [--norma <id> ...]
python registro.py lista          # tutte le richieste
python registro.py mio 01         # solo quelle di un richiedente
python registro.py scadenze       # oltre i 30gg senza esito
python registro.py build          # rigenera REGISTRO.md
```

## Obblighi informativi (livello semantico)

Riferimento operativo completo: **`obblighi/README.md`**. Chiude la catena
norma → ente → fonte → obbligo → richiesta, con dati verificabili e non editoriali.

| File | Contenuto |
|---|---|
| `obblighi/obblighi.yaml` | obblighi, ognuno ancorato a `urn` + `articolo` + `comma` + `testo_ancora` |
| `obblighi/applicazioni.yaml` | un obbligo applicato a un ente/fonte, con evidenza + stato |
| `obblighi/mapping_source_ipa.yaml` | `source_id` (source-observatory) → `codice_ipa` (IPA) |
| `obblighi/locator.py` | verifica l'ancora **dentro il comma** via `legal-graph` (offline) |
| `obblighi/validate.py` | schema + FK + `--with-locator` |
| `obblighi/build_mapping.py` | rigenera il mapping dal clean IPA su GCS |

```bash
python obblighi/validate.py                 # offline: schema + FK
python obblighi/validate.py --with-locator  # offline: ancore nel testo di legge
python obblighi/build_mapping.py --check-contract   # offline (CI)
python obblighi/build_mapping.py --check-names      # rete: nomi IPA (schedulato)
```

Il gate PR è **offline e deterministico**. I check con rete girano nel workflow
`.github/workflows/obblighi-drift.yml` (lunedì) e, se falliscono, aprono una
issue di manutenzione — non rendono rossa una PR.

---

## Setup

```bash
cp richiedente.example.json richiedente.json   # nome + PEC (resta locale, mai committato)
```

Python 3.12+.

- **Runtime** (`registro.py`, `bozza.py`, `portal_scan.py`): solo stdlib.
- **Strumenti `obblighi/`**: richiedono `jsonschema` + `pyyaml` (e `duckdb` per `--refresh`/`--check-names`). Installali con:

```bash
pip install -e ".[obblighi]"
# oppure: pip install jsonschema pyyaml duckdb
```

---

## Dove individuare i target

Il discovery **non** vive in questo repo: i segnali (radar, catalog-inventory,
`readiness_score`) arrivano da `source-observatory`, lo score dell'ente da
`skills/minister-open-data-audit.md`. Qui vive la procedura che trasforma un
segnale in un target pronto: `skills/target-selection.md`. Questo repo consuma
quel segnale e lo trasforma in una richiesta.

---

## Layer 1 (archiviato)

`foia.py` è il tool della campagna catalogo 2026 (29 enti): genera bozze dai
template storici. Il tracker storico è in `data/archivio/tracker.json`.
Esito: 83% degli enti ha risposto, 21% ha consegnato.

---

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
