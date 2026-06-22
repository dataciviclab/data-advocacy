"""Modello dati per il registro delle richieste FOIA."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


class FoiaStatus(str, Enum):
    """Stati possibili di una richiesta FOIA."""

    IDLE = "idle"
    DRAFTING = "drafting"
    SENT = "sent"
    WAITING_RESPONSE = "waiting_response"
    RESPONSE_RECEIVED = "response_received"
    ESCALATION_RPCT = "escalation_rpct"
    ESCALATION_ANAC = "escalation_anac"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class FoiaRequest:
    """Una singola richiesta FOIA."""

    id: str
    ente: str
    source_id: str
    dataset: str
    trigger: str
    stato: FoiaStatus = FoiaStatus.IDLE
    data_invio: Optional[date] = None
    scadenza_risposta: Optional[date] = None
    scadenza_rpct: Optional[date] = None
    template_usato: str = "foia_standard"
    note: str = ""
    evidenze: list[str] = field(default_factory=list)

    def set_sent(self, data_invio: date) -> None:
        """Registra l'invio e calcola scadenze."""
        self.stato = FoiaStatus.SENT
        self.data_invio = data_invio
        self.scadenza_risposta = data_invio + timedelta(days=30)
        self.scadenza_rpct = data_invio + timedelta(days=50)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FoiaRequest":
        stato = FoiaStatus(data["stato"])
        data_invio = (
            date.fromisoformat(data["data_invio"]) if data.get("data_invio") else None
        )
        scadenza_risposta = (
            date.fromisoformat(data["scadenza_risposta"])
            if data.get("scadenza_risposta")
            else None
        )
        scadenza_rpct = (
            date.fromisoformat(data["scadenza_rpct"])
            if data.get("scadenza_rpct")
            else None
        )
        return cls(
            id=data["id"],
            ente=data["ente"],
            source_id=data["source_id"],
            dataset=data["dataset"],
            trigger=data["trigger"],
            stato=stato,
            data_invio=data_invio,
            scadenza_risposta=scadenza_risposta,
            scadenza_rpct=scadenza_rpct,
            template_usato=data.get("template_usato", "foia_standard"),
            note=data.get("note", ""),
            evidenze=data.get("evidenze", []),
        )


class FoiaRegistry:
    """Registro centralizzato delle richieste FOIA."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path("data/foia_registry.json")
        self._requests: dict[str, FoiaRequest] = {}

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._requests = {r["id"]: FoiaRequest.from_dict(r) for r in raw}
        else:
            self._requests = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = [r.to_dict() for r in self._requests.values()]
        self.path.write_text(json.dumps(raw, indent=2, default=str))

    def add(self, request: FoiaRequest) -> None:
        self._requests[request.id] = request

    def get(self, foia_id: str) -> Optional[FoiaRequest]:
        return self._requests.get(foia_id)

    def list_by_status(self, status: FoiaStatus) -> list[FoiaRequest]:
        return [r for r in self._requests.values() if r.stato == status]

    def list_overdue(self, today: Optional[date] = None) -> list[FoiaRequest]:
        """Richieste la cui scadenza risposta e' passata senza aggiornamento."""
        today = today or date.today()
        return [
            r
            for r in self._requests.values()
            if r.stato in (FoiaStatus.SENT, FoiaStatus.WAITING_RESPONSE)
            and r.scadenza_risposta
            and r.scadenza_risposta < today
        ]

    @property
    def all(self) -> list[FoiaRequest]:
        return list(self._requests.values())
