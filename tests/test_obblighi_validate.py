"""Test del validatore obblighi/applicazioni (T3)."""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("validate_ob", REPO / "obblighi" / "validate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validate_ob = _load()

try:  # noqa: SIM105
    import legal_graph.mcp.reports  # noqa: F401

    _HAS_LG = True
except ImportError:
    _HAS_LG = False


@pytest.mark.contract
def test_obblighi_e_applicazioni_validi():
    """Schema + integrità referenziale."""
    assert validate_ob.validate(with_locator=False) == []


@pytest.mark.contract
@pytest.mark.skipif(not _HAS_LG, reason="legal-graph non disponibile")
def test_locatore_allineato_alle_ancore():
    """Ogni obbligo dichiara un locator_status che corrisponde al testo di legge."""
    assert validate_ob.validate(with_locator=True) == []
