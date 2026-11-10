---
name: obblighi
description: Aggiungere o verificare un obbligo informativo nel livello semantico (norma → ente → fonte → obbligo → richiesta).
license: MIT
metadata:
  version: "1.0"
  owner: "DataCivicLab"
  tags: [data-advocacy, obblighi, normative, reference-data]
---

> **Workflow interno al Laboratorio DataCivicLab.** Alcuni passaggi usano strumenti del Lab
> (`dataciviclab` MCP, `toolkit`, `legal-graph`) che non sono disponibili fuori. La procedura
> resta leggibile e adattabile a un contesto diverso.


# Workflow: obblighi informativi (livello semantico)

Riferimento data operativa: `obblighi/` in `incubation/data-advocacy`.
Chiude i join che non esistono altrove: **norma → ente → fonte → obbligo → richiesta**.

## 1. Boundary

- **SÌ**: un obbligo di legge verificabile (`urn` + `articolo` + `comma` + ancora)
  applicato a un ente con evidenza datata.
- **NO**: un artifact pubblicato o un database. È reference data versionata a mano.
- **NO**: mappe editoriali. Ogni ancora deve stare **dentro il comma** dichiarato.
- Il livello vive qui finché DEC #21 (versioning cross-repo) è aperta.

## 2. Modello

| File | Scrivi a mano? | Contenuto |
|---|---|---|
| `obblighi.yaml` | sì | obblighi ancorati al testo di legge |
| `applicazioni.yaml` | sì | obbligo applicato a un ente/fonte + evidenza |
| `mapping_source_ipa.yaml` | **no** (generato) | `source_id` → `codice_ipa` |
| `schemas/` | no | schema JSON di `obligation` / `application` |
| `locator.py`, `validate.py`, `build_mapping.py` | no | strumenti |

## 3. Aggiungere un obbligo

Aggiungi un blocco a `obblighi.yaml`:

```yaml
- id: art9_catalogo_unico
  titolo: "Catalogo nazionale dei dati aperti come punto di accesso unico"
  urn: "urn:nir:stato:decreto.legislativo:2006-01-24;36"
  articolo: "9"
  comma: "2"
  testo_ancora: "utilizzano il catalogo nazionale dei dati aperti gestito dall'Agenzia per l'Italia digitale"
  locator_status: verified
  regime_verifica: locator_verified
  rimedio: catalogo_nazionale
  frequenza: null
  note: "Art. 9, comma 2: il catalogo nazionale è il punto di accesso unico."
```

Poi verifica l'ancora sul testo vigente:

```bash
python obblighi/validate.py --with-locator
```

**Regole**:

- `comma` è obbligatorio in pratica: il locatore cerca l'ancora **dentro** il comma.
- Se `validate` dice `untested`, il comma non è individuabile → controlla il formato
  del testo AKN (`N.` su riga propria).
- `broken` = articolo inesistente/ambiguo o ancora assente: **non** è un problema di rete.

## 4. Aggiungere un'applicazione

Aggiungi un blocco a `applicazioni.yaml`:

```yaml
- id: opencoesione_catalogo_art9c2
  obligation: art9_catalogo_unico
  source_id: opencoesione        # null se la fonte non è in SO
  codice_ipa: PCM                # obbligatorio salvo source_id: null
  canale_previsto: catalogo_nazionale
  canale_osservato: url_datati_404
  application_status: broken     # verified | broken | untested | non_verificabile
  verification_confidence: alta   # alta | media | bassa
  evidenza: "Catalogo punta a pagamenti_20251031.zip (404); portale 200"
  verified_at: "2026-11-06"
  note: ""
```

**Regole**:

- **Un obbligo best-fit per riga**. La base secondaria va in `note`, non in una
  seconda riga (per la v0).
- `evidenza` sempre **datata** (`verified_at`).
- `codice_ipa` obbligatorio; se la fonte non è in SO, `source_id: null` + nota.
- Un ente può avere **più applicazioni** (obblighi diversi sullo stesso fatto).

## 5. Mapping ente ↔ fonte

Non si edita a mano: si rigenera dal clean IPA pubblico su GCS.

```bash
python obblighi/build_mapping.py --refresh         # riscrive lo YAML (nomi da GCS)
python obblighi/build_mapping.py --check-contract  # offline: decisione allineata
python obblighi/build_mapping.py --check-names     # rete: nomi allineati a IPA
```

Se `--check-names` fallisce (rename/accorpamento IPA), rigenera e apri PR.
Se una fonte non è mappabile (es. Terna, società privata), `codice_ipa: null`
con `confidence: nulla`.

## 6. Gate e drift

- **PR (offline, bloccante)**: `validate.py` + `build_mapping.py --check-contract`.
- **Schedulato (rete, non bloccante)**: `obblighi-drift.yml` lunedì →
  `--check-names` + `--with-locator`. Se fallisce apre una issue di manutenzione.

```bash
# prima di una PR
python obblighi/validate.py
python obblighi/build_mapping.py --check-contract
python -m pytest tests/ -q
ruff check .
```

## 7. Errori comuni

- **Art. 7 ha un solo comma**: il formato aperto è il **co. 1**; il co. 3 non esiste
  (il successivo è l'art. 7-bis).
- **Link morto nel catalogo** = art. 9 co. 2 (catalogo unico) + art. 6, **non** art. 7.
- **`untested` ≠ `broken`**: `untested` è "non verificato" (comma non trovato o
  infrastruttura giù); `broken` è una violazione o un articolo inesistente.
- **`source_id: null`** è ammesso solo con `codice_ipa` valorizzato e una nota che
  spiega perché la fonte non è in source-observatory.
- **Non duplicare anagrafiche**: solo `codice_ipa` come FK, mai denominazioni.

## 8. Aggancio al registro

Il record in `richieste/` porta `norma: [<id obbligo>]` e, in v0.1, `codice_ipa`.
Il join è `record.norma ↔ obligation.id` + `record.codice_ipa ↔ application.codice_ipa`.

```bash
python registro.py norma <target>/<file> --norma art9_catalogo_unico
```
