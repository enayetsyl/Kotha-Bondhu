BEGIN;

CREATE TABLE IF NOT EXISTS utterances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL CHECK(role IN ('child', 'system')),
    transcript TEXT NOT NULL,
    normalized TEXT,
    audio_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meta TEXT
);

CREATE TABLE IF NOT EXISTS phrase_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sylheti TEXT NOT NULL,
    standard_bn TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    difficulty INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sylheti, standard_bn)
);

CREATE TABLE IF NOT EXISTS exam_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER,
    prompt TEXT NOT NULL,
    answer TEXT NOT NULL,
    score REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES phrase_pairs(id)
);

COMMIT;
