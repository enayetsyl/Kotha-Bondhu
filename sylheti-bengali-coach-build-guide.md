# Sylheti → Standard Bangla Speaking Coach (Offline AI)
A complete, step‑by‑step guide to build a kid‑friendly trainer that:
- **Listens** to your child speaking Sylheti‑accented Bangla
- **Transcribes** it offline
- **Normalizes/Corrects** into Standard Bengali
- **Speaks back** the corrected line
- **Logs** everything to a local database
- Includes an **Exam Mode** where the app speaks in *Sylheti* and your child answers in *Standard Bengali*.

> Designed for privacy (offline‑first), low cost (free tools), and gentle for a 4‑year‑old.
>
> Works on Windows / macOS / Linux. Android possible via a simple Flask server + phone client (roadmap at the end).

---

## 0) What You’ll Build
**Two modes:**

1) **Practice Mode**
   - Child speaks naturally
   - App transcribes (ASR: Whisper), corrects to Standard Bangla (rules you control), speaks it back (TTS: Piper)
   - Saves: raw audio path (optional), ASR transcript, corrected Standard Bangla, timestamp, tags

2) **Exam Mode**
   - App **speaks a Sylheti prompt**
   - Child responds in **Standard Bangla**
   - App **scores** with fuzzy matching and gives **stars**
   - Results are saved (question, answer, score)

**Data model:** A local SQLite database with two tables:
- `utterances` – every line said by the child or system
- `phrase_pairs` – the growing bank of *Sylheti ↔ Standard* pairs used for exams

---

## 1) System Requirements
- **Python 3.10+** (Windows/macOS/Linux)
- **Mic & Speakers/Headphones**
- **Disk space:** ~3–6 GB if you choose larger ASR/TTS models
- **No GPU required** (CPU‑only)

> Whisper on CPU is fine for short kid phrases. Choose a smaller model if your laptop is older (see section 6.2).

---

## 2) Project Structure
Create a folder anywhere (e.g., `bn-trainer/`) with this structure:

```
bn-trainer/
  app.py                 # main CLI: practice & exam
  asr.py                 # speech-to-text (Whisper/faster-whisper)
  tts.py                 # text-to-speech (Piper)
  normalize.py           # Sylheti ↔ Standard helpers
  db.py                  # SQLite helpers
  schema.sql             # DB schema
  .env                   # model paths, audio dir
  data/
    audio/               # saved wav files (system prompts, optional child audio)
  README.md              # optional
```

> You’ll copy code from this guide into those files.

---

## 3) Install Dependencies
Open a terminal in `bn-trainer/`.

### 3.1 Create & activate a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3.2 Python packages
```bash
pip install --upgrade pip
pip install faster-whisper sounddevice numpy rapidfuzz python-dotenv simpleaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

> **OS Notes**
> - **Windows**: If `sounddevice` complains, install the Visual C++ Redistributable (Microsoft) and re‑try.
> - **macOS**: You might be prompted to allow microphone access.
> - **Linux**: If PortAudio errors appear, install OS package (e.g., `sudo apt install portaudio19-dev`).

---

## 4) Models & Assets

### 4.1 Whisper (ASR) via `faster-whisper`
`faster-whisper` will auto‑download a model if you use the **size name** (e.g., `"large-v3"`, `"medium"`, `"small"`). For older CPUs, start with `"small"` or `"medium"`; for best accuracy, `"large-v3"`.

We’ll reference by **size name** so you don’t need manual paths.

### 4.2 Piper (TTS) for Bengali
Piper is a small, fast, high‑quality TTS engine. You need:
- **Piper binary** (executable for your OS)
- A **Bengali (`bn`) voice model** `.onnx` and its `.json` config

Place them somewhere and record paths in `.env` (next section). You’ll call Piper via command line: `piper -m <model> -c <config> -f <out.wav>` and feed the text via STDIN.

> If Piper isn’t an option for you, you can temporarily skip TTS and just print corrected lines on screen, or use any other Bengali TTS you prefer.

---

## 5) Environment File
Create a `.env` in the project root:

```
# Whisper: use model size name (auto-download) or an absolute path to a local model folder.
WHISPER_MODEL_SIZE=large-v3

# Piper binary and voice (set your real paths)
PIPER_BIN=/absolute/path/to/piper
PIPER_MODEL=/absolute/path/to/bn_voice.onnx
PIPER_CFG=/absolute/path/to/bn_voice.onnx.json

# Where to store audio
AUDIO_DIR=./data/audio
```

> If you prefer a local Whisper model folder (e.g., you already downloaded one), replace `WHISPER_MODEL_SIZE` with `WHISPER_MODEL_DIR=/path/to/folder` and the code below will honor that.

---

## 6) Source Code

### 6.1 `schema.sql`
```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS utterances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT (datetime('now')),
  mode TEXT CHECK(mode IN ('practice','exam')) NOT NULL,
  speaker TEXT CHECK(speaker IN ('child','system')) NOT NULL,
  audio_path TEXT,
  transcript_raw TEXT,             -- what ASR heard
  normalized_bn TEXT,              -- your corrected Standard Bangla
  sylheti_guess TEXT,              -- optional reverse guess (for exam linkage)
  score INTEGER,                   -- only for exam
  meta TEXT                        -- JSON blob (tags, duration, device info, etc.)
);

CREATE TABLE IF NOT EXISTS phrase_pairs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sylheti TEXT NOT NULL,
  standard_bn TEXT NOT NULL,
  source TEXT,                     -- 'from_child','manual','public'
  seen_count INTEGER DEFAULT 0,
  difficulty INTEGER DEFAULT 1,    -- 1 easy, 2 medium, 3 hard
  UNIQUE(sylheti, standard_bn)
);
```

---

### 6.2 `normalize.py` (rules you can grow over time)
```python
# normalize.py
# Minimal starter rules. Add your family's common phrases here.
SYL2STD = {
    "খামু": "খাবো",
    "যামু": "যাবো",
    "আইসা": "এসে",
    "কিতা": "কি",
    "তু": "তুমি",
    "অয়": "হয়",
    "মাইনষ": "মানুষ",
    "লাইমু": "আনব",
    "কিদা": "কী",
}

def to_standard_bn(text: str) -> str:
    out = (text or "").strip()
    for k, v in SYL2STD.items():
        out = out.replace(k, v)
    # light cleanups
    while "  " in out:
        out = out.replace("  ", " ")
    return out

# Optional: produce a Sylheti-like variant from Standard
STD2SYL = {v: k for k, v in SYL2STD.items()}

def to_sylheti_like(text: str) -> str:
    out = (text or "").strip()
    for std, syl in STD2SYL.items():
        out = out.replace(std, syl)
    return out
```

> **Tip:** Keep a simple CSV in `data/rules.csv` and load it to update `SYL2STD` as your child grows.

---

### 6.3 `db.py`
```python
# db.py
import sqlite3, json, os

DB_PATH = "trainer.sqlite"

def get_conn():
    need_init = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if need_init:
        with open("schema.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    return conn

def insert_utterance(conn, **kwargs):
    keys = ("mode", "speaker", "audio_path", "transcript_raw", "normalized_bn",
            "sylheti_guess", "score", "meta")
    vals = [kwargs.get(k) for k in keys]
    conn.execute(
        f"INSERT INTO utterances ({','.join(keys)}) VALUES (?,?,?,?,?,?,?,?)",
        vals
    )
    conn.commit()

def upsert_pair(conn, syl, std, source="from_child"):
    try:
        conn.execute(
            "INSERT INTO phrase_pairs (sylheti, standard_bn, source) VALUES (?,?,?)",
            (syl, std, source)
        )
    except sqlite3.IntegrityError:
        pass
    conn.commit()

def sample_pairs_for_exam(conn, n=10, level=None):
    q = "SELECT id, sylheti, standard_bn FROM phrase_pairs "
    params = ()
    if level:
        q += "WHERE difficulty=? "
        params = (level,)
    q += "ORDER BY seen_count ASC, id ASC LIMIT ?"
    params += (n,)
    rows = conn.execute(q, params).fetchall()
    ids = [r["id"] for r in rows]
    if ids:
        conn.executemany(
            "UPDATE phrase_pairs SET seen_count = seen_count + 1 WHERE id=?",
            [(i,) for i in ids]
        )
        conn.commit()
    return rows
```

---

### 6.4 `asr.py`
```python
# asr.py
import os, numpy as np, sounddevice as sd
from faster_whisper import WhisperModel
from dotenv import load_dotenv; load_dotenv()

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE")
WHISPER_MODEL_DIR  = os.getenv("WHISPER_MODEL_DIR")

# Choose size name or local dir
if WHISPER_MODEL_DIR:
    model = WhisperModel(WHISPER_MODEL_DIR, device="cpu", compute_type="int8")
else:
    model = WhisperModel(WHISPER_MODEL_SIZE or "medium", device="cpu", compute_type="int8")

def record(seconds=3, fs=16000):
    audio = sd.rec(int(seconds*fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    return audio.squeeze(), fs

def transcribe(audio, language="bn"):
    segments, _ = model.transcribe(audio, language=language)
    return "".join(seg.text for seg in segments).strip()
```

**Model sizing tips:**
- `small` → fastest, okay accuracy
- `medium` → good balance
- `large-v3` → best accuracy for BN, slower on old CPUs

---

### 6.5 `tts.py`
```python
# tts.py
import os, subprocess, uuid, simpleaudio as sa
from dotenv import load_dotenv; load_dotenv()

AUDIO_DIR = os.getenv("AUDIO_DIR", "./data/audio")
PIPER_BIN = os.getenv("PIPER_BIN")
PIPER_MODEL = os.getenv("PIPER_MODEL")
PIPER_CFG = os.getenv("PIPER_CFG")

os.makedirs(AUDIO_DIR, exist_ok=True)

def speak_and_save(text: str, prefix="sys"):
    out_wav = os.path.join(AUDIO_DIR, f"{prefix}_{uuid.uuid4().hex}.wav")
    cmd = [PIPER_BIN, "-m", PIPER_MODEL, "-c", PIPER_CFG, "-f", out_wav]
    # Feed text via STDIN
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    p.communicate(input=text or "")
    p.wait()
    # play
    wave_obj = sa.WaveObject.from_wave_file(out_wav)
    play_obj = wave_obj.play()
    play_obj.wait_done()
    return out_wav
```

> If Piper isn’t found, double‑check `PIPER_BIN` and file permissions (`chmod +x` on macOS/Linux).

---

### 6.6 `app.py` (CLI: Practice + Exam)
```python
# app.py
import json, os, argparse
from dotenv import load_dotenv; load_dotenv()
from rapidfuzz import fuzz
from asr import record, transcribe
from db import get_conn, insert_utterance, upsert_pair, sample_pairs_for_exam
from normalize import to_standard_bn, to_sylheti_like
from tts import speak_and_save

AUDIO_DIR = os.getenv("AUDIO_DIR", "./data/audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

def save_child_take(conn, raw_bn, norm_bn, audio_path=None, meta=None):
    insert_utterance(
        conn,
        mode="practice",
        speaker="child",
        audio_path=audio_path,
        transcript_raw=raw_bn,
        normalized_bn=norm_bn,
        sylheti_guess=None,
        score=None,
        meta=json.dumps(meta or {})
    )
    # Create or update a pair from the normalized standard phrase,
    # and a heuristic Sylheti-like version (you can also log the raw)
    syl_guess = to_sylheti_like(norm_bn)
    upsert_pair(conn, syl_guess, norm_bn, source="from_child")

def practice(seconds=3):
    conn = get_conn()
    print("🎤 বলুন… (মাইকে ৩ সেকেন্ড)")
    audio, fs = record(seconds)
    raw = transcribe(audio, language="bn")
    if not raw:
        print("কিছুই ধরা পড়েনি, আবার বলুন.")
        return
    norm = to_standard_bn(raw)
    print(f"আপনি বললেন (ASR): {raw}\nপ্রমিত রূপ: {norm}")
    # Speak it back
    speak_and_save(norm, prefix="practice")
    # Log
    save_child_take(conn, raw, norm, audio_path=None, meta={"fs": fs})

def exam(n=5, level=None, seconds=3, pass_mark=85):
    conn = get_conn()
    items = sample_pairs_for_exam(conn, n=n, level=level)
    if not items:
        print("ফ্রেইজ ব্যাংক খালি। আগে প্র্যাকটিস করুন বা ম্যানুয়ালি কিছু pair যোগ করুন.")
        return

    total = 0
    for i, row in enumerate(items, start=1):
        syl = row["sylheti"]
        std = row["standard_bn"]

        print(f\"\"\"\nপ্রশ্ন {i}/{n}
সিলেটি শোনান হচ্ছে… (প্রমিত বাংলায় বলুন)\"\"\".strip())
        wav = speak_and_save(syl, prefix="exam")

        audio, fs = record(seconds)
        heard = transcribe(audio, language="bn")
        norm = to_standard_bn(heard)

        score = fuzz.token_set_ratio(norm, std)  # 0..100
        badge = "⭐" if score >= pass_mark else ("✅" if score >= 70 else "🙂")

        print(f"আপনি বললেন: {norm}")
        print(f"উত্তর হওয়া উচিত: {std}")
        print(f"স্কোর: {score} {badge}")

        total += score

        # Log both the system prompt and child response
        insert_utterance(conn, mode="exam", speaker="system",
                         audio_path=wav, transcript_raw=syl,
                         normalized_bn=None, sylheti_guess=None, score=None,
                         meta=json.dumps({}))
        insert_utterance(conn, mode="exam", speaker="child",
                         audio_path=None, transcript_raw=heard,
                         normalized_bn=norm, sylheti_guess=syl, score=int(score),
                         meta=json.dumps({"expected": std}))

    avg = round(total / max(1, len(items)), 1)
    print(f\"\"\"\nমোট গড় স্কোর: {avg}\"\"\".strip())

def main():
    ap = argparse.ArgumentParser(description="Sylheti→Standard Bangla Coach")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("practice")
    p.add_argument("--seconds", type=int, default=3)

    e = sub.add_parser("exam")
    e.add_argument("-n", type=int, default=5)
    e.add_argument("--level", type=int, choices=[1,2,3])
    e.add_argument("--seconds", type=int, default=3)
    e.add_argument("--pass_mark", type=int, default=85)

    args = ap.parse_args()
    if args.cmd == "exam":
        exam(n=args.n, level=args.level, seconds=args.seconds, pass_mark=args.pass_mark)
    else:
        practice(seconds=getattr(args, "seconds", 3))

if __name__ == "__main__":
    main()
```

---

## 7) Run the App

### 7.1 First run (Practice)
```bash
# (Inside bn-trainer/, venv active)
python app.py practice --seconds 3
```
- Speak a short line (3 seconds).
- You’ll see the ASR text and the corrected Standard Bangla.
- The corrected line is spoken back via Piper.
- A row is logged to `trainer.sqlite` (`utterances` table), and a guess pair is added to `phrase_pairs`.

### 7.2 Exam Mode
```bash
python app.py exam -n 5 --seconds 3 --pass_mark 85
```
- The app speaks a **Sylheti** prompt (from your phrase bank).
- Your child answers in **Standard Bangla**.
- The app scores, shows stars, and logs everything.

> If the bank is empty, do a few **practice** runs first. You can also add a few pairs manually (see next section).

---

## 8) Growing Your Phrase Bank

### 8.1 Manual insert (SQLite CLI)
```sql
INSERT INTO phrase_pairs (sylheti, standard_bn, source, difficulty)
VALUES ('আমি দুধ খামু', 'আমি দুধ খাবো', 'manual', 1);
```
Use any SQLite GUI (e.g., DB Browser for SQLite) to edit easily.

### 8.2 Auto from Practice
Each practice cycle calls `to_sylheti_like()` to make a heuristic Sylheti form from your corrected Standard line, then upserts a pair (`source='from_child'`). Improve the mapping in `normalize.py` so the auto‑pairs sound more natural.

---

## 9) Kid‑Friendly Routine
- 5–10 minutes **twice a day** (morning/evening)
- Short phrases (3–5 words)
- **Praise first**, then model:  
  “তুমি বলেছো: *আমি দুধ খামু* → আমরা বলি: *আমি দুধ **খাবো***. একসাথে বলি?”
- Keep a star counter: 5 stars → small reward (sticker).

---

## 10) Quality & Performance Tips
- **Model size:** If your laptop is older, set `WHISPER_MODEL_SIZE=small` or `medium` in `.env`.
- **Recording window:** Keep to 2–3 seconds for snappy feedback.
- **Noise:** Try a quiet room; a simple external mic helps.
- **Scoring:** The default fuzzy score is forgiving. You can require **key tokens** (e.g., verb inflection) in addition to similarity—extend in `exam()`.

---

## 11) Troubleshooting
- **No audio / mic errors:**  
  - Windows: check Privacy → Microphone permission → allow Python.
  - macOS: System Settings → Privacy & Security → Microphone.
  - Linux: install PortAudio dev package (`sudo apt install portaudio19-dev`) and re‑install `sounddevice`.
- **Piper not found:** Check `.env` paths. On macOS/Linux: `chmod +x /path/to/piper`.
- **Playback silent:** Ensure your output device is selected; try headphones.
- **Whisper too slow:** Use a smaller model or reduce `--seconds` to 2.
- **Bangla spelling off:** Expand `SYL2STD`; consider integrating a BN spell/grammar checker later.

---

## 12) Optional Upgrades
- **UI:** Wrap with Tkinter or a tiny Flask app with big buttons: **Practice / Exam / Scoreboard**.
- **Tags:** Add theme tags (e.g., *খাবার*, *খেলা*, *রং*) in `utterances.meta` and sample exams by tag.
- **Difficulty:** Curate `phrase_pairs.difficulty` to build graded exams.
- **Data export:** A weekly CSV/MD report for progress.
- **Postgres:** Swap SQLite for Postgres when you want multi‑device sync.
- **Better Sylheti prompts:** Instead of heuristic `to_sylheti_like`, maintain a CSV of curated pairs (family expressions).

---

## 13) (Roadmap) Phone‑Friendly Flow
- Run this Python app as a **local Flask API** on your laptop (endpoints: `/transcribe`, `/speak`, `/exam/start`, `/exam/answer`).
- On Android, build a small app (Flutter/React Native) that records 3‑second clips, POSTs to the Flask API, and plays back WAV replies. All data still stays in your home network.

---

## 14) Safety & Privacy
- Everything runs **offline**. No cloud needed.
- Store only what you need. You can **skip saving raw child audio**—keep transcripts only.
- Back up `trainer.sqlite` occasionally.

---

## 15) Daily Checklist (Quick Start)
1. Activate venv → `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
2. Ensure `.env` is filled (Whisper size, Piper paths)
3. Run: `python app.py practice --seconds 3`
4. Do 5–10 lines, praise and repeat
5. Once/week: `python app.py exam -n 10`
6. Add 5 new rules to `SYL2STD` each week

---

## 16) License & Notes
- This guide and sample code are **yours to modify** for personal/family use.
- If you share it, please remove any child data and anonymize examples.

**দোয়া রইল—আলহামদুলিল্লাহ, আপনার সন্তানের জন্য এটি একটি সুন্দর যাত্রার শুরু হোক।**

