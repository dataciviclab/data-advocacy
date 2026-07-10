# data-advocacy

Campagna FOIA civica — richiedere il catalogo dei dati alle PA centrali.

**Layer 1: FOIA Catalogo.** Chiediamo a ogni ente l'inventario del proprio
patrimonio informativo: quali dati detiene, in che formato, quanto sono
aggiornati, chi li produce. Template Godfather: 3 richieste graduate,
tracciato record CSV allegato.

---

## Uso rapido

```bash
# Pre-verifica (SO + dati.gov.it) → scegli se FOIA o FOIA+DCD
python foia.py --stato ID_ENTE --azione foia       # solo FOIA
python foia.py --stato ID_ENTE --azione foia+dcd    # FOIA + DCD

# Genera file .eml pronto (HTML nel corpo + CSV allegato)
python foia.py --eml ID_ENTE

# Dopo l'invio PEC
python foia.py --send ID_ENTE

# Stato campagna
python foia.py --report
python foia.py --lista
python foia.py --da-fare

# Scadenze ed escalation
python foia.py --scadenze
python foia.py --anac ID_ENTE     # segnalazione ANAC
python foia.py --dcd ID_ENTE      # segnalazione AgID
```

## Dati

| File | Cosa |
|------|------|
| `enti/enti.json` | Anagrafica 42 enti con PEC, stato, note_foia |
| `data/tracker.json` | Richieste inviate e risposte |
| `richiedente.json` | Nome e PEC del richiedente (REDACTED) |
| `template-catalogo.txt` | Template Godfather (unico) |
| `data/allegato_catalogo.csv` | CSV template da allegare alla PEC |
| `skills/foia-verifica-e-azione.md` | Procedura operativa layer 1 |
| `bozze/` | Bozze generate (.txt + .eml), ignorato da git |

## Requisiti

Python 3.12+ — **nessuna dipendenza esterna** (solo stdlib).

## Setup

```bash
git clone git@github.com:dataciviclab/data-advocacy.git
cd data-advocacy
python foia.py --report
```

Prima di inviare, configura `richiedente.json` con il tuo nome e la tua PEC.

## Ciclo operativo

```
── SCEGLI ENTE ──►── PRE-VERIFICA ──►── DECIDI ──►── GENERA ──►── INVIA PEC ──►── TRACK ──►── ATTENDI ──►
                    (SO+dati.gov)      FOIA/DCD   bozza+eml                     30gg      RISPOSTA?
```

La pre-verifica (SO inventory + dati.gov.it) non serve per decidere SE
mandare — si manda sempre — ma per arricchire il FOIA con evidenze reali
e decidere se il DCD può già partire in parallelo (violazione formato
già visibile pubblicamente).

## Layer 2 (futuro)

FOIA su singolo dataset — dopo aver ottenuto il catalogo, richieste
mirate sui dataset critici.

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
