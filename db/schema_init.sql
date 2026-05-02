-- Schéma SQLite pour la base recruitement
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS cv_base_in_all (
    id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
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

CREATE TABLE IF NOT EXISTS job_offer (
    id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    country TEXT NOT NULL,
    city TEXT,
    company_name TEXT,
    company_type TEXT,
    offer_description TEXT,
    company_presentation TEXT
);

CREATE TABLE IF NOT EXISTS candidature_tracking (
    id TEXT PRIMARY KEY,
    job_offer_id TEXT NOT NULL,
    cv_base_in_all_id TEXT NOT NULL,
    lm TEXT,
    matching_score REAL,
    generation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    mail_content TEXT,
    days_to_wait INTEGER,
    response_email TEXT,
    FOREIGN KEY (job_offer_id) REFERENCES job_offer(id) ON DELETE CASCADE,
    FOREIGN KEY (cv_base_in_all_id) REFERENCES cv_base_in_all(id) ON DELETE CASCADE

);

CREATE TABLE IF NOT EXISTS cv_applied_for_job_offer (
    id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    header TEXT,
    summary TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    certifications TEXT,
    projects TEXT,
    languages TEXT,
    interests TEXT,
    job_offer_id TEXT NOT NULL,
    cv_base_in_all_id TEXT NOT NULL,
    matching_score REAL,
    generation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_offer_id) REFERENCES job_offer(id) ON DELETE CASCADE,
    FOREIGN KEY (cv_base_in_all_id) REFERENCES cv_base_in_all(id) ON DELETE CASCADE
);