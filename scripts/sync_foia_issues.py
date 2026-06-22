#!/usr/bin/env python3
"""
Sincronizza FOIA registry → GitHub Issues + Project Board.

Legge data/foia_registry.json e per ogni richiesta FOIA:
  1. Cerca issue esistente (label foia, titolo contiene ID)
  2. Se non esiste → crea issue
  3. Se esiste → aggiorna body
  4. Aggiunge/alimenta i campi del Project Board #7

Utilizzo:
    python scripts/sync_foia_issues.py
    python scripts/sync_foia_issues.py --dry-run  # solo stampa, nessuna creazione

Dipende da: gh CLI autenticata (GITHUB_TOKEN o gh auth)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = "dataciviclab/data-advocacy"
PROJECT_NUMBER = 7
PROJECT_ID = "PVT_kwDOD0_YgM4BbWWj"
PROJECT_OWNER = "dataciviclab"

# ── Project field IDs (recuperati con gh project field-list --format json) ──
FIELD = {
    "source_id": "PVTF_lADOD0_YgM4BbWWjzhWHdWY",
    "ente": "PVTF_lADOD0_YgM4BbWWjzhWHdWU",
    "scadenza": "PVTF_lADOD0_YgM4BbWWjzhWHdWc",
    "trigger": "PVTSSF_lADOD0_YgM4BbWWjzhWHdYM",
    "stato_foia": "PVTSSF_lADOD0_YgM4BbWWjzhWHdZE",
}

OPTIONS = {
    "trigger": {
        "radar_red": "dfd99b95",
        "compliance_low": "4640fee7",
        "ssl": "16cfed24",
        "formato_chiuso": "be6a563f",
        "verifica_umana": "104c6aca",
    },
    "stato_foia": {
        "idle": "41c61e8b",
        "drafting": "09fcc6ef",
        "sent": "df99a6f7",
        "waiting_response": "676b5d79",
        "response_received": "f75cd041",
        "escalation_rpct": "df6a9e4f",
        "escalation_anac": "971880ca",
        "resolved": "0ded892b",
        "ignored": "33d25a01",
    },
}

# Label FOIA → option ID
TRIGGER_MAP = {
    "radar_red": "radar_red",
    "radar RED persistente": "radar_red",
    "compliance_low": "compliance_low",
    "compliance score basso": "compliance_low",
    "ssl": "ssl",
    "SSL non verificato": "ssl",
    "formato_chiuso": "formato_chiuso",
    "Formato chiuso": "formato_chiuso",
    "verifica_umana": "verifica_umana",
    "Verifica umana": "verifica_umana",
}

STATUS_MAP = {
    "idle": "idle",
    "drafting": "drafting",
    "sent": "sent",
    "waiting_response": "waiting_response",
    "response_received": "response_received",
    "escalation_rpct": "escalation_rpct",
    "escalation_anac": "escalation_anac",
    "resolved": "resolved",
    "ignored": "ignored",
}


def _gh(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    """Esegue un comando gh e ritorna il risultato."""
    cmd = ["gh"] + list(args)
    return subprocess.run(
        cmd, capture_output=True, text=True, input=stdin, check=False
    )


def _issue_title(req: dict) -> str:
    return f"[FOIA] {req['id']} — {req['ente']}"


def _issue_body(req: dict) -> str:
    lines = [
        f"**Richiesta**: {req['id']}",
        f"**Ente**: {req['ente']}",
        f"**Dataset**: {req.get('dataset', '—')}",
        f"**Trigger**: {req.get('trigger', '—')}",
        f"**Stato**: {req.get('stato', 'idle')}",
        "",
    ]
    if req.get("data_invio"):
        lines.append(f"**Data invio**: {req['data_invio']}")
    if req.get("scadenza_risposta"):
        lines.append(f"**Scadenza risposta**: {req['scadenza_risposta']} (30gg)")
    if req.get("scadenza_rpct"):
        lines.append(f"**Scadenza RPCT**: {req['scadenza_rpct']} (50gg)")
    if req.get("note"):
        lines.append(f"\n**Note**: {req['note']}")
    return "\n".join(lines)


def _trova_issue_esistente(foia_id: str) -> int | None:
    """Cerca issue aperta con label foia e ID nel titolo."""
    result = _gh(
        "issue", "list",
        "--repo", REPO,
        "--label", "foia",
        "--state", "open",
        "--json", "number,title",
        "--limit", "50",
    )
    if result.returncode != 0:
        print(f"⚠️  gh issue list fallito: {result.stderr.strip()}")
        return None
    issues = json.loads(result.stdout)
    for i in issues:
        if foia_id in i["title"]:
            return i["number"]
    return None


def _crea_issue(title: str, body: str) -> str | None:
    """Crea issue e ritorna URL."""
    result = _gh(
        "issue", "create",
        "--repo", REPO,
        "--title", title,
        "--label", "foia",
        "--body", body,
    )
    if result.returncode != 0:
        print(f"❌ Creazione issue fallita: {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def _aggiorna_issue(numero: int, body: str) -> bool:
    """Aggiorna body di issue esistente."""
    result = _gh("issue", "edit", str(numero), "--repo", REPO, "--body", body)
    if result.returncode != 0:
        print(f"⚠️  aggiornamento issue #{numero} fallito: {result.stderr.strip()}")
        return False
    return True


def _aggiungi_al_project(issue_url: str) -> str | None:
    """Aggiunge issue al Project Board. Ritorna item ID."""
    result = _gh(
        "project", "item-add", str(PROJECT_NUMBER),
        "--owner", PROJECT_OWNER,
        "--url", issue_url,
        "--format", "json",
    )
    if result.returncode != 0:
        print(f"⚠️  aggiunta al project fallita: {result.stderr.strip()}")
        return None
    data = json.loads(result.stdout)
    return data.get("id")


def _aggiorna_campi_project(
    item_id: str, req: dict
) -> None:
    """Aggiorna i campi custom dell'item nel Project."""
    # Source ID
    _gh(
        "project", "item-edit",
        "--id", item_id,
        "--project-id", PROJECT_ID,
        "--field-id", FIELD["source_id"],
        "--text", req.get("source_id", ""),
    )
    # Ente
    _gh(
        "project", "item-edit",
        "--id", item_id,
        "--project-id", PROJECT_ID,
        "--field-id", FIELD["ente"],
        "--text", req.get("ente", ""),
    )
    # Scadenza
    scadenza = req.get("scadenza_risposta")
    if scadenza:
        _gh(
            "project", "item-edit",
            "--id", item_id,
            "--project-id", PROJECT_ID,
            "--field-id", FIELD["scadenza"],
            "--date", scadenza,
        )
    # Trigger
    trigger_raw = req.get("trigger", "").lower()
    trigger_key = TRIGGER_MAP.get(trigger_raw) or TRIGGER_MAP.get(
        req.get("trigger", ""), "verifica_umana"
    )
    opt_id = OPTIONS["trigger"].get(trigger_key)
    if opt_id:
        _gh(
            "project", "item-edit",
            "--id", item_id,
            "--project-id", PROJECT_ID,
            "--field-id", FIELD["trigger"],
            "--single-select-option-id", opt_id,
        )
    # Stato FOIA
    stato_raw = req.get("stato", "idle").lower()
    stato_key = STATUS_MAP.get(stato_raw, "idle")
    opt_id = OPTIONS["stato_foia"].get(stato_key)
    if opt_id:
        _gh(
            "project", "item-edit",
            "--id", item_id,
            "--project-id", PROJECT_ID,
            "--field-id", FIELD["stato_foia"],
            "--single-select-option-id", opt_id,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincronizza FOIA registry → Issue + Board"
    )
    parser.add_argument(
        "--registry",
        default=Path(__file__).resolve().parent.parent / "data" / "foia_registry.json",
        type=Path,
        help="Path a foia_registry.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo stampa, nessuna creazione/modifica",
    )
    args = parser.parse_args()

    if not args.registry.exists():
        print(f"⚠️  Registry non trovato: {args.registry} — nessuna issue da sincronizzare.")
        return

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    if not registry:
        print("⚠️  Registry vuoto.")
        return

    print(f"📋 Sincronizzazione {len(registry)} richieste FOIA...")

    for req in registry:
        foia_id = req.get("id", "?")
        title = _issue_title(req)
        body = _issue_body(req)

        if args.dry_run:
            print(f"\n  [DRY RUN] {title}")
            print(f"    Body: {body[:80]}...")
            continue

        # Cerca issue esistente
        numero = _trova_issue_esistente(foia_id)

        if numero is None:
            # Crea nuova issue
            url = _crea_issue(title, body)
            if not url:
                print(f"  ❌ {foia_id}: creazione fallita")
                continue
            print(f"  ✅ {foia_id}: issue creata → {url}")

            # Aggiungi al project
            item_id = _aggiungi_al_project(url)
            if item_id:
                _aggiorna_campi_project(item_id, req)
                print("     aggiunta al project con campi custom")
        else:
            # Aggiorna issue esistente
            _aggiorna_issue(numero, body)
            print(f"  🔄 {foia_id}: issue #{numero} aggiornata")

            # Riaggiungi al project (se non gia' presente, no-op)
            issue_url = f"https://github.com/{REPO}/issues/{numero}"
            item_id = _aggiungi_al_project(issue_url)
            if item_id:
                _aggiorna_campi_project(item_id, req)

    print("\n✅ Sincronizzazione completata.")


if __name__ == "__main__":
    main()
