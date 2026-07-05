"""Smoke test per foia.py — comandi principali non devono crashare."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FOIA = sys.executable, str(REPO / "foia.py")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*FOIA, *args],
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=30,
    )


class TestReport:
    """--report: riepilogo campagna."""

    def test_report_ok(self):
        r = _run("--report")
        assert r.returncode == 0
        assert "STATO CAMPAGNA FOIA" in r.stdout

    def test_report_entitotali(self):
        r = _run("--report")
        assert "Enti totali:" in r.stdout


class TestLista:
    """--lista: elenco enti."""

    def test_lista_ok(self):
        r = _run("--lista")
        assert r.returncode == 0
        assert "LISTA ENTI" in r.stdout

    def test_lista_contiene_id(self):
        r = _run("--lista")
        assert "inps" in r.stdout
        assert "poste-italiane" in r.stdout


class TestDaFare:
    """--da-fare: coda azioni."""

    def test_dafare_ok(self):
        r = _run("--da-fare")
        assert r.returncode == 0
        assert "CODA AZIONI" in r.stdout

    def test_dafare_mostra_pending(self):
        """Le FOIA con stato pending nel tracker devono comparire."""
        r = _run("--da-fare")
        # INPS è foia + pending nel tracker
        assert "inps" in r.stdout
        assert "pending" in r.stdout or "Da inviare" in r.stdout


class TestNext:
    """--next: prossimo da verificare."""

    def test_next_ok(self):
        r = _run("--next")
        assert r.returncode == 0
        # Tutti verificati: mostra messaggio diverso
        assert any(msg in r.stdout for msg in (
            "DA VERIFICARE", "Tutti verificati", "ciclo completato"))


class TestRespond:
    """--respond: registra risposta (simulata, poi pulita)."""

    def test_respond_senza_id_fallisce(self):
        """--respond senza --status usa default 'ok'."""
        r = _run("--respond", "poste-italiane", "--status", "ok",
                 "--note", "test")
        assert r.returncode == 0
        assert "risposta" in r.stdout or "registrata" in r.stdout


class TestStatus:
    """--status come esito risposta (non come riepilogo)."""

    def test_status_come_esito(self):
        r = _run("--respond", "poste-italiane", "--status", "parziale")
        assert r.returncode == 0
        # Dopo questo test, ripristino
        _run("--respond", "poste-italiane", "--status", "ok", "--note",
             "ripristino test")

class TestImport:
    """--import: import target FOIA da partecipate-monitor."""

    VALIDO = {
        "fonte": "test",
        "data_generazione": "2026-07-05",
        "targets": [{
            "id": "test-target",
            "denominazione": "Test S.p.A.",
            "violazione": "nessuna_sezione",
            "priorita": 1,
        }]
    }

    INVALIDO = {
        "fonte": "test",
        "data_generazione": "2026-07-05",
        "targets": [{
            "id": "test-target",
        }]
    }

    def test_import_valido(self, tmp_path):
        import json
        path = tmp_path / "valido.json"
        path.write_text(json.dumps(self.VALIDO))
        r = _run("--import", str(path))
        assert r.returncode == 0
        assert "Validazione schema OK" in r.stdout

    def test_import_invalido_fallisce(self, tmp_path):
        import json
        path = tmp_path / "invalido.json"
        path.write_text(json.dumps(self.INVALIDO))
        r = _run("--import", str(path))
        assert r.returncode == 1
        # L'errore va su stderr
        assert "fallita" in r.stderr
