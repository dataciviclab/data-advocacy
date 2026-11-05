"""Test per bozza.py — generazione .eml da una nota con blocchi PEC."""

import email
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("bozza", REPO / "bozza.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bozza = _load()


@pytest.mark.contract
def test_build_eml_multiplo(tmp_path, monkeypatch):
    """Due blocchi PEC -> due .eml, con destinatario, oggetto e allegato corretti."""
    nota = tmp_path / "richieste.md"
    allegato = tmp_path / "evidenza.md"
    allegato.write_text("dettaglio")
    nota.write_text(
        """# Nota

<!-- PEC a
TO=ente@pec.it
SUBJECT=Prima richiesta
ATTACH=evidenza.md
FILE=prima
-->
<!-- PEC b
TO=altro@pec.it
SUBJECT=Seconda richiesta
FILE=seconda
-->

<!-- PEC:BODY a -->
Al Responsabile
Corpo della prima.
<!-- /PEC:BODY a -->

<!-- PEC:BODY b -->
Al Responsabile
Corpo della seconda.
<!-- /PEC:BODY b -->
"""
    )
    outdir = tmp_path / "bozze"
    monkeypatch.setattr(bozza, "BOZZE", outdir)
    monkeypatch.setattr(bozza, "RICHIEDENTE", tmp_path / "assente.json")

    made = bozza.build(nota)
    assert {p.name for p in made} == {"prima.eml", "seconda.eml"}

    m1 = email.message_from_bytes((outdir / "prima.eml").read_bytes())
    assert m1["To"] == "ente@pec.it"
    assert m1["Subject"] == "Prima richiesta"
    atts = [x.get_filename() for x in m1.walk() if x.get_filename()]
    assert atts == ["evidenza.md"]

    m2 = email.message_from_bytes((outdir / "seconda.eml").read_bytes())
    assert m2["Subject"] == "Seconda richiesta"


@pytest.mark.pure_unit
def test_fill_da_richiedente_e_data_odierna():
    from datetime import date

    testo, mancanti = bozza._fill("Ciao [NOME COGNOME] il [DATA], firma [RUOLO]", {"nome": "Mario", "firma": "cittadino"})
    assert f"Ciao Mario il {date.today():%d/%m/%Y}, firma cittadino" == testo
    assert mancanti == []


@pytest.mark.pure_unit
def test_fill_segnala_placeholder_mancanti():
    testo, mancanti = bozza._fill("[NOME COGNOME] a [LUOGO]", {"nome": "Mario"})
    assert "Mario" in testo
    assert mancanti == ["[LUOGO]"]


@pytest.mark.policy
def test_blocco_incompleto_fallisce(tmp_path, monkeypatch):
    nota = tmp_path / "r.md"
    nota.write_text("<!-- PEC a\nTO=x@pec.it\n-->\n<!-- PEC:BODY a -->\ntesto\n<!-- /PEC:BODY a -->")
    monkeypatch.setattr(bozza, "BOZZE", tmp_path / "bozze")
    monkeypatch.setattr(bozza, "RICHIEDENTE", tmp_path / "assente.json")
    with pytest.raises(ValueError, match="incompleto"):
        bozza.build(nota)
