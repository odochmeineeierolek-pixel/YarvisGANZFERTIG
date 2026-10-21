import html, json, math, os, re, sys, threading, time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QPen, QFont, QPixmap, QIcon, QShortcut, QKeySequence, QGuiApplication
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget, QTextEdit, QLineEdit, QPushButton,
    QLabel, QComboBox, QFileDialog, QListWidgetItem, QMessageBox, QCheckBox, QSlider, QSystemTrayIcon, QMenu, QFrame, QScrollArea)
import core, voice

CSS = """
*{font-family:'Segoe UI';font-size:13px;color:#e8e8ea}
QWidget{background:#0a0a0c}
QFrame#sidebar{background:#0d0d10;border-right:1px solid #1f1f24}
QFrame#card{background:#131317;border:1px solid #23232a;border-radius:12px}
QFrame#card QWidget{background:transparent}
QLabel{background:transparent}
QLabel#logo{font-size:24px;font-weight:700;color:#ffc400}
QLabel#tiny{font-size:10px;color:#6f6f78}
QLabel#h{font-size:22px;font-weight:600}
QLabel#sub{color:#8a8a93}
QLabel#sec{font-size:14px;font-weight:600;color:#ffc400}
QListWidget#nav{background:transparent;border:none;outline:0}
QListWidget#nav::item{padding:11px 14px;margin:2px 10px;border-radius:8px;color:#a8a8b0}
QListWidget#nav::item:hover{background:#17171c}
QListWidget#nav::item:selected{background:#2a2200;color:#ffc400}
QLineEdit,QComboBox,QTextEdit,QListWidget#l{background:#101014;border:1px solid #26262d;border-radius:8px;padding:7px;selection-background-color:#ffc400;selection-color:#000}
QLineEdit:focus,QComboBox:focus,QTextEdit:focus{border:1px solid #ffc400}
QComboBox QAbstractItemView{background:#101014;selection-background-color:#2a2200;border:1px solid #26262d}
QListWidget#l::item{padding:6px}QListWidget#l::item:selected{background:#2a2200;color:#ffc400}
QPushButton{background:#17171c;border:1px solid #2c2c34;border-radius:8px;padding:8px 14px}
QPushButton:hover{border-color:#ffc400;color:#ffc400}
QPushButton:checked{background:#2a2200;border-color:#ffc400;color:#ffc400}
QPushButton#primary{background:#ffc400;color:#111;border:none;font-weight:600}
QPushButton#primary:hover{background:#ffd54a;color:#000}
QPushButton#danger{border-color:#e5333b;color:#e5333b}
QPushButton#danger:hover{background:#e5333b;color:#fff}
QSlider::groove:horizontal{background:#2a2a31;height:5px;border-radius:2px}
QSlider::sub-page:horizontal{background:#e5333b;border-radius:2px}
QSlider::handle:horizontal{background:#ffc400;width:14px;margin:-5px 0;border-radius:7px}
QScrollArea{border:none}
QScrollBar:vertical{background:transparent;width:10px}QScrollBar::handle:vertical{background:#2c2c34;border-radius:5px;min-height:30px}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
QCheckBox::indicator{width:16px;height:16px;border:1px solid #2c2c34;border-radius:4px;background:#101014}
QCheckBox::indicator:checked{background:#ffc400;border-color:#ffc400}
QToolTip{background:#131317;color:#fff;border:1px solid #ffc400}
"""

EXTRAS = [
 ("🎲 Würfeln", "würfeln"), ("🪙 Münze werfen", "münze"), ("🔢 Zufallszahl", "zufallszahl"), ("🔐 Passwort erzeugen", "passwort"),
 ("🧮 Rechnen (z. B. rechne 12*7)", "rechne "), ("📅 Datum & Wochentag", "datum"), ("🕒 Uhrzeit", "wie spät ist es"), ("💻 Systeminfo", "systeminfo"),
 ("⏱ Timer 5 Minuten", "timer 5 minuten"), ("📝 Notiz machen (notiz: …)", "notiz: "), ("📖 Notizen anzeigen", "notizen"), ("✅ Aufgabe notieren (aufgabe: …)", "aufgabe: "),
 ("📋 Meine Aufgaben", "meine aufgaben"), ("💬 Zitat", "zitat"), ("🧮 Windows-Rechner öffnen", "öffne rechner"), ("📓 Editor öffnen", "öffne notepad"),
 ("📁 Explorer öffnen", "öffne explorer"), ("📊 Task-Manager öffnen", "öffne taskmanager"), ("⚙ Windows-Einstellungen", "öffne einstellungen"), ("✂ Snipping-Tool", "öffne snipping"),
 ("🌐 ChatGPT-Frage (frage chatgpt …)", "frage chatgpt "), ("▶ YouTube öffnen", "youtube"), ("🔎 YouTube-Suche (youtube suche …)", "youtube suche "), ("🌐 Google-Suche (suche nach …)", "suche nach "), ("🎵 Spotify öffnen", "spotify"),
 ("😂 Witz erzählen", "Erzähl mir einen kurzen, lustigen Witz"), ("🧩 Rätsel", "Gib mir ein kurzes Rätsel und warte auf meine Antwort"), ("🎤 Rap über mich", "Schreibe einen kurzen lustigen Rap über den Master"),
 ("📜 Gedicht", "Schreibe ein kurzes Gedicht"), ("🌙 Gute-Nacht-Geschichte", "Erzähle eine sehr kurze Gute-Nacht-Geschichte"), ("🤓 Fakt des Tages", "Nenne einen überraschenden Fakt"),
 ("🗓 Tagesplan", "Plane meinen Arbeitstag, stelle mir zuerst Rückfragen"), ("✉ E-Mail-Entwurf", "Hilf mir, eine E-Mail zu schreiben, frage mich nach Details"), ("💼 Angebot vorbereiten", "Hilf mir, ein Angebot vorzubereiten, frage mich nach Details"),
 ("🛒 Produkt beschreiben", "Hilf mir, ein Produkt für den Verkauf zu beschreiben, frage mich nach Details"), ("💶 Preis recherchieren", "suche nach Gebrauchtpreis "), ("💡 Geschäftsidee prüfen", "Hilf mir, eine Geschäftsidee ehrlich zu analysieren"),
 ("🌍 Übersetzer", "Übersetze für mich ins Englische: "), ("📚 Lernplan", "Erstelle mir einen kurzen Lernplan, frage nach Thema und Zeit"), ("🍳 Rezept-Idee", "Schlage ein einfaches Rezept vor"),
 ("🏋 Workout-Idee", "Schlage ein kurzes Heim-Workout vor"), ("✈ Reiseplan", "Hilf mir, eine Reise zu planen, frage nach Ziel und Budget"), ("💻 Code-Hilfe", "Hilf mir bei einem Programmierproblem, frage nach Details"),
 ("😊 Stimmung: lieb", "sei lieb"), ("😠 Stimmung: böse", "sei böse"), ("😢 Stimmung: traurig", "sei traurig"), ("😐 Stimmung: neutral", "sei neutral"),
]


def make_icon():
    pm = QPixmap(64, 64); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(0, 0, 0)); p.setPen(QPen(QColor(229, 51, 59), 6)); p.drawEllipse(6, 6, 52, 52)
    p.setPen(QPen(QColor(255, 196, 0), 3)); p.drawEllipse(14, 14, 36, 36); p.end(); return QIcon(pm)

def card():
    f = QFrame(); f.setObjectName("card"); l = QVBoxLayout(f); l.setContentsMargins(16, 14, 16, 14); l.setSpacing(8); return f, l

def sec(text):
    t = QLabel(text); t.setObjectName("sec"); return t

class Orb(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(170); self.level = 0.0; self.t = 0; self.active = False
        QTimer(self, timeout=self.tick, interval=33).start()
    def tick(self):
        self.t += 1; target = 0.5 + 0.5 * abs(math.sin(self.t / 4)) if self.active else 0.05
        self.level += (target - self.level) * 0.25; self.update()
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        c = self.rect().center(); r = 42 + 34 * self.level
        g = QRadialGradient(c, r * 1.7); g.setColorAt(0, QColor(255, 196, 0, 190)); g.setColorAt(.6, QColor(229, 51, 59, 110)); g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(g); p.setPen(Qt.NoPen); p.drawEllipse(c, r * 1.7, r * 1.7)
        p.setBrush(QColor(8, 8, 10)); p.setPen(QPen(QColor(229, 51, 59), 4)); p.drawEllipse(c, r, r)
        p.setPen(QPen(QColor(255, 196, 0), 2)); p.drawEllipse(c, r - 6, r - 6)
        p.setPen(QColor(255, 255, 255)); p.setFont(QFont("Segoe UI", 12, QFont.Bold)); p.drawText(self.rect(), Qt.AlignCenter, "YAVIS")

class Bus(QObject):
    reply = Signal(str, str); answer = Signal(str, str, object, int, bool); heard = Signal(str); done = Signal()
    report = Signal(str, str); approval = Signal(str); sysmsg = Signal(str); state = Signal(str); info = Signal(str)
    ollama = Signal(bool); alwaysoff = Signal()

class Main(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle("YAVIS"); self.resize(1200, 780); self.setWindowIcon(make_icon())
        self.s = core.load_settings(); self.last = ("", ""); self._quit = False; self.web = None; self.web_loaded = False; self.always = False; self.ok_ollama = None
        if not self.s.get("catalog_added"):
            self.s["programs"].extend(core.add_catalog(self.s["programs"])); self.s["catalog_added"] = True; core.save_settings(self.s)
        self.convs = core.load_convs(); self.cur = 0; self.bus = Bus()
        b = self.bus; b.reply.connect(self.show_reply); b.answer.connect(self.on_answer); b.heard.connect(self.process); b.done.connect(self.on_done)
        b.report.connect(self.on_report); b.approval.connect(self.on_approval); b.sysmsg.connect(lambda t: self.append("System", t))
        b.state.connect(self.set_state); b.info.connect(lambda t: self.mic_info.setText(t)); b.ollama.connect(self.on_ollama); b.alwaysoff.connect(lambda: self.alw.setChecked(False))
        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        side = QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(220); sl = QVBoxLayout(side); sl.setContentsMargins(0, 22, 0, 16)
        logo = QLabel("Y  A  V  I  S"); logo.setObjectName("logo"); logo.setContentsMargins(22, 0, 0, 0); tiny = QLabel("PERSÖNLICHER ASSISTENT"); tiny.setObjectName("tiny"); tiny.setContentsMargins(22, 0, 0, 14)
        sl.addWidget(logo); sl.addWidget(tiny)
        self.nav = QListWidget(); self.nav.setObjectName("nav")
        for n in ["💬   Chat", "🌐   ChatGPT", "🎵   Musik", "🖥   Programme", "🧠   Gedächtnis", "⚙   Einstellungen", "✨   Extras", "🤖   Autopilot"]: self.nav.addItem(n)
        sl.addWidget(self.nav, 1)
        vl = QLabel("🔊  Lautstärke"); vl.setContentsMargins(22, 0, 0, 0); sl.addWidget(vl)
        self.vol = QSlider(Qt.Horizontal); self.vol.setRange(0, 100); self.vol.setValue(int(self.s["volume"])); self.vol.valueChanged.connect(self.set_vol)
        vw = QWidget(); vwl = QHBoxLayout(vw); vwl.setContentsMargins(22, 4, 22, 0); vwl.addWidget(self.vol); sl.addWidget(vw)
        right = QVBoxLayout(); right.setSpacing(0); self.pages = QStackedWidget(); right.addWidget(self.pages, 1)
        self.sbar = QLabel(""); self.sbar.setContentsMargins(24, 6, 24, 8); self.sbar.setObjectName("tiny"); right.addWidget(self.sbar)
        root.addWidget(side); root.addLayout(right, 1)
        self.build_chat(); self.build_gpt(); self.build_music(); self.build_programs(); self.build_memory(); self.build_settings(); self.build_extras(); self.build_auto()
        self.nav.currentRowChanged.connect(self.on_nav)
        QShortcut(QKeySequence("Esc"), self, activated=self.interrupt); QShortcut(QKeySequence("Ctrl+Space"), self, activated=self.listen)
        self.tray = QSystemTrayIcon(make_icon(), self); m = QMenu(); m.addAction("YAVIS öffnen", self.showNormal); m.addAction("Beenden", self.quit_app)
        self.tray.setContextMenu(m); self.tray.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.Trigger else None); self.tray.show()
        QTimer(self, timeout=self.poll, interval=1000).start(); QTimer(self, timeout=self.tick_auto, interval=30000).start()
        threading.Thread(target=lambda: self.bus.ollama.emit(core.ollama_ok(self.s["host"])), daemon=True).start()
        threading.Thread(target=voice.preload, args=(self.s["stt_model"],), daemon=True).start()
        self.nav.setCurrentRow(0); self.refresh_status(); self.show_reply("", "Hallo Master, YAVIS ist bereit.", True)

    # ---- Allgemein
    def page(self, title, sub=""):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(26, 22, 26, 8); l.setSpacing(12)
        h = QLabel(title); h.setObjectName("h"); l.addWidget(h)
        if sub: s = QLabel(sub); s.setObjectName("sub"); s.setWordWrap(True); l.addWidget(s)
        self.pages.addWidget(w); return l
    def on_nav(self, i):
        self.pages.setCurrentIndex(i)
        if i == 1 and self.web is not None and not self.web_loaded: self.web.setUrl(QUrl("https://chatgpt.com/")); self.web_loaded = True
    def set_vol(self, v): self.s["volume"] = v; core.save_settings(self.s); self.ao.setVolume(v / 100)
    def set_state(self, t): self.state.setText(t)
    def on_ollama(self, ok): self.ok_ollama = ok; self.refresh_status()
    def refresh_status(self):
        o = {None: "<span style='color:#8a8a93'>●</span> Ollama wird geprüft", True: "<span style='color:#3ddc84'>●</span> Ollama bereit",
             False: "<span style='color:#e5333b'>●</span> Ollama nicht erreichbar (installieren & starten)"}[self.ok_ollama]
        v = voice.PROFILE_BY_ID.get(self.s["voice_profile"], {}).get("label", "?")
        self.sbar.setText(f"{o}   |   Stimme: {v}   |   Stimmung: {self.s['mood']}   |   Dauerhaft zuhören: {'an' if self.always else 'aus'}")
    def quit_app(self): self._quit = True; QApplication.quit()
    def closeEvent(self, e):
        if self._quit: e.accept(); return
        e.ignore(); self.hide(); self.tray.showMessage("YAVIS", "Läuft im Hintergrund weiter (Autopilot). Beenden über das Symbol unten rechts.")

    # ---- Chat
    def build_chat(self):
        l = self.page("Chat", "Schreibe oder sprich. Im Modus „Dauerhaft zuhören“ reagiert YAVIS auf „Hallo“ oder seinen Namen. Esc unterbricht.")
        oc, ol = card(); self.orb = Orb(); ol.addWidget(self.orb); self.state = QLabel("Bereit"); self.state.setAlignment(Qt.AlignCenter); self.state.setObjectName("sub"); ol.addWidget(self.state); l.addWidget(oc)
        top = QHBoxLayout(); self.cc = QComboBox(); self.cc.currentIndexChanged.connect(self.switch_conv)
        nb = QPushButton("+ Neues Gespräch"); nb.clicked.connect(self.new_conv); db_ = QPushButton("Löschen"); db_.clicked.connect(self.del_conv)
        top.addWidget(self.cc, 1); top.addWidget(nb); top.addWidget(db_); l.addLayout(top)
        self.log = QTextEdit(readOnly=True); l.addWidget(self.log, 1)
        row = QHBoxLayout(); self.inp = QLineEdit(); self.inp.setPlaceholderText("Nachricht eingeben …"); self.inp.returnPressed.connect(self.send)
        b1 = QPushButton("Senden"); b1.setObjectName("primary"); b1.clicked.connect(self.send)
        b2 = QPushButton("🎤  Sprechen"); b2.clicked.connect(self.listen)
        self.alw = QPushButton("🎧  Dauerhaft zuhören"); self.alw.setCheckable(True); self.alw.toggled.connect(self.toggle_always)
        b3 = QPushButton("■  Stopp"); b3.setObjectName("danger"); b3.clicked.connect(self.stop)
        up = QPushButton("👍"); up.clicked.connect(lambda: self.fb(1)); dn = QPushButton("👎"); dn.clicked.connect(lambda: self.fb(0))
        for w in (self.inp,): row.addWidget(w, 1)
        for w in (b1, b2, self.alw, b3, up, dn): row.addWidget(w)
        l.addLayout(row); self.refresh_convs()
    def conv(self): return self.convs[self.cur]
    def refresh_convs(self):
        self.cc.blockSignals(True); self.cc.clear(); self.cc.addItems([c["title"] for c in self.convs]); self.cc.setCurrentIndex(self.cur); self.cc.blockSignals(False)
        self.log.setHtml("".join(self.conv()["lines"]))
    def switch_conv(self, i):
        if 0 <= i < len(self.convs) and i != self.cur: self.cur = i; self.log.setHtml("".join(self.conv()["lines"]))
    def new_conv(self):
        self.convs.append({"title": f"Gespräch {len(self.convs) + 1}", "hist": [], "lines": [], "gen": 0, "named": False}); self.cur = len(self.convs) - 1; self.refresh_convs()
    def del_conv(self):
        if len(self.convs) > 1: self.convs.pop(self.cur); self.cur = 0; self.refresh_convs(); core.save_convs(self.convs)
    def interrupt(self):
        self.conv()["gen"] += 1; voice.stop_speaking(); self.orb.active = False; self.set_state("Bereit")
    def poll(self):
        while not core.PENDING.empty(): self.show_reply("", core.PENDING.get())
    def append(self, who, t, c=None):
        c = c or self.conv(); col = {"YAVIS": "#ffc400", "Du": "#e5333b"}.get(who, "#8a8a93")
        line = f"<p style='margin:8px 0'><span style='color:{col};font-weight:600'>{who}</span><br>{html.escape(t)}</p>"; c["lines"].append(line)
        if c is self.conv(): self.log.append(line)
    def send(self):
        t = self.inp.text().strip(); self.inp.clear()
        if t: self.process(t)
    def process(self, text):
        self.interrupt(); c = self.conv(); c["gen"] += 1; g = c["gen"]
        _, rest = core.strip_wake(text, self.s["names"]); rest = rest or text
        if not c["named"]: c["title"] = rest[:28]; c["named"] = True; self.cc.setItemText(self.cur, c["title"])
        self.append("Du", text)
        m = re.match(r"^(frage|öffne|starte)\s+chat\s?gpt[,:]?\s*(.*)$", rest, flags=re.I)
        if m: self.to_chatgpt(m.group(2).strip()); return
        self.set_state("Denke nach …")
        def work():
            ans = core.handle_command(rest, self.s); llm = ans is None
            if llm:
                c["hist"].append({"role": "user", "content": rest}); ans = core.ask_ollama(c["hist"], self.s)
            self.bus.answer.emit(rest, ans, c, g, llm)
        threading.Thread(target=work, daemon=True).start()
    def on_answer(self, q, a, c, g, llm):
        if c not in self.convs or g != c["gen"]: return
        a = core.clean_master(a)
        if llm: c["hist"].append({"role": "assistant", "content": a})
        self.append("YAVIS", a, c); self.last = (q, a); core.save_convs(self.convs)
        if c is self.conv(): self.speak(a)
        else: self.set_state("Bereit")
    def show_reply(self, q, a, greet=False):
        if not greet: a = core.clean_master(a)
        self.last = (q, a); self.append("YAVIS", a); self.speak(a)
    def speak(self, a):
        if not self.s["speak"]: self.set_state("Bereit"); return
        self.orb.active = True; self.set_state("Spreche …")
        voice.speak(a, self.s["voice_profile"], self.s["mood"], self.bus.done.emit, self.s["volume"] / 100, self.bus.sysmsg.emit)
    def on_done(self): self.orb.active = False; self.set_state("Bereit")
    def listen(self):
        self.interrupt(); self.set_state("Höre zu …")
        def w():
            try: t = voice.listen(self.s)
            except Exception as e: self.bus.sysmsg.emit(f"Spracherkennung nicht verfügbar: {e}"); self.bus.state.emit("Bereit"); return
            if t: self.bus.heard.emit(t)
            else: self.bus.state.emit("Bereit")
        threading.Thread(target=w, daemon=True).start()
    def toggle_always(self, on):
        self.always = on; self.refresh_status()
        if on: threading.Thread(target=self.listen_loop, daemon=True).start()
    def listen_loop(self):
        while self.always:
            if voice.is_speaking(): time.sleep(0.25); continue
            try: t = voice.listen(self.s, max_s=15, idle_timeout=4)
            except Exception as e: self.bus.sysmsg.emit(f"Dauerhaft zuhören gestoppt: {e}"); self.always = False; self.bus.alwaysoff.emit(); return
            if t and core.strip_wake(t, self.s["names"])[0]: self.bus.heard.emit(t)   # ohne Namen/„Hallo“ wird nichts verarbeitet
    def stop(self): self.interrupt(); self.player.stop()
    def fb(self, good):
        if self.last[1]: core.feedback_add(self.last[0], self.last[1], good); self.append("System", "Danke, ich merke mir das lokal.")

    # ---- ChatGPT
    def build_gpt(self):
        l = self.page("ChatGPT", "Dein ChatGPT-Konto direkt in YAVIS. Kostenlos nutzbar (Login bei OpenAI nötig). Sag: „Yavis, frage ChatGPT …“")
        r = QHBoxLayout()
        for txt, f in [("⟳ Neu laden", lambda: self.web and self.web.reload()), ("Im Browser öffnen", lambda: __import__("webbrowser").open("https://chatgpt.com/")),
                       ("Letzte Frage einfügen", lambda: self.to_chatgpt(self.last[0]))]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        r.addStretch(); l.addLayout(r)
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
            self.web = QWebEngineView(); prof = QWebEngineProfile("yavis-chatgpt", self.web); prof.setPersistentStoragePath(str(core.APP_DIR / "web"))
            self.web.setPage(QWebEnginePage(prof, self.web)); l.addWidget(self.web, 1)
        except Exception:
            self.web = None; t = QLabel("Die eingebettete Ansicht ist nicht verfügbar. Nutze „Im Browser öffnen“."); l.addWidget(t); l.addStretch()
    def to_chatgpt(self, q):
        self.nav.setCurrentRow(1)
        if q: QGuiApplication.clipboard().setText(q)
        if self.web is None:
            __import__("webbrowser").open("https://chatgpt.com/"); self.append("YAVIS", "ChatGPT ist im Browser geöffnet. Deine Frage liegt in der Zwischenablage (Strg+V)."); return
        if q:
            js = "(function(t){var e=document.querySelector('#prompt-textarea');if(!e)return false;e.focus();document.execCommand('insertText',false,t);return true;})(" + json.dumps(q) + ")"
            QTimer.singleShot(1500 if not self.web_loaded else 100, lambda: self.web.page().runJavaScript(js))
        self.append("YAVIS", "ChatGPT ist offen. Deine Frage steht im Eingabefeld (sonst Strg+V). Zum Senden Enter drücken.")

    # ---- Musik
    def build_music(self):
        l = self.page("Musik", "Spiele deine Dateien (MP3, WAV, FLAC, OGG, M4A) direkt in YAVIS ab."); self.player = QMediaPlayer(); self.ao = QAudioOutput(); self.player.setAudioOutput(self.ao); self.ao.setVolume(self.s["volume"] / 100)
        self.songs = QListWidget(); self.songs.setObjectName("l"); self.songs.itemDoubleClicked.connect(self.play); l.addWidget(self.songs, 1)
        r = QHBoxLayout()
        for txt, f in [("Ordner wählen", self.pick_music), ("▶ Abspielen", lambda: self.play(self.songs.currentItem())), ("⏸ Pause", lambda: self.player.pause()), ("■ Stopp", lambda: self.player.stop())]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        r.addStretch(); l.addLayout(r); self.load_music()
    def pick_music(self):
        d = QFileDialog.getExistingDirectory(self, "Musikordner")
        if d: self.s["music_dir"] = d; core.save_settings(self.s); self.load_music()
    def load_music(self):
        self.songs.clear(); d = Path(self.s["music_dir"] or Path.home() / "Music")
        if d.exists():
            for f in sorted(d.rglob("*")):
                if f.suffix.lower() in (".mp3", ".wav", ".flac", ".ogg", ".m4a"):
                    it = QListWidgetItem(f.name); it.setData(Qt.UserRole, str(f)); self.songs.addItem(it)
    def play(self, it):
        if it: self.player.setSource(QUrl.fromLocalFile(it.data(Qt.UserRole))); self.player.play()

    # ---- Programme
    def build_programs(self):
        l = self.page("Programme & Spiele", "Haken = YAVIS darf es starten. Websites wie YouTube sind immer verfügbar.")
        self.plist = QListWidget(); self.plist.setObjectName("l"); l.addWidget(self.plist, 1)
        r = QHBoxLayout()
        for txt, f in [("Standard-Programme (32)", self.add_cat), ("🎮 Spiele scannen", self.scan_games), ("Alle Spiele freigeben", self.allow_games), ("Startmenü scannen", self.scan), ("Hinzufügen", self.add_prog), ("Entfernen", self.rm_prog)]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        l.addLayout(r); self.plist.itemChanged.connect(self.save_progs); self.refresh_progs()
    def refresh_progs(self):
        self.plist.blockSignals(True); self.plist.clear()
        for p in self.s["programs"]:
            it = QListWidgetItem(("🎮 " if p.get("game") else "") + p["name"]); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Checked if p.get("allowed") else Qt.Unchecked); self.plist.addItem(it)
        self.plist.blockSignals(False)
    def save_progs(self, *_):
        for i, p in enumerate(self.s["programs"]): p["allowed"] = self.plist.item(i).checkState() == Qt.Checked
        core.save_settings(self.s)
    def add_cat(self):
        new = core.add_catalog(self.s["programs"]); self.s["programs"].extend(new); core.save_settings(self.s); self.refresh_progs()
        QMessageBox.information(self, "Programme", f"{len(new)} Standard-Programme hinzugefügt (Windows-Tools, Browser, Launcher).")
    def scan(self):
        have = {p["name"].lower() for p in self.s["programs"]}
        for base in (os.environ.get("ProgramData", ""), os.environ.get("APPDATA", "")):
            for f in Path(base, "Microsoft/Windows/Start Menu/Programs").rglob("*.lnk"):
                if f.stem.lower() not in have and "uninstall" not in f.stem.lower():
                    self.s["programs"].append({"name": f.stem, "path": str(f), "allowed": False}); have.add(f.stem.lower())
        core.save_settings(self.s); self.refresh_progs()
    def scan_games(self):
        new = core.scan_games(self.s["programs"]); self.s["programs"].extend(new); core.save_settings(self.s); self.refresh_progs()
        QMessageBox.information(self, "Spiele", f"{len(new)} neue Spiele gefunden. Setze Haken bei den Spielen, die YAVIS starten darf." if new else "Keine neuen Spiele gefunden (Steam/Epic nötig).")
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
        l = self.page("Gedächtnis", "Alles liegt lokal auf deinem PC. Du kannst jederzeit einzelne Einträge oder alles löschen."); self.mem = QListWidget(); self.mem.setObjectName("l"); l.addWidget(self.mem, 1)
        r = QHBoxLayout()
        for txt, f in [("Aktualisieren", self.load_mem), ("Auswahl löschen", self.del_mem), ("Alles löschen", self.del_all)]:
            b = QPushButton(txt); b.clicked.connect(f); r.addWidget(b)
        r.addStretch(); l.addLayout(r); self.load_mem()
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
        outer = self.page("Einstellungen", "Stimme, Mikrofon und Namen. Änderungen mit „Speichern“ übernehmen.")
        sa = QScrollArea(); sa.setWidgetResizable(True); host = QWidget(); hl = QVBoxLayout(host); hl.setContentsMargins(0, 0, 8, 0); hl.setSpacing(12); sa.setWidget(host); outer.addWidget(sa, 1)
        c1, l1 = card(); l1.addWidget(sec("Stimme")); self.vc = QComboBox()
        for p in voice.PROFILES: self.vc.addItem(p["label"], p["id"])
        self.vc.setCurrentIndex(max(0, self.vc.findData(self.s["voice_profile"]))); l1.addWidget(self.vc)
        l1.addWidget(QLabel("Stimmung (Gefühle):")); self.md = QComboBox(); self.md.addItems(core.MOODS); self.md.setCurrentText(self.s["mood"]); l1.addWidget(self.md)
        self.sp = QCheckBox("Antworten vorlesen"); self.sp.setChecked(self.s["speak"]); l1.addWidget(self.sp)
        pv = QPushButton("▶ Stimme anhören"); pv.clicked.connect(self.preview); l1.addWidget(pv)
        n1 = QLabel("Neuronale Offline-Stimmen (Piper). Beim ersten Benutzen lädt YAVIS die Basisstimme einmalig herunter (ca. 20–70 MB, kostenlos)."); n1.setObjectName("sub"); n1.setWordWrap(True); l1.addWidget(n1); hl.addWidget(c1)
        c2, l2 = card(); l2.addWidget(sec("Mikrofon & Zuhören")); l2.addWidget(QLabel("Mikrofon:")); self.dev = QComboBox(); self.dev.addItem("Standard-Mikrofon", None)
        for i, n in voice.input_devices(): self.dev.addItem(n, i)
        self.dev.setCurrentIndex(max(0, self.dev.findData(self.s["mic_device"]))); l2.addWidget(self.dev)
        self.mt = QSlider(Qt.Horizontal); self.mt.setRange(3, 50); self.mt.setValue(int(self.s["mic_threshold"] * 1000)); self.mtl = QLabel(); l2.addWidget(self.mtl); l2.addWidget(self.mt)
        self.ms = QSlider(Qt.Horizontal); self.ms.setRange(4, 20); self.ms.setValue(int(self.s["mic_silence"] * 10)); self.msl = QLabel(); l2.addWidget(self.msl); l2.addWidget(self.ms)
        self.mt.valueChanged.connect(self.upd_mic); self.ms.valueChanged.connect(self.upd_mic); self.upd_mic()
        l2.addWidget(QLabel("Erkennungsmodell (tiny = am schnellsten, small = am genauesten):")); self.stt = QComboBox(); self.stt.addItems(["tiny", "base", "small"]); self.stt.setCurrentText(self.s["stt_model"]); l2.addWidget(self.stt)
        tb = QPushButton("🎙 Mikrofon testen (3 Sekunden sprechen)"); tb.clicked.connect(self.mic_test); l2.addWidget(tb); self.mic_info = QLabel(""); self.mic_info.setObjectName("sub"); self.mic_info.setWordWrap(True); l2.addWidget(self.mic_info); hl.addWidget(c2)
        c3, l3 = card(); l3.addWidget(sec("KI & Aktivierungsnamen")); l3.addWidget(QLabel("Aktivierungsnamen (mit Komma trennen, z. B. yavis, jarvis, hallo):")); self.names = QLineEdit(", ".join(self.s["names"])); l3.addWidget(self.names)
        l3.addWidget(QLabel("Ollama-Modell:")); self.mo = QLineEdit(self.s["model"]); l3.addWidget(self.mo); hl.addWidget(c3)
        sv = QPushButton("Speichern"); sv.setObjectName("primary"); sv.clicked.connect(self.save_set); hl.addWidget(sv); hl.addStretch()
    def upd_mic(self):
        self.mtl.setText(f"Empfindlichkeit (Schwelle {self.mt.value() / 1000:.3f} – niedriger = hört leisere Stimmen):"); self.msl.setText(f"Pause am Satzende: {self.ms.value() / 10:.1f} s (kürzer = schnellere Antwort)")
    def collect(self):
        self.s.update(names=[n.strip().lower() for n in self.names.text().split(",") if n.strip()], voice_profile=self.vc.currentData(), mood=self.md.currentText(),
                      model=self.mo.text().strip(), speak=self.sp.isChecked(), mic_device=self.dev.currentData(), mic_threshold=self.mt.value() / 1000,
                      mic_silence=self.ms.value() / 10, stt_model=self.stt.currentText())
    def save_set(self):
        self.collect(); core.save_settings(self.s); self.refresh_status(); self.append("System", "Einstellungen gespeichert.")
        threading.Thread(target=voice.preload, args=(self.s["stt_model"],), daemon=True).start()
    def preview(self):
        self.collect(); voice.stop_speaking(); self.orb.active = True
        voice.speak("Hallo Master, so klinge ich. Wie gefällt dir meine Stimme?", self.s["voice_profile"], self.s["mood"], self.bus.done.emit, self.s["volume"] / 100, self.bus.sysmsg.emit)
    def mic_test(self):
        self.collect(); self.mic_info.setText("Sprich jetzt 3 Sekunden …")
        def w():
            try:
                peak, noise = voice.mic_test(self.s["mic_device"]); rec = int(min(0.05, max(0.004, noise * 3, peak * 0.15)) * 1000)
                msg = f"Sprechpegel {peak:.3f}, Hintergrund {noise:.3f}. Empfohlene Empfindlichkeit: {rec / 1000:.3f}."
                if peak < 0.02: msg += " Dein Mikrofon ist sehr leise – stelle in Windows (Einstellungen → Sound → Eingabe) die Lautstärke höher."
                self.bus.info.emit(msg)
            except Exception as e: self.bus.info.emit(f"Mikrofon-Test nicht möglich: {e}")
        threading.Thread(target=w, daemon=True).start()

    # ---- Extras
    def build_extras(self):
        l = self.page("Extras", "Doppelklick startet die Funktion. Verkaufen, Bezahlen oder Senden passiert nie ohne deine Bestätigung."); self.ex = QListWidget(); self.ex.setObjectName("l")
        for name, cmd in EXTRAS: it = QListWidgetItem(name); it.setData(Qt.UserRole, cmd); self.ex.addItem(it)
        self.ex.itemDoubleClicked.connect(self.run_extra); l.addWidget(self.ex, 1)
    def run_extra(self, it):
        cmd = it.data(Qt.UserRole); self.nav.setCurrentRow(0)
        if cmd.endswith((" ", ": ")): self.inp.setText(cmd); self.inp.setFocus()
        else: self.process(cmd)

    # ---- Autopilot
    def build_auto(self):
        l = self.page("Autopilot", "YAVIS arbeitet im Hintergrund, solange er läuft (auch im Infobereich). Öffnen, Suchen, Senden, Kaufen, Bezahlen, Löschen führt er nie allein aus – das wartet auf deine Genehmigung.")
        self.jl = QListWidget(); self.jl.setObjectName("l"); l.addWidget(self.jl); self.jl.itemChanged.connect(self.save_jobs)
        r = QHBoxLayout(); self.jc = QLineEdit(); self.jc.setPlaceholderText("Auftrag, z. B. Fasse die wichtigsten Tech-Themen des Tages kurz zusammen")
        self.jm = QLineEdit("60"); self.jm.setFixedWidth(60); ab = QPushButton("Hinzufügen (alle … Min.)"); ab.setObjectName("primary"); ab.clicked.connect(self.add_job)
        rb = QPushButton("Entfernen"); rb.clicked.connect(self.rm_job)
        r.addWidget(self.jc, 1); r.addWidget(self.jm); r.addWidget(ab); r.addWidget(rb); l.addLayout(r)
        l.addWidget(sec("Berichte")); self.rl = QListWidget(); self.rl.setObjectName("l"); l.addWidget(self.rl, 1)
        l.addWidget(sec("Wartet auf deine Genehmigung")); self.al = QListWidget(); self.al.setObjectName("l"); l.addWidget(self.al)
        r2 = QHBoxLayout(); y = QPushButton("Genehmigen & ausführen"); y.setObjectName("primary"); y.clicked.connect(self.approve); n = QPushButton("Ablehnen"); n.clicked.connect(lambda: self.al.takeItem(self.al.currentRow()))
        r2.addWidget(y); r2.addWidget(n); r2.addStretch(); l.addLayout(r2)
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
