"""Locatore normativo (T2): verifica che un obbligo sia ancorato al testo di legge.

Un obbligo informativo è tipicamente `art. 37, co. 1, D.Lgs. 33/2013`. Il grafo
`legal-graph` non ha nodi sotto l'articolo, quindi l'obbligo non può essere una FK:
porta un *locatore* verificabile.

    urn            -> FK a legal-graph (esiste / non esiste)
    articolo       -> stringa ("37", "82-bis")
    comma          -> stringa ("1")
    testo_ancora   -> frammento del comma, normalizzato
    locator_status -> verified | broken | untested

Il check: `legal_text(urn, articolo)` deve contenere `testo_ancora`.
Se non lo contiene, l'obbligo è **non verificabile** e non produce richieste.

Uso:
    python -m obblighi.locator <urn> <articolo> "<testo_ancora>"
"""

from __future__ import annotations

import re
import sys
import unicodedata

FIELDS = ("urn", "articolo", "comma", "testo_ancora", "locator_status")


def normalize(text: str) -> str:
    """Normalizza per il confronto: link markdown, ((...)), accenti, spazi."""
    t = text or ""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)  # [testo](url) -> testo
    t = t.replace("((", "").replace("))", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def check_locator(
    urn: str,
    articolo: int | str,
    comma: str = "",
    testo_ancora: str = "",
) -> dict:
    """Verifica un locatore contro il testo di legal-graph (offline)."""
    base = {
        "urn": urn,
        "articolo": str(articolo),
        "comma": str(comma),
        "testo_ancora": testo_ancora,
    }

    if not testo_ancora.strip():
        return {**base, "locator_status": "untested", "error": "testo_ancora vuoto"}

    try:
        from legal_graph.mcp.reports import _impl_legal_text
    except ImportError as e:  # repo standalone: legal-graph non disponibile
        return {**base, "locator_status": "untested", "error": f"legal_graph non disponibile: {e}"}

    res = _impl_legal_text(urn, articolo=articolo)
    if "error" in res:
        return {**base, "locator_status": "broken", "error": res["error"]}

    text = res.get("text") or ""
    found = normalize(testo_ancora) in normalize(text)
    return {
        **base,
        "locator_status": "verified" if found else "broken",
        "anchor_found": found,
        "text_len": len(text),
        "vigenza": res.get("stato") or res.get("vigenza_fonte") or "",
    }


def main() -> None:
    if len(sys.argv) < 4:
        print('Uso: python -m obblighi.locator <urn> <articolo> "<testo_ancora>"', file=sys.stderr)
        sys.exit(1)
    urn, articolo, ancora = sys.argv[1], sys.argv[2], sys.argv[3]
    comma = sys.argv[4] if len(sys.argv) > 4 else ""
    r = check_locator(urn, articolo, comma, ancora)
    print(r["locator_status"].upper(), "·", r.get("error", ""))
    for k in ("urn", "articolo", "comma", "text_len", "vigenza"):
        if k in r:
            print(f"  {k}: {r[k]}")


if __name__ == "__main__":
    main()
