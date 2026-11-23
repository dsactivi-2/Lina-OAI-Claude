"""YAML-Frontmatter aus Wissensdateien darf nicht in den Anruf-Prompt."""

from lina import prompts, prompts_v2, verzija
from lina.kontekst import izracunaj
from lina.znanje import citaj_znanje, ohne_yaml_frontmatter

VRIJEME = "srijeda, 11. novembar 2026, 10:00"


def test_ohne_frontmatter_laesst_normalen_text():
    assert ohne_yaml_frontmatter("# Znanje\n- a") == "# Znanje\n- a"
    assert ohne_yaml_frontmatter("") == ""
    assert ohne_yaml_frontmatter("--- ohne schluss\nfoo") == "--- ohne schluss\nfoo"


def test_ohne_frontmatter_entfernt_titelblock():
    raw = "---\ntitle: Znanje za Linu v2 (NACRT)\n---\n\n# Znanje\n- Job-Step\n"
    assert ohne_yaml_frontmatter(raw) == "# Znanje\n- Job-Step\n"


def test_ohne_frontmatter_laesst_trennlinie_im_inhalt():
    raw = "---\ntitle: x\n---\n\n# A\n---\nweiter\n"
    assert ohne_yaml_frontmatter(raw) == "# A\n---\nweiter\n"


def test_citaj_znanje_fehlende_datei_fallback(tmp_path):
    assert citaj_znanje(tmp_path / "nema.md") == (
        "Nemaš dodatnih informacija o poslu. "
        "Na pitanja o poslu reci da ćeš zabilježiti pitanje."
    )
    assert citaj_znanje(tmp_path / "nema.md", fallback="") == ""


def _leaks(text: str) -> list[str]:
    found = []
    for marker in (
        "title: Znanje za Linu v2 (NACRT)",
        "title: Znanje za Linu v3",
        "title: Znanje o Job-Stepu",
    ):
        if marker in text:
            found.append(marker)
    if "\n---\ntitle:" in text or text.startswith("---\n"):
        found.append("yaml-start")
    return found


def test_v2_wissen_ohne_doku_titel():
    znanje = prompts_v2._znanje()
    assert _leaks(znanje) == []
    assert znanje.startswith("# Znanje za Linu (NACRT)")
    assert "Job-Step je agencija" in znanje


def test_v2_voice_prompt_ohne_frontmatter():
    k = izracunaj("recX", {}, [], [], [])
    voice = prompts_v2.voice(k, VRIJEME)
    backend = prompts_v2.backend(k, VRIJEME)
    assert _leaks(voice) == []
    assert _leaks(backend) == []
    assert "Job-Step je agencija" in voice


def test_v3_wissen_ohne_doku_titel(monkeypatch):
    monkeypatch.setenv("LINA_PROMPT", "v3")
    assert verzija.je_v3()
    znanje = prompts._znanje()
    assert _leaks(znanje) == []
    assert "Job-Step je agencija" in znanje
    assert "job-step.com" in znanje
    k = izracunaj("recX", {}, [], [], [])
    assert _leaks(prompts.voice(k, VRIJEME)) == []
    assert _leaks(prompts.backend(k, VRIJEME)) == []
