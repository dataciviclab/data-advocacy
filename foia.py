#!/usr/bin/env python3
"""
Campagna FOIA quotidiana — invio, tracking, escalation DCD/ANAC.

Uso:
  python foia.py --next              # Prossimo ente + genera bozza
  python foia.py --send ID           # Segna richiesta come inviata
  python foia.py --respond ID --status ok|parziale|rifiutata|ignorata
  python foia.py --status            # Tabella riepilogativa
  python foia.py --scadenze          # Chi è in ritardo
  python foia.py --dcd ID            # Bozza DCD (AgID) per formato chiuso
  python foia.py --anac ID           # Bozza ANAC per mancata risposta

Dati:
  enti/enti.json        Anagrafica enti con PEC
  data/tracker.json     Stato richieste
  template.txt          Template richiesta FOIA
  bozze/                Bozze generate (non in git)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent
ENTI = REPO / "enti" / "enti.json"
TRACKER = REPO / "data" / "tracker.json"
TEMPLATE = REPO / "template.txt"
BOZZE = REPO / "bozze"

# ── Ciclo FOIA (30gg risposta, 50gg RPCT) ──────────────────────────────
TERMINE_RISPOSTA = 30
TERMINE_RPCT = 50

# ── Caricamento dati ────────────────────────────────────────────────────


def _carica_json(path: Path) -> list | dict:
    if not path.exists():
        print(f"❌ File non trovato: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def _salva_json(path: Path, data: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _recalc_stats(richieste: list[dict]) -> dict:
    return {
        "totale": len(richieste),
        "inviate": sum(1 for r in richieste if r["status"] != "pending"),
        "risposte": sum(1 for r in richieste if r["status"]
                       in ("ok", "parziale", "rifiutata", "ignorata")),
        "escalated": sum(1 for r in richieste if r.get("escalation_anac")),
        "aggiornato": datetime.now().isoformat(),
    }


def carica_enti() -> list[dict]:
    return _carica_json(ENTI)  # type: ignore


def carica_tracker() -> list[dict]:
    if TRACKER.exists():
        raw = _carica_json(TRACKER)
        if isinstance(raw, dict):
            return raw.get("richieste", [])
        return raw  # backward compat: lista semplice
    return []


def salva_tracker(richieste: list[dict]) -> None:
    stats = _recalc_stats(richieste)
    _salva_json(TRACKER, {"richieste": richieste, "_stats": stats})


# ── Anagrafica ──────────────────────────────────────────────────────────


def ente_per_id(enti: list[dict], ente_id: str) -> dict | None:
    for e in enti:
        if e["id"] == ente_id:
            return e
    return None


def prossimo_inviabile(enti: list[dict], tracker: list[dict]) -> dict | None:
    """Il primo ente non ancora inviato (dalla lista ordinata)."""
    inviati = {r["id"] for r in tracker if r["status"] != "pending"}
    for e in enti:
        if e["id"] not in inviati:
            return e
    return None


# ── Template ────────────────────────────────────────────────────────────


def _template_testo() -> str:
    """Legge template.txt o restituisce il default."""
    if TEMPLATE.exists():
        return TEMPLATE.read_text()
    return _template_default()


def _template_default() -> str:
    return """OGGETTO: Richiesta accesso civico generalizzato ex art. 5 D.Lgs. 33/2013

Il/la sottoscritto/a [NOME COGNOME], ai sensi dell'art. 5 del D.Lgs. 33/2013
e dell'art. 6 del D.Lgs. 97/2016, CHIEDE l'accesso ai dati e documenti
dettagliati in calce, che codesto ente è tenuto a detenere e pubblicare.

── ENTE ──
{ENTE_NOME}
PEC: {ENTE_PEC}

── RICHIESTA ──
1. Tutti i dati e documenti oggetto degli obblighi di pubblicazione
   di cui al D.Lgs. 33/2013, in formato aperto (CSV/JSON/XML).
2. Ogni altra informazione connessa, in formato elettronico elaborabile.

── NORME APPLICABILI ──
- Art. 5 D.Lgs. 33/2013: accesso civico (chiunque, senza motivazione)
- Art. 6 D.Lgs. 97/2016: accesso civico generalizzato (FOIA)
- Art. 7 D.Lgs. 33/2013: pubblicazione in formato aperto
- Art. 52 CAD (D.Lgs. 82/2005): open data by default

── RISPOSTA ──
Termine: 30 giorni dalla ricezione | Invio: PEC o email
Gratuito. Decorso il termine: segnalazione ANAC (art. 45 D.Lgs. 33/2013)
Per violazioni formato: segnalazione al Difensore Civico Digitale (AgID)

Data: {DATA}
[NOME] — [PEC/EMAIL RICHIEDENTE]
"""


def genera_bozza(ente: dict, tracker: list[dict]) -> str:
    """Compila il template con i dati dell'ente."""
    tpl = _template_testo()
    oggi = date.today().strftime("%d/%m/%Y")
    return tpl.replace("{ENTE_NOME}", ente.get("nome", "?")) \
              .replace("{ENTE_PEC}", ente.get("pec", "?")) \
              .replace("{DATA}", oggi)


# ── Escalation ──────────────────────────────────────────────────────────


def genera_dcd(ente: dict, violazioni: str = "") -> str:
    """Bozza segnalazione al Difensore Civico per il Digitale (AgID)."""
    oggi = date.today().strftime("%d/%m/%Y")
    return f"""OGGETTO: Segnalazione al Difensore Civico per il Digitale ex art. 17 CAD
         — violazione formato aperto — {ente.get('nome', '?')}

Il/la sottoscritto/a [NOME COGNOME], ai sensi dell'art. 17 del D.Lgs. 82/2005 (CAD),
SEGNALA che l'ente in oggetto non pubblica i dati richiesti in formato aperto.

── ENTE ──
{ente.get('nome', '?')}
PEC: {ente.get('pec', '?')}

── VIOLAZIONE ──
{ violazioni or 'I dati non sono disponibili in formato aperto elaborabile (CSV/JSON/XML), in violazione dell\'art. 7 D.Lgs. 33/2013 e delle Linee Guida AgID Open Data.' }

── RICHIESTA ──
Si chiede l'intervento del Difensore Civico per il Digitale affinché l'ente
adegui le modalità di pubblicazione al formato aperto.

Data: {oggi}
[NOME] — [PEC/EMAIL RICHIEDENTE]
"""


def genera_anac(ente: dict, foia_id: str, data_invio: str) -> str:
    """Bozza segnalazione ANAC per mancata risposta FOIA."""
    oggi = date.today().strftime("%d/%m/%Y")
    return f"""OGGETTO: Segnalazione ai sensi dell'art. 45 D.Lgs. 33/2013
         — mancata risposta a richiesta accesso civico — {ente.get('nome', '?')}

Il/la sottoscritto/a [NOME COGNOME], ai sensi dell'art. 45 del D.Lgs. 33/2013,
SEGNALA la mancata risposta alla richiesta di accesso civico generalizzato
inviata a codesto ente.

── ENTE ──
{ente.get('nome', '?')}
PEC ente: {ente.get('pec', '?')}

── RICHIESTA FOIA ──
ID: {foia_id}
Data invio: {data_invio}
Termine risposta (30gg): scaduto
Richiesta di riesame al RPCT: da inviare / inviata

── VIOLAZIONE ──
Mancata risposta nel termine di 30 giorni dalla richiesta, in violazione
dell'art. 5, comma 6, del D.Lgs. 33/2013.

── RICHIESTA ──
Si chiede all'ANAC di valutare la violazione e adottare i provvedimenti
di cui all'art. 45 del D.Lgs. 33/2013.

Data: {oggi}
[NOME] — [PEC/EMAIL RICHIEDENTE]
"""


# ── Tracker helpers ─────────────────────────────────────────────────────


def trova_richiesta(tracker: list[dict], ente_id: str) -> dict | None:
    for r in tracker:
        if r["id"] == ente_id:
            return r
    return None


def aggiungi_o_aggiorna(tracker: list[dict], ente_id: str, updates: dict) -> None:
    for r in tracker:
        if r["id"] == ente_id:
            r.update(updates)
            return
    # Non trovata: crea nuova
    entry = {"id": ente_id, "status": "pending", "data_invio": None,
             "data_risposta": None, "escalation_anac": False, "note": ""}
    entry.update(updates)
    tracker.append(entry)


# ── Comandi CLI ─────────────────────────────────────────────────────────


def cmd_next(enti: list[dict], tracker: list[dict]) -> None:
    ente = prossimo_inviabile(enti, tracker)
    if not ente:
        print("\n✅ Tutti gli enti sono stati contattati! Ricominciamo il ciclo.")
        return

    n_attesa = sum(1 for r in tracker if r["status"] == "pending")
    n_inviate = sum(1 for r in tracker if r["status"] != "pending")
    totale = len(enti)

    print(f"\n{'='*60}")
    print(f"  PROSSIMO ENTE ({n_inviate}/{totale} inviate)")
    print(f"{'='*60}")
    print(f"  Nome:     {ente['nome']}")
    print(f"  PEC:      {ente.get('pec', '❌ non disponibile')}")
    print(f"  Categoria: {ente.get('categoria', '?')}")
    print(f"  Note:     {ente.get('note', '')}")
    print(f"\n  In attesa risposta: {n_attesa}")

    # Genera bozza
    bozza = genera_bozza(ente, tracker)
    fname = f"{ente['id']}.txt"
    out = BOZZE / fname
    out.parent.mkdir(exist_ok=True)
    out.write_text(bozza)
    print(f"\n  📄 Bozza salvata: {out}")

    # Aggiunge al tracker se non già presente
    aggiungi_o_aggiorna(tracker, ente["id"], {"status": "pending"})
    salva_tracker(tracker)

    print(f"\n  ▶  Invia PEC a: {ente.get('pec', '❌')}")
    print(f"  ▶  Poi esegui: python foia.py --send {ente['id']}")
    print()


def cmd_send(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    if not ente_per_id(enti, ente_id):
        print(f"❌ Ente '{ente_id}' non trovato in enti.json")
        return
    oggi = date.today().isoformat()
    scadenza = (date.today() + timedelta(days=TERMINE_RISPOSTA)).isoformat()
    aggiungi_o_aggiorna(tracker, ente_id, {
        "status": "sent",
        "data_invio": oggi,
        "scadenza_risposta": scadenza,
    })
    salva_tracker(tracker)
    ente = ente_per_id(enti, ente_id)
    print(f"✅ {ente_id} ({ente['nome']}) segnata come inviata il {oggi}")
    print(f"   Scadenza risposta: {scadenza} ({TERMINE_RISPOSTA} giorni)")
    print(f"   ▶  Per escalation automatica: python foia.py --scadenze")


def cmd_respond(tracker: list[dict], ente_id: str, status: str, note: str) -> None:
    if not trova_richiesta(tracker, ente_id):
        print(f"❌ Richiesta '{ente_id}' non trovata nel tracker")
        return
    oggi = date.today().isoformat()
    aggiungi_o_aggiorna(tracker, ente_id, {
        "status": status,
        "data_risposta": oggi,
        "note": note,
    })
    salva_tracker(tracker)
    print(f"✅ {ente_id}: risposta registrata come '{status}'")


def cmd_status(enti: list[dict], tracker: list[dict]) -> None:
    totale = len(enti)
    inviate = sum(1 for r in tracker if r["status"] != "pending")
    pending = sum(1 for r in tracker if r["status"] == "pending")
    risposte = sum(1 for r in tracker if r["status"]
                   in ("ok", "parziale", "rifiutata", "ignorata"))
    anac = sum(1 for r in tracker if r.get("escalation_anac"))
    scadute = sum(1 for r in tracker
                  if r["status"] == "sent" and r.get("scadenza_risposta")
                  and r["scadenza_risposta"] < date.today().isoformat())

    print(f"\n{'='*50}")
    print(f"  STATO CAMPAGNA FOIA")
    print(f"{'='*50}")
    print(f"  Enti totali:      {totale}")
    print(f"  Inviate:          {inviate}")
    print(f"  In attesa invio:  {totale - inviate}")
    print(f"  In attesa risp.:  {inviate - risposte}")
    print(f"  Risposte:         {risposte}")
    print(f"  Scadute (30gg+):  {scadute}")
    print(f"  Escalate ANAC:    {anac}")
    print()

    if not tracker:
        print("  Nessuna richiesta ancora registrata.\n")
        return

    print(f"  {'ID':25s} {'Status':15s} {'Invio':12s} {'Risposta':12s}")
    print(f"  {'-'*25} {'-'*15} {'-'*12} {'-'*12}")
    for r in sorted(tracker, key=lambda x: x.get("data_invio") or "9999-12-31"):
        sid = r["id"][:24]
        st = r["status"]
        inv = (r.get("data_invio") or "--")[:10]
        risp = (r.get("data_risposta") or "--")[:10]
        scad = ""
        if st == "sent" and r.get("scadenza_risposta") and r["scadenza_risposta"] < date.today().isoformat():
            scad = " ⏰ SCADUTA"
        print(f"  {sid:25s} {st:15s} {inv:12s} {risp:12s}{scad}")
    print()

    if scadute > 0:
        print(f"  ▶  python foia.py --scadenze  (per vedere le scadute)")
    if pending > 0:
        n_prossimo = next((i for i, r in enumerate(tracker) if r["status"] == "pending"), None)
        if n_prossimo is not None:
            print(f"  ▶  python foia.py --next")


def cmd_scadenze(enti: list[dict], tracker: list[dict]) -> None:
    oggi = date.today()
    scadute = [r for r in tracker
               if r["status"] == "sent"
               and r.get("scadenza_risposta")
               and r["scadenza_risposta"] < oggi.isoformat()
               and not r.get("escalation_anac")]

    if not scadute:
        print("\n✅ Nessuna richiesta scaduta.\n")
        return

    print(f"\n{'='*50}")
    print(f"  RICHIESTE SCADUTE ({len(scadute)})")
    print(f"{'='*50}")
    for r in scadute:
        ente = ente_per_id(enti, r["id"])
        nome = ente["nome"] if ente else r["id"]
        invio = r.get("data_invio", "?")
        scad = r.get("scadenza_risposta", "?")
        gg = (oggi - date.fromisoformat(scad)).days if scad != "?" else 0
        print(f"\n  ⏰ {r['id']} — {nome}")
        print(f"     Inviata:  {invio}")
        print(f"     Scaduta:  {scad} ({gg} giorni di ritardo)")
        print(f"     ▶  python foia.py --anac {r['id']}  (bozza ANAC)")
    print()


def cmd_dcd(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return
    bozza = genera_dcd(ente)
    fname = f"dcd_{ente_id}.txt"
    out = BOZZE / fname
    out.parent.mkdir(exist_ok=True)
    out.write_text(bozza)
    print(f"\n📄 Bozza DCD generata: {out}")
    print(f"   Inviare a: dcd@agid.gov.it")
    print()


def cmd_anac(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return
    req = trova_richiesta(tracker, ente_id)
    if not req:
        print(f"❌ Richiesta '{ente_id}' non trovata nel tracker")
        return
    if req["status"] != "sent" and req["status"] != "pending":
        print(f"⚠️  La richiesta è in stato '{req['status']}' — genero comunque la bozza.")

    data_invio = req.get("data_invio") or "data non registrata"
    bozza = genera_anac(ente, ente_id, data_invio)
    fname = f"anac_{ente_id}.txt"
    out = BOZZE / fname
    out.parent.mkdir(exist_ok=True)
    out.write_text(bozza)

    # Segna escalation
    aggiungi_o_aggiorna(tracker, ente_id, {"escalation_anac": True})
    salva_tracker(tracker)

    print(f"\n📄 Bozza ANAC generata: {out}")
    print(f"   Inviare a: protocollo@anac.it (PEC: protocollo@pec.anac.it)")
    print()


def cmd_lista(enti: list[dict], tracker: list[dict]) -> None:
    """Mostra lista completa enti con stato."""
    print(f"\n{'='*60}")
    print(f"  LISTA ENTI ({len(enti)})")
    print(f"{'='*60}")
    for e in enti:
        r = trova_richiesta(tracker, e["id"])
        status = r["status"] if r else "—"
        pec = e.get("pec", "❌")[:30]
        print(f"  {e['id']:25s} {status:15s} PEC: {pec}")
    print()


# ── Main ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Campagna FOIA quotidiana — invio, tracking, escalation")
    parser.add_argument("--next", action="store_true", help="Prossimo ente da contattare")
    parser.add_argument("--send", metavar="ID", help="Segna ente come inviato (es. poste-italiane)")
    parser.add_argument("--respond", metavar="ID", help="Registra risposta per ente")
    parser.add_argument("--status", action="store_true", help="Tabella riepilogativa")
    parser.add_argument("--scadenze", action="store_true", help="Richieste scadute (30gg+)")
    parser.add_argument("--dcd", metavar="ID", help="Genera bozza DCD per ente")
    parser.add_argument("--anac", metavar="ID", help="Genera bozza ANAC per ente")
    parser.add_argument("--lista", action="store_true", help="Lista completa enti con stato")
    parser.add_argument("--status-resp", choices=["ok", "parziale", "rifiutata", "ignorata"],
                        default="ok", help="Esito risposta (default: ok)")
    parser.add_argument("--note", default="", help="Nota opzionale per risposta/invio")
    args = parser.parse_args()

    enti = carica_enti()
    tracker = carica_tracker()

    if args.status:
        cmd_status(enti, tracker)
    elif args.next:
        cmd_next(enti, tracker)
    elif args.send:
        cmd_send(enti, tracker, args.send)
    elif args.respond:
        cmd_respond(tracker, args.respond, args.status_resp, args.note)
    elif args.scadenze:
        cmd_scadenze(enti, tracker)
    elif args.dcd:
        cmd_dcd(enti, tracker, args.dcd)
    elif args.anac:
        cmd_anac(enti, tracker, args.anac)
    elif args.lista:
        cmd_lista(enti, tracker)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
