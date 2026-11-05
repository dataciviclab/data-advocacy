# FOIA Catalogo — Procedura Layer 1

Richiedere l'inventario del patrimonio informativo di un ente pubblico.
La richiesta è legittima per qualsiasi ente, a prescindere dal suo stato
di compliance. La pre-verifica serve solo per arricchire il FOIA con
evidenze reali e decidere se il DCD può già essere inviato in parallelo.

Layer 2 (FOIA su singolo dataset) è ora la strada principale: vedi il README
e `registro.py` per il log delle richieste mirate. Questa skill resta la
procedura Layer 1 (catalogo), archiviata.

---

## Principio

> Chiediamo ciò che ogni ente è obbligato per legge a sapere di sé:
> quali dati detiene, in che formato, quanto sono aggiornati, chi li produce.

Non valutiamo, non screeniamo, non classifichiamo. Mandiamo e basta.
La risposta — o il silenzio — è già un dato.

---

## Flusso operativo

```
─── SCEGLI ENTE ──►─── PRE-VERIFICA ──►─── DECIDI ──►─── GENERA ──►─── COMPILA ──►─── INVIA ──►─── TRACK ──►─── ATTENDI ──►
                        │                  │              │                                             │
                        │                  │          csv allegato                                RISPOSTA? ──► PUBBLICA
                        ▼                  ▼                                                              │
                   SO + dati.gov     Solo FOIA?                                                           ▼ no
                                     o FOIA+DCD?                                                    ESCALATION (30gg+)
```

---

## 1. Scegli l'ente target

Seleziona un ente pubblico centrale tra:

- **Ministeri** (MIMIT, MEF, MASE, MIT, Ministero Salute, MIM, MUR, ...)
- **Agenzie nazionali** (AIFA, AGID, INPS, INAIL, ISTAT, ...)
- **Autorità indipendenti** (ANAC, AGCM, Garanti, ...)
- **Partecipate statali** (Consip, PagoPA, FS, Poste, RAI, GSE, ...)
- **Organi costituzionali** (Camera, Senato, Corte Costituzionale)

Criteri di priorità (non vincolanti):
1. Ente con cui hai già un rapporto (es. dati già usati in pipeline Lab)
2. Ente che gestisce dati ad alto impatto civico (sanità, ambiente, economia)
3. Ente di cui vuoi testare la reattività

Non serve preparazione. Si parte.

---

## 2. Pre-verifica rapida (10 min per ente)

Raccogli evidenze pubbliche per arricchire il FOIA e decidere se mandare
anche DCD in parallelo. Non serve per decidere SE mandare — si manda sempre
— ma per COME arricchire la richiesta.

### Strumenti

| Fonte | Cosa cercare | Tool |
|---|---|---|
| Source Observatory | Health score, inventory items, formati, stato portale | `so_source_overview(source_id)` |
| dati.gov.it | Dataset, formati, metadata_modified, facet | `ckan_organization_show(server, id)` |
| Probe URL | Raggiungibilità, SSL, tipo portale | `toolkit_source(action="probe", url=url, routed=True)` |

### Procedura

```
Passo A — Source Observatory
   so_source_overview(source_id="ente")
   → health score, inventory items, formati, raggiungibilità

Passo B — dati.gov.it
   ckan_organization_show(server="https://dati.gov.it/opendata", id="slug-ente")
   → dataset count, metadata_modified
   ckan_package_search(..., fq="organization:slug-ente", facet_field=["res_format"])
   → formati disponibili (es. CSV 59, XLSX 45, PDF 7)

Passo C — Probe URL (se portale noto)
   toolkit_source(action="probe", url="https://dati.ente.gov.it", routed=True)
   → raggiungibilità, tipo (CKAN/HTML/SDMX)
```

### Decisione

Dopo la pre-verifica, decidi se inviare.
**Attenzione**: non tutto ciò che è PDF/XLSX è violazione. Va distinto:

| Evidenza | Azione |
|---|---|
| Dati in formato aperto (CSV/XML/JSON), eventuale PDF è documentazione | Solo FOIA catalogo |
| **Dati** pubblicati in formato chiuso (es. XLS al posto di CSV) | **FOIA + DCD in parallelo** |
| Nessun dato su dati.gov.it | **FOIA** (DCD dopo risposta se serve) |
| Dati fermi da oltre 1 anno | **FOIA** + alla risposta valuta ANAC per aggiornamento |

Il DCD in parallelo va usato solo per **dati in formato chiuso**, non per
documentazione accessoria (schede PDF, manuali). Per verificare, apri
una risorsa: se il PDF descrive il dataset, non è violazione. Se il PDF
contiene i dati al posto del CSV, è violazione.

---

## 3. Genera il pacchetto

```bash
python foia.py --stato ID_ENTE --azione foia
```

Produce in `bozze/`:

| File | Contenuto |
|---|---|
| `bozze/ID_ENTE.txt` | Testo richiesta FOIA (template catalogo) |
| `bozze/ID_ENTE_catalogo.csv` | CSV template vuoto da allegare |

Se vuoi anche la bozza DCD (segnalazione formato chiuso):

```bash
python foia.py --stato ID_ENTE --azione foia+dcd
```

Aggiunge `bozze/dcd_ID_ENTE.txt`.

---

## 4. Compila le evidenze (prima dell'invio)

Apri `bozze/ID_ENTE.txt` e personalizza:

### Punto 7 — Tipo ente
Sostituisci il placeholder con la qualifica giusta:

| Se l'ente è | Sostituisci con |
|---|---|
| Ministero | `ministero` |
| Agenzia nazionale | `agenzia nazionale di cui all'art. 2-bis D.Lgs. 33/2013` |
| Società in controllo pubblico | `società in controllo pubblico ai sensi dell'art. 2-bis, comma 2, D.Lgs. 33/2013` |
| Autorità indipendente | `autorità amministrativa indipendente` |
| Ente pubblico | `ente pubblico di cui all'art. 2-bis D.Lgs. 33/2013` |

### Punto 8 — Evidenze specifiche (opzionale ma raccomandato)
Se hai informazioni su criticità note, inseriscile. Altrimenti lascia il placeholder.
Esempi:
- "Il portale open data risulta irraggiungibile da maggio 2026"
- "4 dataset chiave sono pubblicati in formato XLS (non aperto)"
- "L'ultimo aggiornamento del catalogo risale al 2023"

Se non hai evidenze, cancella le righe o lascia: "Richiesta generica di verifica."

---

## 5. Invia PEC

Dal tuo client PEC (dataciviclab@pec.it):

| Campo | Contenuto |
|---|---|
| **A** | PEC dell'ente (da `enti.json` o verificata su IPA) |
| **Oggetto** | Uguale alla prima riga della bozza |
| **Corpo** | Incolla il contenuto di `bozze/ID_ENTE.txt` |
| **Allegato** | `bozze/ID_ENTE_catalogo.csv` |

Se è presente anche la bozza DCD, la invii a `protocollo@pec.agid.gov.it` solo **dopo** la scadenza dei 30gg (non prima).

---

## 6. Traccia l'invio

```bash
python foia.py --send ID_ENTE
```

Registra data invio, calcola scadenza (30gg), aggiorna il report.

```bash
python foia.py --report       # Riepilogo campagna
python foia.py --da-fare      # Coda azioni pendenti
```

---

## 7. Attendi e monitora

| Giorno | Evento | Azione |
|---|---|---|
| 0 | Invio PEC | `--send` |
| +7 | Nessuna news | Controlla che la PEC non sia rimbalzata |
| +30 | Scadenza risposta | `--scadenze` |
| +30-35 | Se risposta arrivata | `--respond ID --status ok/parziale/rifiutata` |
| +30-35 | Se silenzio | `--anac ID` (mancata risposta ad ANAC) |

---

## 8. Alla risposta

Quando l'ente risponde:

```bash
python foia.py --respond ID_ENTE --status ok --note "CSV ricevuto con N dataset"
```

Poi:

1. **Valida il CSV**: controlla che abbia le 11 colonne del tracciato
2. **Carica in pipeline**: converti in parquet, aggiungi allo schema `catalogo_dati_ENTE`
3. **Accumula**: `catalogo_dati_pa.parquet` (dataset aggregato tra enti)
4. **Pubblica**: su data-explorer
5. **Scrivi analisi**: quanti dataset, formati, aggiornamento, gap

Se la risposta è in formato chiuso (PDF, XLSX, lettera):
- Registra come `parziale`
- Invia DCD ad AgID per violazione formato aperto

---

## 9. Escalation (30gg senza risposta)

```bash
python foia.py --scadenze
python foia.py --anac ID_ENTE     # genera bozza segnalazione ANAC
python foia.py --dcd ID_ENTE      # genera bozza DCD per AgID
```

- **ANAC** (`protocollo@pec.anac.it`): per mancata risposta FOIA (30gg) o dati non aggiornati
- **DCD** (`protocollo@pec.agid.gov.it`): solo per **dati in formato chiuso** (non per documentazione PDF)
- Dopo l'escalation, aggiorna il tracker: `--respond --status ignorata`

---

## Riferimenti

- `foia.py` — script operativo (Layer 1)
- `registro.py` — log delle richieste Layer 2
- `enti/enti.json` — anagrafica enti (da ampliare)
- `data/archivio/tracker.json` — tracker storico Layer 1 (congelato)
- `template-catalogo.txt` — template Godfather
- `data/allegato_catalogo.csv` — CSV template vuoto
- `bozze/` — bozze generate e CSV allegati
