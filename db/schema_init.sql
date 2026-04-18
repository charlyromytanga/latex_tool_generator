PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

BEGIN TRANSACTION;

-- Table principale des offres
CREATE TABLE IF NOT EXISTS offers (
    offer_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    country TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    raw_text TEXT NOT NULL,
    meta_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des CV générés ou stockés
CREATE TABLE IF NOT EXISTS cv (
    cv_id TEXT PRIMARY KEY,
    offer_id TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    content TEXT NOT NULL,
    meta_json TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id) ON DELETE SET NULL
);

-- Table des lettres de motivation générées ou stockées
CREATE TABLE IF NOT EXISTS letters (
    letter_id TEXT PRIMARY KEY,
    offer_id TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    content TEXT NOT NULL,
    meta_json TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id) ON DELETE SET NULL
);

-- Table des artefacts générés (CV, lettre, etc.)
CREATE TABLE IF NOT EXISTS generations (
    generation_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('cv', 'letter')),
    artifact_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed')),
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id) ON DELETE CASCADE
);

-- Table des scores de matching (offre vs artefact)
CREATE TABLE IF NOT EXISTS matchings (
    matching_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    target_type TEXT NOT NULL CHECK (target_type IN ('cv', 'letter')),
    target_id TEXT NOT NULL,
    score REAL NOT NULL CHECK (score >= 0.0 AND score <= 1.0),
    details_json TEXT,
    matched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id) ON DELETE CASCADE
);

COMMIT;


-- Table des expériences personnelles
CREATE TABLE IF NOT EXISTS experiences (
    exp_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    start_date DATE,
    end_date DATE,
    description TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    meta_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des projets personnels
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    technologies_json TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    meta_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des formations
CREATE TABLE IF NOT EXISTS formations (
    formation_id TEXT PRIMARY KEY,
    institution TEXT NOT NULL,
    program TEXT NOT NULL,
    degree TEXT,
    location TEXT,
    start_date DATE,
    end_date DATE,
    description TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    meta_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
