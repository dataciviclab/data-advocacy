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

    def test_dafare_struttura(self):
        """--da-fare mostra sempre la coda azioni, senza dipendere dai dati."""
        r = _run("--da-fare")
        assert r.returncode == 0
        assert "CODA AZIONI" in r.stdout


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
        """--respond su ente non in tracker fallisce."""
        r = _run("--respond", "ente-inesistente", "--status", "ok",
                 "--note", "test")
        assert "non trovata" in r.stdout


class TestStatus:
    """--status come esito risposta (non come riepilogo)."""

    def test_status_come_esito(self):
        r = _run("--respond", "ente-inesistente", "--status", "parziale")
        assert "non trovata" in r.stdout

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

    # cleanup dopo l'import: rimuove test-target da enti.json
    def teardown_method(self):
        import json
        path = Path(__file__).resolve().parent.parent / "enti" / "enti.json"
        enti = json.loads(path.read_text())
        enti = [e for e in enti if e.get("id") != "test-target"]
        path.write_text(json.dumps(enti, indent=2, ensure_ascii=False))

    def test_import_invalido_fallisce(self, tmp_path):
        import json
        path = tmp_path / "invalido.json"
        path.write_text(json.dumps(self.INVALIDO))
        r = _run("--import", str(path))
        assert r.returncode == 1
        # L'errore va su stderr
        assert "fallita" in r.stderr


class TestGenerazioneBozza:
    """Verifica che genera_bozza_foia() produca output pulito."""

    def test_bozza_senza_placeholder_residui(self):
        """La bozza non deve contenere placeholder {XXX} ne' [soggetto...]."""
        import importlib.util
        import json

        # Carica foia come modulo
        spec = importlib.util.spec_from_file_location("foia", REPO / "foia.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Prepara ente con note_foia
        enti_path = REPO / "enti" / "enti.json"
        enti = json.loads(enti_path.read_text())
        ente = next(e for e in enti if e["id"] == "mimit_rna")

        bozza = mod.genera_bozza_foia(ente)
        # Nessun {PLACEHOLDER} residuo
        assert "{" not in bozza, f"Placeholder residuo in bozza"
        # Nessun [soggetto...] residuo
        assert "soggetto di cui all'art. 2-bis" not in bozza, "Punto 7 non sostituito"
        # Punto 8 compilato
        assert "XML" in bozza, "Evidenze non iniettate"
        # Richiedente presente (da richiedente.json locale o default)
        assert mod.carica_richiedente()["nome"] in bozza, "Nome richiedente non iniettato"

    def test_eml_contiene_html(self):
        """--eml deve generare un file .eml parsabile con contenuto HTML."""
        r = _run("--eml", "mimit_rna")
        assert r.returncode == 0

        eml_path = REPO / "bozze" / "mimit_rna.eml"
        assert eml_path.exists(), "File .eml non generato"

        import email
        with open(eml_path) as f:
            msg = email.message_from_file(f)

        # Deve essere multipart/mixed
        assert msg.is_multipart(), "EML deve essere multipart"

        # Cerca text/html tra le parti
        found_html = False
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                found_html = True
                break
        assert found_html, "Nessuna parte text/html nell'eml"

    def teardown_method(self):
        """Non lasciare artefatti in bozze/ dopo il test."""
        for name in ("mimit_rna.eml", "mimit_rna.txt", "mimit_rna_catalogo.csv"):
            p = REPO / "bozze" / name
            if p.exists():
                p.unlink()
