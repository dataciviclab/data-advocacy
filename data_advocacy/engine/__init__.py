"""Macchina a stati FOIA e gestione escalation."""

from __future__ import annotations

from datetime import date
from typing import Optional

from data_advocacy.registry.foia_registry import FoiaRegistry, FoiaStatus


class FoiaEngine:
    """Macchina a stati per il ciclo di vita delle richieste FOIA."""

    TRANSIZIONI = {
        FoiaStatus.IDLE: [FoiaStatus.DRAFTING],
        FoiaStatus.DRAFTING: [FoiaStatus.SENT, FoiaStatus.IDLE],
        FoiaStatus.SENT: [FoiaStatus.WAITING_RESPONSE, FoiaStatus.RESPONSE_RECEIVED],
        FoiaStatus.WAITING_RESPONSE: [
            FoiaStatus.RESPONSE_RECEIVED,
            FoiaStatus.ESCALATION_RPCT,
        ],
        FoiaStatus.ESCALATION_RPCT: [
            FoiaStatus.RESPONSE_RECEIVED,
            FoiaStatus.ESCALATION_ANAC,
            FoiaStatus.RESOLVED,
        ],
        FoiaStatus.ESCALATION_ANAC: [FoiaStatus.RESPONSE_RECEIVED, FoiaStatus.RESOLVED],
        FoiaStatus.RESPONSE_RECEIVED: [FoiaStatus.RESOLVED],
        FoiaStatus.RESOLVED: [],
        FoiaStatus.IGNORED: [],
    }

    def __init__(self, registry: FoiaRegistry):
        self.registry = registry

    def transizione(self, foia_id: str, nuovo_stato: FoiaStatus) -> None:
        """Muove una richiesta a un nuovo stato, se la transizione e' valida."""
        req = self.registry.get(foia_id)
        if req is None:
            raise ValueError(f"FOIA {foia_id} non trovata")

        if nuovo_stato not in self.TRANSIZIONI.get(req.stato, []):
            raise ValueError(
                f"Transizione non valida: {req.stato.value} -> {nuovo_stato.value}"
            )

        req.stato = nuovo_stato

        # Side-effect: se inviato, registra data e scadenze
        if nuovo_stato == FoiaStatus.SENT and req.data_invio is None:
            req.set_sent(date.today())

        self.registry.save()

    def check_escalation(self, oggi: Optional[date] = None) -> list[str]:
        """Trova FOIA scadute e propone escalation."""
        oggi = oggi or date.today()
        escalated: list[str] = []

        for req in self.registry.list_overdue(oggi):
            if req.stato == FoiaStatus.SENT:
                self.transizione(req.id, FoiaStatus.WAITING_RESPONSE)
                escalated.append(
                    f"{req.id}: superata scadenza 30gg -> waiting_response"
                )
            elif req.stato == FoiaStatus.WAITING_RESPONSE and req.scadenza_rpct and req.scadenza_rpct < oggi:
                self.transizione(req.id, FoiaStatus.ESCALATION_RPCT)
                escalated.append(
                    f"{req.id}: superata scadenza 50gg -> escalation RPCT"
                )

        return escalated
