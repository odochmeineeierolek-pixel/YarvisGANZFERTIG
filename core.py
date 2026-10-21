"""YAVIS Kern: Einstellungen, Gedächtnis, Befehle, Ollama. Keine Qt-Abhängigkeit (testbar)."""
import ast, datetime, json, operator, os, platform, queue, random, re, secrets, sqlite3, string, threading, urllib.request, webbrowser
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "YAVIS"
APP_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = APP_DIR / "settings.json"
DB_FILE = APP_DIR / "yavis.db"

DEFAULTS = {
    "names": ["yavis", "jarvis"], "model": "llama3.2:3b", "host": "http://localhost:11434",
    "voice_id": "", "style": "Normal", "mood": "neutral", "speak": True, "music_dir": "",
    "workdir": str(Path.home() / "YAVIS-Arbeitsordner"), "programs": [],
    "volume": 80, "autopilot": [],
}
WEB = {"youtube": "https://www.youtube.com", "google": "https://www.google.com",
       "spotify": "https://open.spotify.com", "twitch": "https://www.twitch.tv",
       "github": "https://github.com", "maps": "https://maps.google.com",
       "netflix": "https://www.netflix.com", "wikipedia": "https://de.wikipedia.org"}
# Stimm-Stile: (Name, Tempo-Faktor, Lautstärke)
STYLES = {"Normal": (1.0, 1.0), "Sanft": (0.85, 0.8), "Ruhig-tief": (0.75, 1.0), "Energisch": (1.2, 1.0),
          "Hart": (1.05, 1.0), "Flüstern": (0.8, 0.45), "Schnell": (1.4, 1.0), "Langsam": (0.65, 1.0)}
MOODS = {"neutral": "Sprich sachlich und neutral.", "lieb": "Sprich warm, nett und liebevoll.",
         "traurig": "Sprich leise und etwas traurig.", "böse": "Sprich genervt, hart und knapp (aber nie beleidigend)."}


def load_settings():
    s = dict(DEFAULTS)
    try:
        s.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return s


def save_settings(s):
    SETTINGS_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def db():
    c = sqlite3.connect(DB_FILE)
    c.execute("CREATE TABLE IF NOT EXISTS memory(id INTEGER PRIMARY KEY, text TEXT, ts TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, q TEXT, a TEXT, good INT)")
    c.execute("CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, ts TEXT, job TEXT, text TEXT)")
    return c


def mem_add(text):
    with db() as c:
        c.execute("INSERT INTO memory(text,ts) VALUES(?,?)", (text, datetime.datetime.now().isoformat(timespec="seconds")))


def mem_list():
    with db() as c:
        return c.execute("SELECT id,text,ts FROM memory ORDER BY id DESC").fetchall()


def mem_delete(i=None):
    with db() as c:
        c.execute("DELETE FROM memory WHERE id=?", (i,)) if i else c.execute("DELETE FROM memory")


def feedback_add(q, a, good):
    with db() as c:
        c.execute("INSERT INTO feedback(q,a,good) VALUES(?,?,?)", (q, a, int(good)))


def learned_hints(n=3):
    with db() as c:
        good = c.execute("SELECT a FROM feedback WHERE good=1 ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        bad = c.execute("SELECT a FROM feedback WHERE good=0 ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    out = ""
    if good: out += "Antworten wie diese gefielen dem Master: " + " | ".join(g[0][:120] for g in good) + ". "
    if bad: out += "Vermeide Antworten wie diese: " + " | ".join(b[0][:120] for b in bad) + ". "
    return out


def is_inside(base, target):
    """Schutz vor Pfadzugriffen außerhalb des Arbeitsordners."""
    b = Path(base).resolve()
    t = Path(target).resolve()
    return t == b or b in t.parents


def strip_wake(text, names):
    """Gibt (aktiviert, Rest) zurück. Erkennt jeden eingestellten Namen am Satzanfang."""
    t = text.strip()
    low = t.lower()
    for n in names:
        n = n.lower().strip()
        if n and re.match(rf"^(hey |hallo |hi )?{re.escape(n)}\b[ ,.:!]*", low):
            return True, re.sub(rf"^(hey |hallo |hi )?{re.escape(n)}\b[ ,.:!]*", "", t, flags=re.I)
    return False, t


def _norm(x):
    return re.sub(r"[^a-z0-9äöüß]", "", x.lower())


def find_program(name, s):
    key = _norm(name)
    if not key: return None
    progs = s["programs"]
    for p in progs:
        if _norm(p["name"]) == key: return p
    if len(key) >= 3:
        hits = [p for p in progs if key in _norm(p["name"]) or _norm(p["name"]) in key and len(_norm(p["name"])) >= 4]
        if hits: return min(hits, key=lambda p: len(p["name"]))
    return None


def launch(name, s):
    p = find_program(name, s)
    if p:
        if not p.get("allowed"):
            return f"{p['name']} ist nicht freigegeben, Master."
        if "://" not in p["path"] and not os.path.exists(p["path"]):
            return f"Der Pfad von {p['name']} existiert nicht mehr, Master."
        os.startfile(p["path"])  # nur Windows; nur freigegebene Einträge (auch steam://-Links)
        return f"{p['name']} wird gestartet, Master."
    key = name.strip().lower()
    if key in WEB:
        webbrowser.open(WEB[key])
        return f"Ich öffne {name} im Browser, Master."
    return f"{name} kenne ich nicht oder es ist nicht freigegeben, Master."


# ---- Spiele-Scan (Steam, Epic)
def _steam_root():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            return winreg.QueryValueEx(k, "SteamPath")[0]
    except Exception:
        pf = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        return str(Path(pf) / "Steam")


def scan_steam(steam=None):
    steam = Path(steam or _steam_root()); libs = [steam]
    vdf = steam / "steamapps" / "libraryfolders.vdf"
    if vdf.exists():
        for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8", errors="ignore")):
            libs.append(Path(p.replace("\\\\", "\\")))
    out, seen = [], set()
    for lib in libs:
        for f in (lib / "steamapps").glob("appmanifest_*.acf"):
            t = f.read_text(encoding="utf-8", errors="ignore")
            aid = re.search(r'"appid"\s+"(\d+)"', t); nm = re.search(r'"name"\s+"([^"]+)"', t)
            if aid and nm and aid.group(1) not in seen and not re.search(r"Redistributable|Proton|Steam Linux Runtime", nm.group(1)):
                seen.add(aid.group(1))
                out.append({"name": nm.group(1), "path": f"steam://rungameid/{aid.group(1)}", "allowed": False, "game": True})
    return out


def scan_epic(manifests=None):
    d = Path(manifests or Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Epic/EpicGamesLauncher/Data/Manifests")
    out = []
    for f in d.glob("*.item"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
            if j.get("LaunchExecutable"):
                out.append({"name": j["DisplayName"], "path": str(Path(j["InstallLocation"]) / j["LaunchExecutable"]), "allowed": False, "game": True})
        except Exception:
            pass
    return out


def scan_games(existing, steam=None, epic=None):
    have = {_norm(p["name"]) for p in existing}; new = []
    for g in scan_steam(steam) + scan_epic(epic):
        if _norm(g["name"]) not in have: new.append(g); have.add(_norm(g["name"]))
    return new


PENDING = queue.Queue()  # Timer-Meldungen, die die Oberfläche abholt
WIN_TOOLS = {"rechner": "calc.exe", "notepad": "notepad.exe", "editor": "notepad.exe", "explorer": "explorer.exe",
             "taskmanager": "taskmgr.exe", "paint": "mspaint.exe", "einstellungen": "ms-settings:",
             "snipping": "snippingtool.exe", "systemsteuerung": "control.exe"}
QUOTES = ["Große Ideen entstehen mit den richtigen Werkzeugen.", "Kleine Schritte jeden Tag schlagen große Pläne ohne Start.",
          "Fehler sind Beweise, dass du es versuchst.", "Heute ist ein guter Tag, um anzufangen."]
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.Mod: operator.mod}


def safe_calc(expr):
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 100: raise ValueError
            return _OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](ev(n.operand))
        raise ValueError
    return ev(ast.parse(expr.replace(",", ".").replace("x", "*").replace(":", "/"), mode="eval").body)


def _notes_dir(s):
    d = Path(s["workdir"]); d.mkdir(parents=True, exist_ok=True); return d


def extra_command(t, low, s):
    """Lokale Extras ohne KI. Gibt Antwort oder None zurück."""
    if low in ("würfel", "würfeln", "wirf einen würfel"): return f"Du hast eine {random.randint(1, 6)} gewürfelt, Master."
    if low in ("münze", "münze werfen", "kopf oder zahl"): return random.choice(["Kopf", "Zahl"]) + ", Master."
    m = re.match(r"^zufallszahl(?: von (\d+) bis (\d+))?$", low)
    if m: a, b = (int(m.group(1)), int(m.group(2))) if m.group(1) else (1, 100); return f"Deine Zahl ist {random.randint(min(a,b), max(a,b))}, Master."
    if low.startswith("passwort"):
        pw = "".join(secrets.choice(string.ascii_letters + string.digits + "!?#$%") for _ in range(16))
        try:
            import subprocess; subprocess.run("clip", input=pw.encode("utf-16"), check=False)
        except Exception: pass
        return f"Neues Passwort: {pw}. Ich habe es in die Zwischenablage gelegt, Master."
    if low.startswith(("rechne ", "was ist ")):
        try: return f"Das Ergebnis ist {round(safe_calc(re.sub(r'^(rechne|was ist) ', '', low)), 6)}, Master."
        except Exception: return None
    if "welcher tag" in low or "welches datum" in low or low in ("datum", "wochentag"):
        d = datetime.date.today(); tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        return f"Heute ist {tage[d.weekday()]}, der {d.strftime('%d.%m.%Y')}, Master."
    if low in ("systeminfo", "systeminformationen"):
        return f"{platform.system()} {platform.release()}, Prozessor {platform.processor() or 'unbekannt'}, {os.cpu_count()} Kerne, Master."
    if low in ("zitat", "motivation"): return random.choice(QUOTES) + " Master."
    m = re.match(r"^timer (\d+) ?(sekunden|sekunde|minuten|minute)$", low)
    if m:
        n = int(m.group(1)) * (60 if m.group(2).startswith("minut") else 1)
        threading.Timer(n, lambda: PENDING.put(f"Dein Timer ist abgelaufen, Master.")).start()
        return f"Timer für {m.group(1)} {m.group(2)} läuft, Master."
    m = re.match(r"^(notiz|notiere)[: ]+(.+)$", t, flags=re.I)
    if m:
        f = _notes_dir(s) / "notizen.txt"
        if not is_inside(s["workdir"], f): return "Zugriff verweigert."
        with open(f, "a", encoding="utf-8") as fh: fh.write(f"[{datetime.datetime.now():%d.%m.%Y %H:%M}] {m.group(2)}\n")
        return "Notiz gespeichert, Master."
    if low in ("zeige notizen", "notizen"):
        f = _notes_dir(s) / "notizen.txt"
        return ("Deine Notizen: " + " ".join(f.read_text(encoding="utf-8").splitlines()[-5:])) if f.exists() else "Keine Notizen vorhanden, Master."
    m = re.match(r"^(aufgabe|todo)[: ]+(.+)$", t, flags=re.I)
    if m: mem_add("AUFGABE: " + m.group(2)); return "Aufgabe notiert, Master."
    if low in ("meine aufgaben", "zeige aufgaben"):
        a = [x[1][9:] for x in mem_list() if x[1].startswith("AUFGABE: ")]
        return ("Offen: " + "; ".join(a[:8])) if a else "Keine offenen Aufgaben, Master."
    m = re.match(r"^(öffne|starte)\s+(.+)$", t, flags=re.I)
    if m and m.group(2).lower() in WIN_TOOLS:
        try: os.startfile(WIN_TOOLS[m.group(2).lower()]); return f"{m.group(2)} wird geöffnet, Master."
        except Exception: return "Das konnte ich nicht öffnen, Master."
    m = re.match(r"^(übersetze|youtube suche|spiele auf youtube)\s+(.+)$", t, flags=re.I)
    if m and m.group(1).lower() != "übersetze":
        webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.request.quote(m.group(2)))
        return f"Ich suche {m.group(2)} auf YouTube, Master."
    return None


def handle_command(text, s):
    """Schnelle lokale Befehle ohne KI. Gibt Antwort oder None zurück."""
    t = text.strip().rstrip(".!?")
    low = t.lower()
    if low in ("neutral", "sei neutral"):
        s["mood"] = "neutral"; save_settings(s); return "Ich bin jetzt neutral, Master."
    for m in ("lieb", "traurig", "böse"):
        if low == f"sei {m}":
            s["mood"] = m; save_settings(s); return f"Stimmung {m} aktiviert, Master."
    if re.search(r"wie (spät|viel uhr)", low):
        return datetime.datetime.now().strftime("Es ist %H:%M Uhr, Master.")
    if low.startswith("merke dir "):
        mem_add(t[10:]); return "Gemerkt, Master."
    if low.startswith("suche nach ") or low.startswith("google "):
        q = re.sub(r"^(suche nach|google) ", "", t, flags=re.I)
        webbrowser.open("https://www.google.com/search?q=" + urllib.request.quote(q))
        return f"Ich suche nach {q}, Master."
    r = extra_command(t, low, s)
    if r: return r
    m = re.match(r"^(öffne|oeffne|starte|open)\s+(.+)$", t, flags=re.I)
    if m:
        return launch(m.group(2), s)
    m = re.match(r"^(spiele|zocke)\s+(.+)$", t, flags=re.I)
    if m and find_program(m.group(2), s):
        return launch(m.group(2), s)
    if low in WEB:
        return launch(low, s)
    return None


def ask_ollama(history, s):
    mem = "; ".join(m[1] for m in mem_list()[:10])
    system = ("Du bist YAVIS, ein persönlicher deutscher Sprachassistent. Nenne den Nutzer 'Master' nur zur Begrüßung, niemals mitten im Satz oder am Satzende. "
              "Antworte kurz (1-3 Sätze), natürlich wie ein Mensch. " + MOODS.get(s["mood"], "") +
              (f" Bekannte Infos über den Master: {mem}." if mem else "") + " " + learned_hints())
    body = json.dumps({"model": s["model"], "stream": False,
                       "messages": [{"role": "system", "content": system}] + history[-12:]}).encode()
    req = urllib.request.Request(s["host"] + "/api/chat", body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return clean_master(json.loads(r.read())["message"]["content"].strip())
    except Exception:
        return ("Ollama antwortet nicht, Master. Bitte installiere Ollama (ollama.com), starte es und lade das Modell: "
                f"ollama pull {s['model']}")


def clean_master(t):
    """'Master' nur zur Begrüßung: entfernt die Anrede aus normalen Antworten."""
    t = re.sub(r",?\s*\bMaster\b(?=\s*[.!?:]|\s*$)", "", t)
    t = re.sub(r"\bMaster,\s*", "", t)
    t = t.strip()
    return t[:1].upper() + t[1:]


CONV_FILE = APP_DIR / "conversations.json"


def load_convs():
    try:
        data = json.loads(CONV_FILE.read_text(encoding="utf-8"))
        convs = [{"title": d["title"], "hist": d["hist"], "lines": d["lines"], "gen": 0, "named": True} for d in data]
        if convs: return convs
    except Exception:
        pass
    return [{"title": "Gespräch 1", "hist": [], "lines": [], "gen": 0, "named": False}]


def save_convs(convs):
    try:
        data = [{"title": c["title"], "hist": c["hist"][-20:], "lines": c["lines"][-60:]} for c in convs]
        CONV_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


RISKY = re.compile(r"\b(öffne|oeffne|starte|suche|google|youtube|spiele|sende|schicke|versende|kaufe|bezahle|überweise|"
                   r"veröffentliche|lösche|installiere|poste)\b", re.I)


def run_autopilot(cmd, s):
    """Autopilot-Auftrag. Riskante Aktionen laufen NIE allein, sie warten auf Genehmigung."""
    if RISKY.search(cmd):
        return "approval", cmd
    r = handle_command(cmd, s)
    if r: return "ok", clean_master(r)
    return "ok", clean_master(ask_ollama([{"role": "user", "content": cmd}], s))


def report_add(job, text):
    with db() as c:
        c.execute("INSERT INTO reports(ts,job,text) VALUES(?,?,?)", (datetime.datetime.now().strftime("%d.%m. %H:%M"), job, text))


def report_list(n=50):
    with db() as c:
        return c.execute("SELECT ts,job,text FROM reports ORDER BY id DESC LIMIT ?", (n,)).fetchall()
