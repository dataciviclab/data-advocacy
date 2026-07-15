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
import base64
import json
import os
import sys
import textwrap
from datetime import date, datetime, timedelta
from email import charset as email_charset
from email import encoders as email_encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

REPO = Path(__file__).resolve().parent
ENTI = REPO / "enti" / "enti.json"
TRACKER = REPO / "data" / "tracker.json"
TEMPLATE = REPO / "template.txt"
TEMPLATE_CATALOGO = REPO / "template-catalogo.txt"
RICHIEDENTE = REPO / "richiedente.json"
ALLEGATO_CSV = REPO / "data" / "allegato_catalogo.csv"
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


def carica_richiedente() -> dict:
    default = {"nome": "NOME COGNOME", "pec": "PEC/EMAIL", "riferimento": "", "firma": "persona fisica"}
    if RICHIEDENTE.exists():
        data = _carica_json(RICHIEDENTE)
        if isinstance(data, dict):
            return {**default, **data}
    return default


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
    # template-catalogo.txt è il template principale (Godfather)
    if TEMPLATE_CATALOGO.exists():
        return TEMPLATE_CATALOGO.read_text()
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


def genera_bozza_foia(ente: dict, richiedente: dict | None = None) -> str:
    tpl = _template_testo()
    oggi = date.today().strftime("%d/%m/%Y")
    anno = str(date.today().year)
    ric = richiedente or carica_richiedente()
    nome_ric = ric.get("nome", "[NOME COGNOME]")
    pec_ric = ric.get("pec", "[PEC/EMAIL]")
    rif = ric.get("riferimento", "DataCivicLab")
    # Tipo ente per punto 7 (da note_foia se presente)
    nf = ente.get("note_foia", {})
    tipo_ente = nf.get("tipo_ente", "[TIPO ENTE]") if nf else "[TIPO ENTE]"
    import re
    result = tpl.replace("{ENTE_NOME}", ente.get("nome", "?")) \
                .replace("{ENTE_PEC}", ente.get("pec", "?")) \
                .replace("{DATA}", oggi) \
                .replace("{ANNO_CORRENTE}", anno) \
                .replace("{NOME_COGNOME}", nome_ric) \
                .replace("{PEC_EMAIL}", pec_ric) \
                .replace("{RIFERIMENTO}", rif)
    # Sostituisce il tipo ente nel punto 7
    result = re.sub(r'(in quanto\s+)\[.*?\]', rf'\1{tipo_ente}', result)
    return result


def genera_bozza_dcd(ente: dict, foia_id: str = "", violazioni: str = "", richiedente: dict | None = None) -> str:
    oggi = date.today().strftime("%d/%m/%Y")
    ric = richiedente or carica_richiedente()
    nome_ric = ric.get("nome", "[NOME COGNOME]")
    pec_ric = ric.get("pec", "[PEC/EMAIL]")

    # Evidenze da note_foia
    nf = ente.get("note_foia", {})
    ev_formato = nf.get("formato", "formato chiuso non aperto")

    # Riferimento FOIA (se fornito)
    rif_foia = f"a seguito della richiesta FOIA (ID: {foia_id}) " if foia_id else ""

    return f"""OGGETTO: Segnalazione al Difensore Civico per il Digitale ex art. 17 CAD
       — violazione formato aperto — {ente.get('nome', '?')}

Il sottoscritto {nome_ric}, ai sensi dell'art. 17 del D.Lgs. 82/2005 (CAD),

PREMESSO CHE
- Il segnalante ha inviato {rif_foia}all'ente in oggetto una richiesta di accesso civico generalizzato per il catalogo dei dati detenuti.
- Dalle verifiche disponibili presso il catalogo nazionale dati.gov.it e i portali istituzionali, si rileva che l'ente pubblica dati in formato non aperto: {ev_formato}.
- L'art. 7 D.Lgs. 33/2013 e l'art. 52 CAD impongono la pubblicazione in formato aperto (CSV, JSON, XML).
- {violazioni or 'La pubblicazione in formato chiuso costituisce violazione degli obblighi di trasparenza e riutilizzo.'}

CHIEDE
1. La verifica della conformita' dell'ente agli obblighi di pubblicazione in formato aperto.
2. L'eventuale prescrizione per l'adeguamento, con cronoprogramma.
3. La comunicazione dell'esito dell'istruttoria al segnalante.

ALLEGA
- Copia della richiesta FOIA inviata all'ente (su richiesta).

Data: {oggi}
{nome_ric} — {pec_ric}
"""


def genera_bozza_anac(ente: dict, foia_id: str, data_invio: str, richiedente: dict | None = None) -> str:
    oggi = date.today().strftime("%d/%m/%Y")
    ric = richiedente or carica_richiedente()
    nome_ric = ric.get("nome", "[NOME COGNOME]")
    pec_ric = ric.get("pec", "[PEC/EMAIL]")
    return f"""OGGETTO: Segnalazione ai sensi dell'art. 45 D.Lgs. 33/2013
       — mancata risposta a richiesta accesso civico — {ente.get('nome', '?')}

Il/la sottoscritto/a {nome_ric}, ai sensi dell'art. 45 del D.Lgs. 33/2013,
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
{nome_ric} — {pec_ric}
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
       # Copia CSV template (tracciato record) come allegato
       if ALLEGATO_CSV.exists():
           csv_out = BOZZE / f"{ente_id}_catalogo.csv"
           csv_out.write_text(ALLEGATO_CSV.read_text())
           print(f"  📎 CSV template: {csv_out}  (allega alla PEC)")
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
       print(f"  ▶  Invia a: protocollo@pec.agid.gov.it")

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


def cmd_ricevi(enti: list[dict], tracker: list[dict], ente_id: str,
               file_path: str, status: str, note: str) -> None:
    """Salva una risposta FOIA (CSV/allegato) e la traccia."""
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return

    # Verifica file
    src = Path(file_path)
    if not src.exists():
        print(f"❌ File non trovato: {file_path}")
        return

    # Crea directory risposte
    risposte_dir = REPO / "data" / "risposte"
    risposte_dir.mkdir(parents=True, exist_ok=True)

    # Copia file con timestamp
    oggi = date.today().isoformat()
    estensione = src.suffix or ".txt"
    dest = risposte_dir / f"{ente_id}_{oggi}{estensione}"
    dest.write_bytes(src.read_bytes())

    # Validazione CSV (se è un CSV)
    report = ""
    if estensione.lower() == ".csv":
        colonne = dest.read_text(encoding="utf-8").split("\n")[0].strip()
        n_col = len(colonne.split(";"))
        if n_col >= 10:
            report = f"✅ CSV valido: {n_col} colonne"
        else:
            report = f"⚠️  CSV con solo {n_col} colonne (attese 11)"
    else:
        report = f"📄 Allegato salvato: {estensione.upper()}"

    # Registra nel tracker
    cmd_respond(tracker, ente_id, status, f"{note} [{report}]")

    print(f"\n📥 Risposta: {ente_id} ({ente['nome']})")
    print(f"   File: {dest}")
    print(f"   Esito: {status}")
    print(f"   {report}")
    print(f"   ▶  Per escalation: python foia.py --scadenze")
    print()


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
    """Genera .eml DCD pronto per l'invio a AgID."""
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return

    bozza = genera_bozza_dcd(ente, foia_id=ente_id)
    ric = carica_richiedente()
    nome_ric = ric.get("nome", "[NOME COGNOME]")
    pec_ric = ric.get("pec", "[PEC/EMAIL]")

    subject = f"Segnalazione ex art. 17 CAD — violazione formato aperto — {ente['nome'][:60]}"

    # HTML
    html_parts = [f"<p>{line}</p>" for line in bozza.split("\n") if line.strip()]
    html_content = "<html><body>\n" + "\n".join(html_parts) + "\n</body></html>"

    CRLF = "\r\n"
    b_mixed = "===============DATACIVICLAB_MIXED_BOUNDARY_1741559805=="
    b_alt = "===============DATACIVICLAB_ALT_BOUNDARY_1741559805=="

    lines = [
        f'From: {nome_ric} <{pec_ric}>',
        'To: protocollo@pec.agid.gov.it',
        f'Subject: {subject}',
        f'Date: {datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")}',
        'MIME-Version: 1.0',
        f'Content-Type: multipart/mixed; boundary="{b_mixed}"',
        '',
        f'--{b_mixed}',
        f'Content-Type: multipart/alternative; boundary="{b_alt}"',
        '',
        f'--{b_alt}',
        'Content-Type: text/plain; charset="utf-8"',
        'Content-Transfer-Encoding: 8bit',
        '',
        bozza,
        '',
        f'--{b_alt}',
        'Content-Type: text/html; charset="utf-8"',
        'Content-Transfer-Encoding: 8bit',
        '',
        html_content,
        '',
        f'--{b_alt}--',
        '',
        f'--{b_mixed}--',
        '',
    ]

    eml_raw = CRLF.join(lines).replace("\r\n", "\n").replace("\n", "\r\n")
    out = BOZZE / f"dcd_{ente_id}.eml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(eml_raw, encoding="utf-8")

    print(f"\n📧 DCD EML: {out}")
    print(f"   Da: {pec_ric}  →  A: protocollo@pec.agid.gov.it")
    print(f"   Oggetto: {subject[:80]}...")
    print(f"   ▶  Invia con: python foia.py --send-now-dcd {ente_id}")
    print()


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
              "dcd": "invia bozza DCD a protocollo@pec.agid.gov.it",
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


def cmd_import(enti: list[dict], path: str) -> None:
    """Importa target FOIA da foia_targets.json e popola enti.json."""
    import json
    try:
       with open(path) as f:
           data = json.load(f)
    except FileNotFoundError:
       print(f"❌ File non trovato: {path}", file=sys.stderr)
       sys.exit(1)

    # Valida contro schema
    schema_path = Path(__file__).resolve().parent / "schemas" / "foia_target_schema.json"
    if schema_path.exists():
       try:
           import jsonschema
           with open(schema_path) as f:
               schema = json.load(f)
           jsonschema.validate(instance=data, schema=schema)
           print("✅ Validazione schema OK")
       except Exception as e:
           print(f"❌ Validazione schema fallita: {e}", file=sys.stderr)
           sys.exit(1)

    targets = data.get("targets", [])
    if not targets:
       print("❌ Nessun target nel file")
       return

    prioritari = [t for t in targets if t.get("priorita") in (1, 2)]
    if not prioritari:
       print("Nessun target prioritario (P1/P2). Importo tutti.")
       prioritari = targets

    aggiunti = 0
    esistenti = 0
    for t in prioritari:
       if not any(e["id"] == t["id"] for e in enti):
          enti.append({
              "id": t["id"],
              "nome": t.get("denominazione", t["id"]),
              "pec": t.get("pec", ""),
              "categoria": t.get("categoria", "altro"),
              "note": f"Target da partecipate-monitor: {t.get('violazione', '?')}. {t.get('dettaglio', '')}",
              "stato": "da-verificare",
          })
          aggiunti += 1
       else:
          esistenti += 1

    _salva_enti(enti)

    p1 = sum(1 for t in prioritari if t.get("priorita") == 1)
    con_pec = sum(1 for t in prioritari if t.get("pec"))
    fonte = data.get("fonte", "?")
    print(f"\n✅ Importati {aggiunti} nuovi enti da '{fonte}' ({len(prioritari)} processati)")
    print(f"   Gia' presenti: {esistenti}")
    print(f"   P1 (urgenti): {p1}")
    print(f"   Con PEC: {con_pec}")
    print(f"   Senza PEC: {len(prioritari) - con_pec}")
    print(f"\n   Prossimo passo: python foia.py --next")


def cmd_eml(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    """Genera .eml direttamente da template + CSV fonte. Nessun file intermedio."""
    ente = ente_per_id(enti, ente_id)
    if not ente:
        print(f"❌ Ente '{ente_id}' non trovato")
        return

    # Auto-registra stato se ente non diagnosticato
    if ente.get("stato", "da-verificare") == "da-verificare":
        cmd_stato(enti, tracker, ente_id, "foia")
        ente = ente_per_id(enti, ente_id)

    ric = carica_richiedente()
    nome_ric = ric.get("nome", "[NOME COGNOME]")
    pec_ric = ric.get("pec", "[PEC/EMAIL]")

    # Genera bozza e oggetto
    bozza = genera_bozza_foia(ente)
    ente_slug = ente.get("nome", ente_id).split("(")[0].strip()[:60]
    subject_flat = f"Richiesta accesso civico generalizzato -- Catalogo dati {ente_slug}"

    # HTML
    html_parts = []
    for line in bozza.split("\n"):
        s = line.strip()
        if not s:
            html_parts.append("<p>&nbsp;</p>")
        elif s.startswith("- ") and s.endswith(" -"):
            html_parts.append(f"<p><strong>{s.strip('- ')}</strong></p>")
        elif s.startswith(("- ", "a) ", "b) ", "c) ", "d) ", "e) ", "f) ", "g) ", "h) ", "i) ", "j) ", "k) ")):
            html_parts.append(f"<p>&nbsp;&nbsp;{s}</p>")
        elif s and s[0].isdigit() and ". " in s[:4]:
            html_parts.append(f"<p>{s}</p>")
        else:
            html_parts.append(f"<p>{s}</p>")
    html_content = "<html><body>\n" + "\n".join(html_parts) + "\n</body></html>"

    # CSV fonte unica
    csv_data = ALLEGATO_CSV.read_bytes() if ALLEGATO_CSV.exists() else None

    # .eml
    CRLF = "\r\n"
    b_mixed = "===============DATACIVICLAB_MIXED_BOUNDARY_1741559805=="
    b_alt = "===============DATACIVICLAB_ALT_BOUNDARY_1741559805=="

    lines = [
        f'From: {nome_ric} <{pec_ric}>',
        f'To: {ente["pec"]}',
        f'Subject: {subject_flat}',
        f'Date: {datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")}',
        'MIME-Version: 1.0',
        f'Content-Type: multipart/mixed; boundary="{b_mixed}"',
        '',
        f'--{b_mixed}',
        f'Content-Type: multipart/alternative; boundary="{b_alt}"',
        '',
        f'--{b_alt}',
        'Content-Type: text/plain; charset="utf-8"',
        'Content-Transfer-Encoding: 8bit',
        '',
        bozza,
        '',
        f'--{b_alt}',
        'Content-Type: text/html; charset="utf-8"',
        'Content-Transfer-Encoding: 8bit',
        '',
        html_content,
        '',
        f'--{b_alt}--',
        '',
    ]
    if csv_data:
        b64 = base64.b64encode(csv_data).decode("ascii")
        lines += [
            f'--{b_mixed}',
            'Content-Type: text/csv; charset="utf-8"',
            'Content-Transfer-Encoding: base64',
            f'Content-Disposition: attachment; filename="{ente_id}_catalogo.csv"',
            '',
            b64,
        ]
    lines += [f'--{b_mixed}--', '']

    eml_raw = CRLF.join(lines).replace("\r\n", "\n").replace("\n", "\r\n")
    out_path = BOZZE / f"{ente_id}.eml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(eml_raw, encoding="utf-8")

    print(f"\n📧 File EML: {out_path}")
    print(f"   Da: {pec_ric}  →  A: {ente['pec']}")
    print(f"   Oggetto: {subject_flat[:80]}...")
    print(f"   Allegato: {ente_id}_catalogo.csv (da data/allegato_catalogo.csv)")
    print(f"\n   ▶  Apri e invia. Poi: python foia.py --send {ente_id}")


# ── Email automation (SMTP/IMAP) ───────────────────────────────────────


def _env(key: str, default: str = "") -> str:
    """Legge variabile da .env (se esiste) o da os.environ."""
    env_path = REPO / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"'")
    return os.environ.get(key, default)


def cmd_send_now(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    """Invia .eml via SMTP Aruba PEC."""
    host = _env("SMTP_HOST")
    port = int(_env("SMTP_PORT", "465"))
    user = _env("SMTP_USER")
    pwd = _env("SMTP_PASS")

    if not all([host, user, pwd]):
        print("❌ Credenziali SMTP mancanti. Crea .env con SMTP_HOST, SMTP_USER, SMTP_PASS")
        return

    eml_path = BOZZE / f"{ente_id}.eml"
    if not eml_path.exists():
        print(f"❌ File .eml non trovato: {eml_path}. Genera con --eml {ente_id}")
        return

    msg_bytes = eml_path.read_bytes()
    ente = ente_per_id(enti, ente_id)
    dest = ente["pec"] if ente else ente_id

    import smtplib
    try:
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(user, pwd)
            s.sendmail(user, [dest], msg_bytes)
    except Exception as e:
        print(f"❌ Errore invio: {e}")
        return

    cmd_send(enti, tracker, ente_id)
    print(f"   ✅ Inviata via SMTP a {dest}")


def cmd_send_now_dcd(enti: list[dict], tracker: list[dict], ente_id: str) -> None:
    """Genera e invia DCD ad AgID via SMTP in un colpo solo."""
    # Genera .eml DCD
    cmd_dcd(enti, tracker, ente_id)

    # Invia via SMTP
    host = _env("SMTP_HOST")
    port = int(_env("SMTP_PORT", "465"))
    user = _env("SMTP_USER")
    pwd = _env("SMTP_PASS")
    if not all([host, user, pwd]):
        print("❌ SMTP non configurato. Crea .env")
        return

    eml_path = BOZZE / f"dcd_{ente_id}.eml"
    if not eml_path.exists():
        return

    import smtplib
    try:
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(user, pwd)
            s.sendmail(user, ["protocollo@pec.agid.gov.it"], eml_path.read_bytes())
    except Exception as e:
        print(f"❌ Errore invio DCD: {e}")
        return

    print(f"   ✅ DCD inviato a protocollo@pec.agid.gov.it")


def cmd_controlla(enti: list[dict], tracker: list[dict]) -> None:
    """Controlla la casella PEC via IMAP per nuove risposte."""
    host = _env("IMAP_HOST")
    port = int(_env("IMAP_PORT", "993"))
    user = _env("IMAP_USER")
    pwd = _env("IMAP_PASS")

    if not all([host, user, pwd]):
        host = _env("SMTP_HOST")
        user = _env("SMTP_USER")
        pwd = _env("SMTP_PASS")
        if not all([host, user, pwd]):
            print("❌ Credenziali IMAP mancanti. Crea .env")
            return

    import imaplib
    import email as em
    try:
        conn = imaplib.IMAP4_SSL(host, port, timeout=30)
        conn.login(user, pwd)
        conn.select("INBOX")
        status, data = conn.search(None, '(SUBJECT "Richiesta accesso civico")')
        if status != "OK" or not data[0]:
            print("📭 Nessuna nuova risposta FOIA trovata.")
            conn.logout()
            return

        ids = data[0].split()
        print(f"\n📬 Trovati {len(ids)} messaggi con oggetto FOIA:")

        for mid in ids[-10:]:  # ultimi 10
            status, data = conn.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
            msg = em.message_from_bytes(data[0][1])
            subj = msg["Subject"][:80] if msg["Subject"] else "(senza oggetto)"
            frm = msg["From"] if msg["From"] else "(mittente sconosciuto)"
            date_ = msg["Date"][:25] if msg["Date"] else ""

            # Cerca allegati
            allegati = 0
            for part in msg.walk():
                if part.get_filename():
                    allegati += 1

            print(f"  📧 {f'{frm[:40]}':40s} {subj[:60]:60s} {date_:20s} {'📎'+str(allegati) if allegati else ''}")

        conn.logout()
        print(f"\n   ▶  Per scaricare: usa --ricevi con --file")
    except Exception as e:
        print(f"❌ Errore IMAP: {e}")


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
    parser.add_argument("--ricevi", metavar="ID",
                      help="Salva risposta FOIA (CSF/allegato) e traccia")
    parser.add_argument("--file", metavar="PATH",
                      help="Percorso del file ricevuto (con --ricevi)")
    parser.add_argument("--status", choices=["ok", "parziale", "rifiutata", "ignorata"],
                      default="ok", help="Esito risposta (con --respond/--ricevi)")
    parser.add_argument("--report", action="store_true", help="Riepilogo campagna")
    parser.add_argument("--scadenze", action="store_true", help="Richieste scadute")
    parser.add_argument("--dcd", metavar="ID", help="Genera bozza DCD")
    parser.add_argument("--anac", metavar="ID", help="Genera bozza ANAC")
    parser.add_argument("--send-now", metavar="ID",
                      help="Invia .eml via SMTP (richiede .env)")
    parser.add_argument("--send-now-dcd", metavar="ID",
                      help="Genera e invia DCD ad AgID via SMTP")
    parser.add_argument("--controlla", action="store_true",
                      help="Controlla la casella PEC via IMAP per risposte")
    parser.add_argument("--lista", action="store_true", help="Lista enti con stato")
    parser.add_argument("--da-fare", action="store_true", help="Coda azioni pendenti")
    parser.add_argument("--import", dest="import_path", metavar="FILE",
                      help="Importa target FOIA da foia_targets.json (partecipate-monitor)")
    parser.add_argument("--eml", metavar="ID",
                      help="Genera file .eml pronto per client PEC")
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
    elif args.ricevi:
        if not args.file:
            print("❌ Usa --file per specificare il percorso del file ricevuto")
        else:
            cmd_ricevi(enti, tracker, args.ricevi, args.file, args.status, args.note)
    elif args.respond:
        cmd_respond(tracker, args.respond, args.status, args.note)
    elif args.scadenze:
       cmd_scadenze(enti, tracker)
    elif args.dcd:
       cmd_dcd(enti, tracker, args.dcd)
    elif args.send_now:
        cmd_send_now(enti, tracker, args.send_now)
    elif args.send_now_dcd:
        cmd_send_now_dcd(enti, tracker, args.send_now_dcd)
    elif args.controlla:
        cmd_controlla(enti, tracker)
    elif args.anac:
        cmd_anac(enti, tracker, args.anac)
    elif args.lista:
       cmd_lista(enti, tracker)
    elif args.da_fare:
       cmd_da_fare(enti, tracker)
    elif args.eml:
        cmd_eml(enti, tracker, args.eml)
    elif args.import_path:
        cmd_import(enti, args.import_path)
    else:
       parser.print_help()


if __name__ == "__main__":
    main()
