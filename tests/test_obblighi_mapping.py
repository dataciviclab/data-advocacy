"""Contratto del mapping source_id -> codice_ipa (obblighi/T4a)."""

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
MAPPING = REPO / "obblighi" / "mapping_source_ipa.yaml"

CONFIDENCE = {"alta", "media", "nulla"}
CAMPI = {"codice_ipa", "denominazione", "categoria", "confidence"}


def _mapping() -> dict:
    return yaml.safe_load(MAPPING.read_text())["mapping"]


@pytest.mark.contract
def test_mapping_copre_le_fonti():
    """Il mapping ha una voce per ogni fonte attesa (36 al 2026-11-06)."""
    assert len(_mapping()) >= 36


@pytest.mark.contract
def test_ogni_voce_ha_i_campi_e_confidence_valida():
    for src, v in _mapping().items():
        assert CAMPI <= set(v), f"{src}: campi mancanti {CAMPI - set(v)}"
        assert v["confidence"] in CONFIDENCE, f"{src}: confidence non valida"


@pytest.mark.policy
def test_null_solo_se_confidence_nulla():
    """Un codice_ipa assente è ammesso solo con confidence 'nulla'."""
    for src, v in _mapping().items():
        if not v["codice_ipa"]:
            assert v["confidence"] == "nulla", f"{src}: null ma confidence {v['confidence']}"
        else:
            assert v["confidence"] != "nulla", f"{src}: codice_ipa con confidence 'nulla'"
