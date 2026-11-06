"""Test per registro.py — log condiviso delle richieste FOIA.

Contratto protetto: forma del record, scadenza a 30gg, registro derivato,
regola di escalation sulle richieste scadute non esitate.
"""

import argparse
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("registro", REPO / "registro.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


registro = _load()


@pytest.mark.contract
def test_nuova_crea_record(tmp_path):
    p = registro.record_nuovo(
        "ART D15", issue=19, richiedente="01", data_invio="2026-11-03", base=tmp_path
    )
    assert p.exists()
    rec = json.loads(p.read_text())
    assert rec["target"] == "art_d15"
    assert rec["issue"] == 19
    assert rec["esito"] is None
    assert rec["escalation"] == "none"
    assert rec["scadenza"] == "2026-12-03"  # data invio + 30gg


@pytest.mark.policy
def test_nuova_rifiuta_duplicato(tmp_path):
    registro.record_nuovo("art_d15", data_invio="2026-11-03", base=tmp_path)
    with pytest.raises(FileExistsError):
        registro.record_nuovo("art_d15", data_invio="2026-11-03", base=tmp_path)


@pytest.mark.contract
def test_aggiorna_record_esito(tmp_path):
    p = registro.record_nuovo("art_d15", data_invio="2026-11-03", base=tmp_path)
    registro.aggiorna_record(p, esito="rifiutata", protocollo="0053634/2026")
    rec = json.loads(p.read_text())
    assert rec["esito"] == "rifiutata"
    assert rec["protocollo"] == "0053634/2026"


@pytest.mark.contract
def test_build_registro_contiene_target(tmp_path):
    registro.record_nuovo("art_d15", issue=19, data_invio="2026-11-03", base=tmp_path)
    md = registro.build_registro(tmp_path)
    assert "art_d15" in md
    assert "#19" in md
    assert "Inviate" in md


@pytest.mark.policy
def test_scadenze_rileva_non_esitate(tmp_path):
    vecchia = (date.today() - timedelta(days=40)).isoformat()
    registro.record_nuovo("scaduto", data_invio=vecchia, base=tmp_path)
    registro.record_nuovo("recente", data_invio=date.today().isoformat(), base=tmp_path)
    scad = registro.scadenze(registro.carica_tutti(tmp_path))
    assert len(scad) == 1
    assert scad[0][1]["target"] == "scaduto"


@pytest.mark.policy
def test_scadenze_ignora_esitate_e_escalate(tmp_path):
    vecchia = (date.today() - timedelta(days=40)).isoformat()
    p = registro.record_nuovo("risposta", data_invio=vecchia, base=tmp_path)
    registro.aggiorna_record(p, esito="ok")
    q = registro.record_nuovo("escalata", data_invio=vecchia, base=tmp_path)
    registro.aggiorna_record(q, escalation="rpct")
    assert registro.scadenze(registro.carica_tutti(tmp_path)) == []


@pytest.mark.pure_unit
def test_slug_target():
    assert registro.slug_target("ART D15") == "art_d15"
    assert registro.slug_target("  Ministero del Lavoro ") == "ministero_del_lavoro"


@pytest.mark.contract
def test_record_shape_contratto():
    """Tutti i record in richieste/ rispettano la forma del contratto."""
    keys = {
        "target", "issue", "richiedente", "data_invio", "scadenza",
        "protocollo", "data_risposta", "esito", "escalation", "note",
    }
    optional = {"norma", "tipo_risposta", "verificato_il"}  # retro-compatibile
    files = list((REPO / "richieste").glob("*/*.json"))
    assert files, "nessun record da validare"
    for p in files:
        rec = json.loads(p.read_text())
        assert keys <= set(rec), f"{p.name}: chiavi mancanti {keys - set(rec)}"
        assert set(rec) <= keys | optional, f"{p.name}: chiavi inattese {set(rec) - keys - optional}"
        assert isinstance(rec.get("norma", []), list), p.name
        assert rec.get("tipo_risposta") in (
            None, "nessuna", "interlocutoria", "negativa_motivata", "documentazione", "impegno",
        ), p.name
        assert rec["escalation"] in ("none", "rpct", "anac"), p.name
        assert rec["esito"] in (None, "ok", "parziale", "rifiutata", "ignorata"), p.name


@pytest.mark.policy
def test_norma_dei_record_esiste_negli_obblighi():
    """Ogni id in `norma` deve esistere in obblighi/obblighi.yaml."""
    import yaml

    obblighi = {o["id"] for o in yaml.safe_load((REPO / "obblighi" / "obblighi.yaml").read_text())}
    for p in (REPO / "richieste").glob("*/*.json"):
        rec = json.loads(p.read_text())
        for nid in rec.get("norma", []):
            assert nid in obblighi, f"{p.name}: norma '{nid}' non esiste negli obblighi"


@pytest.mark.contract
def test_aggiorna_nota(tmp_path):
    p = registro.record_nuovo("art_d15", data_invio="2026-11-03", base=tmp_path)
    registro.aggiorna_record(p, note="protocollata 04/11/2026")
    assert json.loads(p.read_text())["note"] == "protocollata 04/11/2026"


@pytest.mark.policy
def test_cmd_nota_append(tmp_path, monkeypatch):
    """--append preserva la nota esistente (le note legali non si sovrascrivono)."""
    p = registro.record_nuovo("art_d15", data_invio="2026-11-03", base=tmp_path)
    registro.aggiorna_record(p, note="prima")
    monkeypatch.setattr(registro, "RICHIESTE", tmp_path)
    registro.cmd_nota(
        argparse.Namespace(
            arg="art_d15/2026-11-03_01.json",
            note="seconda",
            arg2=None,
            append=True,
        )
    )
    assert json.loads(p.read_text())["note"] == "prima\nseconda"
