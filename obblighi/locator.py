"""Locatore normativo (T2): verifica che un obbligo sia ancorato al testo di legge.

Un obbligo informativo è tipicamente `art. 37, co. 1, D.Lgs. 33/2013`. Il grafo
`legal-graph` non ha nodi sotto l'articolo, quindi l'obbligo non può essere una FK:
porta un *locatore* verificabile.

    urn            -> FK a legal-graph (esiste / non esiste)
    articolo       -> stringa ("37", "82-bis")
    comma          -> stringa ("1")
    testo_ancora   -> frammento del comma, normalizzato
    locator_status -> verified | broken | untested

Il check: `legal_text(urn, articolo)` deve contenere `testo_ancora` **dentro il comma**.
Se `comma` è valorizzato ma non individuabile, lo stato è `untested` (non si può verificare).
Un errore di infrastruttura (rete, mart mancante) è `untested`, non `broken`: un disservizio
non deve silenziare obblighi validi.

Uso:
    python obblighi/locator.py <urn> <articolo> "<testo_ancora>" [comma]
"""

from __future__ import annotations

import re
import sys
import unicodedata


def normalize(text: str) -> str:
    """Normalizza per il confronto: link markdown, ((...)), accenti, spazi."""
    t = text or ""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)  # [testo](url) -> testo
    t = t.replace("((", "").replace("))", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def extract_comma(article_text: str, comma: str) -> str | None:
    """Estrae il blocco del comma dal markdown AKN (riga 'N.' -> prossimo 'M.')."""
    num = str(comma).strip()
    if not num:
        return article_text
    m = re.search(rf"(?m)^\s*{re.escape(num)}\.\s*$", article_text)
    if not m:
        return None
    rest = article_text[m.end():]
    nxt = re.search(r"(?m)^\s*\d+\.\s*$", rest)
    return rest[: nxt.start()] if nxt else rest


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

    try:
        res = _impl_legal_text(urn, articolo=articolo)
    except Exception as e:  # rete/mart/parse: infrastruttura, non obbligo
        return {**base, "locator_status": "untested", "error": f"errore infrastruttura: {e}"}

    if "error" in res:
        msg = str(res["error"])
        # nodo inesistente o id ambiguo = l'obbligo punta al nulla
        if "Nodo non trovato" in msg or "ambiguo" in msg:
            return {**base, "locator_status": "broken", "error": msg}
        return {**base, "locator_status": "untested", "error": msg}

    text = res.get("text") or ""
    if comma:
        scope = extract_comma(text, comma)
        if scope is None:
            return {
                **base,
                "locator_status": "untested",
                "error": f"comma {comma} non individuato nell'articolo {articolo}",
            }
        text = scope

    found = normalize(testo_ancora) in normalize(text)
    return {
        **base,
        "locator_status": "verified" if found else "broken",
        "anchor_found": found,
        "text_len": len(text),
    }


def main() -> None:
    if len(sys.argv) < 4:
        print('Uso: python obblighi/locator.py <urn> <articolo> "<testo_ancora>" [comma]',
              file=sys.stderr)
        sys.exit(1)
    urn, articolo, ancora = sys.argv[1], sys.argv[2], sys.argv[3]
    comma = sys.argv[4] if len(sys.argv) > 4 else ""
    r = check_locator(urn, articolo, comma, ancora)
    print(r["locator_status"].upper(), "·", r.get("error", ""))
    for k in ("urn", "articolo", "comma", "text_len"):
        if k in r:
            print(f"  {k}: {r[k]}")


if __name__ == "__main__":
    main()
