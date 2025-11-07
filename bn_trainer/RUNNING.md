# Running the Sylheti → Standard Bangla Coach

Follow these steps after cloning this repository to set up and run the offline speaking coach.

## 1. Create a Virtual Environment
```bash
cd bn_trainer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

## 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you do not want to use `requirements.txt`, install the packages individually:
```bash
pip install faster-whisper sounddevice numpy rapidfuzz python-dotenv simpleaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 3. Prepare Assets
1. Copy `.env.example` to `.env` and fill in your Piper binary + voice model paths.
2. Download Piper Bengali voice if you have not already.
3. (Optional) Pre-download a Whisper model; otherwise it will download on first use.

## 4. Initialize the Database
The database initializes automatically on first run. To pre-create it:
```bash
python -m bn_trainer.app practice --seconds 1
```
You can also run `sqlite3 bn_trainer/trainer.sqlite < bn_trainer/schema.sql`.

## 5. Practice Mode
```bash
python -m bn_trainer.app practice --seconds 3
```
Speak a short Sylheti sentence. The app will:
- Transcribe it using Whisper (`faster-whisper`).
- Normalize to Standard Bangla.
- Speak the corrected line via Piper.
- Log everything to `trainer.sqlite`.

## 6. Exam Mode
After collecting some phrase pairs in the database:
```bash
python -m bn_trainer.app exam -n 5 --seconds 3 --pass_mark 85
```
The app will play Sylheti prompts and score your Standard Bangla answers.

## 7. Troubleshooting
- **Audio errors:** install OS-specific PortAudio packages.
- **Piper missing:** ensure `.env` paths are correct and Piper is executable.
- **Slow transcription:** choose a smaller `WHISPER_MODEL_SIZE`.

Happy practicing! ✨
