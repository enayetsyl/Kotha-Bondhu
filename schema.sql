PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS utterances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT (datetime('now')),
  mode TEXT CHECK(mode IN ('practice','exam')) NOT NULL,
  speaker TEXT CHECK(speaker IN ('child','system')) NOT NULL,
  audio_path TEXT,
  transcript_raw TEXT,
  normalized_bn TEXT,
  sylheti_guess TEXT,
  score INTEGER,
  meta TEXT
);

CREATE TABLE IF NOT EXISTS phrase_pairs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sylheti TEXT NOT NULL,
  standard_bn TEXT NOT NULL,
  source TEXT,
  seen_count INTEGER DEFAULT 0,
  difficulty INTEGER DEFAULT 1,
  UNIQUE(sylheti, standard_bn)
);
