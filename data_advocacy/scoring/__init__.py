"""Modelli e logica per il compliance scoring delle fonti."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class ComplianceScore:
    """Punteggio compliance su 6 assi (0-100)."""

    source_id: str
    # A: Formato aperto (peso 3)
    formato_aperto: float = 0.0  # 0-100
    # B: Aggiornamento dati (peso 2)
    aggiornamento: float = 0.0  # 0-100
    # C: Licenza aperta (peso 1)
    licenza_aperta: float = 0.0  # 0-100
    # D: Presenza su dati.gov.it (peso 2)
    presenza_datigovit: float = 0.0  # 0-100
    # E: HVD compliance (peso 3)
    hvd_compliance: float = 0.0  # 0-100
    # F: Accessibilita' FOIA (peso 1)
    accessibilita_foia: float = 0.0  # 0-100

    # Pesi
    PESI: dict[str, int] = {
        "formato_aperto": 3,
        "aggiornamento": 2,
        "licenza_aperta": 1,
        "presenza_datigovit": 2,
        "hvd_compliance": 3,
        "accessibilita_foia": 1,
    }

    @property
    def totale(self) -> float:
        """Punteggio ponderato su 100."""
        numeratore = sum(
            getattr(self, k) * v for k, v in self.PESI.items()
        )
        denominatore = sum(self.PESI.values()) * 100
        return round((numeratore / denominatore) * 100, 1)

    @property
    def livello(self) -> str:
        """Label qualitativo."""
        t = self.totale
        if t >= 80:
            return "buono"
        elif t >= 50:
            return "medio"
        elif t >= 30:
            return "critico"
        else:
            return "gravemente_carente"

    @property
    def azione_raccomandata(self) -> str:
        """Azione suggerita in base al punteggio."""
        if self.totale < 30:
            return "FOIA + segnalazione DCD"
        elif self.totale < 50:
            return "FOIA"
        elif self.totale < 70 and self.formato_aperto < 50:
            return "segnalazione DCD (formato chiuso)"
        return "monitoraggio"

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "totale": self.totale,
            "livello": self.livello,
            "azione_raccomandata": self.azione_raccomandata,
        }
