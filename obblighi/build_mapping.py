#!/usr/bin/env python3
"""Rigenera obblighi/mapping_source_ipa.yaml dal dump IPA.

Riproducibile da terzi:
  - la **scelta** del mapping (source_id -> codice_ipa, confidence) è qui, versionata;
  - i **nomi** (denominazione/categoria) vengono dal dump IPA ufficiale, scaricato
    all'esecuzione (o passato con --ipa-csv).

Uso:
    python obblighi/build_mapping.py                  # scarica IPA e scrive lo YAML
    python obblighi/build_mapping.py --ipa-csv f.csv   # usa un dump locale
    python obblighi/build_mapping.py --check           # verifica che lo YAML sia aggiornato
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
OUT = REPO / "obblighi" / "mapping_source_ipa.yaml"
IPA_URL = "https://indicepa.gov.it/ipa-dati/datastore/dump/d09adf99-dc10-4349-8c53-27b1e5aa97b6?bom=True"
UA = "Mozilla/5.0 (X11; Linux x86_64) DataCivicLab/1.0"

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
# Rigenerare:  python obblighi/build_mapping.py
# Verificare:  python obblighi/build_mapping.py --check
#
# confidence:
#   alta  = match diretto per nome/categoria
#   media = ente corretto ma con ambiguita' (dipartimento, denominazione, societa')
#   nulla = nessun ente IPA corrispondente (es. societa' privata)
"""


def load_ipa(src: str | None) -> dict[str, dict]:
    if src:
        raw = Path(src).read_bytes()
    else:
        req = urllib.request.Request(IPA_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            raw = r.read()
    rows = {}
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        rows[r["Codice_IPA"]] = {
            "denominazione": r["Denominazione_ente"],
            "categoria": r.get("Codice_Categoria", ""),
        }
    if not rows:
        raise ValueError("dump IPA vuoto o illeggibile")
    return rows


def render(ipa: dict[str, dict]) -> str:
    lines = [HEADER.rstrip(), "", "mapping:"]
    for src, (code, conf, note) in MAPPING.items():
        lines.append(f"  {src}:")
        if code:
            d = ipa.get(code)
            if d is None:
                raise ValueError(f"{src}: codice_ipa {code!r} non presente nel dump IPA")
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Rigenera il mapping source_id -> codice_ipa")
    ap.add_argument("--ipa-csv", help="dump IPA locale (default: scarica dall'URL ufficiale)")
    ap.add_argument("--out", default=str(OUT), help="file di output")
    ap.add_argument("--check", action="store_true", help="verifica che il file sia aggiornato")
    args = ap.parse_args()

    out = Path(args.out)
    generated = render(load_ipa(args.ipa_csv))

    if args.check:
        current = out.read_text() if out.exists() else ""
        if current != generated:
            print(f"❌ {out} non è aggiornato. Rigenera con: python obblighi/build_mapping.py", file=sys.stderr)
            sys.exit(1)
        print(f"✅ {out} aggiornato ({len(MAPPING)} righe)")
        return

    out.write_text(generated)
    print(f"✅ scritto {out} ({len(MAPPING)} righe)")


if __name__ == "__main__":
    main()
