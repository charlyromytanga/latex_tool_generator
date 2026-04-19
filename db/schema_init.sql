PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

BEGIN TRANSACTION;

-- Table 1 : Base CV (sections principales)
CREATE TABLE IF NOT EXISTS cv_base_in_all (
    id TEXT PRIMARY KEY,
    language TEXT NOT NULL CHECK (language IN ('fr', 'en')),
    header TEXT,
    summary TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    certifications TEXT,
    projects TEXT,
    languages TEXT,
    interests TEXT
);

-- Table 2 : Offres d'emploi enrichies (une ligne par offre)
CREATE TABLE IF NOT EXISTS job_offer (
    id TEXT PRIMARY KEY,
    cv_base_id TEXT NOT NULL DEFAULT 'cv_base_in_all',
    language TEXT NOT NULL CHECK (language IN ('fr', 'en')),
    country TEXT NOT NULL CHECK (country IN ('fr', 'uk', 'lu', 'de', 'ch')),
    city TEXT,
    compagny_name TEXT,
    compagny_type TEXT CHECK (compagny_type IN ('grand groupe', 'tpe', 'pme', 'esn', 'banque', 'assurance', 'industrie', 'cabinet conseil')),
    offer_title TEXT,
    offer_description TEXT,
    compagny_presentation TEXT,
    llm_header TEXT,
    llm_summary TEXT,
    llm_skills TEXT,
    llm_experience TEXT,
    llm_education TEXT,
    llm_certifications TEXT,
    llm_projects TEXT,
    llm_languages TEXT,
    llm_interests TEXT,
    date_offer DATE DEFAULT (DATE('now')),
    FOREIGN KEY (cv_base_id) REFERENCES cv_base_in_all(id) ON DELETE CASCADE
);

-- Table 3 : Suivi des candidatures et génération CV/LM
CREATE TABLE IF NOT EXISTS candidature_tracking (
    id TEXT PRIMARY KEY,
    job_offer_id TEXT NOT NULL,
    cv TEXT,
    lm TEXT,
    matching_score REAL CHECK (matching_score >= 0.0 AND matching_score <= 1.0),
    generation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    mail_content TEXT,
    days_to_wait INTEGER,
    response_email TEXT,
    FOREIGN KEY (job_offer_id) REFERENCES job_offer(id) ON DELETE CASCADE
);

COMMIT;
