# YAVIS – kostenloser KI-Assistent für Windows 11
## EXE bekommen (nur GitHub, nichts lokal)
1. Neues GitHub-Repository anlegen, alle Dateien dieses Ordners hochladen (inkl. Ordner `.github`).
2. Tab **Actions** → „Build YAVIS-Setup“ läuft automatisch (oder „Run workflow“).
3. Nach grünem Haken: unten bei **Artifacts** `YAVIS-Setup` herunterladen, entpacken, `YAVIS-Setup.exe` starten.
## Einmalig auf dem PC (kostenlos)
- Ollama installieren (ollama.com), dann in Eingabeaufforderung: `ollama pull llama3.2:3b`
- Beim ersten Zuhören lädt faster-whisper einmalig das Sprachmodell (Internet nötig).
## Bedienung
Programme-Seite: Startmenü scannen, Haken setzen = YAVIS darf starten. Sage z. B. „Yavis, öffne YouTube“.
Aktivierungsnamen, Stimme, Stil und Stimmung: Einstellungen. „Sei neutral“ schaltet Gefühle aus.
Daten liegen lokal in `%APPDATA%\YAVIS`.

## Neu
- Stimmen: 36 Piper-Profile (Basisstimme wird beim ersten Benutzen einmalig geladen). Fallback: Windows-Stimme.
- ChatGPT-Seite: eingebetteter Browser mit deinem eigenen ChatGPT-Login.
- Einstellungen → Mikrofon: Gerät, Empfindlichkeit, Pause, Modell, Mikrofon-Test.
