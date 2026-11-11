# Strumenti e comandi

## Setup

```bash
cp richiedente.example.json richiedente.json   # nome e PEC: resta locale, mai committato
```

Python 3.12+.

- **Runtime** (`registro.py`, `bozza.py`, `portal_scan.py`): solo standard library.
- **Strumenti `obblighi/`**: richiedono `jsonschema` e `pyyaml` (`duckdb` per i comandi con rete).

```bash
pip install -e ".[obblighi]"
# oppure: pip install jsonschema pyyaml duckdb
```

---

## `registro.py` — il registro delle richieste

```bash
python registro.py nuova <target> [--issue N] [--data AAAA-MM-GG] [--richiedente 01] [--norma ID]
python registro.py risposta <target>/<file> --esito ok|parziale|rifiutata|ignorata \
    [--tipo ...] [--verificato-il AAAA-MM-GG] [--data-risposta AAAA-MM-GG] [--protocollo ...]
python registro.py verifica <target>/<file> [--tipo ...] [--verificato-il AAAA-MM-GG]
python registro.py escalation <target>/<file> rpct|anac
python registro.py nota <target>/<file> "testo" [--append]
python registro.py norma <target>/<file> --norma <id> [--norma <id> ...]
python registro.py lista          # tutte le richieste
python registro.py mio 01         # solo quelle di un richiedente
python registro.py scadenze       # oltre i 30 giorni senza esito
python registro.py build          # rigenera REGISTRO.md
```

Il ciclo completo:

```
segnala il difetto
  → apri Issue (target)                                        [GitHub]
  → scrivi la nota-richiesta (vedi skills/target-selection.md)
  → python bozza.py <nota.md>                                  [genera il .eml]
  → invia la PEC dal client                                    [ricevute PEC]
  → python registro.py nuova <target> --issue N --norma <id>
  → commenta la Issue (data di consegna, scadenza, norme, path del record)
  → risposta        → registro.py risposta ... --esito ... --tipo ...
  → verifica sul dato → registro.py verifica ... --verificato-il AAAA-MM-GG
  → silenzio/rigetto → registro.py escalation ... rpct
  → registro.py build                                          [aggiorna REGISTRO.md]
```

---

## `bozza.py` — dalla nota alla PEC

Legge una nota markdown con un blocco di metadati e un corpo delimitato, e produce un file
`.eml` pronto da aprire nel client di posta.

```markdown
<!-- PEC
TO=protocollo@pec.ente.gov.it
SUBJECT=Richiesta di accesso civico generalizzato ...
FILE=ente_target
-->

<!-- PEC:BODY -->
Al Responsabile ...
<!-- /PEC:BODY -->
```

I placeholder (`[NOME COGNOME]`, `[DATA]`) sono compilati da `richiedente.json`; `[DATA]` è la
data odierna.

```bash
python bozza.py <nota.md>            # tutte le richieste della nota
python bozza.py <nota.md> --id m1    # una sola
```

Le bozze finiscono in `bozze/`, che è in `.gitignore`.

---

## `portal_scan.py` — portale diretto vs catalogo nazionale

Elenca i dataset di un portale dal suo sitemap e li confronta con `dati.gov.it`, che è un harvest
spesso parziale e non aggiornato. Il portale diretto è la fonte di verità su cosa un ente pubblica
davvero.

```bash
python portal_scan.py <sitemap-index> --catalog <org-dati.gov.it>
python portal_scan.py <sitemap-index> --match <tema>
```

Il sitemap si trova in `robots.txt` (`Sitemap:`).

---

## `obblighi/` — il livello semantico

```bash
python obblighi/validate.py                          # schema + chiavi esterne
python obblighi/validate.py --with-locator           # verifica le ancore nel testo di legge
python obblighi/build_mapping.py --check-contract    # contratto del mapping (offline, in CI)
python obblighi/build_mapping.py --check-names       # nomi IPA (richiede rete)
```

Il gate sulle PR è **offline e deterministico**: i controlli con rete girano in un workflow
separato e, se falliscono, aprono una issue di manutenzione invece di bloccare la PR.

> Nota: `--with-locator` e `--refresh` usano infrastruttura del Laboratorio (`legal-graph`, il
> clean IPA su storage interno). Il codice è leggibile e la procedura è riproducibile, ma fuori
> dal Lab quei comandi non girano. Vedi [`../obblighi/README.md`](../obblighi/README.md).
