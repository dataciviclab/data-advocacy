#!/usr/bin/env python3
"""Valida obblighi e applicazioni (T3).

- schema JSON per ogni voce;
- integrità referenziale: `application.obligation` esiste,
  `application.codice_ipa` coerente col mapping `source_id -> codice_ipa`;
- opzionale `--with-locator`: verifica l'ancora di ogni obbligo con legal-graph.

Uso:
    python obblighi/validate.py
    python obblighi/validate.py --with-locator
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import yaml

REPO = Path(__file__).resolve().parent.parent
OBBLIGHI = Path(__file__).resolve().parent / "obblighi.yaml"
APPLICAZIONI = Path(__file__).resolve().parent / "applicazioni.yaml"
MAPPING = Path(__file__).resolve().parent / "mapping_source_ipa.yaml"
SCHEMAS = Path(__file__).resolve().parent / "schemas"


def _load_yaml(path: Path) -> list:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{path}: atteso una lista")
    return data


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text())


def _locator():
    spec = importlib.util.spec_from_file_location(
        "locator", Path(__file__).resolve().parent / "locator.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate(with_locator: bool = False) -> list[str]:
    errors: list[str] = []

    obblighi = _load_yaml(OBBLIGHI)
    applicazioni = _load_yaml(APPLICAZIONI)
    mapping = yaml.safe_load(MAPPING.read_text())["mapping"]

    ob_schema = _schema("obligation.schema.json")
    ap_schema = _schema("application.schema.json")

    ob_ids = set()
    for ob in obblighi:
        try:
            jsonschema.validate(ob, ob_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"obbligo {ob.get('id')}: {e.message}")
            continue
        if ob["id"] in ob_ids:
            errors.append(f"obbligo duplicato: {ob['id']}")
        ob_ids.add(ob["id"])

    for ap in applicazioni:
        try:
            jsonschema.validate(ap, ap_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"applicazione {ap.get('id')}: {e.message}")
            continue
        if ap["obligation"] not in ob_ids:
            errors.append(f"{ap['id']}: obligation '{ap['obligation']}' inesistente")
        sid = ap.get("source_id")
        if sid:
            if sid not in mapping:
                errors.append(f"{ap['id']}: source_id '{sid}' non nel mapping")
            else:
                expected = mapping[sid]["codice_ipa"]
                if ap.get("codice_ipa") != expected:
                    errors.append(
                        f"{ap['id']}: codice_ipa '{ap.get('codice_ipa')}' != mapping '{expected}'"
                    )

    if with_locator:
        loc = _locator()
        for ob in obblighi:
            if not ob.get("testo_ancora"):
                continue
            r = loc.check_locator(ob["urn"], ob["articolo"], ob.get("comma", ""), ob["testo_ancora"])
            status = r["locator_status"]
            if status != ob["locator_status"]:
                errors.append(
                    f"obbligo {ob['id']}: locator {status} (atteso {ob['locator_status']})"
                    + (f" — {r.get('error')}" if r.get("error") else "")
                )

    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description="Valida obblighi e applicazioni")
    ap.add_argument("--with-locator", action="store_true", help="verifica le ancore con legal-graph")
    args = ap.parse_args()

    errors = validate(args.with_locator)
    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    print("✅ obblighi e applicazioni validi")


if __name__ == "__main__":
    main()
