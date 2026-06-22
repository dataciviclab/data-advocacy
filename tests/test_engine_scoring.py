"""Test per engine e scoring di data-advocacy."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from data_advocacy.engine import FoiaEngine
from data_advocacy.registry.foia_registry import FoiaRegistry, FoiaRequest, FoiaStatus
from data_advocacy.scoring import HealthScore


class TestFoiaEngine:
    """Macchina a stati FOIA: transizioni ed escalation."""

    def _make_registry(self, tmp_path) -> FoiaRegistry:
        p = tmp_path / "registry.json"
        reg = FoiaRegistry(path=p)
        reg.load()
        return reg

    @pytest.mark.contract
    def test_transizione_valida(self, tmp_path):
        reg = self._make_registry(tmp_path)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        reg.add(r)
        engine = FoiaEngine(reg)
        engine.transizione("F1", FoiaStatus.DRAFTING)
        assert r.stato == FoiaStatus.DRAFTING

    @pytest.mark.contract
    def test_transizione_non_valida(self, tmp_path):
        reg = self._make_registry(tmp_path)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        reg.add(r)
        engine = FoiaEngine(reg)
        with pytest.raises(ValueError, match="Transizione non valida"):
            engine.transizione("F1", FoiaStatus.SENT)  # IDLE → SENT non permesso

    @pytest.mark.contract
    def test_transizione_foia_inesistente(self, tmp_path):
        reg = self._make_registry(tmp_path)
        engine = FoiaEngine(reg)
        with pytest.raises(ValueError, match="non trovata"):
            engine.transizione("INEXISTENT", FoiaStatus.DRAFTING)

    @pytest.mark.policy
    def test_transizione_a_sent_imposta_data(self, tmp_path):
        reg = self._make_registry(tmp_path)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        r.stato = FoiaStatus.DRAFTING
        reg.add(r)
        engine = FoiaEngine(reg)
        engine.transizione("F1", FoiaStatus.SENT)
        assert r.stato == FoiaStatus.SENT
        assert r.data_invio is not None
        assert r.scadenza_risposta is not None
        assert r.scadenza_rpct is not None

    @pytest.mark.regression
    def test_check_escalation_nessuna_scaduta(self, tmp_path):
        reg = self._make_registry(tmp_path)
        oggi = date(2026, 7, 1)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        r.set_sent(oggi - timedelta(days=15))  # 15gg fa, non scaduta
        reg.add(r)
        engine = FoiaEngine(reg)
        escalated = engine.check_escalation(oggi)
        assert escalated == []

    @pytest.mark.policy
    def test_check_escalation_scaduta_30gg(self, tmp_path):
        """Policy: dopo 30gg senza risposta → waiting_response."""
        reg = self._make_registry(tmp_path)
        oggi = date(2026, 7, 1)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        r.set_sent(oggi - timedelta(days=35))  # 35gg fa, scaduta
        reg.add(r)
        engine = FoiaEngine(reg)
        escalated = engine.check_escalation(oggi)
        assert len(escalated) == 1
        assert "waiting_response" in escalated[0]
        assert r.stato == FoiaStatus.WAITING_RESPONSE

    @pytest.mark.policy
    def test_check_escalation_scaduta_50gg(self, tmp_path):
        """Policy: dopo 50gg senza risposta → escalation RPCT."""
        reg = self._make_registry(tmp_path)
        oggi = date(2026, 7, 1)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        r.set_sent(oggi - timedelta(days=60))  # 60gg fa
        # Porta prima a waiting_response
        r.stato = FoiaStatus.WAITING_RESPONSE
        r.scadenza_rpct = oggi - timedelta(days=10)  # RPCT scaduta 10gg fa
        reg.add(r)
        engine = FoiaEngine(reg)
        escalated = engine.check_escalation(oggi)
        assert len(escalated) == 1
        assert "RPCT" in escalated[0]
        assert r.stato == FoiaStatus.ESCALATION_RPCT


class TestHealthScore:
    """Modello HealthScore: totale, livello, azione."""

    @pytest.mark.pure_unit
    def test_totale_massimo(self):
        hs = HealthScore(
            source_id="test",
            formato_aperto=100,
            raggiungibilita=100,
            licenza_aperta=100,
            presenza_datigovit=100,
            hvd_compliance=100,
            accessibilita_foia=100,
        )
        assert hs.totale == 100.0

    @pytest.mark.pure_unit
    def test_totale_minimo(self):
        hs = HealthScore(source_id="test")
        assert hs.totale == 0.0

    @pytest.mark.pure_unit
    def test_totale_ponderato(self):
        """(80*3 + 70*2 + 50*1 + 60*2) / 12 = 68.3"""
        hs = HealthScore(
            source_id="test",
            formato_aperto=80,
            raggiungibilita=70,
            licenza_aperta=50,
            presenza_datigovit=60,
            hvd_compliance=0,
            accessibilita_foia=0,
        )
        expected = (80*3 + 70*2 + 50*1 + 60*2) / 12
        assert hs.totale == round(expected, 1)

    @pytest.mark.contract
    def test_livello_buono(self):
        hs = HealthScore(source_id="t", formato_aperto=100, raggiungibilita=100,
                         licenza_aperta=100, presenza_datigovit=80, hvd_compliance=100, accessibilita_foia=100)
        assert hs.livello == "buono"

    @pytest.mark.contract
    def test_livello_medio(self):
        # (90*3 + 80*2 + 70*1 + 80*2) / 12 = 660/12 = 55.0 → medio (≥55)
        hs = HealthScore(source_id="t", formato_aperto=90, raggiungibilita=80,
                         licenza_aperta=70, presenza_datigovit=80, hvd_compliance=0, accessibilita_foia=0)
        assert hs.livello == "medio"

    @pytest.mark.contract
    def test_livello_debole(self):
        # (45*3 + 40*2 + 30*1 + 30*2) / 12 = 305/12 ≈ 25.4 → debole (≥25)
        hs = HealthScore(source_id="t", formato_aperto=45, raggiungibilita=40,
                         licenza_aperta=30, presenza_datigovit=30, hvd_compliance=0, accessibilita_foia=0)
        assert hs.livello == "debole"

    @pytest.mark.contract
    def test_livello_carente(self):
        hs = HealthScore(source_id="t")
        assert hs.livello == "carente"

    @pytest.mark.policy
    def test_azione_monitoraggio(self):
        hs = HealthScore(source_id="t", formato_aperto=90, raggiungibilita=90,
                         licenza_aperta=80, presenza_datigovit=80, hvd_compliance=0, accessibilita_foia=0)
        assert hs.azione_raccomandata == "monitoraggio"

    @pytest.mark.policy
    def test_azione_verifica_umana(self):
        # totale=25.4 → debole, formato=45 (≥40) → DCD non scatta → verifica umana
        hs = HealthScore(source_id="t", formato_aperto=45, raggiungibilita=40,
                         licenza_aperta=30, presenza_datigovit=30, hvd_compliance=0, accessibilita_foia=0)
        assert hs.azione_raccomandata == "verifica umana"

    @pytest.mark.policy
    def test_azione_foia_dcd(self):
        hs = HealthScore(source_id="t",
                         formato_aperto=10, raggiungibilita=10,
                         licenza_aperta=10, presenza_datigovit=10,
                         hvd_compliance=0, accessibilita_foia=0)
        assert hs.azione_raccomandata == "FOIA + verifica DCD"

    @pytest.mark.policy
    def test_azione_dcd_formato_chiuso(self):
        hs = HealthScore(source_id="t", formato_aperto=30, raggiungibilita=80,
                         licenza_aperta=60, presenza_datigovit=60, hvd_compliance=0, accessibilita_foia=0)
        assert "DCD" in hs.azione_raccomandata

    @pytest.mark.contract
    def test_to_dict(self):
        hs = HealthScore(source_id="t", formato_aperto=80)
        d = hs.to_dict()
        assert d["source_id"] == "t"
        assert "totale" in d
        assert "livello" in d
        assert "azione_raccomandata" in d
