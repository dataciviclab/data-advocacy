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

## Prossimi passi (audit)

T2 locatore normativo → T3 schema `obligation`/`application` → T4b resolver → T5 caso #29 (AGENAS).
