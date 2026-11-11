# obblighi — riferimento operativo (v0)

> **Workflow interno al Laboratorio DataCivicLab.** Alcuni passaggi usano strumenti del Lab
> (`dataciviclab` MCP, `toolkit`, `legal-graph`) che non sono disponibili fuori. La procedura
> resta leggibile e adattabile a un contesto diverso.

Livello semantico **obbligo informativo → ente** (audit T1, 2026-11-06).

Non è un artifact pubblicato: è **reference data operativa**, versionata a mano.
Sta qui (e non in un repo autonomo) finché DEC #21 (versioning cross-repo) è aperta.

## Modello

```
norma (urn + articolo + comma + ancora)   obblighi.yaml
  → ente  (codice_ipa)                    mapping_source_ipa.yaml
  → fonte (source_id)                     └─ stessa riga del mapping
  → obbligo applicato                     applicazioni.yaml
  → richiesta (record)                    ../richieste/*.json  (join via norma + codice_ipa)
```

| File | Cosa contiene |
|---|---|
| `obblighi.yaml` | 5 obblighi, ognuno ancorato al testo di legge |
| `applicazioni.yaml` | 5 applicazioni: un obbligo applicato a un ente/fonte, con evidenza |
| `mapping_source_ipa.yaml` | 36 `source_id` → `codice_ipa` (fonte ↔ ente) |
| `schemas/` | schema JSON di `obligation` e `application` |
| `locator.py` | verifica l'ancora **dentro il comma** (offline, via `legal-graph`) |
| `validate.py` | schema + FK + integrità; `--with-locator` per le ancore |
| `build_mapping.py` | genera/verifica il mapping dal clean IPA |

## Obblighi (`obblighi.yaml`)

| id | norma | cosa copre |
|---|---|---|
| `art6_qualita` | art. 6 co. 1 D.Lgs. 33/2013 | qualità, aggiornamento, completezza |
| `art7_formato_aperto` | art. 7 co. 1 D.Lgs. 33/2013 | pubblicazione in formato aperto |
| `art9_elenchi_riutilizzo` | art. 9 co. 1 D.Lgs. 36/2006 | elenchi annuali delle categorie di dati |
| `art9_catalogo_unico` | art. 9 co. 2 D.Lgs. 36/2006 | catalogo nazionale come punto di accesso unico |
| `art6_formati_dlgs36` | art. 6 co. 1 D.Lgs. 36/2006 | formati leggibili meccanicamente e metadati |
| `art37_contratti` | art. 37 co. 1 D.Lgs. 33/2013 | dati e atti sui contratti pubblici |

Ogni obbligo porta `urn`, `articolo`, `comma`, `testo_ancora` e `locator_status`.
`art7_formato_aperto` ha **comma 1**: l'art. 7 ha un solo comma (il successivo è
l'art. 7-bis). `art9_elenchi_riutilizzo` e `art37_contratti` sono oggi
**reference-only** (nessuna applicazione): non entrano in metrica finché non
hanno un caso reale.

## Applicazioni (`applicazioni.yaml`)

Un'obbligazione può avere **N applicazioni** (enti diversi), e un ente può avere
più applicazioni (obblighi diversi sullo stesso fatto). Regola:

- **un obbligo best-fit per riga**; la base secondaria va in `note`, non in una
  seconda riga (per la v0);
- `evidenza` sempre **datata** (`verified_at`);
- `codice_ipa` obbligatorio, salvo `source_id: null` con nota esplicita.

Stati: `verified` (rispettato) · `broken` (violato) · `untested` (non verificato) ·
`non_verificabile` (fuori perimetro). `verification_confidence`: `alta` · `media` · `bassa`.

## Locatore normativo (`locator.py`)

Verifica che un obbligo sia ancorato al testo di legge, **dentro il comma dichiarato**:

```bash
python obblighi/locator.py <urn> <articolo> "<testo_ancora>" [comma]
# -> VERIFIED | BROKEN | UNTESTED
```

Esiti:

- `verified` — ancora trovata nel comma;
- `broken` — articolo inesistente/ambiguo, o ancora assente;
- `untested` — comma non individuabile, `testo_ancora` vuoto, o **errore di
  infrastruttura** (rete, mart, timeout).

Un errore di infrastruttura **non** è `broken`: un disservizio non deve
silenziare obblighi validi. Un obbligo `broken` **non produce richieste**.

## Mapping ente ↔ fonte (`mapping_source_ipa.yaml`)

| | |
|---|---|
| Fonti mappate | 36 |
| Con `codice_ipa` | 35 |
| Senza (non-PA) | 1 (`terna_opendata`, società privata) |
| `confidence: alta` | 32 |
| `confidence: media` | 3 |
| `confidence: nulla` | 1 |

### Da rivedere (confidence media)

- `openbdap` → `m_ef` — BDAP è MEF/RGS; la Ragioneria non è un ente IPA a sé.
- `openga` → `cds` — Consiglio di Stato / giustizia amministrativa (C2).
- `unioncamere` → `UICCIAA` — Unione Italiana delle Camere di Commercio (da confermare).

### Non mappabile

- `terna_opendata` → `null`: Terna S.p.A. è società privata quotata, non presente in IPA.

**Regole**:

- **Nessuna anagrafica duplicata**: solo `codice_ipa` come FK. Se IPA cambia, cambia a monte.
- Il mapping va rivisto **a mano** quando `source-observatory` aggiunge fonti o IPA cambia.
- Una fonte senza `codice_ipa` **non produce obblighi** (non si sa a chi applicarli).

### Come si rigenera (riproducibile da terzi)

Fonte dei nomi: il **nostro clean su GCS** (`indice-pa/ipa_enti`, pubblico, nessuna credenziale).
Fallback: `--ipa-csv` (dump locale) o `--ipa-url` (dump ufficiale).

```bash
python obblighi/build_mapping.py --refresh         # riscrive lo YAML (nomi da GCS)
python obblighi/build_mapping.py --check-contract  # offline: decisione allineata (CI)
python obblighi/build_mapping.py --check-names     # rete: nomi allineati a IPA (schedulato)
python obblighi/build_mapping.py --ipa-csv <dump.csv>
```

- La **decisione** (`source_id -> codice_ipa`, `confidence`, `note`) sta nel codice:
  volatilità zero, check **offline** e bloccante in CI.
- I **nomi** (`denominazione`, `categoria`) sono derivati: check **con rete** in un
  job schedulato, non nel gate PR (evita rossi da rinomine IPA).
- Nessun path locale hardcoded, nessun file in `/tmp`.

## Verifica e gate

```bash
python obblighi/validate.py                 # offline: schema + FK + integrità
python obblighi/validate.py --with-locator  # offline: ancore nel testo di legge
```

- **Gate PR** (`.github/workflows/ci.yml`): `validate.py` + `--check-contract`.
  Offline e deterministico.
- **Drift schedulato** (`.github/workflows/obblighi-drift.yml`, lunedì):
  `--check-names` (IPA) + `--with-locator` (legal-graph). Se fallisce apre una
  issue di manutenzione; non blocca le PR.

## Stato attuale

- **T2** locatore — fatto (comma-scoped, `untested` ≠ `broken`).
- **T3** schema + validatore — fatto.
- **T4a** mapping `source_id → codice_ipa` — fatto (35/36, 3 `media` da rivedere).
- **T5** caso end-to-end AGENAS — fatto (buco `source_id` chiuso con `codice_ipa`).
- **T7** check automatici — fatto (gate offline + drift schedulato).
- **T8** estensione a 15–20 obblighi — **dopo un ciclo chiuso** (prime risposte reali).

## Prossimi passi

1. Chiudere le 3 `confidence: media` del mapping.
2. Trovare la fonte SO per AGENAS (o dichiarare il buco).
3. v0.1: aggiungere `codice_ipa` al record, per chiudere formalmente
   l'hop `obbligo → richiesta` (oggi il join è per convenzione via `source_id`).
4. T8: estendere gli obblighi a 15–20, solo quando ci sono 3–4 risposte reali.
