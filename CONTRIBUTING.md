# Contribuire a data-advocacy

## Cosa sta in questo repo

- `registro.py` — log condiviso delle richieste FOIA (campagna Layer 2)
- `bozza.py` — genera la bozza `.eml` da una nota-richiesta
- `portal_scan.py` — confronto portale diretto vs catalogo nazionale
- `richieste/` — un file JSON per ogni PEC inviata (**fonte di verità**)
- `REGISTRO.md` — tabella pubblica, **generata** da `registro.py build`
- `richiedente.json` — dati del richiedente, **locale e non versionato**
- `foia.py` — tool Layer 1 archiviato (bozze catalogo) + `enti/enti.json`
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

### 4. Registrare risposta o escalation

```bash
python registro.py risposta <target>/<file> --esito ok|parziale|rifiutata|ignorata
python registro.py escalation <target>/<file> rpct|anac
```

### 5. Aggiornare il registro

```bash
python registro.py build
```

## Regole

- **Mai committare dati personali**: `richiedente.json`, PEC, documenti
  d'identità, corrispondenza grezza.
- `REGISTRO.md` è **generato**: non editarlo a mano.
- I record in `richieste/` sono **append-only**: non riscrivere quelli altrui.
- Un target = una Issue. Lo stato vive nel record, non nella Issue.

## Cosa NON sta in questo repo

- **Monitoraggio fonti** → `source-observatory`
- **Pipeline dati** → `toolkit`
- **Analisi SQL** → `data-explorer`

## PR template

Usa `.github/PULL_REQUEST_TEMPLATE.md`. Ogni PR deve:
- `pytest tests/` passare
- `python registro.py build` aggiornare `REGISTRO.md` senza errori
- includere test per nuova logica (se applicabile)

## Riferimenti

- [DataCivicLab .github](https://github.com/dataciviclab/.github)
- [Source Observatory](https://github.com/dataciviclab/source-observatory)
