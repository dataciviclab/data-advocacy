"""Test del locatore normativo (T2). Skip se legal-graph non è installato."""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
URN = "urn:nir:stato:decreto.legislativo:2013-03-14;33"


def _load():
    spec = importlib.util.spec_from_file_location("locator", REPO / "obblighi" / "locator.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


locator = _load()

try:  # noqa: SIM105
    import legal_graph.mcp.reports  # noqa: F401

    _HAS_LG = True
except ImportError:
    _HAS_LG = False

pytestmark = pytest.mark.skipif(not _HAS_LG, reason="legal-graph non disponibile")


@pytest.mark.pure_unit
def test_normalize():
    assert locator.normalize("[articolo 28 del codice](http://x)") == "articolo 28 del codice"
    assert locator.normalize("((Pubblicita'))") == "pubblicita"


@pytest.mark.contract
def test_ancora_valida_verificata():
    r = locator.check_locator(
        URN, 37, "1", "le pubbliche amministrazioni e le stazioni appaltanti pubblicano i dati"
    )
    assert r["locator_status"] == "verified"
    assert r["anchor_found"] is True


@pytest.mark.policy
def test_ancora_assente_broken():
    r = locator.check_locator(URN, 37, "1", "questa frase non esiste nell'articolo")
    assert r["locator_status"] == "broken"
    assert r["anchor_found"] is False


@pytest.mark.policy
def test_ancora_vuota_untested():
    assert locator.check_locator(URN, 37, "1", "")["locator_status"] == "untested"
