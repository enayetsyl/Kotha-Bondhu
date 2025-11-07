# Sylheti → Standard Bangla Speaking Coach

This repository packages the offline, privacy-first speaking coach described in
`sylheti-bengali-coach-build-guide.md` into an executable Python project. The
application listens to a child speaking Sylheti-accented Bangla, normalises the
speech into Standard Bangla, speaks the correction aloud via Piper, and stores
progress for practice and exam sessions.

## Features

- 🎙️ **Practice mode** for quick call-and-response feedback loops.
- 🧠 **Exam mode** that plays Sylheti prompts and grades Standard Bangla replies.
- 💾 **SQLite persistence** for utterances, phrase pairs, and exam history.
- 🔁 **Phrase harvesting** from practice runs to grow the exam bank.
- 🗣️ **Piper integration** for Bengali text-to-speech playback.

## Repository layout

```
app.py               # CLI entry point for practice/exam flows
asr.py               # Audio recording + Whisper transcription helpers
db.py                # SQLite models and helper utilities
normalize.py         # Sylheti ↔ Standard Bangla heuristics
tts.py               # Piper text-to-speech wrapper
schema.sql           # Database schema initialiser
data/audio/         # Recorded audio artefacts (gitignored via .gitkeep)
README.md            # Project overview (this file)
sylheti-bengali-coach-build-guide.md  # Original long-form build guide
```

## Quick start

1. Follow the detailed environment setup inside
   [`RUNNING.md`](RUNNING.md) to install dependencies and configure models.
2. Activate your virtual environment and run `python app.py practice` to try a
   3-second practice capture.
3. Seed your phrase bank through practice, then run `python app.py exam -n 5`
   for graded sessions.

## Extending the coach

The code is intentionally modular so you can:

- Swap in alternative ASR/TTS providers.
- Expand the heuristics in `normalize.py` to improve Sylheti↔Standard
  conversions.
- Build lightweight UIs (Tkinter/Flask/mobile clients) on top of the CLI.

For deeper background, reference the original guide in
`sylheti-bengali-coach-build-guide.md`.
