# data-advocacy

Strumenti di advocacy sui dati pubblici: compliance scoring, FOIA engine,
segnalazioni DCD/ANAC, tracciamento della pressione su fonti e dataset.

## Posizione nell'ecosistema

```
source-observatory ──► data-advocacy ──► enti (FOIA/PEC/DCD)
       │                      │
       │                 issue pubbliche
  segnali radar         dataciviclab/discussions
  inventory
  compliance scores
```

`data-advocacy` consuma gli artifact di `source-observatory` (radar, signals,
compliance scores) e li trasforma in azioni: richieste FOIA, segnalazioni
DCD/ANAC, tracciamento risposte, escalation.

## Cosa fa

| Componente | Cosa fa |
|---|---|
| **Compliance scoring** | Valuta ogni fonte su 6 assi (formato, aggiornamento, licenza, dati.gov.it, HVD, FOIA accessibility) |
| **FOIA engine** | Macchina a stati: trigger → bozza → invio → attesa risposta → escalation RPCT/ANAC |
| **Template FOIA** | Bozze precompilate basate su segnali radar/signals |
| **Registro FOIA** | Tracciamento richieste inviate, risposte ricevute, scadenze |
| **Anagrafica enti** | Contatti URP, PEC, RPCT per ministeri ed enti pubblici |
| **Segnalazioni DCD** | Generazione bozze segnalazione AgID per violazione formato aperto |

## Come si collega a Source Observatory

I segnali prodotti da SO (radar RED persistente, compliance score basso,
SSL rotto, dati mancanti) sono i trigger per le azioni di advocacy.

Contratto tra i due repo:

| Artifact SO | Consumato da | Uso |
|---|---|---|
| `radar/radar_summary.json` | FOIA engine | RED streak >= 5 → trigger FOIA |
| `catalog/catalog_signals.json` | Compliance scorer | Segnali inventory/drift |
| `catalog/sources_registry.yaml` | Anagrafica | Esteso con contatti FOIA |

## Struttura del repo

```
data_advocacy/
├── registry/        # FOIA registry, anagrafica enti, modelli dati
├── engine/          # Macchina a stati FOIA, escalation
├── scoring/         # Compliance scoring (modelli e logica)
├── connectors/      # Canali di pressione (email, PEC, DCD)
data/                # Artifact versionati (registry JSON, anagrafica YAML)
scripts/             # Script operativi e CI
skills/              # Guide operative per agenti
tests/               # Test
```

## Setup locale

```bash
pip install -e ".[dev]"
```

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
