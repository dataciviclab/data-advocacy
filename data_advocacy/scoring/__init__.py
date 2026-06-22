"""Modello dati per health scores allineato al contratto di source-observatory.

ATTENZIONE: questo modulo NON e' usato dal generatore bozze (che consuma
direttamente gli health scores da SO via open_data_health_scores.json).
E' un modello consumer-side per eventuali elaborazioni locali.

Contratto (allineato a SO):
  assi:     formato_aperto, raggiungibilita, licenza_aperta,
            presenza_datigovit, hvd_compliance, accessibilita_foia
  livelli:  buono (>=80), medio (>=55), debole (>=25), carente (<25)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

_PESI: dict[str, int] = {
    "formato_aperto": 3,
    "raggiungibilita": 2,
    "licenza_aperta": 1,
    "presenza_datigovit": 2,
    "hvd_compliance": 3,
    "accessibilita_foia": 1,
}


@dataclass
class HealthScore:
    """Punteggio su 6 assi allineato al contratto SO."""

    source_id: str
    formato_aperto: float = 0.0
    raggiungibilita: float = 0.0
    licenza_aperta: float = 0.0
    presenza_datigovit: float = 0.0
    hvd_compliance: float = 0.0
    accessibilita_foia: float = 0.0

    @property
    def totale(self) -> float:
        """Punteggio ponderato su 100."""
        numeratore = sum(getattr(self, k) * v for k, v in _PESI.items())
        denominatore = sum(_PESI.values()) * 100
        return round((numeratore / denominatore) * 100, 1)

    @property
    def livello(self) -> str:
        t = self.totale
        if t >= 80:
            return "buono"
        elif t >= 55:
            return "medio"
        elif t >= 25:
            return "debole"
        return "carente"

    @property
    def azione_raccomandata(self) -> str:
        if self.livello == "carente":
            return "FOIA + verifica DCD"
        elif self.livello == "debole":
            return "verifica umana"
        elif self.totale < 70 and self.formato_aperto < 40:
            return "segnalazione DCD (formato chiuso — verificare)"
        elif self.totale < 70 and self.raggiungibilita < 30:
            return "verifica raggiungibilita'"
        return "monitoraggio"

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "totale": self.totale,
            "livello": self.livello,
            "azione_raccomandata": self.azione_raccomandata,
        }
