# Contribuire a data-advocacy

## Cosa sta in questo repo

- `registro.py` — log condiviso delle richieste FOIA (campagna Layer 2)
- `bozza.py` — genera la bozza `.eml` da una nota-richiesta
- `portal_scan.py` — confronto portale diretto vs catalogo nazionale
- `richieste/` — un file JSON per ogni PEC inviata (**fonte di verità**)
- `REGISTRO.md` — tabella pubblica, **generata** da `registro.py build`
- `richiedente.json` — dati del richiedente, **locale e non versionato**
- `foia.py` — tool Layer 1 archiviato (bozze catalogo) + `enti/enti.json`
- `obblighi/` — livello semantico obblighi informativi (norma → ente → fonte → obbligo)
- `skills/` — procedure operative

## Come contribuire

### 1. Proporre un target (dataset da chiedere)

Apri una Issue con il template `foia-request.yml`: ente, dataset, trigger,
evidenza del difetto, base normativa. **Il target è la Issue.**

### 2. Inviare la PEC

Genera la bozza dal testo della richiesta:

```bash
python bozza.py <nota-richiesta.md>
```

Ogni richiedente invia la **propria** PEC come persona fisica. L'identità e la
PEC restano in locale (`richiedente.json`): non vanno mai committate.

### 3. Registrare l'invio

```bash
python registro.py nuova <target> --issue <N>
```

Subito dopo, **lascia un commento sulla Issue**: data di consegna, scadenza, norme e path
del record. La Issue è il contesto pubblico del target; il commento è la traccia di invio,
visibile a chi non apre `richieste/`.

```markdown
**PEC inviata** — 2026-11-11, consegna 17:37:51

- Destinatario: `protocollo@pec.ente.gov.it`
- Scadenza risposta: **2026-12-11**
- Norme: art. 6 co. 1 D.Lgs. 36/2006 · art. 7 co. 1 D.Lgs. 33/2013
- Record: `richieste/<target>/2026-11-11_01.json`
```

### 4. Registrare risposta o escalation

```bash
python registro.py risposta <target>/<file> --esito ok|parziale|rifiutata|ignorata --tipo <tipo>
python registro.py verifica <target>/<file> --verificato-il AAAA-MM-GG
python registro.py escalation <target>/<file> rpct|anac
```

`tipo_risposta` (`nessuna`, `interlocutoria`, `negativa_motivata`, `documentazione`,
`impegno`) è ortogonale all'esito. `verificato_il` segna la correzione verificata sul dato.

### 5. Aggiornare il registro

```bash
python registro.py build
```

### 6. Aggiornare gli obblighi informativi

Se aggiungi un obbligo o un'applicazione, segui `skills/obblighi.md`.
Il gate è offline:

```bash
python obblighi/validate.py
python obblighi/build_mapping.py --check-contract
```

## Regole

- **Mai committare dati personali**: `richiedente.json`, PEC, documenti
  d'identità, corrispondenza grezza.
- `REGISTRO.md` è **generato**: non editarlo a mano.
- I record in `richieste/` sono **append-only**: non riscrivere quelli altrui.
- Un target = una Issue. Lo stato vive nel record, non nella Issue.

## Cosa NON sta in questo repo

Sono altri progetti del Laboratorio DataCivicLab, con i propri repo e i propri maintainer:

- **Monitoraggio e scouting delle fonti** → `source-observatory`
- **Pipeline dati** (raw → clean → mart) → `toolkit`
- **Analisi e pagine pubbliche** → `data-explorer`

Qui vive la campagna: dal segnale alla richiesta, e il registro delle richieste inviate. Non
serve accedere agli altri repo per contribuire: i target si propongono da una Issue.

## PR template

Usa `.github/PULL_REQUEST_TEMPLATE.md`. Ogni PR deve:
- `ruff check .` e `pytest tests/` passare
- `python registro.py build` aggiornare `REGISTRO.md` senza errori
- `python obblighi/validate.py` e `python obblighi/build_mapping.py --check-contract` passare
- includere test per nuova logica (se applicabile)

## Riferimenti

- [DataCivicLab .github](https://github.com/dataciviclab/.github) — policy e componenti condivisi
- `source-observatory` — repo del Laboratorio, può essere privato: la procedura in
  `skills/target-selection.md` è comunque leggibile e adattabile
