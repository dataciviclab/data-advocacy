#!/usr/bin/env python3
"""bozza.py — genera bozze .eml pronte da aprire/inviare nel client PEC.

Legge una nota-richiesta in markdown e produce un .eml per ogni blocco PEC.
Una nota può contenere più richieste (una per blocco, con id).

Metadati (uno per richiesta; l'id è opzionale):

    <!-- PEC m1
    TO=m_inf@pec.mit.gov.it
    SUBJECT=Richiesta di accesso civico generalizzato ...
    ATTACH=2026-11-05_allegato_GTFS_NAP.md
    FILE=mit_gtfs_nap
    -->

    ... testo della nota ...

    <!-- PEC:BODY m1 -->
    Al Ministero ...
    <!-- /PEC:BODY m1 -->

I percorsi in ATTACH sono relativi alla cartella della nota.
`FILE` (opzionale) fissa il nome del .eml; altrimenti si usa `<nota>__<id>.eml`.

Uso:
    python bozza.py <nota.md>              # tutte le richieste della nota
    python bozza.py <nota.md> --id m1      # una sola
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

REPO = Path(__file__).resolve().parent
RICHIEDENTE = REPO / "richiedente.json"
BOZZE = REPO / "bozze"

_META_RE = re.compile(r"<!--\s*PEC(\s+[A-Za-z0-9_-]+)?\s*\n(.*?)-->", re.S)
_BODY_RE = re.compile(
    r"<!--\s*PEC:BODY(\s+[A-Za-z0-9_-]+)?\s*-->(.*?)<!--\s*/PEC:BODY(\s+[A-Za-z0-9_-]+)?\s*-->",
    re.S,
)


def _richiedente() -> tuple[str, str]:
    nome, pec = "NOME COGNOME", "PEC"
    if RICHIEDENTE.exists():
        d = json.loads(RICHIEDENTE.read_text())
        nome, pec = d.get("nome", nome), d.get("pec", pec)
    return nome, pec


def _blocks(nota: str) -> dict[str, dict]:
    """Estrae i blocchi PEC: id -> {TO, SUBJECT, ATTACH[], FILE, body}."""
    out: dict[str, dict] = {}
    for m in _META_RE.finditer(nota):
        bid = (m.group(1) or "").strip() or "default"
        meta: dict = {"ATTACH": []}
        for line in m.group(2).splitlines():
            line = line.strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip().upper(), v.strip()
            if k == "ATTACH":
                meta["ATTACH"].append(v)
            else:
                meta[k] = v
        out.setdefault(bid, {}).update(meta)
    for m in _BODY_RE.finditer(nota):
        bid = (m.group(1) or "").strip() or "default"
        out.setdefault(bid, {})["body"] = m.group(2).strip()
    return out


def _plain(md: str) -> str:
    out = []
    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("#"):
            s = s.lstrip("# ").upper()
        out.append(s.replace("**", ""))
    return "\n".join(out).strip() + "\n"


def _html(md: str) -> str:
    parts = ["<html><body>"]
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        parts.append(f"<h3>{s.lstrip('# ')}</h3>" if line.startswith("#") else f"<p>{s}</p>")
    parts.append("</body></html>")
    return "\n".join(parts)


def build(nota_path: Path, only: str | None = None) -> list[Path]:
    blocks = _blocks(nota_path.read_text())
    nome, pec = _richiedente()
    made: list[Path] = []

    for bid, meta in blocks.items():
        if only and bid != only:
            continue
        to, subject, body = meta.get("TO"), meta.get("SUBJECT"), meta.get("body")
        if not (to and subject and body):
            raise ValueError(f"Blocco '{bid}' incompleto (TO/SUBJECT/BODY)")

        msg = EmailMessage()
        msg["From"] = f"{nome} <{pec}>"
        msg["To"] = to
        if meta.get("CC"):
            msg["Cc"] = meta["CC"]
        msg["Subject"] = subject
        msg["Date"] = datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M:%S %z")
        msg.set_content(_plain(body))
        msg.add_alternative(_html(body), subtype="html")

        for rel in meta["ATTACH"]:
            p = Path(rel)
            if not p.is_absolute():
                p = nota_path.parent / rel
            if not p.exists():
                raise FileNotFoundError(f"Allegato non trovato: {p}")
            msg.add_attachment(
                p.read_bytes(), maintype="application", subtype="octet-stream", filename=p.name
            )

        name = meta.get("FILE") or (
            nota_path.stem if bid == "default" else f"{nota_path.stem}__{bid}"
        )
        out = BOZZE / f"{name}.eml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(msg.as_bytes())
        made.append(out)

    if not made:
        raise ValueError("Nessun blocco PEC trovato nella nota")
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera bozze .eml da una nota-richiesta")
    ap.add_argument("nota", help="file markdown della richiesta (con blocchi PEC)")
    ap.add_argument("--id", help="genera solo il blocco con questo id")
    args = ap.parse_args()

    for out in build(Path(args.nota), args.id):
        print(f"✅ Bozza: {out}")


if __name__ == "__main__":
    main()
