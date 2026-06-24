# DCD Segnalazione — Segnalazione al Difensore civico per il digitale

Procedura per preparare e inviare segnalazioni al **Difensore civico per il
digitale (DCD)** presso AgID, ai sensi dell'art. 17, comma 1-quater CAD.

## Cos'è il DCD e quando usarlo

Il DCD è un canale **distinto e parallelo al FOIA** (vedi `foia-campaign.md`,
"due binari separati"). Mentre il FOIA chiede accesso ai dati, il DCD contesta
la **violazione degli obblighi di pubblicazione e formato**.

| Canale | Cosa contesta | Termine | Escalation |
|---|---|---|---|
| **FOIA** | Mancata pubblicazione / accesso negato | 30gg + 20gg RPCT | ANAC |
| **DCD** | Formato chiuso, HVD senza API, SSL rotto, assenza da dati.gov.it | Nessuno (diffida) | AgID → sanzioni art. 18-bis CAD |

**Regola**: FOIA e DCD possono (e dovrebbero) partire lo stesso giorno, così
l'ente riceve pressione su due fronti contemporaneamente.

## Trigger

Inviare segnalazione DCD quando:

- **Formato chiuso** — dataset pubblicati solo in XLSX/XLS/PDF/DOC
  (viola Art. 1(l-bis) CAD + Art. 7 D.Lgs 33/2013)
- **HVD in formato chiuso o senza API** — dataset HVD non accessibili via API
  né scaricabili in blocco in formato aperto
  (viola Reg. UE 2023/138 + Art. 12-bis D.Lgs 36/2006)
- **SSL rotto persistente** — portale open data con certificato scaduto o non valido
  (viola Art. 6 D.Lgs 33/2013 — qualità accesso)
- **Assenza da dati.gov.it** — ente che pubblica dati ma non li cataloga
  (viola Art. 52 CAD + Art. 9 D.Lgs 36/2006)
- **Licenza assente** — dati pubblicati senza licenza esplicita
  (Art. 52 CAD li rende comunque aperti, ma va segnalata l'omissione)

## Ciclo DCD

1. **Identifica violazione** — usa `foia-evidence-collection.md` per raccogliere
   evidenze verificabili (data, URL, formato, normativa)
2. **Prepara segnalazione** — compila template `dcd_segnalazione.j2` con evidenze
3. **Verifica contatti** — il DCD accetta email normali a `dcd@agid.gov.it`
4. **Invia** — da PEC o email ordinaria (PEC consigliata per tracciabilità)
5. **Registra** — nel FOIA registry come `sent` (o in registro DCD separato)
6. **Attendi riscontro** — DCD non ha termine vincolato. Se dopo 60gg nessuna
   azione, valuta:
   - Diffida formale via PEC
   - Segnalazione ad AgID per sanzioni ex art. 18-bis CAD
   - Pubblicazione del caso su canali pubblici

## Procedura dettagliata

### Fase 1 — Raccolta evidenze

Segui la skill `foia-evidence-collection.md` per ogni dataset coinvolto.
Per una segnalazione DCD servono almeno:

- **Evidenza di formato chiuso**: URL, Content-Type, estensione file
- **Data verifica**: timestamp ISO (es. `2026-06-23T10:04:09Z`)
- **Stato raggiungibilità**: HTTP status code
- **Norma violata**: articolo specifico (non generico)
- **Anni di mancato aggiornamento**: se il dato è fermo

### Fase 2 — Compilazione template

Usa il template `dcd_segnalazione.j2` (in `data_advocacy/templates/`).

Parametri del template:

| Parametro | Descrizione | Obbligatorio |
|---|---|---|
| `data` | Data segnalazione (ISO) | Sì |
| `ente_nome` | Nome ente da anagrafica | Sì |
| `mittente_nome` | Nome e cognome | Sì |
| `mittente_email` | Email di contatto | Sì |
| `violazioni` | Lista di oggetti `{problema, evidenza, norma}` | Sì |
| `formato_chiuso` | `true` se violazione formato chiuso | No |
| `hvd` | `true` se violazione HVD | No |
| `hvd_categoria` | Categoria HVD (Mobility, Geospatial...) | Se hvd=true |
| `aggiornamento` | Anno ultimo aggiornamento (se fermo) | No |

### Fase 3 — Invio

```
Destinatario: dcd@agid.gov.it
CC: protocollo@pec.agid.gov.it (solo da PEC)
Oggetto: Segnalazione ex art. 17, comma 1-quater CAD — [ENTE]: [VIOLAZIONE]
```

**Raccomandazioni**:
- Invia **da PEC** se possibile (tracciabilità legale)
- Allega **screenshot** della pagina o del dato incriminato
- Allega **tabella evidenze** in formato riproducibile (URL, data verifica)
- Se FOIA già inviato, cita il protocollo e allega la risposta (se c'è)

### Fase 4 — Registrazione (registro DCD separato)

⚠️ **Non usare il FOIA registry** (`foia_registry.json`) per le segnalazioni
DCD. Il FOIA registry ha stati e scadenze (30gg/50gg) progettati per il
ciclo FOIA. Registrare una DCD nel FOIA registry farebbe scattare
`check_deadlines.py` su una segnalazione che ha un ciclo diverso.

Usa invece un **registro DCD separato** (`data/dcd_registry.json`):

```json
{
  "id": "DCD-001",
  "ente": "Ministero della Giustizia",
  "source_id": "giustizia_statistiche",
  "data_invio": "2026-06-24",
  "violazioni": ["formato_chiuso", "licenza_assente"],
  "stato": "sent",
  "esito": "",
  "note": "Inviata a dcd@agid.gov.it, 9 dataset XLSX"
}
```

Stati DCD: `draft` → `sent` → `pending` → `response_received` → `resolved`.

Registra almeno:
- **id**: identificativo univoco (DCD-001, DCD-002...)
- **ente**: nome ente (da anagrafica)
- **data_invio**: ISO format
- **violazioni**: lista (formato_chiuso, hvd, ssl_rotto, datigovit_assente, licenza_assente)
- **stato**: draft / sent / pending / response_received / resolved
- **esito**: risposta ricevuta (se presente)

> 📌 *Issue tecnica aperta*: implementare `DcdRegistry` come modello dati
> dedicato con load/save JSON, analogo a `FoiaRegistry`.

## Template di segnalazione rapida

Per violazioni semplici (es. un singolo dataset in formato chiuso):

```
Oggetto: Segnalazione DCD — [ENTE]: dataset "[NOME]" in formato chiuso

Al DCD,

segnalo che [ENTE] pubblica il dataset "[NOME]" esclusivamente in formato
[FORMATO], che non è un formato aperto ai sensi dell'art. 1(l-bis) CAD.

Evidenza:
- URL: [URL]
- Formato: [XLSX/XLS/PDF]
- Verificato il: [DATA]
- Norma violata: Art. 7 D.Lgs 33/2013 + Art. 1(l-bis) CAD

Chiedo di diffidare [ENTE] a pubblicare in formato aperto (CSV/JSON).
```

## Differenze con segnalazione ANAC

| DCD | ANAC |
|---|---|
| Violazioni **formali** (formato, licenza, catalogazione) | Violazioni **procedurali** (silenzio dopo FOIA) |
| Nessun termine vincolato | Termini precisi (30gg FOIA + 20gg RPCT) |
| Sanzioni ex art. 18-bis CAD (10k-100k EUR) | Ordine pubblicazione + illecito disciplinare |
| Destinatario: AgID/DCD | Destinatario: ANAC |
| Può partire **insieme** al FOIA | Solo **dopo** FOIA + RPCT senza risposta |

## Riferimenti normativi

- Art. 17, comma 1-quater CAD — Poteri del Difensore civico per il digitale
- Art. 18-bis CAD — Sanzioni AgID (da 10.000 a 100.000 EUR)
- Art. 7 D.Lgs 33/2013 — Obbligo formato di tipo aperto
- Art. 6 D.Lgs 33/2013 — Qualità e aggiornamento
- Art. 52 CAD — Open data by default
- Art. 9 D.Lgs 36/2006 — Catalogo dati.gov.it
- Art. 12-bis D.Lgs 36/2006 — Obblighi HVD
- Reg. UE 2023/138 — Categorie e obblighi HVD
