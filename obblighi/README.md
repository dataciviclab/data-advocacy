# obblighi — riferimento operativo (v0)

Livello semantico **obbligo informativo → ente** (audit T1, 2026-11-06).

Non è un artifact pubblicato: è **reference data operativa**, versionata a mano.
Sta qui (e non in un repo autonomo) finché DEC #21 (versioning cross-repo) è aperta.

## `mapping_source_ipa.yaml` (T4a)

Mappa ogni `source_id` di `source-observatory` al `codice_ipa` dell'ente in `indice-pa`.
È il join **ente ↔ fonte** che oggi non esiste in nessun repo.

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

## Regole

- **Nessuna anagrafica duplicata**: solo `codice_ipa` come FK. Se IPA cambia, cambia a monte.
- Il mapping va rivisto **a mano** quando `source-observatory` aggiunge fonti o IPA cambia.
- Una fonte senza `codice_ipa` **non produce obblighi** (non si sa a chi applicarli).

## Come si rigenera (riproducibile da terzi)

Fonte dei nomi: il **nostro clean su GCS** (`indice-pa/ipa_enti`, pubblico, nessuna credenziale).
Fallback: `--ipa-csv` (dump locale) o `--ipa-url` (dump ufficiale).

```bash
python obblighi/build_mapping.py --refresh         # riscrive lo YAML (nomi da GCS)
python obblighi/build_mapping.py --check-contract  # offline: decisione allineata (CI)
python obblighi/build_mapping.py --check-names     # rete: nomi allineati a IPA (schedulato)
python obblighi/build_mapping.py --ipa-csv <dump.csv>
```

- La **decisione** (`source_id -> codice_ipa`, `confidence`, `note`) sta nel codice: volatilità
  zero, check **offline** e bloccante in CI.
- I **nomi** (`denominazione`, `categoria`) sono derivati: check **con rete** in un job schedulato,
  non nel gate PR (evita rossi da rinomine IPA).
- Nessun path locale hardcoded, nessun file in `/tmp`.

## Locatore normativo (T2)

Verifica che un obbligo sia ancorato al testo di legge (offline, via `legal-graph`):

```bash
python obblighi/locator.py <urn> <articolo> "<testo_ancora>"
# -> VERIFIED | BROKEN | UNTESTED
```

Un obbligo `broken` **non produce richieste**.

## Prossimi passi (audit)

T2 locatore normativo → T3 schema `obligation`/`application` → T4b resolver → T5 caso #29 (AGENAS).
