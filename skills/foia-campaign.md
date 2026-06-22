# FOIA Campaign Skill

Procedura operativa per condurre una campagna FOIA.

## Trigger

Una fonte diventa candidata FOIA quando:

- **Radar RED per >=5 giorni consecutivi**: fonte irraggiungibile
- **Compliance score < 40**: violazione obblighi pubblicazione
- **SSL rotto persistente**: segnalazione DCD
- **Dato pubblicato solo in formato chiuso**: segnalazione DCD

## Ciclo FOIA

1. **Apri issue** con template `foia-request.yml` in `data-advocacy`
2. **Genera bozza** usando il template appropriato in `templates/`
3. **Verifica contatti** in anagrafica (PEC > URP email)
4. **Invia** via PEC (o email ordinaria)
5. **Registra** come `sent` nel FOIA registry
6. **Attendi 30 giorni** → se nessuna risposta: escalation RPCT
7. **Attendi 20 giorni** → se nessuna risposta: escalation ANAC
8. **Archivia** come `resolved` o `ignored`

## Template disponibili

| Template | Per |
|---|---|
| `foia_standard.j2` | Richiesta generica art. 5 D.Lgs 33/2013 |
| `foia_formato_chiuso.j2` | Dato pubblicato in formato chiuso (art. 7, CAD) |
| `dcd_segnalazione.j2` | Segnalazione AgID/DCD per formato chiuso o HVD |

## Riferimenti normativi

- Art. 5 D.Lgs 33/2013 — Accesso civico semplice
- Art. 5-bis D.Lgs 33/2013 — Accesso civico generalizzato
- Art. 7 D.Lgs 33/2013 — Obblighi di pubblicazione
- Art. 9 D.Lgs 200/2021 — High Value Datasets
- Art. 45 D.Lgs 33/2013 — Poteri ANAC
- Art. 50 c.3-ter CAD — Poteri AgID/DCD
