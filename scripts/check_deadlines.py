#!/usr/bin/env python3
"""Controllo giornaliero scadenze FOIA e proposte escalation.

Eseguito dal workflow daily-advocacy.yml per:
1. Verificare richieste FOIA con scadenza superata
2. Proporre escalation (RPCT / ANAC)
3. Aggiornare il registro
"""
from __future__ import annotations

import sys
from pathlib import Path

# Assume esecuzione dalla root del repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_advocacy.engine import FoiaEngine
from data_advocacy.registry.foia_registry import FoiaRegistry


def main():
    repo_root = Path(__file__).resolve().parent.parent
    registry_path = repo_root / "data" / "foia_registry.json"

    registry = FoiaRegistry(path=registry_path)
    registry.load()

    engine = FoiaEngine(registry)
    escalated = engine.check_escalation()

    if escalated:
        print("## Escalation automatiche proposte oggi")
        for msg in escalated:
            print(f"- {msg}")
    else:
        print("Nessuna escalation necessaria oggi.")

    # Stampa riepilogo
    stati = {}
    for r in registry.all:
        stati[r.stato.value] = stati.get(r.stato.value, 0) + 1

    print("\n## Riepilogo FOIA")
    for stato, count in sorted(stati.items()):
        print(f"- {stato}: {count}")


if __name__ == "__main__":
    main()
