"""Modello dati per anagrafica enti pubblici e contatti FOIA."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Contatti:
    """Contatti per richieste FOIA a un ente."""

    urp_email: str = ""
    pec: str = ""  # PEC (diretta o promossa da ipa_pec in from_dict)
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
        raw_contatti = data.get("contatti", {})
        # Promuove ipa_pec a pec se la PEC diretta non è valorizzata —
        # IPA è la fonte ufficiale per i contatti della PA.
        if not raw_contatti.get("pec") and raw_contatti.get("ipa_pec"):
            raw_contatti["pec"] = raw_contatti["ipa_pec"]
        # Filtra solo i campi del dataclass (ignora ipa_pec/altri residui JSON)
        contatti_kw = {
            k: v for k, v in raw_contatti.items()
            if k in Contatti.__dataclass_fields__
        }
        contatti = Contatti(**contatti_kw)
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
