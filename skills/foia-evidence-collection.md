# FOIA Evidence Collection — Raccolta evidenze per richieste FOIA

Procedura per raccogliere evidenze verificabili da usare nei template FOIA,
DCD e segnalazioni ANAC. Le evidenze trasformano una richiesta generica
("i dati non sono aperti") in una contestazione puntuale ("9 dataset in XLSX,
URL verificato il 23/06/2026, accessibile ma in formato chiuso").

## Trigger

Raccogliere evidenze quando:

- **Health score < 60** su uno o più assi (formato_aperto, raggiungibilita)
- **Radar YELLOW/RED** persistente (>3 giorni)
- **Formato chiuso** segnalato da inventory (`res_format = XLSX/XLS/PDF/DOC`)
- **Prima di segnalazione DCD**: serve prova del formato chiuso + normativa violata

## Procedura

### Passo 1 — Identificare la fonte e i dataset target

```bash
# 1. Ottieni overview della fonte (registry + radar + inventory)
so_source_overview --source-id <source_id>

# 2. Elenca item della fonte con formati
so_list_source_items --source-id <source_id> --limit 200

# 3. Cerca item specifici per formato chiuso
so_catalog_inventory_search --query "xlsx" --source-id <source_id>
so_catalog_inventory_search --query "pdf" --source-id <source_id>
```

**Output atteso**: lista di item con source_id, item_name, format, URL, captured_at.

### Passo 2 — Verifica raggiungibilità (probe HTTP)

Per ogni URL sospetto (formato chiuso o irraggiungibile):

```bash
# Probe HTTP leggero: status code, content-type, content-disposition
toolkit_probe_url --url "<URL_dataset>"

# Se è CSV/TSV: preview remoto con schema e righe
toolkit_preview_url --url "<URL_dataset>"

# Se è HTML: estrai link dati
toolkit_html_extract_links --url "<URL_portale>"
```

**Documenta**:
- Data e ora della verifica (es. `2026-06-23T10:04:09Z`)
- Status code HTTP (200 = raggiungibile, 500 = giù, 404 = scomparso)
- Content-Type e Content-Disposition
- Se il formato è chiuso o aperto

### Passo 3 — Verifica su dati.gov.it (se catalogato)

```bash
# Cerca organizzazione su dati.gov.it
ckan_organization_search --server https://dati.gov.it/opendata --pattern "<ministero>"

# Cerca dataset per parola chiave
ckan_find_relevant_datasets --server https://dati.gov.it/opendata --query "<tema>"
```

**Documenta**:
- Nome organizzazione su dati.gov.it
- Data di ultimo aggiornamento dei metadati
- Formato prevalente dei dataset
- Presenza/assenza di licenza

### Passo 4 — Normativa violata (ricerca italia-corpus)

Identifica la norma specifica violata:

```bash
# Cerca nell'italia-corpus
italia-corpus legal_search --query "formato aperto obbligo pubblicazione" --collezione "D.Lgs 33-2013"
```

**Riferimenti rapidi**:

| Problema | Norma |
|---|---|
| Formato chiuso (XLSX, PDF, DOC) | Art. 7 D.Lgs 33/2013 + Art. 1(l-bis) CAD |
| Dati non aggiornati | Art. 6 D.Lgs 33/2013 |
| Portale irraggiungibile | Art. 6 D.Lgs 33/2013 (qualità accesso) |
| Assenza da dati.gov.it | Art. 9 D.Lgs 36/2006 |
| Licenza assente | Art. 1(l-ter) CAD + Art. 3 D.Lgs 33/2013 |

## Template di evidenza

Per ogni dataset target, compila:

```
## [NOME DATASET]

| Campo | Valore |
|---|---|
| Nome | `item_name` |
| URL | `url_download` |
| Formato | `format` |
| Anni coperti | `years` |
| Stato raggiungibilità | HTTP 200 / 500 / timeout |
| Verificato il | `YYYY-MM-DD` |
| Licenza | `license_id` (se presente) |
| Aggiornamento | `metadata_modified` |
| Norma violata | Art. X D.Lgs Y |

**Evidenza supplementare**:
- Screenshot della pagina (se portale HTML)
- Output probe (se irraggiungibile)
- Collegamento a source-check (se già verificato)
```

## Controllo qualità evidenze

Prima di inserire in un template FOIA, verificare:

- [ ] **Data e ora** di ogni verifica sono registrate
- [ ] **URL** funzionante o prova di irraggiungibilità
- [ ] **Formato** dichiarato corrisponde a quello reale (`Content-Type` vs estensione)
- [ ] **Norma** citata è quella corretta per il problema specifico
- [ ] **Fonte** è la stessa indicata nell'anagrafica (source_id → ente)
- [ ] **Evidenza riproducibile**: chiunque può rifare la verifica

## Integrazione con FOIA engine

Le evidenze raccolte alimentano:

1. **Template FOIA** — `foia_standard.j2` / `foia_formato_chiuso.j2`
   - Usa il template evidenza per popolare la sezione "Evidenze" della lettera
   - Includi almeno 3 elementi per dataset: URL, formato, data verifica

2. **Segnalazione DCD** — `dcd_segnalazione.j2`
   - Evidenza di formato chiuso + assenza su dati.gov.it (se applicabile)
   - Cita esplicitamente art. 7 D.Lgs 33/2013

3. **Segnalazione ANAC** — `anac_segnalazione.j2`
   - Evidenza di silenzio dopo FOIA (30gg) + mancata risposta RPCT
   - Allegare cronologia verifiche e invii

4. **Issue FOIA** — template `foia-request.yml`
   - Le evidenza vanno nel body dell'issue come tabella markdown

## Esempio completo

```markdown
# Evidenze — Ministero della Giustizia (giustizia_statistiche)
Verificato il: 2026-06-23
Fonte: datiestatistiche.giustizia.it

## Clearance rate civile
| Campo | Valore |
|---|---|
| Nome | Indicatori_Civili |
| URL | https://datiestatistiche.giustizia.it/.../Indicatori_Civili.xlsx |
| Formato | XLSX |
| Stato | HTTP 200 (raggiungibile) |
| Licenza | Assente |
| Aggiornamento | 2025 |
| Norma violata | Art. 7 D.Lgs 33/2013 + Art. 1(l-bis) CAD |

## Clearance rate penale
... (stessa struttura)
```

## Strumenti MCP utili

| Tool | Cosa fa | Quando usarlo |
|---|---|---|
| `so_source_overview` | Overview completa fonte | Passo 1 |
| `so_list_source_items` | Lista item fonte | Passo 1 |
| `so_catalog_inventory_search` | Cerca item per formato/testo | Passo 1 |
| `toolkit_probe_url` | Verifica raggiungibilità HTTP | Passo 2 |
| `toolkit_preview_url` | Preview CSV/TSV remoto | Passo 2 |
| `toolkit_html_extract_links` | Estrai link dati da HTML | Passo 2 |
| `ckan_find_relevant_datasets` | Cerca su dati.gov.it | Passo 3 |
| `ckan_package_search` | Cerca organizzazioni CKAN | Passo 3 |
| `italia-corpus legal_search` | Ricerca normativa | Passo 4 |
