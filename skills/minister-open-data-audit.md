# Minister Open Data Audit — Valutazione conformità open data dei ministeri

Procedura sistematica per valutare la conformità di un ministero agli obblighi
di pubblicazione e formato aperto, con classificazione e gap analysis.

Base normativa: CAD (D.Lgs 82/2005), D.Lgs 33/2013, D.Lgs 36/2006 (recepimento
direttiva PSI), Reg. UE 2023/138 (HVD).

## Trigger

Eseguire un audit quando:

- **Nuovo ministero** aggiunto a source-observatory o all'anagrafica
- **Health score < 60** o formato chiuso segnalato da radar/signals
- **Prima di aprire un FOIA** — l'audit produce le evidenze necessarie
- **Aggiornamento trimestrale** della classifica trasparenza (mar, giu, set, dic)

## Criteri di valutazione

Ogni criterio deriva da una norma precisa. Punteggio: 0 (violazione) / 0.5 (parziale) / 1 (conforme).

### A. Formato aperto — Peso: 3
Riferimento: Art. 1(l-bis) CAD + Art. 7 D.Lgs 33/2013

| Punteggio | Criterio | Evidenza |
|---|---|---|
| 1 | ≥80% risorse in formato aperto (CSV, JSON, XML, ODS, GeoJSON, SHP...) | Facet `res_format` su CKAN |
| 0.5 | 50-80% in formato aperto | |
| 0 | <50% o solo PDF/XLS/XLSX/DOC | |

### B. Aggiornamento dati — Peso: 2
Riferimento: Art. 6 + Art. 8 D.Lgs 33/2013

| Punteggio | Criterio | Evidenza |
|---|---|---|
| 1 | Mediana aggiornamento < 1 anno | `metadata_modified` dei dataset |
| 0.5 | Mediana 1-3 anni | |
| 0 | Mediana > 3 anni o dati fermi | |

### C. Licenza aperta — Peso: 1
Riferimento: Art. 1(l-ter) CAD + Art. 3 D.Lgs 33/2013

| Punteggio | Criterio | Evidenza |
|---|---|---|
| 1 | ≥80% dataset con licenza esplicita (CC-BY, ODbL, IODL...) | `license_id` nei metadati |
| 0.5 | 50-80% | |
| 0 | <50% o assente | |

### D. Presenza su dati.gov.it — Peso: 2
Riferimento: Art. 9 D.Lgs 36/2006

| Punteggio | Criterio | Evidenza |
|---|---|---|
| 1 | Organizzazione presente su dati.gov.it con aggiornamento recente | `package_search` su dati.gov.it |
| 0.5 | Presente ma non aggiornato | |
| 0 | Non presente | |

### E. HVD compliance — Peso: 3
Riferimento: Art. 12-bis D.Lgs 36/2006 + Reg. UE 2023/138

| Punteggio | Criterio | Evidenza |
|---|---|---|
| 1 | Dataset HVD pubblicati con API + download in blocco + gratuiti | Verifica su dataset Mobility, Geospatial, Statistics... |
| 0.5 | HVD presenti ma senza API o con formati chiusi | |
| 0 | HVD assenti o tutti in formato chiuso | |

### F. Accessibilità FOIA — Peso: 1
Riferimento: Art. 5 D.Lgs 33/2013

| Punteggio | Criterio | Evidenza |
|---|---|---|
| 1 | RPCT facilmente reperibile, sezione Amministrazione Trasparente completa | Verifica sito ministero |
| 0.5 | RPCT presente ma sezione parziale | |
| 0 | RPCT non reperibile o sezione assente | |

## Calcolo punteggio

```
Punteggio finale = Σ (punteggio_criterio × peso) / Σ(pesi_max)
                 = valore da 0 a 1
                 = × 100 → punteggio in centesimi
```

### Griglia di valutazione

| Punteggio | Giudizio | Colore | Azione |
|---|---|---|---|
| 90-100 | **Eccellente** | 🟢 | Monitoraggio |
| 70-89 | **Buono** | 🟢 | Monitoraggio, segnalazione miglioramenti |
| 50-69 | **Sufficiente** | 🟡 | FOIA/DCD sulle carenze |
| 30-49 | **Insufficiente** | 🟠 | FOIA + DCD + escalation programmata |
| 0-29 | **Grave** | 🔴 | FOIA immediato + DCD + escalation |

## Procedura di raccolta dati

### Fase 1 — Ricognizione fonti (30 min per ministero)

```bash
# 1. Cerca organizzazione su dati.gov.it
# Usa il nome ministero in inglese o italiano
# Es: ministero-della-salute, ministero-infrastrutture-e-trasporti

# 2. Cerca portale CKAN dedicato
# Prova: dati.[ministero].gov.it / opendata.[ministero].gov.it

# 3. Cerca portale HTML
# Prova: sito istituzionale / statistiche / open-data

# 4. Verifica su Source Observatory
# so_registry_query source_id <ministero>
# so_list_source_items source_id <ministero>
# so_source_overview source_id <ministero>
```

### Fase 2 — Verifica conformità (20 min per ministero)

Per ogni dataset del ministero:

1. **Formato**: è aperto? (CSV/JSON/XML/ODS/GeoJSON = sì)
2. **Licenza**: è presente? (CC-BY/ODbL/IODL = sì)
3. **Aggiornato**: `metadata_modified` < 1 anno?
4. **HVD**: ricade in una delle 6 categorie del Reg. UE 2023/138?

### Fase 3 — Pubblicazione classifica

1. Tabella: Ministero | Punteggio | Giudizio | Gap principale
2. Per ogni ministero: link alla normativa violata (da italia-corpus)
3. Pubblicazione su dataciviclab discussion + report periodico

## Strumenti utili

```bash
# Query SO per contare dataset per formato
so_list_source_items --source-id <ministero> --limit 500

# Verifica presenza su dati.gov.it
ckan_organization_search --server https://dati.gov.it/opendata --pattern "<ministero>"

# Health score corrente
so_source_overview --source-id <ministero>

# Ricerca normativa violata
italia-corpus legal_search --query "formato aperto CAD" --collezione "D.Lgs 82-2005"
```

## Template report pubblicabile

```markdown
# Classifica trasparenza open data — Ministeri italiani
Data: [data]
Fonte: dati.gov.it + portali ministeriali + italia-corpus + source-observatory

## Classifica

| # | Ministero | Punteggio | Voto | Gap principale |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |

## Criteri usati
1. Formato aperto (Art. 1(l-bis) CAD + Art. 7 D.Lgs 33/2013) — peso 3
2. Aggiornamento (Art. 6+8 D.Lgs 33/2013) — peso 2
3. Licenza aperta (Art. 1(l-ter) CAD) — peso 1
4. Presenza su dati.gov.it (Art. 9 D.Lgs 36/2006) — peso 2
5. HVD compliance (Art. 12-bis D.Lgs 36/2006) — peso 3
6. Accessibilità FOIA (Art. 5 D.Lgs 33/2013) — peso 1

## Dettaglio per ministero
[Per ognuno: tabella violazioni con norme]
```

## Classifica verificata (SO inventory, 23-24 giugno 2026)

Punteggi calcolati con dati reali da Source Observatory: inventory items, formati,
raggiungibilità radar, presenza su dati.gov.it, licenze. Criteri e pesi in §2.

| # | Ministero | Score | Giudizio | Gap principale | Fonte SO |
|---|---|---|---|---|---|
| 1 | **Giustizia Amministrativa** (OpenGA) | 83 | 🟢 Buono | HVD non marcato, no RPCT verificato | 436 item CSV/JSON/ODS, CC-BY 4.0 ✅ |
| 2 | **Lavoro** | 58 | 🟡 Sufficiente | Licenza non esplicita, HVD assente | 83 item CSV/XML, su dati.gov.it ✅ |
| 3 | **Università (MUR)** | 58 | 🟡 Sufficiente | Licenza non esplicita, aggiornamento annuale | 69 item CSV/XML, su dati.gov.it ✅ |
| 4 | **Interno** | 46 | 🟠 Insufficiente | Formati misti, aggiornamento non verificato | 38 item su dati.gov.it ✅ |
| 5 | **Imprese (MIMIT)** | 46 | 🟠 Insufficiente | Solo XML, HVD assente | 370 item XML, su dati.gov.it ✅ |
| 6 | **Salute** | 46 | 🟠 Insufficiente | 4 dataset chiave in XLS (personale SSN), aggiornamento fermo | 51 item (47 CSV + 4 XLS) su dati.gov.it ✅ |
| 7 | **Istruzione (MIM)** | 42 | 🟠 Insufficiente | Non catalogato su dati.gov.it, inventory in calo (-67%) | 1128 link CSV/JSON/XML, portale HTML diretto |
| 8 | **MIT** | 42 | 🟠 Insufficiente | Portale diretto IRRAGGIUNGIBILE (da mag 2026), dati incidentalità fermi al 2018, HVD Mobility in XLSX | 70 item CKAN via proxy dati.gov.it |
| 9 | **Giustizia Ordinaria** (statistiche) | 13 | 🔴 Grave | 9 dataset tutti XLSX, nessuna licenza, nessun dato su dati.gov.it, FOIA #4 aperto | 9 item XLSX, portale HTML |
| 10 | **Ambiente (MASE)** | 0 | 🔴 Grave | Non monitorato da SO, non su dati.gov.it, 2 portali noti non censiti | Non censito |
| — | **Agricoltura (MASAF)** | — | 🔴 Non censito | Nessuna presenza su dati.gov.it, non in SO | — |
| — | **Esteri (MAECI)** | — | 🔴 Non censito | Portale irraggiungibile, non in SO | — |
| — | **Difesa** | — | 🔴 Non censito | Portale 404, non in SO | — |
| — | **Turismo** | — | 🔴 Non censito | Non ancora aggiunto al SO | — |

**Dettaglio criteri per ministero** (verifica 24/06/2026):

| Ministero | Formato aperto (p3) | Aggiornamento (p2) | Licenza (p1) | dati.gov.it (p2) | HVD (p3) | Accesso FOIA (p1) |
|---|---|---|---|---|---|---|
| Giustizia Amm. | 1.0 — 100% CSV/JSON | 1.0 — mensile | 1.0 — CC-BY 4.0 | 1.0 — presente | 0.5 — statistico non HVD | 0.5 — non verificato |
| Lavoro | 1.0 — CSV/XML | 0.5 — mensile/trim. | 0.5 — da verificare | 1.0 — presente | 0.0 — non HVD | 0.5 — non verificato |
| MUR | 1.0 — CSV/XML | 0.5 — annuale | 0.5 — da verificare | 1.0 — presente | 0.0 — non HVD | 0.5 — non verificato |
| Interno | 0.5 — da verificare | 0.5 — annuale | 0.5 — da verificare | 1.0 — presente | 0.0 — non HVD | 0.5 — non verificato |
| MIMIT | 0.5 — XML (aperto) | 0.5 — mensile | 0.5 — da verificare | 1.0 — presente | 0.0 — non HVD | 0.5 — non verificato |
| Salute | 0.5 — 92% CSV, ma XLS su personale | 0.5 — misto (alcuni fermi 2019) | 0.5 — da verificare | 1.0 — presente | 0.0 — non HVD | 0.5 — non verificato |
| Istruzione | 1.0 — 100% CSV/JSON/XML | 0.5 — annuale | 0.5 — da verificare | 0.0 — assente | 0.0 — non HVD | 0.5 — non verificato |
| MIT | 0.5 — 89% open ma HVD in XLSX | 0.0 — incidentalità ferma 2018 | 1.0 — CC-BY 4.0 | 1.0 — presente | 0.0 — HVD in XLSX | 0.5 — non verificato |
| Giustizia Ord. | 0.0 — 100% XLSX | 0.5 — aggiornato 2014-2025 | 0.0 — assente | 0.0 — assente | 0.0 — non HVD | 0.5 — non verificato |
| MASE | 0.0 — non censito | 0.0 — non censito | 0.0 — non censito | 0.0 — assente | 0.0 — non censito | 0.0 — non censito |

## Riferimenti normativi

- Art. 1(l-bis) D.Lgs 82/2005 (CAD) — Definizione di formato aperto
- Art. 1(l-ter) D.Lgs 82/2005 (CAD) — Definizione di dati di tipo aperto
- Art. 5 D.Lgs 33/2013 — Accesso civico semplice e generalizzato
- Art. 6 D.Lgs 33/2013 — Qualità e aggiornamento delle informazioni
- Art. 7 D.Lgs 33/2013 — Obbligo pubblicazione in formato di tipo aperto
- Art. 12-bis D.Lgs 36/2006 — High Value Datasets (introdotto da D.Lgs 200/2021)
- Reg. UE 2023/138 — Elenco HVD e obblighi di pubblicazione
