# Sylheti → Standard Bangla Speaking Coach

This repository captures the full build guide for creating an offline Sylheti-accent Bangla speaking coach for kids. The coach listens, corrects pronunciation, speaks back the corrected line, and logs each interaction for gentle progress tracking.

## What You Will Build
- **Practice mode** for listening, transcribing (Whisper), correcting, and speaking the corrected line.
- **Exam mode** where the app prompts in Sylheti, evaluates the child’s Standard Bangla reply, and awards stars.
- **Local SQLite storage** for transcripts, phrase pairs, and exam history.

## System Requirements
- Python 3.10+
- Microphone and speakers/headphones
- 3–6 GB free disk space depending on chosen ASR/TTS models
- CPU-only operation is supported

## Project Structure
```
bn-trainer/
  app.py                 # CLI entry point (practice & exam)
  asr.py                 # Whisper/faster-whisper ASR helpers
  tts.py                 # Piper TTS wrapper
  normalize.py           # Sylheti ↔ Standard transformations
  db.py                  # SQLite utilities
  schema.sql             # Database schema
  .env                   # Configuration (model paths, audio dirs)
  data/
    audio/
```

## Setup Steps
1. **Create project folder:** `mkdir bn-trainer && cd bn-trainer`
2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install faster-whisper sounddevice numpy rapidfuzz python-dotenv simpleaudio
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```
4. **Download Piper TTS assets** (binary + Bengali voice model) and note their paths.
5. **Create a `.env` file** with Whisper model size and Piper paths.
6. **Run the database schema:** `sqlite3 trainer.sqlite < schema.sql`

## Usage Overview
- **Practice mode:** `python app.py practice --seconds 3`
- **Exam mode:** `python app.py exam -n 5 --seconds 3 --pass_mark 85`
- **Manage phrase bank:** Use SQLite tools or automate via practice sessions.

## Troubleshooting Highlights
- Install PortAudio (`portaudio19-dev`) on Linux if `sounddevice` fails to build.
- Allow microphone permissions on Windows/macOS.
- Ensure Piper binary is executable (`chmod +x`).
- Switch to a smaller Whisper model (`small`, `medium`) if transcription feels slow.

## Roadmap Ideas
- Wrap the CLI with a Tkinter or Flask UI.
- Tag phrases for themed practice sessions.
- Export weekly progress reports from SQLite.
- Expose a simple Flask API for an Android companion app.

## Reference
For full, detailed instructions, consult [`sylheti-bengali-coach-build-guide.md`](sylheti-bengali-coach-build-guide.md).
