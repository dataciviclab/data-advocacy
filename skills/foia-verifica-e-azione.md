# FOIA — Verifica e Azione

Procedura operativa per la campagna FOIA quotidiana: **prima verifica,
poi agisci**. Non si manda FOIA alla cieca.

## Flusso

```
──next──► VERIFICA ──stato──► AZIONE ──send──► TRACKING ──respond──► CHIUSO
            │                    │
            │  ok                │  foia/dcd
            ▼                    ▼
          SKIP              GENERA BOZZA
```

## 1. Prossimo ente

```bash
python foia.py --next
```

Mostra il primo ente con `stato = da-verificare` (ordinati per categoria).
Se non ce ne sono, mostra il prossimo da inviare o segnala ciclo completato.

## 2. Verifica

Apri il sito/portale dell'ente. Cerca:

- **Sezione "Open Data"** o **"Amministrazione Trasparente"**
- I dati sono scaricabili in **formato aperto** (CSV, JSON, XML)?
- Il portale è **raggiungibile e funzionante**?
- I dati sono **aggiornati**?
- È presente su **dati.gov.it**?

Puoi aiutarti con strumenti automatici:
- `toolkit_probe_url_routed` per verificare raggiungibilità del sito
- `brave_web_search` per cercare il portale open data dell'ente
- `ckan_package_search` su dati.gov.it per vedere se l'ente ha dataset

## 3. Diagnosi

| Se trovi... | Azione |
|---|---|
| Dati già pubblicati in formato aperto, portale OK | `--stato ID --azione ok` (nessuna azione) |
| Dati non pubblicati (sezione assente o vuota) | `--stato ID --azione foia` |
| Dati pubblicati ma in formato chiuso (PDF/XLS non elaborabile) | `--stato ID --azione dcd` |
| Entrambi (dati assenti + sito con problemi) | `--stato ID --azione foia+dcd` |
| Portale inaccessibile (SSL rotto, errore 500, down) | `--stato ID --azione dcd` (problema accessibilità) |

```bash
# Esempi
python foia.py --stato poste-italiane --azione foia
python foia.py --stato consip --azione dcd
python foia.py --skip aifa          # alias per --stato aifa --azione ok
```

La diagnosi registra lo stato in `enti/enti.json` e **genera automaticamente**
la bozza della PEC/DCD se l'azione lo richiede.

## 4. Invio

Le bozze sono in `bozze/`. Per ogni bozza:

1. Apri il file `.txt`
2. Sostituisci `[NOME COGNOME RICHIEDENTE]` e `[PEC/EMAIL RICHIEDENTE]`
3. Invia via PEC all'indirizzo indicato nella bozza

Dopo l'invio:

```bash
python foia.py --send poste-italiane      # Traccia invio FOIA
```

Le bozze DCD si inviano a `dcd@agid.gov.it` (non serve `--send`, non si tracciano).

## 5. Follow-up

### Risposta ricevuta

```bash
python foia.py --respond poste-italiane --status ok
# Altri status: parziale, rifiutata, ignorata
```

### Mancata risposta (30gg+)

```bash
python foia.py --scadenze          # Elenca scadute
python foia.py --anac poste-italiane  # Genera bozza ANAC
```

La bozza ANAC va inviata a `protocollo@pec.anac.it`.

## 6. Stato campagna

```bash
python foia.py --status     # Riepilogo generale
python foia.py --lista      # Tutti gli enti con stato
python foia.py --da-fare    # Coda azioni pendenti
```

## Riferimenti

- `foia.py` — script operativo
- `enti/enti.json` — anagrafica enti
- `data/tracker.json` — richieste inviate
- `template.txt` — template FOIA
- `bozze/` — bozze generate
