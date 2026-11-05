"""Test per portal_scan.py — helper puri."""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("portal_scan", REPO / "portal_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


portal_scan = _load()


@pytest.mark.pure_unit
def test_slug_of():
    assert portal_scan.slug_of("https://x/it/dataset/posti-letto-2023/") == "posti-letto-2023"


@pytest.mark.pure_unit
def test_year_of_prende_l_ultimo_anno():
    assert portal_scan.year_of("posti-letto-regione-e-disciplina-2023") == 2023
    assert portal_scan.year_of("importazione-animali-01012026-30062026") == 2026
    assert portal_scan.year_of("apparecchiature-sanitarie") is None
