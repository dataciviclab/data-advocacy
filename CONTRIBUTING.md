# Contribuire a data-advocacy

## Cosa sta in questo repo

- `foia.py` — script unico per campagna FOIA (verifica, diagnosi, invio, tracking)
- `enti/enti.json` — anagrafica enti pubblici e partecipate con PEC
- `data/tracker.json` — richieste FOIA inviate
- `skills/` — procedure operative

## Cosa NON sta in questo repo

- **Monitoraggio fonti** → `source-observatory`
- **Pipeline dati** → `toolkit`
- **Analisi SQL** → `dataciviclab/analisi/`

## PR template

Usa `.github/PULL_REQUEST_TEMPLATE.md`. Ogni PR deve:
- `python foia.py --report` passare senza errori
- Includere test per nuova logica (se applicabile)

## Riferimenti

- [DataCivicLab .github](https://github.com/dataciviclab/.github)
- [Source Observatory](https://github.com/dataciviclab/source-observatory)
