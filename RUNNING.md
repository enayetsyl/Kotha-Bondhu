# Running the Sylheti → Standard Bangla Speaking Coach

Follow these steps once you have created the project structure and installed dependencies described in the main guide.

## 1. Prepare the Environment
1. Open a terminal inside your `bn-trainer/` project directory.
2. Activate the virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. Ensure your `.env` file contains:
   ```
   WHISPER_MODEL_SIZE=large-v3   # or small/medium for slower machines
   PIPER_BIN=/absolute/path/to/piper
   PIPER_MODEL=/absolute/path/to/bn_voice.onnx
   PIPER_CONFIG=/absolute/path/to/bn_voice.json
   AUDIO_DIR=./data/audio
   ```

## 2. Initialize the Database (first run)
```bash
sqlite3 trainer.sqlite < schema.sql
```

## 3. Practice Mode
Use practice mode for daily speaking drills:
```bash
python app.py practice --seconds 3
```
- Speaks the corrected Standard Bangla via Piper.
- Logs child/system utterances in `trainer.sqlite`.

## 4. Exam Mode
Run structured quizzes to award stars:
```bash
python app.py exam -n 5 --seconds 3 --pass_mark 85
```
- Prompts the child with Sylheti phrases.
- Scores the Standard Bangla response using fuzzy matching.

## 5. Managing Phrase Pairs
Populate the exam phrase bank manually when needed:
```sql
INSERT INTO phrase_pairs (sylheti, standard_bn, source, difficulty)
VALUES ('আমি দুধ খামু', 'আমি দুধ খাবো', 'manual', 1);
```

## 6. Tips for Smooth Runs
- Keep recordings short (2–3 seconds) for faster CPU transcription.
- Use a quiet room and an external mic if possible.
- If Piper output is silent, verify the audio device and ensure the binary is executable.
- Reduce `WHISPER_MODEL_SIZE` for older CPUs.

Happy coaching!
