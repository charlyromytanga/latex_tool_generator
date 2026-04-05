-- Migration 002: add formations and formation matching tables

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS formations (
    formation_id TEXT PRIMARY KEY,
    institution TEXT NOT NULL,
    program TEXT NOT NULL,
    degree TEXT,
    location TEXT,
    start_date DATE,
    end_date DATE,
    is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
    description TEXT,
    courses_json TEXT NOT NULL,
    course_categories_json TEXT NOT NULL,
    achievements_json TEXT NOT NULL,
    tags_json TEXT,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_formations_institution ON formations(institution);
CREATE INDEX IF NOT EXISTS idx_formations_program ON formations(program);
CREATE INDEX IF NOT EXISTS idx_formations_dates ON formations(start_date, end_date);

CREATE TABLE IF NOT EXISTS formation_matching_scores (
    match_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    formation_id TEXT NOT NULL,
    match_score REAL NOT NULL CHECK (match_score >= 0.0 AND match_score <= 1.0),
    reasoning TEXT NOT NULL,
    model_version TEXT NOT NULL,
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE,
    FOREIGN KEY (formation_id) REFERENCES formations(formation_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_formation_matching_offer ON formation_matching_scores(offer_id);
CREATE INDEX IF NOT EXISTS idx_formation_matching_formation ON formation_matching_scores(formation_id);
CREATE INDEX IF NOT EXISTS idx_formation_matching_score ON formation_matching_scores(match_score DESC);

COMMIT;
