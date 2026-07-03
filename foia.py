#!/usr/bin/env python3
"""
Campagna FOIA quotidiana — verifica, diagnosi, azione.

Flusso:
  1. --next              Mostra prossimo ente da verificare
  2. Verifica manuale    Apri il sito/portale, raccogli evidenze
  3. --stato ID --azione ok|foia|dcd|foia+dcd   Diagnosi + genera bozze
  4. Invia PEC a mano
  5. --send ID           Traccia invio
  6. --respond ID        Quando arriva risposta
  7. --dcd / --anac      Escalation (se necessario)

Uso:
  python foia.py --next                         # Prossimo da verificare
  python foia.py --stato ID --azione foia       # Diagnosi + genera bozza
  python foia.py --skip ID                      # Ente OK, nessuna azione
  python foia.py --send ID                      # Segna come inviato
  python foia.py --respond ID --status ok       # Registra risposta
  python foia.py --report            # Riepilogo
  python foia.py --lista                        # Tutti gli enti con stato
  python foia.py --scadenze                     # Richieste scadute
  python foia.py --dcd ID                       # Bozza DCD
  python foia.py --anac ID                      # Bozza ANAC

Dati:
  enti/enti.json        Anagrafica enti con PEC e stato verifica
  data/tracker.json     Richieste inviate
  template.txt          Template FOIA
  bozze/                Bozze generate
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

TERMINE_RISPOSTA = 30

AZIONI_VALIDE = ("ok", "foia", "dcd", "foia+dcd")

# ── JSON ─────────────────────────────────────────────────────────────────


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


# ── Caricamento ──────────────────────────────────────────────────────────


def carica_enti() -> list[dict]:
    return _carica_json(ENTI)  # type: ignore


def _salva_enti(enti: list[dict]) -> None:
    _salva_json(ENTI, enti)


def carica_tracker() -> list[dict]:
    if TRACKER.exists():
        raw = _carica_json(TRACKER)
        if isinstance(raw, dict):
            return raw.get("richieste", [])
        return raw
    return []


def salva_tracker(richieste: list[dict]) -> None:
    stats = _recalc_stats(richieste)
    _salva_json(TRACKER, {"richieste": richieste, "_stats": stats})


# ── Helpers ──────────────────────────────────────────────────────────────


def ente_per_id(enti: list[dict], ente_id: str) -> dict | None:
    for e in enti:
        if e["id"] == ente_id:
            return e
    return None


def aggiorna_ente(enti: list[dict], ente_id: str, updates: dict) -> None:
    for e in enti:
        if e["id"] == ente_id:
            e.update(updates)
            _salva_enti(enti)
            return
    print(f"❌ Ente '{ente_id}' non trovato", file=sys.stderr)


def prossimo_da_verificare(enti: list[dict]) -> dict | None:
    for e in enti:
        if e.get("stato", "da-verificare") == "da-verificare":
            return e
    return None


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
    entry = {"id": ente_id, "status": "pending", "data_invio": None,
             "data_risposta": None, "escalation_anac": False, "note": ""}
    entry.update(updates)
    tracker.append(entry)


# ── Template ─────────────────────────────────────────────────────────────


def _template_testo() -> str:
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


def genera_bozza_foia(ente: dict) -> str:
    tpl = _template_testo()
    oggi = date.today().strftime("%d/%m/%Y")
    return tpl.replace("{ENTE_NOME}", ente.get("nome", "?")) \
              .replace("{ENTE_PEC}", ente.get("pec", "?")) \
              .replace("{DATA}", oggi)


def genera_bozza_dcd(ente: dict, violazioni: str = "") -> str:
    oggi = date.today().strftime("%d/%m/%Y")
    return f"""OGGETTO: Segnalazione al Difensore Civico per il Digitale ex art. 17 CAD
         — violazione formato aperto — {ente.get('nome', '?')}

Il/la sottoscritto/a [NOME COGNOME], ai sensi dell'art. 17 del D.Lgs. 82/2005 (CAD),
SEGNALA che l'ente in oggetto non pubblica i dati richiesti in formato aperto.

── ENTE ──
{ente.get('nome', '?')}
PEC: {ente.get('pec', '?')}

── VIOLAZIONE ──
{violazioni or 'I dati non sono disponibili in formato aperto elaborabile (CSV/JSON/XML), in violazione dell\'art. 7 D.Lgs. 33/2013 e delle Linee Guida AgID Open Data.'}

── RICHIESTA ──
Si chiede l'intervento del Difensore Civico per il Digitale affinché l'ente
adegui le modalità di pubblicazione al formato aperto.

Data: {oggi}
[NOME] — [PEC/EMAIL RICHIEDENTE]
"""


def genera_bozza_anac(ente: dict, foia_id: str, data_invio: str) -> str:
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

── VIOLAZIONE ──
Mancata risposta nel termine di 30 giorni dalla richiesta, in violazione
dell'art. 5, comma 6, del D.Lgs. 33/2013.

── RICHIESTA ──
Si chiede all'ANAC di valutare la violazione e adottare i provvedimenti
di cui all'art. 45 del D.Lgs. 33/2013.

Data: {oggi}
[NOME] — [PEC/EMAIL RICHIEDENTE]
"""


# ── Comandi ──────────────────────────────────────────────────────────────


def cmd_next(enti: list[dict], tracker: list[dict]) -> None:
    ente = prossimo_da_verificare(enti)
    if not ente:
        # Tutti verificati: mostra prossimo da inviare
        verif_foia = [e for e in enti if e.get("stato") in ("foia", "foia+dcd")]
        if verif_foia:
            print("\n✅ Tutti verificati. Prossimo da inviare:")
            e = verif_foia[0]
            print(f"  {e['nome']}  →  python foia.py --send {e['id']}")
            return
        print("\n✅ Tutti gli enti sono stati verificati e processati. Ciclo completato!")
        return

    n_verificati = sum(1 for e in enti if e.get("stato", "da-verificare") != "da-verificare")
    totale = len(enti)

    print(f"\n{'='*60}")
    print(f"  DA VERIFICARE ({n_verificati}/{totale} fatti)")
    print(f"{'='*60}")
    print(f"  Ente:      {ente['nome']}")
    print(f"  PEC:       {ente.get('pec', '❌ non disponibile')}")
    print(f"  Categoria: {ente.get('categoria', '?')}")
    print(f"  Note:      {ente.get('note', '')}")
    print()
    print(f"  ▶  Verifica il portale dell'ente (cerca sezione open data / trasparenza)")
    print(f"  ▶  Poi registra la diagnosi:")
    print(f"       python foia.py --stato {ente['id']} --azione ok")
    print(f"       python foia.py --stato {ente['id']} --azione foia")
    print(f"       python foia.py --stato {ente['id']} --azione dcd")
    print(f"       python foia.py --stato {ente['id']} --azione foia+dcd")
    print()


def cmd_stato(enti: list[dict], tracker: list[dict], ente_id: str, azione: str) -> None:
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return

    aggiorna_ente(enti, ente_id, {"stato": azione})
    label = {
        "ok": "✅ ok — nessuna azione necessaria",
        "foia": "📄 FOIA — da inviare",
        "dcd": "📄 DCD — da inviare",
        "foia+dcd": "📄 FOIA + DCD — entrambi da inviare",
    }
    print(f"\n{label.get(azione, azione)}")

    # Genera bozze se necessario
    if azione in ("foia", "foia+dcd"):
        bozza = genera_bozza_foia(ente)
        fname = f"{ente_id}.txt"
        out = BOZZE / fname
        out.parent.mkdir(exist_ok=True)
        out.write_text(bozza)
        print(f"  📄 Bozza FOIA: {out}")
        # Prepara tracker
        aggiungi_o_aggiorna(tracker, ente_id, {"status": "pending"})
        salva_tracker(tracker)
        print(f"  ▶  Invia PEC e poi: python foia.py --send {ente_id}")

    if azione in ("dcd", "foia+dcd"):
        bozza = genera_bozza_dcd(ente)
        fname = f"dcd_{ente_id}.txt"
        out = BOZZE / fname
        out.parent.mkdir(exist_ok=True)
        out.write_text(bozza)
        print(f"  📄 Bozza DCD: {out}")
        print(f"  ▶  Invia a: dcd@agid.gov.it")

    if azione == "ok":
        print(f"  ▶  Nessuna azione. Ente marcato come verificato.")

    print()


def cmd_skip(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    cmd_stato(enti, tracker, ente_id, "ok")


def cmd_send(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato in enti.json")
        return
    stato = ente.get("stato", "da-verificare")
    if stato not in ("foia", "foia+dcd"):
        print(f"⚠️  Attenzione: ente in stato '{stato}' — la verifica non ha indicato FOIA")
    oggi = date.today().isoformat()
    scadenza = (date.today() + timedelta(days=TERMINE_RISPOSTA)).isoformat()
    aggiungi_o_aggiorna(tracker, ente_id, {
        "status": "sent",
        "data_invio": oggi,
        "scadenza_risposta": scadenza,
    })
    salva_tracker(tracker)
    ente = ente_per_id(enti, ente_id)
    print(f"✅ {ente_id} ({ente['nome']}) — inviata il {oggi}")
    print(f"   Scadenza risposta: {scadenza}")
    print(f"   ▶  Per escalation: python foia.py --scadenze")


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
    print(f"✅ {ente_id}: risposta '{status}' registrata")


def cmd_status(enti: list[dict], tracker: list[dict]) -> None:
    da_verificare = [e for e in enti if e.get("stato", "da-verificare") == "da-verificare"]
    ok = [e for e in enti if e.get("stato") == "ok"]
    in_coda = [e for e in enti if e.get("stato") in ("foia", "dcd", "foia+dcd")]
    inviate = sum(1 for r in tracker if r["status"] != "pending")
    risposte = sum(1 for r in tracker if r["status"]
                   in ("ok", "parziale", "rifiutata", "ignorata"))
    scadute = sum(1 for r in tracker
                  if r["status"] == "sent" and r.get("scadenza_risposta")
                  and r["scadenza_risposta"] < date.today().isoformat())

    print(f"\n{'='*50}")
    print(f"  STATO CAMPAGNA FOIA")
    print(f"{'='*50}")
    print(f"  Enti totali:        {len(enti)}")
    print(f"  Da verificare:      {len(da_verificare)}")
    print(f"  OK (nessuna az.):   {len(ok)}")
    print(f"  In coda (FOIA/DCD): {len(in_coda)}")
    print(f"  Richieste inviate:  {inviate}")
    print(f"  Risposte:           {risposte}")
    print(f"  Scadute (30gg+):    {scadute}")
    print()

    if not tracker and not da_verificare and not in_coda:
        print("  Nessuna attività. Enti tutti verificati e processati.\n")
        return

    if da_verificare:
        print(f"  ▶  python foia.py --next  ({len(da_verificare)} da verificare)")

    if in_coda:
        for e in in_coda:
            r = trova_richiesta(tracker, e["id"])
            st = r["status"] if r else "—"
            print(f"  📋 {e['id']:25s} stato={e['stato']:12s} tracker={st}")
    print()


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
    print(f"  SCADUTE ({len(scadute)})")
    print(f"{'='*50}")
    for r in scadute:
        ente = ente_per_id(enti, r["id"])
        nome = ente["nome"] if ente else r["id"]
        invio = r.get("data_invio", "?")
        scad = r.get("scadenza_risposta", "?")
        gg = (oggi - date.fromisoformat(scad)).days if scad != "?" else 0
        print(f"\n  ⏰ {r['id']} — {nome}")
        print(f"     Inviata: {invio}  Scaduta: {scad}  ({gg}gg ritardo)")
        print(f"     ▶  python foia.py --anac {r['id']}")
    print()


def cmd_dcd(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return
    bozza = genera_bozza_dcd(ente)
    fname = f"dcd_{ente_id}.txt"
    out = BOZZE / fname
    out.parent.mkdir(exist_ok=True)
    out.write_text(bozza)
    print(f"\n📄 Bozza DCD generata: {out}")
    print(f"   Destinazione: dcd@agid.gov.it\n")


def cmd_anac(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return
    req = trova_richiesta(tracker, ente_id)
    if not req:
        print(f"❌ Nessuna richiesta FOIA trovata per '{ente_id}' nel tracker")
        return
    data_invio = req.get("data_invio") or "data non registrata"
    bozza = genera_bozza_anac(ente, ente_id, data_invio)
    fname = f"anac_{ente_id}.txt"
    out = BOZZE / fname
    out.parent.mkdir(exist_ok=True)
    out.write_text(bozza)
    aggiungi_o_aggiorna(tracker, ente_id, {"escalation_anac": True})
    salva_tracker(tracker)
    print(f"\n📄 Bozza ANAC generata: {out}")
    print(f"   Destinazione: protocollo@pec.anac.it\n")


def cmd_lista(enti: list[dict], tracker: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"  LISTA ENTI ({len(enti)})")
    print(f"{'='*60}")
    for e in enti:
        r = trova_richiesta(tracker, e["id"])
        st = e.get("stato", "da-verificare")
        pec = e.get("pec", "❌")[:30]
        tr = r["status"] if r else "—"
        print(f"  {e['id']:25s} verifica={st:12s} tracker={tr:10s} PEC={pec}")
    print()


def cmd_da_fare(enti: list[dict], tracker: list[dict]) -> None:
    """Lista enti in coda (FOIA/DCD) da inviare o già inviati in attesa."""
    in_coda = [e for e in enti if e.get("stato") in ("foia", "foia+dcd", "dcd")]
    inviate = [r for r in tracker if r["status"] == "sent"]
    da_inviare = [e for e in in_coda
                  if not trova_richiesta(tracker, e["id"])
                  or trova_richiesta(tracker, e["id"])["status"] == "pending"]
    print(f"\n{'='*50}")
    print(f"  CODA AZIONI")
    print(f"{'='*50}")
    if da_inviare:
        print(f"  Da inviare ({len(da_inviare)}):")
        for e in da_inviare:
            r = trova_richiesta(tracker, e["id"])
            stato_tracker = f" [{r['status']}]" if r else ""
            azione = e['stato']
            suggerimento = {
                "foia": f"--send {e['id']}",
                "dcd": "invia bozza DCD a dcd@agid.gov.it",
                "foia+dcd": f"--send {e['id']} + bozza DCD",
            }.get(azione, azione)
            print(f"    📋 {e['id']:25s} {azione:12s}{stato_tracker:12s} → {suggerimento}")
    else:
        print(f"  ✅ Tutte le richieste sono state inviate.")
    if inviate:
        print(f"\n  In attesa risposta ({len(inviate)}):")
        for r in inviate:
            print(f"    ⏳ {r['id']:25s} inviata {r.get('data_invio','?')[:10]}")
    print()


# ── Main ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Campagna FOIA — verifica, diagnosi, azione, tracking")
    parser.add_argument("--next", action="store_true", help="Prossimo ente da verificare")
    parser.add_argument("--stato", metavar="ID", help="Registra diagnosi per ente")
    parser.add_argument("--azione", choices=AZIONI_VALIDE, default="ok",
                        help="Esito verifica (default: ok)")
    parser.add_argument("--skip", metavar="ID", help="Ente OK, nessuna azione")
    parser.add_argument("--send", metavar="ID", help="Segna FOIA come inviata")
    parser.add_argument("--respond", metavar="ID", help="Registra risposta")
    parser.add_argument("--status", choices=["ok", "parziale", "rifiutata", "ignorata"],
                        default="ok", help="Esito risposta (con --respond)")
    parser.add_argument("--report", action="store_true", help="Riepilogo campagna")
    parser.add_argument("--scadenze", action="store_true", help="Richieste scadute")
    parser.add_argument("--dcd", metavar="ID", help="Genera bozza DCD")
    parser.add_argument("--anac", metavar="ID", help="Genera bozza ANAC")
    parser.add_argument("--lista", action="store_true", help="Lista enti con stato")
    parser.add_argument("--da-fare", action="store_true", help="Coda azioni pendenti")
    parser.add_argument("--note", default="", help="Nota per risposta/invio")
    args = parser.parse_args()

    enti = carica_enti()
    tracker = carica_tracker()

    if args.report:
        cmd_status(enti, tracker)
    elif args.next:
        cmd_next(enti, tracker)
    elif args.stato:
        cmd_stato(enti, tracker, args.stato, args.azione)
    elif args.skip:
        cmd_skip(enti, tracker, args.skip)
    elif args.send:
        cmd_send(enti, tracker, args.send)
    elif args.respond:
        cmd_respond(tracker, args.respond, args.status, args.note)
    elif args.scadenze:
        cmd_scadenze(enti, tracker)
    elif args.dcd:
        cmd_dcd(enti, tracker, args.dcd)
    elif args.anac:
        cmd_anac(enti, tracker, args.anac)
    elif args.lista:
        cmd_lista(enti, tracker)
    elif args.da_fare:
        cmd_da_fare(enti, tracker)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
