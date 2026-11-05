#!/usr/bin/env python3
"""registro.py — log condiviso delle richieste FOIA (campagna Layer 2).

Modello (vedi README):
  Target     = Issue GitHub: il dataset individuato + l'evidenza del difetto.
  Richiesta  = un file JSON in richieste/<target>/<data_invio>_<richiedente>.json,
               un file per ogni PEC inviata (append-only, nessun conflitto).
  Registro   = REGISTRO.md, generato da questo script. Mai editato a mano.

L'identità del richiedente resta locale (richiedente.json, non versionato):
nel log pubblico compare solo un'etichetta anonima (es. "01").

Uso:
  python registro.py nuova <target> [--issue N] [--richiedente 01] [--data AAAA-MM-GG]
  python registro.py risposta <target>/<file> --esito ok|parziale|rifiutata|ignorata [--protocollo ...]
  python registro.py escalation <target>/<file> rpct|anac
  python registro.py nota <target>/<file> "testo nota"
  python registro.py lista
  python registro.py mio <richiedente>
  python registro.py scadenze
  python registro.py build
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent
RICHIESTE = REPO / "richieste"
REGISTRO = REPO / "REGISTRO.md"
RICHIEDENTE_LOCALE = REPO / "richiedente.json"

TERMINE_RISPOSTA = 30
ESITI = ("ok", "parziale", "rifiutata", "ignorata")
ESCALATION = ("none", "rpct", "anac")


# ── Record ────────────────────────────────────────────────────────────────


def slug_target(nome: str) -> str:
    """Normalizza un target in uno slug usabile come nome di cartella."""
    s = nome.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def percorso_record(
    target: str, data_invio: str, richiedente: str, base: Path = RICHIESTE
) -> Path:
    return base / slug_target(target) / f"{data_invio}_{richiedente}.json"


def record_nuovo(
    target: str,
    *,
    issue: int | None = None,
    richiedente: str = "01",
    data_invio: str | None = None,
    scadenza: str | None = None,
    base: Path = RICHIESTE,
) -> Path:
    """Crea un record per una PEC inviata. Rifiuta duplicati identici."""
    data_invio = data_invio or date.today().isoformat()
    if scadenza is None:
        scadenza = (
            date.fromisoformat(data_invio) + timedelta(days=TERMINE_RISPOSTA)
        ).isoformat()
    rec = {
        "target": slug_target(target),
        "issue": issue,
        "richiedente": richiedente,
        "data_invio": data_invio,
        "scadenza": scadenza,
        "protocollo": None,
        "data_risposta": None,
        "esito": None,
        "escalation": "none",
        "note": "",
    }
    path = percorso_record(target, data_invio, richiedente, base)
    if path.exists():
        raise FileExistsError(f"Record già esistente: {path}")
    salva_record(path, rec)
    return path


def salva_record(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")


def carica_record(path: Path) -> dict:
    return json.loads(path.read_text())


def aggiorna_record(path: Path, **updates) -> dict:
    rec = carica_record(path)
    rec.update(updates)
    salva_record(path, rec)
    return rec


def risolvi_record(key: str, base: Path = RICHIESTE) -> Path:
    """Accetta un path, oppure 'target/file' (con o senza .json)."""
    p = Path(key)
    if p.is_file():
        return p
    for cand in (base / key, base / f"{key}.json"):
        if cand.is_file():
            return cand
    raise FileNotFoundError(f"Record non trovato: {key}")


def carica_tutti(base: Path = RICHIESTE) -> list[tuple[Path, dict]]:
    """Tutti i record, ordinati per data invio (più recenti prima)."""
    out: list[tuple[Path, dict]] = []
    if not base.exists():
        return out
    for p in sorted(base.glob("*/*.json")):
        try:
            out.append((p, carica_record(p)))
        except json.JSONDecodeError:
            print(f"⚠️  Record illeggibile, saltato: {p}", file=sys.stderr)
    out.sort(
        key=lambda t: (t[1].get("data_invio") or "", t[1].get("target") or ""),
        reverse=True,
    )
    return out


# ── Statistiche e registro ─────────────────────────────────────────────────


def statistiche(records: list[tuple[Path, dict]]) -> dict:
    return {
        "totale": len(records),
        "risposte": sum(1 for _, r in records if r.get("esito")),
        "consegne": sum(1 for _, r in records if r.get("esito") == "ok"),
        "rigetti": sum(1 for _, r in records if r.get("esito") == "rifiutata"),
        "escalation": sum(
            1 for _, r in records if r.get("escalation") not in (None, "none")
        ),
    }


def _riga_registro(r: dict) -> str:
    issue = f"#{r['issue']}" if r.get("issue") else "—"
    esito = r.get("esito") or "in attesa"
    esc = r.get("escalation") or "none"
    esc = "—" if esc == "none" else esc.upper()
    return (
        f"| {r.get('target', '—')} | {issue} | {r.get('data_invio', '—')} "
        f"| {r.get('richiedente', '—')} | {r.get('scadenza', '—')} "
        f"| {esito} | {esc} | {r.get('protocollo') or '—'} |"
    )


def build_registro(base: Path = RICHIESTE) -> str:
    records = carica_tutti(base)
    s = statistiche(records)
    righe = [
        "# Registro FOIA — richieste inviate",
        "",
        f"_Generato: {date.today().isoformat()} · {s['totale']} richieste_",
        "",
        f"- **Inviate**: {s['totale']}",
        f"- **Risposte**: {s['risposte']}",
        f"- **Consegne** (`ok`): {s['consegne']}",
        f"- **Rigetti**: {s['rigetti']}",
        f"- **Escalation**: {s['escalation']}",
        "",
        "| Target | Issue | Data invio | Richiedente | Scadenza | Esito | Escalation | Protocollo |",
        "|---|---|---|---|---|---|---|---|",
    ]
    righe += [_riga_registro(r) for _, r in records]
    return "\n".join(righe) + "\n"


def scadenze(records: list[tuple[Path, dict]], oggi: date | None = None) -> list[tuple[Path, dict]]:
    """Richieste senza esito, oltre la scadenza e non ancora escalate."""
    oggi = oggi or date.today()
    out = []
    for p, r in records:
        scad = r.get("scadenza")
        if not scad or r.get("esito") or r.get("escalation") not in (None, "none"):
            continue
        if scad < oggi.isoformat():
            out.append((p, r))
    return out


# ── Comandi ────────────────────────────────────────────────────────────────


def cmd_nuova(args: argparse.Namespace) -> None:
    richiedente = args.richiedente or _richiedente_locale()
    try:
        path = record_nuovo(
            args.arg,
            issue=args.issue,
            richiedente=richiedente,
            data_invio=args.data,
        )
    except FileExistsError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    rec = carica_record(path)
    print(f"✅ Richiesta registrata: {path}")
    print(f"   Target: {rec['target']}  ·  richiedente {rec['richiedente']}")
    print(f"   Inviata: {rec['data_invio']}  ·  scadenza risposta: {rec['scadenza']}")
    print("   ▶  Quando arriva la risposta: python registro.py risposta "
          f"{rec['target']}/{path.name} --esito ok")


def cmd_risposta(args: argparse.Namespace) -> None:
    if not args.esito:
        print("❌ Usa --esito ok|parziale|rifiutata|ignorata", file=sys.stderr)
        sys.exit(1)
    try:
        path = risolvi_record(args.arg)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    rec = carica_record(path)
    updates: dict = {
        "esito": args.esito,
        "data_risposta": date.today().isoformat(),
    }
    if args.protocollo:
        updates["protocollo"] = args.protocollo
    if args.note:
        updates["note"] = args.note
    rec = aggiorna_record(path, **updates)
    print(f"✅ {rec['target']} ({path.name}): esito '{args.esito}' registrato")
    if args.esito == "rifiutata":
        print("   ▶  Valuta riesame RPCT: python registro.py escalation "
              f"{rec['target']}/{path.name} rpct")


def cmd_escalation(args: argparse.Namespace) -> None:
    tipo = (args.arg2 or "").lower()
    if tipo not in ("rpct", "anac"):
        print("❌ Specifica 'rpct' o 'anac'", file=sys.stderr)
        sys.exit(1)
    try:
        path = risolvi_record(args.arg)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    rec = carica_record(path)
    rec = aggiorna_record(path, escalation=tipo)
    print(f"✅ {rec['target']} ({path.name}): escalation {tipo.upper()} registrata")


def cmd_nota(args: argparse.Namespace) -> None:
    testo = args.note or args.arg2
    if not testo:
        print('❌ Usa: registro.py nota <target>/<file> "testo"', file=sys.stderr)
        sys.exit(1)
    try:
        path = risolvi_record(args.arg)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    rec = aggiorna_record(path, note=testo)
    print(f"✅ {rec['target']} ({path.name}): nota aggiornata")


def cmd_lista(args: argparse.Namespace) -> None:
    records = carica_tutti()
    if args.arg:
        records = [(p, r) for p, r in records if r.get("richiedente") == args.arg]
    if not records:
        print("Nessuna richiesta registrata.")
        return
    print(f"\n{'='*72}")
    print(f"  RICHIESTE ({len(records)})")
    print(f"{'='*72}")
    for _, r in records:
        print(
            f"  {r.get('target', '?'):28s} {r.get('data_invio', '?'):11s} "
            f"rich.{r.get('richiedente', '?'):3s} "
            f"esito={r.get('esito') or 'in attesa':10s} "
            f"esc={r.get('escalation', 'none')}"
        )
    print()


def cmd_scadenze(_args: argparse.Namespace) -> None:
    scadute = scadenze(carica_tutti())
    if not scadute:
        print("\n✅ Nessuna richiesta scaduta.\n")
        return
    print(f"\n{'='*72}")
    print(f"  SCADUTE ({len(scadute)})")
    print(f"{'='*72}")
    for p, r in scadute:
        print(f"\n  ⏰ {r.get('target')} — {p.name}")
        print(f"     Inviata {r.get('data_invio')}  ·  scaduta {r.get('scadenza')}")
        print(f"     ▶  python registro.py escalation {r.get('target')}/{p.name} rpct")
    print()


def cmd_build(_args: argparse.Namespace) -> None:
    REGISTRO.write_text(build_registro())
    print(f"✅ Registro aggiornato: {REGISTRO}")


def _richiedente_locale() -> str:
    if RICHIEDENTE_LOCALE.exists():
        try:
            data = json.loads(RICHIEDENTE_LOCALE.read_text())
            return str(data.get("id", "01"))
        except json.JSONDecodeError:
            pass
    return "01"


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Log condiviso delle richieste FOIA")
    parser.add_argument(
        "comando",
        choices=["nuova", "risposta", "escalation", "nota", "lista", "mio", "scadenze", "build"],
    )
    parser.add_argument("arg", nargs="?", help="target (nuova) o record (risposta/escalation)")
    parser.add_argument("arg2", nargs="?", help="rpct|anac (escalation)")
    parser.add_argument("--issue", type=int, help="numero della Issue GitHub (target)")
    parser.add_argument("--richiedente", help="etichetta anonima (default: da richiedente.json)")
    parser.add_argument("--data", help="data invio AAAA-MM-GG (default: oggi)")
    parser.add_argument("--esito", choices=ESITI, help="esito della risposta")
    parser.add_argument("--protocollo", help="numero di protocollo della risposta")
    parser.add_argument("--note", default="", help="nota libera")
    args = parser.parse_args()

    if args.comando == "nuova":
        if not args.arg:
            parser.error("'nuova' richiede un target")
        cmd_nuova(args)
    elif args.comando == "risposta":
        cmd_risposta(args)
    elif args.comando == "escalation":
        cmd_escalation(args)
    elif args.comando == "nota":
        cmd_nota(args)
    elif args.comando in ("lista", "mio"):
        cmd_lista(args)
    elif args.comando == "scadenze":
        cmd_scadenze(args)
    elif args.comando == "build":
        cmd_build(args)


if __name__ == "__main__":
    main()
