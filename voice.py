"""Sprachausgabe (Windows-Stimmen via pyttsx3) und lokale Spracherkennung (faster-whisper)."""
import threading
from core import STYLES

_engine = None
_token = 0
_lock = threading.Lock()

def list_voices():
    try:
        import pyttsx3
        return [(v.id, v.name) for v in pyttsx3.init().getProperty("voices")]
    except Exception:
        return []

def speak(text, voice_id, style, mood_rate=1.0, on_done=None, volume=1.0):
    global _token
    _token += 1; my = _token
    def run():
        with _lock:
            if my != _token: return  # inzwischen unterbrochen
            try:
                import pyttsx3
                e = pyttsx3.init()
                if voice_id: e.setProperty("voice", voice_id)
                tempo, vol = STYLES.get(style, (1.0, 1.0))
                e.setProperty("rate", int(180 * tempo * mood_rate))
                e.setProperty("volume", max(0.0, min(1.0, vol * volume)))
                global _engine; _engine = e
                e.say(text); e.runAndWait()
            except Exception:
                pass
        if on_done and my == _token: on_done()
    threading.Thread(target=run, daemon=True).start()

def stop_speaking():
    global _token
    _token += 1
    try:
        if _engine: _engine.stop()
    except Exception:
        pass

_model = None

def listen(max_s=12):
    """Nimmt auf, bis ~1 s Stille herrscht, und transkribiert lokal (Deutsch)."""
    import numpy as np, sounddevice as sd
    from faster_whisper import WhisperModel
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    sr, chunk, frames, quiet, started = 16000, 1600, [], 0, False
    with sd.InputStream(samplerate=sr, channels=1, dtype="float32") as st:
        for _ in range(int(max_s * sr / chunk)):
            data, _ = st.read(chunk)
            lvl = float(np.abs(data).mean())
            frames.append(data.copy())
            if lvl > 0.01: started, quiet = True, 0
            elif started: quiet += 1
            if started and quiet > 10: break
    audio = np.concatenate(frames).flatten()
    segs, _ = _model.transcribe(audio, language="de", vad_filter=True)
    return " ".join(s.text for s in segs).strip()
