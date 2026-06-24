#!/usr/bin/env python3
"""
Genera bozze FOIA precompilate a partire da open_data_health_scores.json e anagrafica enti.

Legge open_data_health_scores.json (prodotto da source-observatory), abbina ogni
fonte critica all'ente corrispondente in anagrafica, seleziona il template
appropriato, e produce un file .txt con la bozza pronta per invio.

Utilizzo:
    python scripts/generate_foia_draft.py
    python scripts/generate_foia_draft.py --source mit_opendata
    python scripts/generate_foia_draft.py --all-critical --out-dir bozze/
    python scripts/generate_foia_draft.py --all
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Path
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ANAGRAFICA = REPO_ROOT / "data" / "anagrafica_enti.json"
_SO_DATA_DIR = Path(os.environ.get("SO_DATA_DIR", REPO_ROOT.parent / "source-observatory" / "data"))
DEFAULT_HEALTH_SCORES = _SO_DATA_DIR / "health" / "open_data_health_scores.json"
DEFAULT_TEMPLATES = REPO_ROOT / "data_advocacy" / "templates"
DEFAULT_OUT = REPO_ROOT / "bozze"

# Template per scenario
# Nota: "anac" e' elencato ma NON selezionato da _scegli_template() —
# la segnalazione ANAC va generata manualmente dopo escalation FOIA,
# perche' richiede dati post-FOIA (data_foia, foia_id, data_rpct)
# che il generatore non possiede.
TEMPLATE_MAP = {
    "formato_chiuso": "foia_formato_chiuso.j2",
    "standard": "foia_standard.j2",
    "dcd": "dcd_segnalazione.j2",
    "anac": "anac_segnalazione.j2",
}


MESI_ITALIANI = [
    "", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


def _data_italiana(d: date) -> str:
    return f"{d.day} {MESI_ITALIANI[d.month]} {d.year}"


def _carica_json(path: Path) -> dict | list:
    if not path.exists():
        print(f"⚠️  File non trovato: {path}")
        return {} if path.suffix == ".json" and not str(path).endswith("s.json") else []
    return json.loads(path.read_text(encoding="utf-8"))


def _carica_anagrafica(path: Path) -> dict:
    """Carica anagrafica e costruisce indice per source_id."""
    raw = _carica_json(path)
    if isinstance(raw, list):
        return {e["source_id"]: e for e in raw if "source_id" in e}
    return {}


def _scegli_template(score_entry: dict) -> str:
    """Sceglie il template in base agli assi dello score."""
    assi = score_entry.get("assi", {})
    formato = assi.get("formato_aperto", {}).get("score", 100)
    hvd = assi.get("hvd_compliance", {}).get("score", 100)
    hvd_fonte = assi.get("hvd_compliance", {}).get("fonte", "missing")

    if formato < 50:
        return TEMPLATE_MAP["formato_chiuso"]
    if hvd < 50 and hvd_fonte != "missing":
        return TEMPLATE_MAP["dcd"]
    return TEMPLATE_MAP["standard"]


def _violazioni_da_score(score_entry: dict) -> list[dict]:
    """Costruisce lista violazioni dallo score."""
    assi = score_entry.get("assi", {})
    violazioni = []

    mapping = {
        "formato_aperto": ("Formato chiuso", "Art. 7 D.Lgs 33/2013 + Art. 1(l-bis) CAD"),
        "raggiungibilita": ("Fonte non raggiungibile", "Art. 6 D.Lgs 33/2013"),
        "licenza_aperta": ("Licenza assente o non aperta", "Art. 1(l-ter) CAD"),
        "presenza_datigovit": ("Non presente su dati.gov.it", "Art. 52 CAD — open data by default"),
        "hvd_compliance": ("Violazione obblighi HVD", "Reg. UE 2023/138 + Art. 12-bis D.Lgs 36/2006"),
        "accessibilita_foia": ("Contatti FOIA non reperibili", "Art. 5 D.Lgs 33/2013"),
    }

    for asse_key, (problema, norma) in mapping.items():
        info = assi.get(asse_key, {})
        score = info.get("score", 100)
        fonte = info.get("fonte", "estimated")
        # Solo assi "computed" (evidenza certa) diventano violazioni.
        # "estimated" significa "non lo sappiamo" — non va in un FOIA.
        if score < 60 and fonte == "computed":
            violazioni.append({
                "problema": problema,
                "evidenza": f"Score: {score}/100 (dato verificato)",
                "norma": norma,
            })

    return violazioni


def _formato_da_protocollo(protocol: str) -> str:
    """Rappresentazione leggibile del formato."""
    mappa = {
        "ckan": "CKAN (formato variabile)",
        "html": "HTML (formato non determinabile)",
        "sdmx": "SDMX-ML",
        "sparql": "SPARQL/RDF",
        "aem": "API AEM",
        "rest": "API REST",
    }
    return mappa.get(protocol, protocol)


def genera_bozza(
    source_id: str,
    score_entry: dict,
    ente: dict | None,
    template_env: Environment,
    mittente_nome: str,
    mittente_email: str,
) -> str | None:
    """Genera bozza FOIA per una fonte. Restituisce il testo o None."""

    # Seleziona template
    template_name = _scegli_template(score_entry)
    template = template_env.get_template(template_name)

    assi = score_entry.get("assi", {})

    # Prepara contesto
    ctx = {
        "mittente_nome": mittente_nome,
        "mittente_email": mittente_email,
        "data": _data_italiana(date.today()),
        "ente_nome": ente["nome"] if ente else source_id,
        "dataset_nome": f"Dataset associati alla fonte {source_id}",
        "dataset_url": ente.get("sito", "") if ente else "",
        "trigger_detail": f"Fonte: {source_id}. Score compliance: {score_entry.get('totale')}/100 ({score_entry.get('livello')}). Azione raccomandata: {score_entry.get('azione_raccomandata')}",
        "violazioni": _violazioni_da_score(score_entry),
        "formato_attuale": _formato_da_protocollo(score_entry.get("protocol", "")),
        "formato_chiuso": True,
        "hvd": assi.get("hvd_compliance", {}).get("fonte", "missing") != "missing",
        "hvd_categoria": "Mobility",
        "raggiungibilita": assi.get("raggiungibilita", {}).get("score", 100),
        "anni_mancanti": "anni precedenti",
    }

    # Se abbiamo un'entrata con contatti PEC, includili
    if ente:
        contatti = ente.get("contatti", {})
        if contatti.get("pec"):
            ctx["ente_pec"] = contatti["pec"]
        if contatti.get("urp_email"):
            ctx["ente_urp"] = contatti["urp_email"]

    return template.render(**ctx)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera bozze FOIA precompilate")
    parser.add_argument(
        "--health-scores",
        default=DEFAULT_HEALTH_SCORES,
        type=Path,
        help="Path a open_data_health_scores.json",
    )
    parser.add_argument(
        "--anagrafica",
        default=DEFAULT_ANAGRAFICA,
        type=Path,
        help="Path a anagrafica_enti.json",
    )
    parser.add_argument(
        "--templates",
        default=DEFAULT_TEMPLATES,
        type=Path,
        help="Directory template Jinja2",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT,
        type=Path,
        help="Directory output bozze",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Genera solo per un source_id specifico",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Genera per tutte le fonti in anagrafica",
    )
    parser.add_argument(
        "--all-critical",
        action="store_true",
        help="Genera solo per fonti con livello critico/grave",
    )
    parser.add_argument(
        "--mittente-nome",
        default="REDACTED",
        help="Nome del richiedente",
    )
    parser.add_argument(
        "--mittente-email",
        default="dataciviclab@gmail.com",
        help="Email del richiedente",
    )
    args = parser.parse_args()

    # Carica dati
    scores_data = _carica_json(args.health_scores)
    anagrafica = _carica_anagrafica(args.anagrafica)

    if isinstance(scores_data, dict):
        scores_list = scores_data.get("scores", [])
    else:
        scores_list = scores_data

    # Template engine
    if not args.templates.exists():
        print(f"❌ Directory template non trovata: {args.templates}")
        return
    env = Environment(
        loader=FileSystemLoader(str(args.templates)),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Filtra
    targets = []
    if args.source:
        targets = [s for s in scores_list if s.get("source_id") == args.source]
        if not targets:
            print(f"⚠️  source_id '{args.source}' non trovato in health scores")
            # Prova a generare anche senza health score
            if args.source in anagrafica:
                targets = [{"source_id": args.source, "totale": 0, "livello": "sconosciuto", "azione_raccomandata": "verifica", "assi": {}, "protocol": "unknown"}]
    elif args.all:
        targets = scores_list
    elif args.all_critical:
        targets = [
            s for s in scores_list
            if s.get("livello") in ("debole", "carente")
        ]
    else:
        # Default: solo deboli/carenti
        targets = [
            s for s in scores_list
            if s.get("livello") in ("debole", "carente")
        ]

    if not targets:
        print("Nessun target da processare.")
        return

    # Genera
    args.out_dir.mkdir(parents=True, exist_ok=True)
    generati = 0
    for entry in targets:
        sid = entry.get("source_id", "unknown")
        ente = anagrafica.get(sid)

        testo = genera_bozza(
            source_id=sid,
            score_entry=entry,
            ente=ente,
            template_env=env,
            mittente_nome=args.mittente_nome,
            mittente_email=args.mittente_email,
        )

        if testo:
            livello = entry.get("livello", "sconosciuto")
            filename = f"FOIA-{sid}_{livello}.txt"
            out_path = args.out_dir / filename
            out_path.write_text(testo, encoding="utf-8")
            print(f"✅ {filename} ({entry.get('totale', '?')}/100)")
            generati += 1
        else:
            print(f"⚠️  {sid}: generazione saltata (nessun template匹配)")

    print(f"\nBozze generate: {generati} in {args.out_dir}")


if __name__ == "__main__":
    main()
