# Escalation ANAC — Segnalazione all'Autorità Nazionale Anticorruzione

Procedura per gestire le escalation ad ANAC dopo il mancato riscontro a una
richiesta FOIA, ai sensi degli artt. 5 e 45 del D.Lgs. 33/2013.

L'escalation ANAC è l'**ultimo stadio del ciclo FOIA**, dopo che l'ente e il
suo RPCT hanno ignorato la richiesta. Non va usata per violazioni di formato
(quelle vanno al DCD, vedi `dcd-segnalazione.md`).

## Trigger

L'escalation ANAC scatta quando:

| Stato FOIA | Condizione | Azione |
|---|---|---|
| `SENT` → `WAITING_RESPONSE` | Nessuna risposta dopo **30 giorni** dall'invio | Attendere 20gg per RPCT |
| `WAITING_RESPONSE` → `ESCALATION_RPCT` | Nessuna risposta dopo **50 giorni** dall'invio (30+20) | Inviare richiesta riesame RPCT |
| `ESCALATION_RPCT` → `ESCALATION_ANAC` | Nessuna risposta RPCT dopo **20 giorni** ulteriori (70 totali) | Segnalazione ad ANAC |
| `SENT` diretta → `ESCALATION_ANAC` | Risposta ricevuta ma **negata senza motivazione** | Segnalazione ad ANAC |

### Verifica automatica

Il workflow daily `check_deadlines.py` esegue questo controllo:

```bash
python scripts/check_deadlines.py
# Output:
# - FOIA-001: superata scadenza 30gg -> waiting_response
# - FOIA-002: superata scadenza 50gg -> escalation RPCT
```

## Ciclo di escalation completo

```
GIORNO 0  — Invio FOIA (SENT)
    ↓ 30gg
GIORNO 30 — Scadenza risposta → WAITING_RESPONSE
    ↓ 20gg
GIORNO 50 — Scadenza RPCT → ESCALATION_RPCT
           → Invia richiesta riesame al RPCT
    ↓ 20gg
GIORNO 70 — Scadenza ANAC → ESCALATION_ANAC
           → Invia segnalazione ad ANAC
    ↓
Attendi ordine ANAC o risposta ente
```

## Procedura dettagliata

### Fase 1 — Verifica termini (al giorno 30)

Prima di qualsiasi escalation, verifica:

```bash
# Controlla stato FOIA nel registry
# Il workflow daily check_deadlines.py fa questo automaticamente
python scripts/check_deadlines.py
```

Se il FOIA è in `WAITING_RESPONSE` da oltre 20 giorni (giorno 50 totale):

- Passo a **Fase 2** (richiesta riesame RPCT)
- Se passati altri 20 giorni senza risposta RPCT (giorno 70):
- Passo a **Fase 3** (segnalazione ANAC)

### Fase 2 — Richiesta riesame RPCT (al giorno 50)

Il RPCT (Responsabile per la Prevenzione della Corruzione e della Trasparenza)
è il primo livello di escalation interno all'ente.

**Prepara richiesta**:

```
Destinatario: RPCT di [ENTE_NOME]
Trovare contatto in:
- anagrafica_enti.json → rpct_email
- Sezione "Amministrazione Trasparente" del sito dell'ente
- IPA (codice_ipa → rpct)

Oggetto: Richiesta di riesame ex art. 5, comma 7 D.Lgs 33/2013 — FOIA [ID]
         del [DATA_INVIO] — mancata risposta
```

**Testo richiesta**:

```
Con la presente, ai sensi dell'art. 5, comma 7 del D.Lgs. 33/2013,
richiedo il riesame della richiesta di accesso civico FOIA [ID],
inviata in data [DATA_INVIO] a [ENTE] via [PEC/email], ad oggi
senza riscontro.

La richiesta FOIA chiedeva: [DESCRIZIONE DATASET / DOCUMENTI]

L'art. 5, comma 6 D.Lgs. 33/2013 prescrive che «il rilascio di dati
o documenti in formato elettronico o cartaceo è gratuito [...] e deve
avvenire entro trenta giorni».

A distanza di [N] giorni, l'Amministrazione non ha fornito riscontro.

Alla presente allego:
1. Copia della richiesta FOIA inviata
2. Ricevuta di invio (PEC/email)
3. Evidenze raccolte (da foia-evidence-collection)
```

**Cosa fare dopo invio RPCT**:
- Registra nel FOIA registry: `stato = ESCALATION_RPCT`
- Nota: `richiesta_riesame_rpct_inviata = [DATA]`
- Attendi 20 giorni

### Fase 3 — Segnalazione ANAC (al giorno 70)

Se anche il RPCT non risponde entro 20 giorni, si procede con la segnalazione
formale ad ANAC usando il template `anac_segnalazione.j2`.

**Prepara segnalazione**:

Parametri del template `anac_segnalazione.j2`:

| Parametro | Descrizione | Obbligatorio |
|---|---|---|
| `data` | Data segnalazione | Sì |
| `ente_nome` | Nome ente | Sì |
| `mittente_nome` | Nome e cognome | Sì |
| `mittente_email` | Email di contatto | Sì |
| `data_foia` | Data invio FOIA originale | Sì |
| `foia_id` | ID FOIA nel registry | Sì |
| `dataset_nome` | Dataset / oggetto richiesta | Sì |
| `data_rpct` | Data richiesta riesame RPCT | Se inviato |
| `violazioni` | Lista `{problema, evidenza, norma}` | No |

**Template minimo per ANAC**:

```
Oggetto: Segnalazione ex art. 45 D.Lgs. 33/2013 — Mancata risposta a
         richiesta FOIA [ID] da parte di [ENTE]

All'Autorità Nazionale Anticorruzione
PEC: protocollo@pec.anac.it

Il sottoscritto [NOME], ai sensi dell'art. 45 del D.Lgs. 33/2013,
SEGNALA la mancata ottemperanza agli obblighi di trasparenza da parte
di [ENTE].

FATTI:
1. In data [DATA_FOIA] è stata inviata richiesta FOIA [ID] via [PEC/email]
2. Oggetto: [DESCRIZIONE]
3. A [N] giorni dalla richiesta, nessun riscontro
4. In data [DATA_RPCT] è stata inviata richiesta di riesame al RPCT
5. A [N] giorni dalla richiesta RPCT, nessun riscontro

VIOLAZIONI:
- Art. 5, comma 6 D.Lgs 33/2013: mancata risposta entro 30 giorni
- Art. 5, comma 7: mancato riesame da parte del RPCT
- (eventuale) Art. 7: mancata pubblicazione in formato aperto

Si chiede all'ANAC di:
1. Accertare le violazioni
2. Ordinare la pubblicazione dei dati ex art. 45, comma 2
3. Segnalare agli organi competenti per responsabilità dirigenziale

Allego:
- Copia richiesta FOIA
- Ricevuta invio FOIA
- Richiesta riesame RPCT
- Cronologia completa delle verifiche
```

**Invio**:

```
Destinatario: protocollo@pec.anac.it
Canale: SOLO PEC (ANAC non accetta email ordinaria per segnalazioni)
Oggetto: Segnalazione ex art. 45 D.Lgs 33/2013 — [ENTE] — FOIA [ID]
```

### Fase 4 — Dopo la segnalazione ANAC

L'ANAC, una volta ricevuta la segnalazione:

1. **Valuta** la sussistenza della violazione
2. **Ordina** la pubblicazione dei dati entro un termine (art. 45, c.2)
3. **Segnala** alle amministrazioni competenti per:
   - Responsabilità dirigenziale (art. 46)
   - Sanzioni disciplinari (art. 47)

Se l'ANAC **non risponde entro 60 giorni**, valuta:
- Sollecito via PEC
- Ricorso al TAR (silenzio-inadempimento)
- Pubblicazione del caso su canali pubblici

## Template evidenze per ANAC

La segnalazione ANAC deve includere **tutta la cronologia del caso**:

```markdown
## Cronologia caso FOIA [ID]

| Data | Evento | Evidenza |
|---|---|---|
| [DATA] | Invio FOIA | Ricevuta PEC allegata |
| [DATA+30] | Scaduta risposta 30gg | (nessuna risposta) |
| [DATA+50] | Richiesta riesame RPCT | Copia richiesta allegata |
| [DATA+70] | Segnalazione ANAC | Presente documento |

## Evidenze tecniche
[Da foia-evidence-collection: dataset, URL, formato, normativa]
```

## Registrazione escalation

Dopo ogni passo, aggiorna il FOIA registry:

```bash
# Il file foia_registry.json viene aggiornato automaticamente
# dal FoiaEngine quando si chiama transizione().
# Manualmente:
#   stato: escalation_rpct / escalation_anac
#   note: inviata richiesta riesame RPCT il [data]
```

## Controlli qualità pre-invio

Prima di inviare qualsiasi escalation:

- [ ] **Termini rispettati**: 30gg senza risposta → RPCT, 20gg RPCT → ANAC
- [ ] **Contatti verificati**: RPCT email presente in anagrafica? ANAC PEC valida?
- [ ] **Allegati completi**: FOIA originale, ricevuta invio, cronologia
- [ ] **PEC usata** per ANAC (non accetta email ordinaria)
- [ ] **Evidenze aggiornate**: data verifica non più vecchia di 7 giorni
- [ ] **Normativa citata corretta**: articolo + comma + decreto

## Riferimenti normativi

- Art. 5 D.Lgs 33/2013 — Accesso civico (c.6: risposta 30gg; c.7: riesame RPCT)
- Art. 7 D.Lgs 33/2013 — Obbligo formato di tipo aperto
- Art. 45 D.Lgs 33/2013 — Poteri ANAC (segnalazione, ordine pubblicazione)
- Art. 46 D.Lgs 33/2013 — Responsabilità dirigenziale
- Art. 47 D.Lgs 33/2013 — Sanzioni a carico del dirigente
- Art. 43 D.Lgs 33/2013 — Ruolo e funzioni RPCT
