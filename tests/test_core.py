import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import core

def test_wake_word():
    ok, rest = core.strip_wake("Hey Jarvis, öffne YouTube", ["yavis", "jarvis"])
    assert ok and rest == "öffne YouTube"
    assert core.strip_wake("hallo welt", ["yavis"])[0] is False

def test_path_guard(tmp_path):
    assert core.is_inside(tmp_path, tmp_path / "a.txt")
    assert not core.is_inside(tmp_path, tmp_path / ".." / "x")

def test_unallowed_program():
    s = dict(core.DEFAULTS); s["programs"] = [{"name": "Spiel", "path": "x", "allowed": False}]
    assert "nicht freigegeben" in core.launch("Spiel", s)

def test_unknown_program():
    s = dict(core.DEFAULTS); s["programs"] = []
    assert "nicht" in core.launch("Unbekannt", s)

def test_time_command():
    assert "Uhr" in core.handle_command("Wie spät ist es?", dict(core.DEFAULTS))

def test_calc_safe():
    assert core.safe_calc("12*7") == 84
    import pytest
    with pytest.raises(Exception): core.safe_calc("__import__('os')")
    with pytest.raises(Exception): core.safe_calc("9**9999")

def test_extras_local(tmp_path):
    s = dict(core.DEFAULTS); s["workdir"] = str(tmp_path)
    assert "gewürfelt" in core.handle_command("würfeln", s)
    assert "84" in core.handle_command("rechne 12*7", s)
    assert "gespeichert" in core.handle_command("notiz: Milch kaufen", s)
    assert "Milch" in core.handle_command("notizen", s)

def test_master_only_greeting():
    assert core.clean_master("Notiz gespeichert, Master.") == "Notiz gespeichert."
    assert core.clean_master("Master, es ist 5 Uhr.") == "Es ist 5 Uhr."

def test_autopilot_risky_needs_approval():
    s = dict(core.DEFAULTS)
    assert core.run_autopilot("öffne Steam", s)[0] == "approval"
    assert core.run_autopilot("kaufe das Produkt", s)[0] == "approval"
    assert core.run_autopilot("rechne 2+2", s)[0] == "ok"

def test_game_scan_and_launch(tmp_path):
    steam = tmp_path / "Steam"; (steam / "steamapps").mkdir(parents=True)
    (steam / "steamapps" / "appmanifest_730.acf").write_text('"AppState"\n{\n"appid"\t\t"730"\n"name"\t\t"Counter-Strike 2"\n}')
    epic = tmp_path / "Epic"; epic.mkdir()
    (epic / "a.item").write_text('{"DisplayName":"Fortnite","InstallLocation":"C:\\\\Games\\\\Fortnite","LaunchExecutable":"fn.exe"}')
    games = core.scan_games([], str(steam), str(epic))
    names = {g["name"] for g in games}
    assert names == {"Counter-Strike 2", "Fortnite"}
    s = dict(core.DEFAULTS); s["programs"] = games
    assert "nicht freigegeben" in core.handle_command("starte counter strike", s)
    assert "nicht freigegeben" in core.handle_command("spiele Fortnite", s)
    assert core.handle_command("spiele ein lied", s) is None

def test_greeting_reaction():
    s = dict(core.DEFAULTS)
    for g in ("Hallo", "hallo yavis", "Hey Jarvis", "Guten Morgen"):
        assert "Hallo Master" in core.handle_command(g, s)
    assert "Hallo Master" in core.clean_master("Hallo Master, was kann ich für dich tun?")

def test_catalog_has_20_plus():
    assert len(core.add_catalog([])) >= 30
    assert core.add_catalog([{"name": "Rechner", "path": "x"}])[0]["name"] != "Rechner"

def test_voice_profiles():
    import voice
    assert len(voice.PROFILES) >= 30
    assert len({p["id"] for p in voice.PROFILES}) == len(voice.PROFILES)
    assert all(p["base"] in voice.BASES for p in voice.PROFILES)
