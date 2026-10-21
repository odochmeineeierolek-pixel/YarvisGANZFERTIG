import math, os, sys, threading, time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QPen, QFont, QPixmap, QIcon, QShortcut, QKeySequence
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QFileDialog, QListWidgetItem, QMessageBox, QCheckBox, QSlider, QSystemTrayIcon, QMenu)
import core, voice

CSS = """
QWidget{background:#0b0b0b;color:#f2f2f2;font-size:14px}
QListWidget{background:#0b0b0b;border:none;font-size:15px}
QListWidget::item{padding:10px}QListWidget::item:selected{background:#3a2d00;color:#ffd400}
QTextEdit,QLineEdit,QComboBox,QListWidget#l{background:#141414;border:1px solid #ff2a2a;border-radius:10px;padding:6px}
QPushButton{background:#1a1a1a;border:1px solid #ffd400;border-radius:10px;padding:8px 14px;color:#ffd400}
QPushButton:hover{background:#ffd400;color:#000}
QPushButton#stop{border-color:#ff2a2a;color:#ff2a2a}
QSlider::groove:horizontal{background:#333;height:6px;border-radius:3px}QSlider::sub-page:horizontal{background:#ff2a2a;border-radius:3px}QSlider::handle:horizontal{background:#ffd400;width:16px;margin:-6px 0;border-radius:8px}
QLabel#h{font-size:24px;font-weight:bold}
"""

EXTRAS = [
 ("🎲 Würfeln", "würfeln"), ("🪙 Münze werfen", "münze"), ("🔢 Zufallszahl", "zufallszahl"), ("🔐 Passwort erzeugen", "passwort"),
 ("🧮 Rechnen (z. B. rechne 12*7)", "rechne "), ("📅 Datum & Wochentag", "datum"), ("🕒 Uhrzeit", "wie spät ist es"), ("💻 Systeminfo", "systeminfo"),
 ("⏱ Timer 5 Minuten", "timer 5 minuten"), ("📝 Notiz machen (notiz: …)", "notiz: "), ("📖 Notizen anzeigen", "notizen"), ("✅ Aufgabe notieren (aufgabe: …)", "aufgabe: "),
 ("📋 Meine Aufgaben", "meine aufgaben"), ("💬 Zitat", "zitat"), ("🧮 Windows-Rechner öffnen", "öffne rechner"), ("📓 Editor öffnen", "öffne notepad"),
 ("📁 Explorer öffnen", "öffne explorer"), ("📊 Task-Manager öffnen", "öffne taskmanager"), ("⚙ Windows-Einstellungen", "öffne einstellungen"), ("✂ Snipping-Tool", "öffne snipping"),
 ("▶ YouTube öffnen", "youtube"), ("🔎 YouTube-Suche (youtube suche …)", "youtube suche "), ("🌐 Google-Suche (suche nach …)", "suche nach "), ("🎵 Spotify öffnen", "spotify"),
 ("😂 Witz erzählen", "Erzähl mir einen kurzen, lustigen Witz"), ("🧩 Rätsel", "Gib mir ein kurzes Rätsel und warte auf meine Antwort"), ("🎤 Rap über mich", "Schreibe einen kurzen lustigen Rap über den Master"),
 ("📜 Gedicht", "Schreibe ein kurzes Gedicht"), ("🌙 Gute-Nacht-Geschichte", "Erzähle eine sehr kurze Gute-Nacht-Geschichte"), ("🤓 Fakt des Tages", "Nenne einen überraschenden Fakt"),
 ("🗓 Tagesplan", "Plane meinen Arbeitstag, stelle mir zuerst Rückfragen"), ("✉ E-Mail-Entwurf", "Hilf mir, eine E-Mail zu schreiben, frage mich nach Details"), ("💼 Angebot vorbereiten", "Hilf mir, ein Angebot vorzubereiten, frage mich nach Details"),
 ("🛒 Produkt beschreiben", "Hilf mir, ein Produkt für den Verkauf zu beschreiben, frage mich nach Details"), ("💶 Preis recherchieren", "suche nach Gebrauchtpreis "), ("💡 Geschäftsidee prüfen", "Hilf mir, eine Geschäftsidee ehrlich zu analysieren"),
 ("🌍 Übersetzer", "Übersetze für mich ins Englische: "), ("📚 Lernplan", "Erstelle mir einen kurzen Lernplan, frage nach Thema und Zeit"), ("🍳 Rezept-Idee", "Schlage ein einfaches Rezept vor"),
 ("🏋 Workout-Idee", "Schlage ein kurzes Heim-Workout vor"), ("✈ Reiseplan", "Hilf mir, eine Reise zu planen, frage nach Ziel und Budget"), ("💻 Code-Hilfe", "Hilf mir bei einem Programmierproblem, frage nach Details"),
 ("😊 Stimmung: lieb", "sei lieb"), ("😠 Stimmung: böse", "sei böse"), ("😢 Stimmung: traurig", "sei traurig"), ("😐 Stimmung: neutral", "sei neutral"),
]

class Orb(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(230); self.level = 0.0; self.t = 0; self.active = False
        QTimer(self, timeout=self.tick, interval=33).start()
    def tick(self):
        self.t += 1; target = 0.5 + 0.5 * abs(math.sin(self.t / 4)) if self.active else 0.05
        self.level += (target - self.level) * 0.25; self.update()
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        c = self.rect().center(); r = 55 + 45 * self.level
        g = QRadialGradient(c, r * 1.6); g.setColorAt(0, QColor(255, 212, 0, 200)); g.setColorAt(.6, QColor(255, 42, 42, 120)); g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(g); p.setPen(Qt.NoPen); p.drawEllipse(c, r * 1.6, r * 1.6)
        p.setBrush(QColor(0, 0, 0)); p.setPen(QPen(QColor(255, 42, 42), 5)); p.drawEllipse(c, r, r)
        p.setPen(QPen(QColor(255, 212, 0), 2)); p.drawEllipse(c, r - 6, r - 6)
        p.setPen(QColor(255, 255, 255)); p.setFont(QFont("Segoe UI", 14, QFont.Bold)); p.drawText(self.rect(), Qt.AlignCenter, "YAVIS")

def make_icon():
    pm = QPixmap(64, 64); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(0, 0, 0)); p.setPen(QPen(QColor(255, 42, 42), 6)); p.drawEllipse(6, 6, 52, 52)
    p.setPen(QPen(QColor(255, 212, 0), 3)); p.drawEllipse(14, 14, 36, 36); p.end(); return QIcon(pm)

class Bus(QObject):
    reply = Signal(str, str); answer = Signal(str, str, object, int, bool); heard = Signal(str); done = Signal()
    report = Signal(str, str); approval = Signal(str)

class Main(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle("YAVIS"); self.resize(1100, 720); self.setWindowIcon(make_icon())
        self.s = core.load_settings(); self.last = ("", ""); self._quit = False
        self.convs = core.load_convs(); self.cur = 0; self.bus = Bus()
        self.bus.reply.connect(self.show_reply); self.bus.answer.connect(self.on_answer); self.bus.heard.connect(self.on_heard)
        self.bus.done.connect(lambda: setattr(self.orb, "active", False)); self.bus.report.connect(self.on_report); self.bus.approval.connect(self.on_approval)
        root = QHBoxLayout(self); left = QVBoxLayout(); self.nav = QListWidget(); self.nav.setFixedWidth(170)
        for n in ["Home / Chat", "Musik", "Programme", "Gedächtnis", "Einstellungen", "Extras", "Autopilot"]: self.nav.addItem(n)
        self.vol = QSlider(Qt.Horizontal); self.vol.setRange(0, 100); self.vol.setValue(int(self.s["volume"])); self.vol.valueChanged.connect(self.set_vol)
        left.addWidget(self.nav, 1); left.addWidget(QLabel("🔊 Lautstärke")); left.addWidget(self.vol)
        self.pages = QStackedWidget(); root.addLayout(left); root.addWidget(self.pages, 1)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.build_chat(); self.build_music(); self.build_programs(); self.build_memory(); self.build_settings(); self.build_extras(); self.build_auto()
        QShortcut(QKeySequence("Esc"), self, activated=self.interrupt); QShortcut(QKeySequence("Ctrl+Space"), self, activated=self.listen)
        self.tray = QSystemTrayIcon(make_icon(), self); m = QMenu(); m.addAction("YAVIS öffnen", self.showNormal); m.addAction("Beenden", self.quit_app)
        self.tray.setContextMenu(m); self.tray.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.Trigger else None); self.tray.show()
        QTimer(self, timeout=self.poll, interval=1000).start(); QTimer(self, timeout=self.tick_auto, interval=30000).start()
        self.nav.setCurrentRow(0); self.say_startup()

    def set_vol(self, v):
        self.s["volume"] = v; core.save_settings(self.s); self.ao.setVolume(v / 100)
    def quit_app(self): self._quit = True; QApplication.quit()
    def closeEvent(self, e):
        if self._quit: e.accept(); return
        e.ignore(); self.hide(); self.tray.showMessage("YAVIS", "Läuft weiter im Hintergrund (Autopilot). Beenden über das Symbol unten rechts.")

    def page(self, title):
        w = QWidget(); l = QVBoxLayout(w); h = QLabel(title); h.setObjectName("h"); l.addWidget(h); self.pages.addWidget(w); return l

    # ---- Chat (mehrere Gespräche, jederzeit unterbrechbar)
    def build_chat(self):
        l = self.page("Hallo, ich bin YAVIS."); self.orb = Orb(); l.addWidget(self.orb)
        top = QHBoxLayout(); self.cc = QComboBox(); self.cc.currentIndexChanged.connect(self.switch_conv)
        nb = QPushButton("+ Neues Gespräch"); nb.clicked.connect(self.new_conv); db_ = QPushButton("Gespräch löschen"); db_.clicked.connect(self.del_conv)
        for w in (self.cc, nb, db_): top.addWidget(w)
        l.addLayout(top)
        self.log = QTextEdit(readOnly=True); l.addWidget(self.log, 1)
        row = QHBoxLayout(); self.inp = QLineEdit(); self.inp.setPlaceholderText("Schreibe oder sprich … (Esc = unterbrechen, Strg+Leertaste = zuhören)")
        self.inp.returnPressed.connect(self.send); b1 = QPushButton("Senden"); b1.clicked.connect(self.send)
        b2 = QPushButton("🎤 Zuhören"); b2.clicked.connect(self.listen); b3 = QPushButton("■ Stopp"); b3.setObjectName("stop"); b3.clicked.connect(self.stop)
        up = QPushButton("👍"); up.clicked.connect(lambda: self.fb(1)); dn = QPushButton("👎"); dn.clicked.connect(lambda: self.fb(0))
        for w in (self.inp, b1, b2, b3, up, dn): row.addWidget(w)
        l.addLayout(row); self.refresh_convs()
    def conv(self): return self.convs[self.cur]
    def refresh_convs(self):
        self.cc.blockSignals(True); self.cc.clear(); self.cc.addItems([c["title"] for c in self.convs]); self.cc.setCurrentIndex(self.cur); self.cc.blockSignals(False)
        self.log.setHtml("<br>".join(self.conv()["lines"]))
    def switch_conv(self, i):
        if 0 <= i < len(self.convs) and i != self.cur: self.cur = i; self.log.setHtml("<br>".join(self.conv()["lines"]))
    def new_conv(self):
        self.convs.append({"title": f"Gespräch {len(self.convs) + 1}", "hist": [], "lines": [], "gen": 0, "named": False}); self.cur = len(self.convs) - 1; self.refresh_convs()
    def del_conv(self):
        if len(self.convs) > 1: self.convs.pop(self.cur); self.cur = 0; self.refresh_convs(); core.save_convs(self.convs)
    def interrupt(self):
        """Bricht Sprechen und die laufende Antwort des aktuellen Gesprächs ab; andere Gespräche laufen weiter."""
        self.conv()["gen"] += 1; voice.stop_speaking(); self.orb.active = False
    def say_startup(self): self.show_reply("", "Hallo Master, YAVIS ist bereit.", True)
    def poll(self):
        while not core.PENDING.empty(): self.show_reply("", core.PENDING.get())
    def append(self, who, t, c=None):
        c = c or self.conv(); line = f"<b style='color:#ffd400'>{who}:</b> {t}"; c["lines"].append(line)
        if c is self.conv(): self.log.append(line)
    def send(self):
        t = self.inp.text().strip(); self.inp.clear()
        if t: self.process(t)
    def on_heard(self, t): self.process(t)
    def process(self, text):
        self.interrupt(); c = self.conv(); c["gen"] += 1; g = c["gen"]
        _, rest = core.strip_wake(text, self.s["names"]); rest = rest or text
        if not c["named"]: c["title"] = rest[:28]; c["named"] = True; self.cc.setItemText(self.cur, c["title"])
        self.append("Du", text)
        def work():
            ans = core.handle_command(rest, self.s); llm = ans is None
            if llm:
                c["hist"].append({"role": "user", "content": rest}); ans = core.ask_ollama(c["hist"], self.s)
            self.bus.answer.emit(rest, ans, c, g, llm)
        threading.Thread(target=work, daemon=True).start()
    def on_answer(self, q, a, c, g, llm):
        if c not in self.convs or g != c["gen"]: return  # abgebrochen oder Gespräch gelöscht
        a = core.clean_master(a)
        if llm: c["hist"].append({"role": "assistant", "content": a})
        self.append("YAVIS", a, c); self.last = (q, a); core.save_convs(self.convs)
        if c is self.conv(): self.speak(a)
    def show_reply(self, q, a, greet=False):
        if not greet: a = core.clean_master(a)
        self.last = (q, a); self.append("YAVIS", a); self.speak(a)
    def speak(self, a):
        if not self.s["speak"]: return
        self.orb.active = True; rate = {"böse": 1.15, "traurig": 0.8}.get(self.s["mood"], 1.0)
        voice.speak(a, self.s["voice_id"], self.s["style"], rate, self.bus.done.emit, self.s["volume"] / 100)
    def listen(self):
        self.interrupt(); self.append("System", "Ich höre zu …")
        def w():
            try: t = voice.listen()
            except Exception as e: self.bus.reply.emit("", f"Spracherkennung nicht verfügbar: {e}"); return
            if t: self.bus.heard.emit(t)
        threading.Thread(target=w, daemon=True).start()
    def stop(self): self.interrupt(); self.player.stop()
    def fb(self, good):
        if self.last[1]: core.feedback_add(self.last[0], self.last[1], good); self.append("System", "Danke, ich merke mir das lokal.")

    # ---- Musik
    def build_music(self):
        l = self.page("Musik"); self.player = QMediaPlayer(); self.ao = QAudioOutput(); self.player.setAudioOutput(self.ao); self.ao.setVolume(self.s['volume'] / 100)
        self.songs = QListWidget(); self.songs.setObjectName("l"); self.songs.itemDoubleClicked.connect(self.play); l.addWidget(self.songs)
        r = QHBoxLayout()
        for txt, f in [("Ordner wählen", self.pick_music), ("▶ Abspielen", lambda: self.play(self.songs.currentItem())), ("⏸ Pause", lambda: self.player.pause()), ("■ Stopp", lambda: self.player.stop())]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        l.addLayout(r); self.load_music()
    def pick_music(self):
        d = QFileDialog.getExistingDirectory(self, "Musikordner");
        if d: self.s["music_dir"] = d; core.save_settings(self.s); self.load_music()
    def load_music(self):
        self.songs.clear(); d = Path(self.s["music_dir"] or Path.home() / "Music")
        if d.exists():
            for f in sorted(d.rglob("*")):
                if f.suffix.lower() in (".mp3", ".wav", ".flac", ".ogg", ".m4a"):
                    it = QListWidgetItem(f.name); it.setData(Qt.UserRole, str(f)); self.songs.addItem(it)
    def play(self, it):
        if it: self.player.setSource(QUrl.fromLocalFile(it.data(Qt.UserRole))); self.player.play()

    # ---- Programme (Freigabe)
    def build_programs(self):
        l = self.page("Programme – was YAVIS starten darf"); self.plist = QListWidget(); self.plist.setObjectName("l"); l.addWidget(self.plist)
        r = QHBoxLayout()
        for txt, f in [("Startmenü scannen (Apps & Spiele)", self.scan), ("🎮 Spiele scannen (Steam/Epic)", self.scan_games), ("Alle Spiele freigeben", self.allow_games), ("Programm hinzufügen", self.add_prog), ("Auswahl entfernen", self.rm_prog)]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        l.addLayout(r); l.addWidget(QLabel("Haken = YAVIS darf es starten. Webseiten wie YouTube sind immer verfügbar.")); self.plist.itemChanged.connect(self.save_progs); self.refresh_progs()
    def refresh_progs(self):
        self.plist.blockSignals(True); self.plist.clear()
        for p in self.s["programs"]:
            it = QListWidgetItem(("🎮 " if p.get("game") else "") + p["name"]); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Checked if p.get("allowed") else Qt.Unchecked); self.plist.addItem(it)
        self.plist.blockSignals(False)
    def save_progs(self, *_):
        for i, p in enumerate(self.s["programs"]): p["allowed"] = self.plist.item(i).checkState() == Qt.Checked
        core.save_settings(self.s)
    def scan(self):
        have = {p["name"].lower() for p in self.s["programs"]}
        for base in (os.environ.get("ProgramData", ""), os.environ.get("APPDATA", "")):
            for f in Path(base, "Microsoft/Windows/Start Menu/Programs").rglob("*.lnk"):
                if f.stem.lower() not in have and "uninstall" not in f.stem.lower():
                    self.s["programs"].append({"name": f.stem, "path": str(f), "allowed": False}); have.add(f.stem.lower())
        core.save_settings(self.s); self.refresh_progs()
    def scan_games(self):
        new = core.scan_games(self.s["programs"]); self.s["programs"].extend(new); core.save_settings(self.s); self.refresh_progs()
        QMessageBox.information(self, "Spiele", f"{len(new)} neue Spiele gefunden. Setze Haken bei den Spielen, die YAVIS starten darf." if new else "Keine neuen Spiele gefunden (Steam/Epic müssen installiert sein).")
    def allow_games(self):
        if QMessageBox.question(self, "Bestätigen", "YAVIS darf ALLE gefundenen Spiele starten?") == QMessageBox.Yes:
            for p in self.s["programs"]:
                if p.get("game"): p["allowed"] = True
            core.save_settings(self.s); self.refresh_progs()
    def add_prog(self):
        f, _ = QFileDialog.getOpenFileName(self, "Programm wählen", "", "Programme (*.exe *.lnk *.url)")
        if f: self.s["programs"].append({"name": Path(f).stem, "path": f, "allowed": True}); core.save_settings(self.s); self.refresh_progs()
    def rm_prog(self):
        i = self.plist.currentRow()
        if i >= 0: self.s["programs"].pop(i); core.save_settings(self.s); self.refresh_progs()

    # ---- Gedächtnis
    def build_memory(self):
        l = self.page("Gedächtnis (lokal)"); self.mem = QListWidget(); self.mem.setObjectName("l"); l.addWidget(self.mem)
        r = QHBoxLayout()
        for txt, f in [("Aktualisieren", self.load_mem), ("Auswahl löschen", self.del_mem), ("Alles löschen", self.del_all)]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        l.addLayout(r); self.load_mem()
    def load_mem(self):
        self.mem.clear()
        for i, t, ts in core.mem_list(): it = QListWidgetItem(f"{t}  ({ts})"); it.setData(Qt.UserRole, i); self.mem.addItem(it)
    def del_mem(self):
        it = self.mem.currentItem()
        if it: core.mem_delete(it.data(Qt.UserRole)); self.load_mem()
    def del_all(self):
        if QMessageBox.question(self, "Bestätigen", "Wirklich ALLES im Gedächtnis löschen?") == QMessageBox.Yes: core.mem_delete(); self.load_mem()

    # ---- Einstellungen
    def build_settings(self):
        l = self.page("Einstellungen")
        l.addWidget(QLabel("Aktivierungsnamen (mit Komma trennen):")); self.names = QLineEdit(", ".join(self.s["names"])); l.addWidget(self.names)
        l.addWidget(QLabel("Stimme (Windows-Stimmen):")); self.vc = QComboBox()
        for vid, n in voice.list_voices(): self.vc.addItem(n, vid)
        l.addWidget(self.vc)
        l.addWidget(QLabel("Stimm-Stil (Stimme × Stil ergibt über 30 Varianten):")); self.st = QComboBox(); self.st.addItems(core.STYLES); self.st.setCurrentText(self.s["style"]); l.addWidget(self.st)
        l.addWidget(QLabel("Stimmung:")); self.md = QComboBox(); self.md.addItems(core.MOODS); self.md.setCurrentText(self.s["mood"]); l.addWidget(self.md)
        l.addWidget(QLabel("Ollama-Modell:")); self.mo = QLineEdit(self.s["model"]); l.addWidget(self.mo)
        self.sp = QCheckBox("Antworten vorlesen"); self.sp.setChecked(self.s["speak"]); l.addWidget(self.sp)
        b = QPushButton("Speichern + Stimme testen"); b.clicked.connect(self.save_set); l.addWidget(b); l.addStretch()
    def save_set(self):
        self.s.update(names=[n.strip().lower() for n in self.names.text().split(",") if n.strip()], voice_id=self.vc.currentData() or "",
                      style=self.st.currentText(), mood=self.md.currentText(), model=self.mo.text().strip(), speak=self.sp.isChecked())
        core.save_settings(self.s); self.show_reply("", "Einstellungen gespeichert, Master.")

    # ---- Extras
    def run_extra(self, it):
        cmd = it.data(Qt.UserRole); self.nav.setCurrentRow(0)
        if cmd.endswith((" ", ": ")): self.inp.setText(cmd); self.inp.setFocus()
        else: self.process(cmd)
    def build_extras(self):
        l = self.page("Extras"); self.ex = QListWidget(); self.ex.setObjectName("l")
        for name, cmd in EXTRAS:
            it = QListWidgetItem(name); it.setData(Qt.UserRole, cmd); self.ex.addItem(it)
        self.ex.itemDoubleClicked.connect(self.run_extra); l.addWidget(self.ex)
        l.addWidget(QLabel("Doppelklick = ausführen. Verkaufen/Bezahlen/Senden passiert nie ohne deine Bestätigung."))

    # ---- Autopilot
    def build_auto(self):
        l = self.page("Autopilot – YAVIS arbeitet ohne dich")
        info = QLabel("Aufträge laufen wiederholt im Hintergrund, solange YAVIS läuft (auch im Infobereich neben der Uhr). Ergebnisse landen unter Berichte. "
                      "Öffnen, Suchen, Senden, Kaufen, Bezahlen, Löschen u. Ä. führt YAVIS nie allein aus – das wartet auf deine Genehmigung."); info.setWordWrap(True); l.addWidget(info)
        self.jl = QListWidget(); self.jl.setObjectName("l"); l.addWidget(self.jl); self.jl.itemChanged.connect(self.save_jobs)
        r = QHBoxLayout(); self.jc = QLineEdit(); self.jc.setPlaceholderText("Auftrag, z. B. Fasse die wichtigsten Tech-Themen des Tages kurz zusammen")
        self.jm = QLineEdit("60"); self.jm.setFixedWidth(60); ab = QPushButton("Hinzufügen (alle … Min.)"); ab.clicked.connect(self.add_job)
        rb = QPushButton("Auswahl entfernen"); rb.clicked.connect(self.rm_job)
        for w in (self.jc, self.jm, ab, rb): r.addWidget(w)
        l.addLayout(r); l.addWidget(QLabel("Berichte:")); self.rl = QListWidget(); self.rl.setObjectName("l"); l.addWidget(self.rl)
        l.addWidget(QLabel("Wartet auf deine Genehmigung:")); self.al = QListWidget(); self.al.setObjectName("l"); l.addWidget(self.al)
        r2 = QHBoxLayout(); y = QPushButton("Genehmigen + ausführen"); y.clicked.connect(self.approve); n = QPushButton("Ablehnen"); n.clicked.connect(lambda: self.al.takeItem(self.al.currentRow()))
        r2.addWidget(y); r2.addWidget(n); l.addLayout(r2)
        for ts, job, text in reversed(core.report_list()): self.rl.insertItem(0, f"[{ts}] {job}: {text}")
        self.refresh_jobs()
    def refresh_jobs(self):
        self.jl.blockSignals(True); self.jl.clear()
        for j in self.s["autopilot"]:
            it = QListWidgetItem(f"{j['cmd']}  (alle {j['every']} Min.)"); it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if j.get("enabled") else Qt.Unchecked); self.jl.addItem(it)
        self.jl.blockSignals(False)
    def save_jobs(self, *_):
        for i, j in enumerate(self.s["autopilot"]): j["enabled"] = self.jl.item(i).checkState() == Qt.Checked
        core.save_settings(self.s)
    def add_job(self):
        cmd = self.jc.text().strip()
        try: every = max(1, int(self.jm.text()))
        except ValueError: every = 60
        if cmd: self.s["autopilot"].append({"cmd": cmd, "every": every, "enabled": True, "last": 0}); core.save_settings(self.s); self.jc.clear(); self.refresh_jobs()
    def rm_job(self):
        i = self.jl.currentRow()
        if i >= 0: self.s["autopilot"].pop(i); core.save_settings(self.s); self.refresh_jobs()
    def tick_auto(self):
        now = time.time()
        for j in self.s["autopilot"]:
            if j.get("enabled") and now - j.get("last", 0) >= j["every"] * 60:
                j["last"] = now; core.save_settings(self.s)
                def work(cmd=j["cmd"]):
                    st, text = core.run_autopilot(cmd, self.s)
                    if st == "approval": self.bus.approval.emit(cmd)
                    else: core.report_add(cmd, text); self.bus.report.emit(cmd, text)
                threading.Thread(target=work, daemon=True).start()
    def on_report(self, cmd, text):
        self.rl.insertItem(0, f"[{time.strftime('%d.%m. %H:%M')}] {cmd}: {text}"); self.tray.showMessage("YAVIS Bericht", f"{cmd}: {text[:120]}")
    def on_approval(self, cmd):
        if not self.al.findItems(cmd, Qt.MatchExactly): self.al.addItem(cmd); self.tray.showMessage("YAVIS", f"Wartet auf Genehmigung: {cmd}")
    def approve(self):
        it = self.al.currentItem()
        if it and QMessageBox.question(self, "Bestätigen", f"Ausführen: {it.text()} ?") == QMessageBox.Yes:
            cmd = it.text(); self.al.takeItem(self.al.currentRow()); self.nav.setCurrentRow(0); self.process(cmd)

if __name__ == "__main__":
    a = QApplication(sys.argv); a.setStyleSheet(CSS); a.setQuitOnLastWindowClosed(False); w = Main(); w.show(); sys.exit(a.exec())
