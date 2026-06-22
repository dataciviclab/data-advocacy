"""Test per il registry FOIA e anagrafica."""
from __future__ import annotations

from datetime import date, timedelta
import pytest

from data_advocacy.registry.foia_registry import FoiaRequest, FoiaStatus, FoiaRegistry
from data_advocacy.registry.anagrafica import Ente, Contatti, Anagrafica


class TestFoiaRequest:
    def test_set_sent_calcola_scadenze(self):
        r = FoiaRequest(id="FOIA-001", ente="MIT", source_id="mit", dataset="incidenti", trigger="radar_red")
        r.set_sent(date(2026, 6, 1))
        assert r.stato == FoiaStatus.SENT
        assert r.data_invio == date(2026, 6, 1)
        assert r.scadenza_risposta == date(2026, 7, 1)
        assert r.scadenza_rpct == date(2026, 7, 21)

    def test_serde_ciclo(self):
        r = FoiaRequest(id="FOIA-002", ente="Salute", source_id="salute", dataset="spesa_sanitaria", trigger="compliance_low")
        r.set_sent(date(2026, 5, 15))
        d = r.to_dict()
        r2 = FoiaRequest.from_dict(d)
        assert r2.id == r.id
        assert r2.stato == r.stato
        assert r2.data_invio == r.data_invio
        assert r2.scadenza_risposta == r.scadenza_risposta


class TestFoiaRegistry:
    def test_list_overdue(self, tmp_path):
        p = tmp_path / "registry.json"
        reg = FoiaRegistry(path=p)

        oggi = date(2026, 7, 1)

        # Non scaduta (inviata ieri)
        r1 = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        r1.set_sent(oggi - timedelta(days=29))
        reg.add(r1)

        # Scaduta (inviata 35gg fa)
        r2 = FoiaRequest(id="F2", ente="E2", source_id="s2", dataset="d2", trigger="t2")
        r2.set_sent(oggi - timedelta(days=35))
        reg.add(r2)

        overdue = reg.list_overdue(oggi)
        assert len(overdue) == 1
        assert overdue[0].id == "F2"

    def test_save_load(self, tmp_path):
        p = tmp_path / "registry.json"
        reg = FoiaRegistry(path=p)
        r = FoiaRequest(id="F1", ente="E1", source_id="s1", dataset="d1", trigger="t1")
        reg.add(r)
        reg.save()

        reg2 = FoiaRegistry(path=p)
        reg2.load()
        assert reg2.get("F1") is not None
        assert reg2.get("F1").ente == "E1"


class TestAnagrafica:
    def test_ente_con_contatti(self):
        c = Contatti(pec="protocollo@pec.mit.gov.it", urp_email="urp@mit.gov.it")
        e = Ente(source_id="mit", nome="Ministero delle Infrastrutture", tipo="MINISTERO", contatti=c)
        assert e.contatti.can_send_foia is True
        assert e.contatti.has_pec is True

    def test_ente_senza_contatti(self):
        e = Ente(source_id="sconosciuto", nome="Ente Sconosciuto")
        assert e.contatti.can_send_foia is False

    def test_search(self):
        a = Anagrafica()
        a.add(Ente(source_id="mit", nome="Ministero delle Infrastrutture e Trasporti"))
        a.add(Ente(source_id="salute", nome="Ministero della Salute"))
        results = a.search("infrastrutture")
        assert len(results) == 1
        assert results[0].source_id == "mit"


class TestTransizioni:
    """Test per i marker standard del Lab."""
    @pytest.mark.contract
    def test_foiarequest_to_dict_keys(self):
        r = FoiaRequest(id="T1", ente="E", source_id="s", dataset="d", trigger="t")
        d = r.to_dict()
        assert "id" in d
        assert "ente" in d
        assert "stato" in d
        assert "data_invio" in d

    @pytest.mark.policy
    def test_scadenza_30gg(self):
        """Policy: 30 giorni per risposta FOIA ex art. 5 D.Lgs 33/2013."""
        r = FoiaRequest(id="T2", ente="E", source_id="s", dataset="d", trigger="t")
        r.set_sent(date(2026, 1, 1))
        assert r.scadenza_risposta == date(2026, 1, 31)
