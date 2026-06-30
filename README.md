# data-advocacy

Campagna FOIA quotidiana — verifica, diagnosi, azione, tracking.

**Prima verifica, poi agisci.** Ogni giorno:
1. Identifica il prossimo ente da verificare
2. Controlla il suo portale open data
3. Decidi se serve FOIA, DCD, entrambi o niente
4. Genera la bozza, invia PEC, traccia

## Uso

```bash
# Prossimo ente da verificare
python foia.py --next

# Dopo verifica manuale: registra diagnosi
python foia.py --stato poste-italiane --azione foia        # solo FOIA
python foia.py --stato consip --azione dcd                  # solo DCD
python foia.py --stato gse --azione foia+dcd                # entrambi
python foia.py --skip aifa                                  # OK, nessuna azione

# Traccia invio
python foia.py --send poste-italiane

# Registra risposta
python foia.py --respond poste-italiane --status ok

# Escalation
python foia.py --scadenze         # richieste scadute
python foia.py --anac poste-italiane   # bozza ANAC

# Riepilogo
python foia.py --status
python foia.py --lista
python foia.py --da-fare
```

## Dati

| File | Cosa |
|------|------|
| `enti/enti.json` | Anagrafica 40 enti con PEC e stato verifica |
| `data/tracker.json` | Richieste inviate |
| `template.txt` | Template FOIA |
| `bozze/` | Bozze generate (ignorato da git) |

## Requisiti

Python 3.12+ — **nessuna dipendenza esterna** (solo stdlib).

## Setup

```bash
git clone ...
cd data-advocacy
python foia.py --status
```

## Ciclo operativo

```
Giorno 0  → --next → verifica → --stato → --send
Giorno 30 → --scadenze → --anac
Se formato chiuso → --dcd
```

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
