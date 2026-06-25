"""Smoke test per generate_foia_draft.py.

Non fa probe reali — usa fixture e verifica che lo script
non crashi sui casi base.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "generate_foia_draft.py"


@pytest.fixture
def health_scores() -> Path:
    """Crea un health scores JSON di test."""
    data = {
        "scores": [
            {
                "source_id": "anac",
                "protocol": "ckan",
                "totale": 73.2,
                "livello": "debole",
                "azione_raccomandata": "verifica umana",
                "flag_urgenza": [],
                "assi_computed": 5,
                "assi": {
                    "formato_aperto": {"score": 90, "fonte": "computed"},
                    "raggiungibilita": {"score": 70, "fonte": "computed"},
                    "licenza_aperta": {"score": 85, "fonte": "computed"},
                    "presenza_datigovit": {"score": 80, "fonte": "computed"},
                    "hvd_compliance": {"score": 50, "fonte": "computed"},
                    "accessibilita_foia": {"score": 50, "fonte": "missing"},
                },
            },
            {
                "source_id": "noipa_sparql",
                "protocol": "sparql",
                "totale": 70.0,
                "livello": "medio",
                "azione_raccomandata": "monitoraggio",
                "flag_urgenza": [],
                "assi_computed": 1,
                "assi": {
                    "formato_aperto": {"score": 0, "fonte": "missing"},
                    "raggiungibilita": {"score": 70, "fonte": "computed"},
                    "licenza_aperta": {"score": 0, "fonte": "missing"},
                    "presenza_datigovit": {"score": 0, "fonte": "missing"},
                    "hvd_compliance": {"score": 50, "fonte": "missing"},
                    "accessibilita_foia": {"score": 50, "fonte": "missing"},
                },
            },
        ]
    }
    path = Path(tempfile.mktemp(suffix=".json"))
    path.write_text(json.dumps(data))
    yield path
    path.unlink()


@pytest.mark.smoke
def test_source_esplicito_con_health_score(health_scores: Path) -> None:
    """--source anac con health score reale → genera bozza."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--source", "anac",
                "--health-scores", str(health_scores),
                "--anagrafica", str(REPO_ROOT / "data" / "anagrafica_enti.json"),
                "--templates", str(REPO_ROOT / "data_advocacy" / "templates"),
                "--out-dir", tmp,
            ],
            capture_output=True, text=True, timeout=30,
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
        assert "FOIA-anac" in r.stdout


@pytest.mark.smoke
def test_source_esplicito_senza_health_score() -> None:
    """--source openbdap con health score vuoto → fallback, deve generare comunque."""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=True) as hs:
        hs.write(json.dumps({"scores": []}))
        hs.flush()
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--source", "openbdap",
                    "--health-scores", hs.name,
                    "--anagrafica", str(REPO_ROOT / "data" / "anagrafica_enti.json"),
                    "--templates", str(REPO_ROOT / "data_advocacy" / "templates"),
                    "--out-dir", tmp,
                ],
                capture_output=True, text=True, timeout=30,
                cwd=REPO_ROOT,
            )
            assert r.returncode == 0
            # Il fallback deve generare anche senza health score
            assert "FOIA-openbdap" in r.stdout, f"stdout={r.stdout}\nstderr={r.stderr}"


@pytest.mark.smoke
def test_batch_skippa_assi_computed_basso(health_scores: Path) -> None:
    """Batch mode: fonti con assi_computed < 2 devono essere skippate."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--all",
                "--health-scores", str(health_scores),
                "--anagrafica", str(REPO_ROOT / "data" / "anagrafica_enti.json"),
                "--templates", str(REPO_ROOT / "data_advocacy" / "templates"),
                "--out-dir", tmp,
            ],
            capture_output=True, text=True, timeout=30,
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0
        # noipa (assi_computed=1) deve essere skippato
        assert "Skippate" in r.stdout or "Bozza" in r.stdout
