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

## 3b. Confronto portale diretto vs catalogo nazionale

Un ente può pubblicare **più** e **più aggiornato** sul proprio portale che sul catalogo
nazionale `dati.gov.it` (che è un harvest, spesso parziale e stale). Il portale diretto è la
fonte di verità su cosa l'ente pubblica davvero.

```bash
python portal_scan.py <sitemap-index-url> --catalog <org-dati.gov.it>
python portal_scan.py <sitemap-index-url> --match <tema>
```

Il sitemap si trova in `robots.txt` (`Sitemap:`). La pagina-lista può essere bloccata (403), ma
sitemap e pagine-dataset sono raggiungibili.

Il confronto fa emergere difetti tipici:

- **scheda di catalogo stale** (es. catalogo 2010-2019, portale 2020-2023) → art. 6 D.Lgs. 33/2013 (qualità/aggiornamento) e art. 9 co. 1 D.Lgs. 36/2006 (elenchi aggiornati annualmente);
- **link di catalogo morto** mentre il file esiste sul portale → art. 9 co. 2 D.Lgs. 36/2006 (catalogo come punto di accesso unico) e art. 6 D.Lgs. 33/2013;
- **formato** diverso tra catalogo e portale → art. 7 co. 1 D.Lgs. 33/2013.

Quando il dato **esiste** sul portale, la richiesta non è "dammi il dato" ma "**allinea il
catalogo**" — posizione più forte: l'ente non può negare la disponibilità.

## 4. Priorità

1. Il difetto è **già visibile pubblicamente** — l'ente non può negarlo.
2. Il dato ha **impatto civico** (sanità, ambiente, lavoro, trasporti, soldi).
3. L'ente è **già in source-observatory** — evidenza riusabile.

## 5. Output — target pronto come Issue

Apri una Issue con `foia-request.yml`, compilando:

- **Ente** destinatario (PEC da `enti/enti.json` o IPA)
- **Dataset**: nome + URL esatto
- **Difetto** + **evidenza datata** (URL / HTTP code / data verifica)
- **Norma**: usa gli id canonici di `obblighi/obblighi.yaml` — `art6_qualita`,
  `art7_formato_aperto` (co. 1), `art9_elenchi_riutilizzo` (co. 1),
  `art9_catalogo_unico` (co. 2), `art37_contratti`. L'accesso è art. 5 D.Lgs. 33/2013.
- **Perché passa**: richiesta puntuale, non censimento; se possibile
  circoscritta, con offerta di restringere ulteriormente
- **Formato richiesto** (CSV, colonne, granularità, periodo)

L'**Issue è il target**. Al momento dell'invio della PEC, il numero della Issue va nel registro:

```bash
python registro.py nuova <target> --issue <N>
```

Così il record (in `richieste/`) è collegato all'Issue. Il registro traccia la PEC inviata; l'Issue
resta il contesto del target (evidenza, discussione).

## 6. Anti-pattern

- "Catalogo completo del patrimonio informativo" → Layer 1, respinto.
- Affermazioni senza data ("il portale è down") → serve verifica datata.
- Documentazione PDF scambiata per dato.
- Target senza URL (non verificabile).
- Duplicare un target già presente come Issue.

## 7. Agganci

```
segnale SO ──► target-selection ──► Issue (target) ──► PEC ──► registro.py (--issue N)
```

**Riferimenti**: `skills/minister-open-data-audit.md` (score dell'ente),
`skills/obblighi.md` (come si aggiunge un obbligo/applicazione),
`obblighi/obblighi.yaml` (catalogo canonico delle norme),
`skills/foia-verifica-e-azione.md` (Layer 1), `source-observatory` `source-check`
(per l'ingest, non per l'advocacy).
