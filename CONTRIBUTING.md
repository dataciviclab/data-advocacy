# Contribuire a data-advocacy

## Cosa sta in questo repo

- Compliance scoring delle fonti pubbliche
- FOIA engine (macchina a stati, template, invio, tracciamento)
- Anagrafica enti pubblici (contatti URP, PEC, RPCT)
- Segnalazioni DCD/ANAC
- Skill operative per campagne FOIA

## Cosa NON sta in questo repo

- **Monitoraggio fonti** → `source-observatory`
- **Pipeline dati** → `toolkit`
- **Analisi SQL** → `dataciviclab/analisi/`

## Issue template

Usa i template issue per:

- **FOIA Request** — nuova richiesta FOIA da preparare/inviare
- **Compliance Report** — segnalazione su fonte con compliance score basso

## PR template

Usa `.github/PULL_REQUEST_TEMPLATE.md`. I PR devono:
- Passare `ruff check .`
- Passare `mypy data_advocacy/`
- Passare `pytest tests/`
- Includere test per nuova logica

## Riferimenti

- [DataCivicLab .github](https://github.com/dataciviclab/.github)
- [Source Observatory](https://github.com/dataciviclab/source-observatory)
