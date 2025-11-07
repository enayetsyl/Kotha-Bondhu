# Running the Sylheti → Standard Bangla Coach

These instructions assume you have checked out this repository and you are in its root directory.

## 1. Create a Python virtual environment
```bash
python -m venv venv
```

Activate it:
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source venv/bin/activate`

## 2. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> The `requirements.txt` file installs the packages referenced in the build guide, including `faster-whisper`, `sounddevice`, `simpleaudio`, `rapidfuzz`, and the CPU wheels for PyTorch.

## 3. Configure environment variables
Copy `.env.example` to `.env` and edit the paths to match your system:
```bash
cp .env.example .env
```
Set `PIPER_BIN`, `PIPER_MODEL`, and `PIPER_CFG` to the Piper binary and Bengali voice model you downloaded.

## 4. Prepare the database (first run only)
The first time you run the app a `trainer.sqlite` database is created automatically using `schema.sql`. No manual migration step is required.

## 5. Practice mode
```bash
python app.py practice --seconds 3
```
Speak a short sentence when prompted. The app will transcribe it, normalise the text into Standard Bangla, speak it back using Piper, and log the result to the database.

## 6. Exam mode
Populate the phrase bank through practice sessions or by inserting rows into `phrase_pairs`. Then run:
```bash
python app.py exam -n 5 --seconds 3 --pass_mark 85
```
The coach will play Sylheti prompts, record your Standard Bangla replies, score them, and store the session details.

## 7. Optional: custom database location
To store the SQLite database elsewhere, set `TRAINER_DB` in your `.env` file before running the app.

Happy coaching! :sparkles:
