# data-advocacy

Campagna FOIA quotidiana — invio, tracking, escalation DCD/ANAC.

1 richiesta FOIA al giorno, template quasi identico, pressione sistemica
su enti pubblici e partecipate 100% pubbliche.

## Come funziona

```bash
# Prossimo ente da contattare
python foia.py --next

# Segna come inviato (dopo aver inviato la PEC a mano)
python foia.py --send poste-italiane

# Registra risposta ricevuta
python foia.py --respond poste-italiane --status ok

# Tabella riepilogativa
python foia.py --status

# Richieste scadute (30gg senza risposta)
python foia.py --scadenze

# Genera bozza segnalazione DCD (AgID) per formato chiuso
python foia.py --dcd poste-italiane

# Genera bozza segnalazione ANAC per mancata risposta
python foia.py --anac poste-italiane
```

## Ciclo operativo

| Giorno | Azione |
|--------|--------|
| 0 | `--next` → genera bozza → **invia PEC a mano** → `--send` |
| 30 | Se nessuna risposta → `--scadenze` → `--anac` |
| Se violazione formato | `--dcd` → segnalazione ad AgID |

## Dati

| File | Cosa |
|------|------|
| `enti/enti.json` | Anagrafica enti con PEC |
| `data/tracker.json` | Stato richieste (inviate, risposte, scadenze) |
| `template.txt` | Template unico richiesta FOIA |
| `bozze/` | Bozze generate (ignorato da git) |

## Requisiti

Python 3.12+ — **nessuna dipendenza esterna** (solo stdlib).

## Setup

```bash
git clone ...
cd data-advocacy
python foia.py --status
```

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
