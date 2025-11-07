# Sylheti → Standard Bangla Speaking Coach

This repository implements the offline coaching tool described in `sylheti-bengali-coach-build-guide.md`. It records short Sylheti-accented Bangla phrases, transcribes them with Whisper (via `faster-whisper`), normalises to Standard Bangla, plays the corrected line back with Piper TTS, and stores both practice and exam sessions in SQLite.

- `app.py` – command line entry point with **practice** and **exam** modes.
- `asr.py` – audio recording and transcription helpers.
- `tts.py` – Piper-based text-to-speech playback.
- `normalize.py` – Sylheti ↔ Standard Bangla mappings you can customise.
- `db.py` / `schema.sql` – local SQLite storage.
- `RUNNING.md` – quick-start instructions.

See the guide for deeper explanations, tips, and roadmap ideas. Happy coaching!
