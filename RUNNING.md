# Running the Sylheti → Standard Bangla Speaking Coach

This quick reference distils the setup and usage instructions for the offline
coach. For the rationale and deeper explanations, see the long-form guide in
`sylheti-bengali-coach-build-guide.md`.

## 1. Prerequisites

- **Python**: 3.10 or later.
- **Audio hardware**: microphone and speakers/headphones.
- **Disk space**: 3–6 GB depending on chosen Whisper/Piper models.
- **Optional GPU**: the project targets CPU-only setups.

## 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

Upgrade `pip` before installing packages:

```bash
pip install --upgrade pip
```

## 3. Install dependencies

```bash
pip install faster-whisper sounddevice numpy rapidfuzz python-dotenv simpleaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

> **Platform notes**
> - *Windows*: install the Microsoft Visual C++ Redistributable if `sounddevice`
>   fails to compile.
> - *macOS*: grant microphone access when prompted.
> - *Linux*: install PortAudio headers (e.g. `sudo apt install portaudio19-dev`)
>   if you encounter audio backend errors.

## 4. Configure models via `.env`

Create a `.env` file in the repository root:

```dotenv
# Whisper ASR model size or absolute model path.
WHISPER_MODEL_SIZE=small
WHISPER_COMPUTE_TYPE=int8

# Piper configuration (provide real paths on your system).
PIPER_BIN=/absolute/path/to/piper
PIPER_MODEL=/absolute/path/to/bengali_voice.onnx
PIPER_CONFIG=/absolute/path/to/bengali_voice.onnx.json

# Optional overrides.
DB_PATH=trainer.sqlite
AUDIO_DIR=data/audio
SAVE_AUDIO=true
PASS_MARK=85
```

Whisper will auto-download the requested size on first run. Piper binaries and
voices can be fetched from the [Rhasspy/Piper releases](https://github.com/rhasspy/piper/releases).

## 5. Initialise the database (first run only)

The schema is loaded automatically, but you can pre-create the SQLite file by
running practice mode once or executing the helper below:

```bash
python - <<'PY'
from pathlib import Path
import db
from app import load_settings
settings = load_settings()
db.init_db(settings.db_path)
print(f"Initialised database at {settings.db_path.resolve()}")
PY
```

## 6. Practice mode

```bash
python app.py practice --seconds 3
```

- Records a short clip (default 3 seconds).
- Transcribes with Whisper, normalises the text, and speaks the corrected
  Standard Bangla via Piper.
- Logs utterances to `trainer.sqlite` and grows the `phrase_pairs` table.

## 7. Exam mode

```bash
python app.py exam -n 5 --seconds 3 --pass_mark 85
```

- Plays Sylheti prompts (TTS required) and records Standard Bangla responses.
- Scores with fuzzy matching and stores the run in the database.
- Reports an average score at the end of the session.

## 8. Managing the phrase bank

- Use practice sessions to auto-harvest Sylheti↔Standard pairs.
- Manually curate entries by inserting into `phrase_pairs` using your favourite
  SQLite client.

```sql
INSERT INTO phrase_pairs (sylheti, standard_bn, source, difficulty)
VALUES ('আমি দুধ খামু', 'আমি দুধ খাবো', 'manual', 1);
```

## 9. Troubleshooting tips

| Issue | Fix |
| --- | --- |
| `sounddevice` missing backend | Install PortAudio dev package (Linux) or VC++ runtime (Windows). |
| Piper binary not found | Verify `PIPER_BIN` path and mark it executable (`chmod +x`). |
| Whisper too slow | Reduce `--seconds` or switch to `WHISPER_MODEL_SIZE=small`. |
| Silent playback | Check system output device; try headphones. |

## 10. Next steps

- Review recent utterances with a SQLite browser to track progress.
- Expand `normalize.py` with community-specific vocabulary.
- Consider wrapping the CLI with a simple GUI for child-friendly controls.
