# data-advocacy

Strumenti di advocacy sui dati pubblici: health scoring, FOIA engine,
segnalazioni DCD/ANAC, tracciamento della pressione su fonti e dataset.

**Avvertenza**: i punteggi e le azioni raccomandate sono diagnostici, non
certificativi. Richiedono verifica umana prima di qualsiasi azione legale.

## Posizione nell'ecosistema

```
source-observatory ──► data-advocacy ──► enti (FOIA/PEC/DCD)
       │                      │
       │                 bozze precompilate
  radar/health/signals    tracciamento scadenze
```

`data-advocacy` consuma gli artifact di `source-observatory` (radar, health
scores, signals) e li trasforma in azioni: richieste FOIA, segnalazioni
DCD/ANAC, tracciamento risposte, escalation.

## Cosa fa

| Componente | Cosa fa |
|---|---|
| **Open Data Health Scores** | Valuta ogni fonte su 6 assi (formato, raggiungibilita', licenza, dati.gov.it, HVD, FOIA). Bridge da SO |
| **FOIA engine** | Macchina a stati: trigger → bozza → invio → attesa risposta → escalation RPCT/ANAC |
| **Template FOIA** | 3 template Jinja2 (standard, formato chiuso, DCD) |
| **Generatore bozze** | `generate_foia_draft.py`: da health score + anagrafica → bozza precompilata |
| **Registro FOIA** | Tracciamento richieste inviate, risposte ricevute, scadenze (30gg / 50gg) |
| **Anagrafica enti** | 16 enti con contatti PEC, URP, RPCT |
| **Segnalazioni DCD** | Generazione bozze segnalazione AgID per formato chiuso |
| **Board FOIA** | [Project #7](https://github.com/orgs/dataciviclab/projects/7) — tracciamento pubblico stato richieste |
| **Syncer** | `sync_foia_issues.py` — registry JSON → Issue + Board |

## Contratto con Source Observatory

| Artifact SO (data/) | Consumato da | Uso |
|---|---|---|
| `health/open_data_health_scores.json` | Generatore bozze | Trigger per azione |
| `radar/radar_summary.json` | (riferimento) | Stato raggiungibilita' |
| `catalog/catalog_signals.json` | (riferimento) | Segnali formati |
| `radar/sources_registry.yaml` | (riferimento) | Lista fonti |

## Struttura del repo

```
data_advocacy/
├── registry/              # FoiaRequest, Ente, Contatti, Registry JSON
├── engine/                # Macchina a stati FOIA, escalation
├── templates/             # 3 template Jinja2 (foia_standard, formato_chiuso, dcd)
├── connectors/            # (futuro) canali di pressione
├── data/                  # Anagrafica enti (JSON)
├── scripts/
│   ├── check_deadlines.py        # Daily: trova FOIA scadute → escalation
│   ├── generate_foia_draft.py    # Da health scores → bozza FOIA
│   └── sync_foia_issues.py       # Registry → Issue + Project Board
├── skills/
│   └── foia-campaign.md          # Procedura operativa
└── tests/
    └── test_registry.py          # Test FOIA registry + anagrafica
```

## Setup locale

```bash
pip install -e ".[dev]"
```

## Generare una bozza FOIA

```bash
# Per tutte le fonti deboli/carenti
python scripts/generate_foia_draft.py --all-critical --out-dir bozze/

# Per una fonte specifica
python scripts/generate_foia_draft.py --source mit_opendata --out-dir bozze/

# Per tutte le fonti (33)
python scripts/generate_foia_draft.py --all --out-dir bozze/
```

## Verifiche pre-commit

```bash
ruff check .
mypy data_advocacy/
pytest tests/ --cov=data_advocacy
```

## Board pubblica

Le richieste FOIA sono tracciate pubblicamente su GitHub Projects:

https://github.com/orgs/dataciviclab/projects/7

Ogni issue nella board ha stato, scadenza, ente e trigger. L'aggiornamento
e' automatico via `sync_foia_issues.py` (workflow daily).

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
