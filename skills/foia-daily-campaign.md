# FOIA Daily Campaign Skill

Procedura operativa per la campagna FOIA giornaliera automatizzata
su partecipate e fonti SO, usando `foia_campaign.py`.

## Trigger

Run giornaliero, 10 minuti. Alterna:
- **Giorni pari**: `--campaign partecipate` (97 candidate, score 0→100)
- **Giorni dispari**: `--campaign sources` (33 fonti SO, health score 30→81)

## Ciclo daily (10 min)

### 1. Prossima candidata

```bash
cd data-advocacy

# Giorno pari
python scripts/foia_campaign.py -c partecipate --next

# Giorno dispari
python scripts/foia_campaign.py -c sources --next
```

Output:
- Partecipate → `bozze/partecipate/partecipate_NNN_CF.txt`
- Sources → `bozze/sources/sources_NNN_SOURCEID.txt`
- Candidata aggiunta al tracker (`data/foia_tracker.json`)

### 2. Revisione umana

Apri la bozza generata e verifica:

| Cosa | Partecipate | Sources |
|---|---|---|
| **Destinatario PEC** | Cercalo su IPA o sul sito della società | Già in anagrafica (se presente) |
| **Mittente** | Sostituisci `[NOME COGNOME]` e `[PEC/EMAIL]` | Idem |
| **Testo** | Coerente con le violazioni dello scanner? | Coerente con health score? |
| **Allegati** | Vuoi allegare screenshot dello scanner? | Vuoi allegare health score? |

**Se la bozza è OK** → invia via PEC.

**Se la bozza non va bene** → skip (passa alla prossima) o modifica a mano.

### 3. Invio

Invia la PEC con:
- **Oggetto**: idem bozza
- **Corpo**: testo generato
- **Allegati** (opzionali): screenshot scanner / health score

Dopo invio:

```bash
python scripts/foia_campaign.py -c partecipate --mark-sent --index N
# oppure
python scripts/foia_campaign.py -c sources --mark-sent --index N
```

### 4. Follow-up risposte

Quando arriva una risposta:

```bash
python scripts/foia_campaign.py -c partecipate --mark-response --index N --status-resp responded_partial
# Opzioni: responded_full, responded_partial, ignored, refused
```

### 5. Stato campagna

```bash
python scripts/foia_campaign.py -c partecipate --status
python scripts/foia_campaign.py -c sources --status
```

## Tempistiche

| Giorno | Evento |
|---|---|
| 0 | Invio PEC |
| 30 | Scadenza risposta — se silenzio → prepara escalation RPCT |
| 50 | Scadenza RPCT — se silenzio → prepara escalation ANAC |
| 65 | Fine primo giro (97+33) — ricomincia |

## Escalation

Dopo 30 giorni senza risposta:

### Per partecipate
1. Segui `skills/foia-evidence-collection.md` per preparare il pacchetto
2. Segui `skills/escalation-anac.md` per segnalazione ANAC
3. Segui `skills/dcd-segnalazione.md` se il problema è formato chiuso

### Per fonti SO
1. Stessa procedura ma il destinatario è l'ente nell'anagrafica
2. Alcune fonti hanno già PEC in anagrafica — usala

## Output del sistema

| Artifact | Contiene | Dove |
|---|---|---|
| `bozze/{campaign}/` | Testo PEC generato | `data-advocacy/bozze/` |
| `foia_tracker.json` | Stato richieste, date, escalation | `data-advocacy/data/` |
| `scan_ranking.json` | Score e classifiche partecipate | `source-observatory/data/partecipate/` |
| `open_data_health_scores.json` | Health score fonti SO | `source-observatory/data/health/` |

## Riferimenti

- `data-advocacy/scripts/foia_campaign.py` — lo script
- `data-advocacy/skills/foia-campaign.md` — ciclo FOIA generale
- `data-advocacy/skills/escalation-anac.md` — escalation ANAC
- `source-observatory/scripts/scanner_partecipate.py` — scanner partecipate
- `AGENTS.md` — regole per agenti AI nel workspace
