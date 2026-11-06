#!/usr/bin/env python3
"""Rigenera/verifica obblighi/mapping_source_ipa.yaml.

Due cose separate, con volatilità diversa:

  1. la **decisione** (source_id -> codice_ipa, confidence, note) sta qui, versionata,
     volatilità zero  ->  `--check-contract` (offline, bloccante in CI)
  2. i **nomi** (denominazione, categoria) vengono da IPA  ->  `--refresh` / `--check-names`
     (rete, job schedulato)

Fonte di default dei nomi: il nostro clean su GCS (pubblico, nessuna credenziale).
Fallback: `--ipa-csv` (dump locale) o `--ipa-url` (dump ufficiale).

Uso:
    python obblighi/build_mapping.py --refresh        # riscrive lo YAML (GCS)
    python obblighi/build_mapping.py --check-contract # offline: decisione allineata?
    python obblighi/build_mapping.py --check-names    # rete: nomi allineati a IPA?
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "mapping_source_ipa.yaml"

# Clean pubblico del Lab (pipeline indice-pa). Nessuna credenziale.
GCS_URL = (
    "https://storage.googleapis.com/dataciviclab-clean/"
    "indice-pa/ipa_enti/2026/ipa_enti_2026_clean.parquet"
)
IPA_URL = "https://indicepa.gov.it/ipa-dati/datastore/dump/d09adf99-dc10-4349-8c53-27b1e5aa97b6?bom=True"
UA = "Mozilla/5.0 DataCivicLab/1.0"

# source_id -> (codice_ipa | None, confidence, nota)
# confidence: alta = match diretto | media = ente corretto ma ambiguo | nulla = non in IPA
MAPPING: dict[str, tuple[str | None, str, str]] = {
    "istat_sdmx": ("ISTAT", "alta", ""),
    "anac": ("cvtiap", "alta", ""),
    "inps": ("inps", "alta", "nome IPA: 'Istituto Nazionale Previdenza Sociale - INPS'"),
    "openbdap": ("m_ef", "media", "BDAP è MEF/RGS; la Ragioneria non è un ente IPA a sé"),
    "inail_opendata": ("inail", "alta", ""),
    "mim_opendata": ("m_pi", "alta", ""),
    "dati_camera": ("camera", "alta", ""),
    "dati_senato": ("sdr", "alta", ""),
    "dati_cultura": ("m_bac", "alta", ""),
    "ispra_linked_data": ("ispra_rm", "alta", ""),
    "consip_open_data": ("consips", "alta", "società in controllo pubblico (S01)"),
    "lavoro_opendata": ("m_lps", "alta", ""),
    "mur_ustat": ("KH5RHFCV", "alta", ""),
    "opencoesione": ("PCM", "alta", "Presidenza del Consiglio; dati del Dip. Politiche di Coesione"),
    "mef_irpef": ("m_ef", "alta", ""),
    "opencivitas": ("m_ef", "alta", "portale MEF/DF gestito da Sogei"),
    "aifa": ("aifa_rm", "alta", ""),
    "dait": ("m_it", "alta", ""),
    "eligendo": ("m_it", "alta", ""),
    "mit_opendata": ("m_inf", "alta", ""),
    "openga": ("cds", "media", "Consiglio di Stato / giustizia amministrativa (C2)"),
    "giustizia_statistiche": ("m_dg", "alta", ""),
    "cortecostituzionale": ("corte_cost", "alta", ""),
    "terna_opendata": (None, "nulla", "Terna S.p.A.: società privata quotata, non presente in IPA"),
    "ministero_interno": ("m_it", "alta", ""),
    "agid": ("agid", "alta", ""),
    "noipa_sparql": ("m_ef", "alta", "NoiPA è MEF"),
    "mimit_rna": ("m_svec", "alta", "IPA: 'MIMIT - Ministero delle Imprese e del Made in Italy'"),
    "ministero_turismo_opendata": ("WQF3ZW8F", "alta", ""),
    "ministero_salute": ("m_sa", "alta", ""),
    "agcm": ("agcm_", "alta", ""),
    "unioncamere": ("UICCIAA", "media", "Unione Italiana delle Camere di Commercio (nazionale); da confermare"),
    "pagopa": ("5N2TR557", "alta", "società in controllo pubblico (SAG)"),
    "art_opendata": ("art", "alta", ""),
    "aci": ("aci", "alta", ""),
    "adm_opendata": ("agdogane", "alta", ""),
}

HEADER = """# Mapping source_id (source-observatory) -> codice_ipa (indice-pa)
# T4a dell'audit obblighi informativi (2026-11-06).
#
# GENERATO da obblighi/build_mapping.py — non modificare a mano.
# Rigenerare:      python obblighi/build_mapping.py --refresh
# Check offline:   python obblighi/build_mapping.py --check-contract
# Check nomi:      python obblighi/build_mapping.py --check-names
#
# confidence:
#   alta  = match diretto per nome/categoria
#   media = ente corretto ma con ambiguita' (dipartimento, denominazione, societa')
#   nulla = nessun ente IPA corrispondente (es. societa' privata)
"""


def _rows_from_csv(raw: bytes) -> dict[str, dict]:
    out = {}
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        out[r["Codice_IPA"]] = {
            "denominazione": r["Denominazione_ente"],
            "categoria": r.get("Codice_Categoria", ""),
        }
    return out


def _rows_from_gcs(url: str) -> dict[str, dict]:
    import duckdb

    con = duckdb.connect()
    try:
        cur = con.execute(
            f"select codice_ipa, denominazione_ente, codice_categoria from read_parquet('{url}')"
        )
        return {
            c: {"denominazione": d, "categoria": cat or ""}
            for c, d, cat in cur.fetchall()
        }
    finally:
        con.close()


def load_ipa(args: argparse.Namespace) -> dict[str, dict]:
    if args.ipa_csv:
        return _rows_from_csv(Path(args.ipa_csv).read_bytes())
    if args.ipa_url:
        req = urllib.request.Request(args.ipa_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            return _rows_from_csv(r.read())
    return _rows_from_gcs(args.gcs_url)


def render(ipa: dict[str, dict]) -> str:
    lines = [HEADER.rstrip(), "", "mapping:"]
    for src, (code, conf, note) in MAPPING.items():
        lines.append(f"  {src}:")
        if code:
            d = ipa.get(code)
            if d is None:
                raise ValueError(f"{src}: codice_ipa {code!r} non presente nella fonte IPA")
            lines.append(f"    codice_ipa: {json.dumps(code)}")
            lines.append(f"    denominazione: {json.dumps(d['denominazione'], ensure_ascii=False)}")
            lines.append(f"    categoria: {json.dumps(d['categoria'], ensure_ascii=False)}")
        else:
            lines.append("    codice_ipa: null")
            lines.append("    denominazione: null")
            lines.append("    categoria: null")
        lines.append(f"    confidence: {conf}")
        if note:
            lines.append(f"    note: {json.dumps(note, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def _current() -> dict:
    import yaml

    return yaml.safe_load(OUT.read_text())["mapping"]


def check_contract() -> list[str]:
    """Offline: la tabella decisionale nel file corrisponde a MAPPING."""
    errors = []
    current = _current()
    for src, (code, conf, note) in MAPPING.items():
        c = current.get(src)
        if not c:
            errors.append(f"{src}: assente dal file")
            continue
        if c.get("codice_ipa") != code:
            errors.append(f"{src}: codice_ipa {c.get('codice_ipa')!r} != {code!r}")
        if c.get("confidence") != conf:
            errors.append(f"{src}: confidence {c.get('confidence')!r} != {conf!r}")
        if (c.get("note") or "") != note:
            errors.append(f"{src}: note diverge")
    extra = set(current) - set(MAPPING)
    for e in sorted(extra):
        errors.append(f"{e}: presente nel file ma non in MAPPING")
    if len(MAPPING) < 36:
        errors.append(f"attese >= 36 fonti, trovate {len(MAPPING)}")
    return errors


def check_names(args: argparse.Namespace) -> list[str]:
    """Con rete: denominazione/categoria corrispondono alla fonte IPA."""
    errors = []
    ipa = load_ipa(args)
    current = _current()
    for src, (code, _conf, _note) in MAPPING.items():
        if not code:
            continue
        exp = ipa.get(code)
        if exp is None:
            errors.append(f"{src}: {code} assente nella fonte IPA")
            continue
        cur = current.get(src, {})
        if cur.get("denominazione") != exp["denominazione"]:
            errors.append(f"{src}: denominazione divergente (IPA: {exp['denominazione']!r})")
        if cur.get("categoria") != exp["categoria"]:
            errors.append(f"{src}: categoria {cur.get('categoria')!r} != {exp['categoria']!r}")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description="Rigenera/verifica il mapping source_id -> codice_ipa")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="riscrive lo YAML dalla fonte IPA")
    mode.add_argument("--check-contract", action="store_true", help="offline: decisione allineata")
    mode.add_argument("--check-names", action="store_true", help="rete: nomi allineati a IPA")
    ap.add_argument("--gcs-url", default=GCS_URL, help="clean parquet su GCS (default: pubblico)")
    ap.add_argument("--ipa-csv", help="dump IPA locale")
    ap.add_argument("--ipa-url", help="dump IPA remoto (default: GCS)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    out = Path(args.out)

    if args.check_contract:
        errors = check_contract()
    elif args.check_names:
        errors = check_names(args)
    else:  # --refresh (default)
        out.write_text(render(load_ipa(args)))
        print(f"✅ scritto {out} ({len(MAPPING)} righe)")
        return

    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {out} allineato ({len(MAPPING)} righe)")


if __name__ == "__main__":
    main()
