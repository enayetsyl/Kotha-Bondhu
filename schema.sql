PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS utterances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL CHECK(role IN ('child', 'system')),
    transcript TEXT NOT NULL,
    normalized TEXT,
    audio_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    meta JSON
);

CREATE TABLE IF NOT EXISTS phrase_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sylheti TEXT NOT NULL,
    standard_bn TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    difficulty INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sylheti, standard_bn)
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_questions INTEGER NOT NULL,
    pass_mark INTEGER NOT NULL,
    score INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS exam_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    expected_answer TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    score REAL NOT NULL,
    is_pass INTEGER NOT NULL CHECK(is_pass IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
