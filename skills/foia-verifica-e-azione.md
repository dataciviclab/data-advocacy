# FOIA — Verifica e Azione

Procedura operativa per la campagna FOIA quotidiana: **prima verifica
sistematica, poi diagnosi, poi azione**.

## Flusso

```
──next──► VERIFICA (5 criteri) ──stato──► AZIONE ──send──► TRACKING
            │        ▲                         │
            │  ok    │   evidence               │  foia/dcd
            ▼        │                         ▼
          SKIP       └── audit completo    GENERA BOZZA
```

## 1. Prossimo ente

```bash
python foia.py --next
```

Mostra il primo ente con `stato = da-verificare`.

## 2. Verifica — 5 criteri obbligatori

Per ogni ente vanno **tutti** verificati. Non basta un probe URL.

### A. Formato aperto (art. 7 D.Lgs. 33/2013, art. 1 CAD)

| Punteggio | Criterio |
|---|---|
| 1 | ≥80% delle risorse in formato aperto (CSV, JSON, XML, ODS) |
| 0.5 | 50-80% |
| 0 | <50% o solo XLS/XLSX/PDF/DOC |

**Evidenza**: cerca su dati.gov.it o nel portale dell'ente i formati delle risorse.

### B. Aggiornamento dati (art. 6 D.Lgs. 33/2013)

| Punteggio | Criterio |
|---|---|
| 1 | Mediana aggiornamento < 1 anno |
| 0.5 | Mediana 1-3 anni |
| 0 | Mediana > 3 anni o dati fermi |

**Evidenza**: controlla `metadata_modified` nei dataset chiave. Se un dataset
importante (es. incidentalità, bilanci) è fermo da anni → punteggio 0.

### C. Licenza aperta (art. 1 CAD)

| Punteggio | Criterio |
|---|---|
| 1 | ≥80% dataset con licenza esplicita (CC-BY, ODbL, IODL) |
| 0.5 | 50-80% o non verificabile |
| 0 | Assente o non aperta |

### D. Presenza su dati.gov.it (art. 9 D.Lgs. 36/2006)

| Punteggio | Criterio |
|---|---|
| 1 | Organizzazione presente su dati.gov.it con aggiornamento recente |
| 0.5 | Presente ma non aggiornato |
| 0 | Non presente |

### E. Accessibilità (art. 6 D.Lgs. 33/2013 + art. 17 CAD)

| Punteggio | Criterio |
|---|---|
| 1 | Portale raggiungibile, SSL valido, sezione trasparenza presente |
| 0.5 | Raggiungibile ma con problemi minori (SSL in scadenza, sezione parziale) |
| 0 | Irraggiungibile, SSL scaduto/assente, sezione trasparenza assente |

### Calcolo score

```
score = (A×3 + B×2 + C×1 + D×2 + E×1) / 9 × 100
```

| Score | Giudizio | Azione |
|---|---|---|
| 90-100 | 🟢 Eccellente | Monitoraggio |
| 70-89 | 🟢 Buono | Monitoraggio |
| 50-69 | 🟡 Sufficiente | FOIA/DCD sulle carenze |
| 30-49 | 🟠 Insufficiente | FOIA + DCD + escalation |
| 0-29 | 🔴 Grave | FOIA immediato + DCD + escalation |

### Strumenti per la verifica

```bash
# Probe raggiungibilità + routing (CKAN, SDMX, HTML)
toolkit_probe_url_routed --url https://dati.ente.gov.it

# SSL check
echo | openssl s_client -connect host:443 -servername host 2>/dev/null \
  | openssl x509 -noout -dates -subject

# Presenza su dati.gov.it
ckan_organization_search --server https://dati.gov.it/opendata --pattern "ente"

# Formati e aggiornamento (su dati.gov.it)
ckan_package_search --server https://dati.gov.it/opendata \
  --fq "organization:slug-ente" --facet-field "res_format" --rows 0

# Source Observatory (se presente)
so_source_overview --source-id ente
```

## 3. Diagnosi

Registra la diagnosi dopo aver valutato tutti e 5 i criteri:

```bash
python foia.py --stato poste-italiane --azione foia
python foia.py --stato consip --azione dcd
python foia.py --skip aifa          # alias per --stato aifa --azione ok
```

La diagnosi genera automaticamente la/e bozza/e in `bozze/`.

## 4. Invio

1. Apri la bozza in `bozze/`
2. Compila `[NOME COGNOME RICHIEDENTE]` e `[PEC/EMAIL RICHIEDENTE]`
3. Invia PEC al destinatario indicato
4. `python foia.py --send ID` per tracciare

DCD si invia a `dcd@agid.gov.it` (non si traccia con --send).

## 5. Follow-up

| Giorno | Evento | Azione |
|---|---|---|
| 0 | Invio FOIA | `--send` |
| 30 | Scadenza risposta | `--scadenze` → `--anac` se silenzio |
| 30 | Se formato chiuso | `--dcd` (segnalazione ad AgID) |
| 50 | Scadenza RPCT | Richiesta riesame (manuale) |
| 60+ | ANAC + pubblicazione | Segnalazione + report |

```bash
python foia.py --respond ID --status ok
python foia.py --scadenze
python foia.py --anac ID
```

## 6. Stato campagna

```bash
python foia.py --report
python foia.py --lista
python foia.py --da-fare
```

## Riferimenti

- `foia.py` — script operativo
- `enti/enti.json` — anagrafica enti
- `data/tracker.json` — richieste inviate
- `template.txt` — template FOIA
- `bozze/` — bozze generate
- `minister-open-data-audit.md` — audit formale (stessi criteri, report pubblicabile)
