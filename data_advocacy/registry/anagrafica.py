"""Modello dati per anagrafica enti pubblici e contatti FOIA."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Contatti:
    """Contatti per richieste FOIA a un ente."""

    urp_email: str = ""
    pec: str = ""
    rpct_email: str = ""
    urp_url: str = ""
    note: str = ""

    @property
    def has_pec(self) -> bool:
        return bool(self.pec)

    @property
    def has_urp(self) -> bool:
        return bool(self.urp_email)

    @property
    def can_send_foia(self) -> bool:
        """Per FOIA serve PEC o almeno URP email."""
        return self.has_pec or self.has_urp


@dataclass
class Ente:
    """Un ente pubblico."""

    source_id: str
    nome: str
    tipo: str = ""  # MINISTERO, REGIONE, COMUNE, ASL, ATENEO, AGENZIA, AUTORITA
    sito: str = ""
    contatti: Contatti = field(default_factory=Contatti)
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Ente":
        contatti = Contatti(**data.get("contatti", {}))
        return cls(
            source_id=data["source_id"],
            nome=data["nome"],
            tipo=data.get("tipo", ""),
            sito=data.get("sito", ""),
            contatti=contatti,
            note=data.get("note", ""),
        )


class Anagrafica:
    """Anagrafica degli enti pubblici monitorati/contattabili."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path("data/anagrafica_enti.json")
        self._enti: dict[str, Ente] = {}

    def load(self) -> None:
        if self.path.exists():
            import json
            raw = json.loads(self.path.read_text())
            self._enti = {e["source_id"]: Ente.from_dict(e) for e in raw}
        else:
            self._enti = {}

    def add(self, ente: Ente) -> None:
        self._enti[ente.source_id] = ente

    def get(self, source_id: str) -> Optional[Ente]:
        return self._enti.get(source_id)

    def search(self, query: str) -> list[Ente]:
        query = query.lower()
        return [e for e in self._enti.values() if query in e.nome.lower()]

    @property
    def all(self) -> list[Ente]:
        return list(self._enti.values())

    @property
    def contactabili(self) -> list[Ente]:
        return [e for e in self._enti.values() if e.contatti.can_send_foia]
