"""Sprache: Piper (neuronale, kostenlose Offline-Stimmen) mit Windows-Fallback + lokale Spracherkennung."""
import collections, io, json, re, threading, time, urllib.request, wave
from core import APP_DIR, STYLES

VOICE_DIR = APP_DIR / "voices"
BASES = {"eva_k": "x_low", "kerstin": "low", "ramona": "low", "karlsson": "low", "pavoque": "low",
         "thorsten": "medium", "thorsten_emotional": "medium"}
URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/{n}/{q}/de_DE-{n}-{q}.onnx"

# (Schlüssel, Beschriftung, Tonhöhe, Tempo-Faktor (>1 = langsamer), Ausdruck)
F_STYLES = [("warm", "reif & warm", 0.93, 1.12, 0.6), ("sanft", "sanft & ruhig", 1.0, 1.22, 0.45), ("jung", "jung & frisch", 1.12, 0.95, 0.7),
            ("energisch", "energisch", 1.05, 0.88, 0.75), ("souveraen", "souverän", 0.9, 1.02, 0.6)]
M_STYLES = [("hart", "hart", 0.87, 0.9, 0.75), ("tief", "tief & ruhig", 0.8, 1.12, 0.55), ("ruhig", "ruhig", 0.95, 1.18, 0.5),
            ("energisch", "energisch", 1.0, 0.86, 0.8), ("jung", "jung", 1.1, 0.95, 0.7)]
EMOTIONS = [("neutral", "neutral"), ("angry", "wütend"), ("sleepy", "müde"), ("whisper", "flüsternd"), ("surprised", "überrascht"), ("amused", "amüsiert")]


def _build():
    out = []
    for base, name in (("eva_k", "Eva"), ("kerstin", "Kerstin"), ("ramona", "Ramona")):
        for k, lab, p, l, n in F_STYLES: out.append({"id": f"{base}_{k}", "label": f"♀ {name} – {lab}", "base": base, "pitch": p, "length": l, "noise": n})
    for base, name in (("karlsson", "Karlsson"), ("pavoque", "Pavoque"), ("thorsten", "Thorsten")):
        for k, lab, p, l, n in M_STYLES: out.append({"id": f"{base}_{k}", "label": f"♂ {name} – {lab}", "base": base, "pitch": p, "length": l, "noise": n})
    for e, lab in EMOTIONS:
        out.append({"id": f"thorsten_emotional_{e}", "label": f"♂ Thorsten – {lab}", "base": "thorsten_emotional", "pitch": 1.0, "length": 1.0, "noise": 0.667, "emotion": e})
    return out

PROFILES = _build()
PROFILE_BY_ID = {p["id"]: p for p in PROFILES}
MOODS_V = {"neutral": (1.0, 1.0, None), "lieb": (1.03, 1.05, None), "traurig": (0.96, 1.2, "sleepy"), "böse": (0.96, 0.88, "angry")}

_token = 0; _lock = threading.Lock(); _speaking = False; _cache = {}; _sapi_engine = None


def is_speaking(): return _speaking


def ensure_model(base, status=None):
    q = BASES[base]; VOICE_DIR.mkdir(parents=True, exist_ok=True)
    f = VOICE_DIR / f"de_DE-{base}-{q}.onnx"; j = VOICE_DIR / f"de_DE-{base}-{q}.onnx.json"
    url = URL.format(n=base, q=q)
    for path, u in ((j, url + ".json"), (f, url)):
        if not path.exists():
            if status: status(f"Lade Stimme „{base}“ einmalig herunter (kostenlos) …")
            tmp = path.with_name(path.name + ".part"); urllib.request.urlretrieve(u, tmp); tmp.rename(path)
    return f, j


def _load(base, status=None):
    if base not in _cache:
        from piper import PiperVoice
        f, j = ensure_model(base, status); _cache[base] = (PiperVoice.load(str(f), config_path=str(j)), j)
    return _cache[base]


def _speak_piper(text, pid, mood, volume, my, status):
    import numpy as np, sounddevice as sd
    from piper import SynthesisConfig
    prof = PROFILE_BY_ID.get(pid) or PROFILE_BY_ID["kerstin_warm"]
    pm, lm, emo = MOODS_V.get(mood, (1.0, 1.0, None))
    pitch, length = prof["pitch"] * pm, prof["length"] * lm
    v, cfgfile = _load(prof["base"], status)
    spk = None
    if prof["base"] == "thorsten_emotional":
        try: spk = json.loads(cfgfile.read_text(encoding="utf-8")).get("speaker_id_map", {}).get(prof.get("emotion") if mood == "neutral" else (emo or prof.get("emotion")))
        except Exception: spk = None
    cfg = SynthesisConfig(speaker_id=spk, length_scale=length * pitch, noise_scale=prof["noise"], noise_w_scale=0.8)
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not sent or my != _token: continue
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w: v.synthesize_wav(sent, w, syn_config=cfg)
        buf.seek(0)
        with wave.open(buf, "rb") as r: sr, raw = r.getframerate(), r.readframes(r.getnframes())
        data = np.frombuffer(raw, dtype=np.int16).astype("float32") / 32768 * max(0.0, min(1.0, volume))
        if my != _token: return
        sd.play(data, int(sr * pitch)); sd.wait()   # Tonhöhe über Abspielrate, Tempo über length_scale ausgeglichen


def _speak_sapi(text, volume, mood):
    global _sapi_engine
    import pyttsx3
    e = pyttsx3.init(); _sapi_engine = e
    e.setProperty("rate", int(180 * {"böse": 1.15, "traurig": 0.8}.get(mood, 1.0))); e.setProperty("volume", max(0.0, min(1.0, volume)))
    e.say(text); e.runAndWait()


def speak(text, profile_id, mood="neutral", on_done=None, volume=1.0, status=None):
    global _token
    _token += 1; my = _token
    def run():
        global _speaking
        with _lock:
            if my != _token: return
            _speaking = True
            try: _speak_piper(text, profile_id, mood, volume, my, status)
            except Exception as e:
                if status: status(f"Piper nicht verfügbar ({type(e).__name__}) – Windows-Stimme als Ersatz.")
                try: _speak_sapi(text, volume, mood)
                except Exception: pass
            finally: _speaking = False
        if on_done and my == _token: on_done()
    threading.Thread(target=run, daemon=True).start()


def stop_speaking():
    global _token
    _token += 1
    try:
        import sounddevice as sd; sd.stop()
    except Exception: pass
    try:
        if _sapi_engine: _sapi_engine.stop()
    except Exception: pass


# ---- Zuhören
_stt = {}

def _model(name):
    if name not in _stt:
        from faster_whisper import WhisperModel
        _stt[name] = WhisperModel(name, device="cpu", compute_type="int8")
    return _stt[name]


def preload(name):
    try: _model(name)
    except Exception: pass


def input_devices():
    try:
        import sounddevice as sd
        return [(i, d["name"]) for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0]
    except Exception:
        return []


def mic_test(device=None, secs=3):
    import numpy as np, sounddevice as sd
    lv = []
    with sd.InputStream(samplerate=16000, channels=1, dtype="float32", device=device) as st:
        for _ in range(secs * 10): lv.append(float(np.abs(st.read(1600)[0]).mean()))
    return float(np.percentile(lv, 95)), float(np.percentile(lv, 20))  # Spitze, Hintergrund


def listen(s, max_s=15, idle_timeout=None):
    """Nimmt auf (mit Vorlauf, automatischer Rauschanpassung, einstellbarer Pause) und erkennt Deutsch lokal."""
    import numpy as np, sounddevice as sd
    sr, ch = 16000, 1600
    thr = float(s.get("mic_threshold", 0.012)); sil = max(2, int(float(s.get("mic_silence", 0.8)) * 10))
    pre = collections.deque(maxlen=4); frames = []; quiet = 0; started = False; waited = 0.0
    with sd.InputStream(samplerate=sr, channels=1, dtype="float32", device=s.get("mic_device")) as st:
        amb = [float(np.abs(st.read(ch)[0]).mean()) for _ in range(3)]
        thr = max(thr, 2.5 * max(amb))
        for _ in range(int(max_s * sr / ch)):
            d, _ = st.read(ch); lvl = float(np.abs(d).mean())
            if not started:
                pre.append(d.copy())
                if lvl > thr: started = True; frames = list(pre)
                else:
                    waited += ch / sr
                    if idle_timeout and waited > idle_timeout: return ""
                continue
            frames.append(d.copy()); quiet = 0 if lvl > thr * 0.7 else quiet + 1
            if quiet >= sil: break
    if not started: return ""
    audio = np.concatenate(frames).flatten()
    segs, _ = _model(s.get("stt_model", "base")).transcribe(audio, language="de", beam_size=1, vad_filter=True,
                                                            condition_on_previous_text=False, initial_prompt="Yavis, Jarvis, Hallo, öffne, starte, spiele")
    return " ".join(x.text for x in segs).strip()
