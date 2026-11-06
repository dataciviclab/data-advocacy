"""Test del locatore normativo (T2).

I test che parlano col grafo sono marcati skipif; gli altri girano sempre.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
URN_33 = "urn:nir:stato:decreto.legislativo:2013-03-14;33"
URN_36 = "urn:nir:stato:decreto.legislativo:2006-01-24;36"


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

needs_lg = pytest.mark.skipif(not _HAS_LG, reason="legal-graph non disponibile")


@pytest.mark.pure_unit
def test_normalize():
    assert locator.normalize("[articolo 28 del codice](http://x)") == "articolo 28 del codice"
    assert locator.normalize("((Pubblicita'))") == "pubblicita"


@pytest.mark.pure_unit
def test_extract_comma():
    art = "## Art. 9.\n\n1.\n\nPrimo comma.\n\n2.\n\nSecondo comma.\n\n3.\n\nTerzo.\n"
    assert "Primo comma" in locator.extract_comma(art, "1")
    assert "Secondo comma" in locator.extract_comma(art, "2")
    assert "Terzo" in locator.extract_comma(art, "3")
    assert locator.extract_comma(art, "9") is None


@pytest.mark.policy
def test_ancora_vuota_untested():
    assert locator.check_locator(URN_33, 37, "1", "")["locator_status"] == "untested"


@needs_lg
@pytest.mark.contract
def test_ancora_valida_verificata():
    r = locator.check_locator(
        URN_33, 37, "1", "le pubbliche amministrazioni e le stazioni appaltanti pubblicano i dati"
    )
    assert r["locator_status"] == "verified"
    assert r["anchor_found"] is True


@needs_lg
@pytest.mark.policy
def test_ancora_assente_broken():
    r = locator.check_locator(URN_33, 37, "1", "questa frase non esiste nell'articolo")
    assert r["locator_status"] == "broken"
    assert r["anchor_found"] is False


@needs_lg
@pytest.mark.policy
def test_comma_vincola_la_verifica():
    """L'ancora del comma 1 non è valida per il comma 2 (stesso articolo)."""
    ancora_c1 = "pubblicano e aggiornano annualmente sui propri siti istituzionali"
    r = locator.check_locator(URN_36, 9, "2", ancora_c1)
    assert r["locator_status"] == "broken"

    ancora_c2 = "utilizzano il catalogo nazionale dei dati aperti"
    r2 = locator.check_locator(URN_36, 9, "2", ancora_c2)
    assert r2["locator_status"] == "verified"
