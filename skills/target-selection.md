---
name: target-selection
description: Da un segnale pubblico a un target FOIA Layer 2 — un dataset individuato con un difetto documentato, pronto come Issue.
license: MIT
metadata:
  version: "1.0"
  owner: "DataCivicLab"
  tags: [data-advocacy, foia, layer2, scouting]
---

# Workflow: target-selection (Layer 2)

Trasforma un segnale pubblico in un **target FOIA pronto**: un dataset
individuato + un difetto documentato. Non un catalogo, non un tema — un dato
preciso che l'ente detiene e non pubblica, o pubblica male.

## 1. Boundary

- **SÌ**: un dataset specifico, con URL e difetto verificabile e datato.
- **NO**: la richiesta del catalogo completo (Layer 1). La giurisprudenza
  (Ad. Plen. CdS 10/2020, LG ANAC 1309/2016) la respinge come "censimento non
  dovuto". Il Layer 2 invece regge: una richiesta puntuale ottiene risposta.
- **NO**: temi, aree, "i dati su X". Serve un artefatto.

## 2. Input

| Fonte | Cosa | Strumento |
|---|---|---|
| Source Observatory | health, inventory, signals, formati | artifact in `infra/source-observatory/data/` |
| dati.gov.it | `res_format`, `metadata_modified`, `package_search` | `dataciviclab` MCP / webfetch |
| Reachability | status HTTP datato | `toolkit_source(action="probe", url=...)` |
| Portale ente | pagina open data / Amministrazione Trasparente | webfetch |
| Norme | riferimento violato | `legal-graph` |

## 3. Tassonomia dei difetti

Per ogni difetto: cosa osservi e quale evidenza serve.

| Difetto | Evidenza richiesta |
|---|---|
| Portale/endpoint irraggiungibile | probe HTTP (status/000) + **data** della verifica |
| Formato chiuso **sul dato** (XLS/PDF al posto di CSV) | link alla risorsa + il dato è dentro il formato chiuso |
| Serie storica troncata o ferma | anni reali vs frequenza dichiarata; ultimo anno presente |
| Contraddizione pubblica (rimanda a pagina vuota/portale morto) | URL citato + verifica datata che è vuoto/morto |
| Detenuto per legge ma non pubblicato | norma istitutiva + assenza su dati.gov.it/portale |

**Regola**: il PDF/documentazione **non** è un difetto. Se il PDF *descrive* il
dataset, non è violazione. Se il PDF *contiene* il dato al posto del CSV, sì.

## 4. Priorità

1. Il difetto è **già visibile pubblicamente** — l'ente non può negarlo.
2. Il dato ha **impatto civico** (sanità, ambiente, lavoro, trasporti, soldi).
3. L'ente è **già in source-observatory** — evidenza riusabile.

## 5. Output — target pronto come Issue

Apri una Issue con `foia-request.yml`, compilando:

- **Ente** destinatario (PEC da `enti/enti.json` o IPA)
- **Dataset**: nome + URL esatto
- **Difetto** + **evidenza datata** (URL / HTTP code / data verifica)
- **Norma** (art. 5 D.Lgs. 33/2013; art. 7 per formato aperto)
- **Perché passa**: richiesta puntuale, non censimento; se possibile
  circoscritta, con offerta di restringere ulteriormente
- **Formato richiesto** (CSV, colonne, granularità, periodo)

## 6. Anti-pattern

- "Catalogo completo del patrimonio informativo" → Layer 1, respinto.
- Affermazioni senza data ("il portale è down") → serve verifica datata.
- Documentazione PDF scambiata per dato.
- Target senza URL (non verificabile).
- Duplicare un target già presente come Issue.

## 7. Agganci

```
segnale SO ──► target-selection ──► Issue (foia-request.yml) ──► PEC ──► registro.py
```

**Riferimenti**: `skills/minister-open-data-audit.md` (score dell'ente),
`skills/foia-verifica-e-azione.md` (Layer 1), `source-observatory` `source-check`
(per l'ingest, non per l'advocacy).
