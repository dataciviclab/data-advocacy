# data-advocacy

Richiediamo alle pubbliche amministrazioni i dati che già detengono, in un formato che si possa
usare. Una richiesta per volta: un dataset individuato, un difetto documentato, una PEC.

**Un esempio vero.** ANAS pubblica il traffico giornaliero medio annuo solo come PDF, un file per
anno dal 2013 al 2025. Il dato esiste, è aggiornato, ma per riusarlo bisogna trascriverlo a mano.
Abbiamo chiesto il CSV con una richiesta di accesso civico. Stessa impostazione con RFI, ASPI ed
ENAC: ognuna di queste amministrazioni pubblica un dataset in un formato che non si può elaborare.

Le richieste in corso e il loro esito: [`REGISTRO.md`](REGISTRO.md).

---

## Come partecipare

Quattro ruoli. Non serve farli tutti: il punto è che si possono **separare**.

| Ruolo | Cosa fa | Serve la PEC? |
|---|---|---|
| **Segnalatore** | trova il dataset e il difetto, apre la Issue con l'evidenza | no |
| **Richiedente** | invia la richiesta come persona fisica | sì |
| **Revisore** | controlla che l'evidenza sia datata e riproducibile prima dell'invio | no |
| **Manutentore** | merge, registro, coerenza del board | no |

I target già pronti e non ancora inviati sono in [`TARGETS.md`](TARGETS.md). Chi non ha una PEC
può comunque proporre un target, verificarlo e scrivere la richiesta: **un'altra persona la
invierà**.

Board operativo: [FOIA Layer 2](https://github.com/orgs/dataciviclab/projects/8).

---

## Cosa chiediamo — e cosa no

**Sì** — un dataset pubblicato male: dentro un PDF, dietro una dashboard, in XLSX, con una serie
storica ferma, o assente dal catalogo nazionale.

**No** — il catalogo completo del patrimonio informativo di un ente. La giurisprudenza lo
respinge come censimento non dovuto (Ad. Plen. CdS 10/2020): una richiesta puntuale ottiene
risposta, una richiesta enciclopedica no.

**No** — dati personali, atti riservati, documenti coperti da segreto.

Ogni difetto dichiarato deve avere tre cose: un **URL**, una **data di verifica**, un esito
**riproducibile**. Le regole complete sono in [`DISCLAIMER.md`](DISCLAIMER.md).

---

## Come funziona

| Entità | Dove vive | Chi la scrive |
|---|---|---|
| **Target** — dataset + evidenza del difetto | Issue GitHub (`foia-request.yml`) | chiunque |
| **Richiesta** — una PEC inviata | `richieste/<target>/<data>_<richiedente>.json` | `registro.py` |
| **Registro** — tabella pubblica | `REGISTRO.md` | `registro.py` (generato) |

Una sola fonte di verità: i file in `richieste/`. Il registro è **derivato**, mai editato a mano.
L'identità e la PEC del richiedente restano **locali** (`richiedente.json`, non versionato): nel
log pubblico compare solo un'etichetta anonima (`01`, `02`, …). Più persone possono inviare verso
lo stesso target, ognuna con il proprio file, senza conflitti.

Forma del record, stati e regole di escalation: [`docs/modello-dati.md`](docs/modello-dati.md).

---

## Strumenti

| File | Cosa fa |
|---|---|
| `registro.py` | registro delle richieste: record, scadenze, tabella pubblica |
| `bozza.py` | genera la bozza `.eml` (testo + HTML + allegati) da una nota-richiesta |
| `portal_scan.py` | confronta il portale diretto di un ente col catalogo nazionale |
| `obblighi/` | obblighi informativi ancorati al testo di legge (norma → ente → evidenza) |
| `foia.py` | campagna 2026 archiviata (Layer 1) |

Setup, comandi e dettagli: [`docs/strumenti.md`](docs/strumenti.md).

---

## Storia

Nel 2026 il progetto ha tentato la strada opposta: chiedere il **catalogo completo** del
patrimonio informativo a 29 enti. Il 83% ha risposto, il 21% ha consegnato. La lezione è che il
censimento non regge: da lì è nato il modello a richiesta singola che usiamo oggi. Il tooling
storico resta in `foia.py` e `data/archivio/`.

---

## Documenti

- [Come contribuire](CONTRIBUTING.md)
- [Codice di condotta](CODE_OF_CONDUCT.md)
- [Cosa pubblichiamo e diritto di replica](DISCLAIMER.md)
- [Target pronti da inviare](TARGETS.md)
- [Modello dati](docs/modello-dati.md) · [Strumenti](docs/strumenti.md)

## Licenza

MIT — Copyright (c) 2026 DataCivicLab
