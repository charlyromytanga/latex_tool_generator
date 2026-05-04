-- PostgreSQL schema initialization for recruitment assistant
-- Mirror of db/schema_init.sql for future Render Postgres migration

BEGIN;

CREATE TABLE IF NOT EXISTS offers_raw (
    offer_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    location TEXT NOT NULL,
    country TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    raw_text TEXT NOT NULL,
    sections_json TEXT NOT NULL,
    ingestion_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    source_file TEXT NOT NULL,
    extracted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_offers_raw_company ON offers_raw(company_name);
CREATE INDEX IF NOT EXISTS idx_offers_raw_country ON offers_raw(country);
CREATE INDEX IF NOT EXISTS idx_offers_raw_tier ON offers_raw(tier);

CREATE TABLE IF NOT EXISTS offer_keywords (
    keyword_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    keywords_json TEXT NOT NULL,
    model_version TEXT NOT NULL,
    extraction_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_offer_keywords_offer ON offer_keywords(offer_id);

CREATE TABLE IF NOT EXISTS my_experiences (
    exp_id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    duration_months INTEGER,
    description TEXT NOT NULL,
    skills_json TEXT NOT NULL,
    achievements_json TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    tags_json TEXT,
    indexed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_my_experiences_role ON my_experiences(role);
CREATE INDEX IF NOT EXISTS idx_my_experiences_company ON my_experiences(company);

CREATE TABLE IF NOT EXISTS my_projects (
    project_id TEXT PRIMARY KEY,
    repo_name TEXT NOT NULL UNIQUE,
    repo_url TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    languages_json TEXT NOT NULL,
    technologies_json TEXT NOT NULL,
    readme_full_text TEXT,
    stars INTEGER,
    last_updated DATE,
    indexed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_my_projects_repo ON my_projects(repo_name);

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
    indexed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_formations_institution ON formations(institution);
CREATE INDEX IF NOT EXISTS idx_formations_program ON formations(program);
CREATE INDEX IF NOT EXISTS idx_formations_dates ON formations(start_date, end_date);

CREATE TABLE IF NOT EXISTS formation_matching_scores (
    match_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    formation_id TEXT NOT NULL,
    match_score DOUBLE PRECISION NOT NULL CHECK (match_score >= 0.0 AND match_score <= 1.0),
    reasoning TEXT NOT NULL,
    model_version TEXT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE,
    FOREIGN KEY (formation_id) REFERENCES formations(formation_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_formation_matching_offer ON formation_matching_scores(offer_id);
CREATE INDEX IF NOT EXISTS idx_formation_matching_formation ON formation_matching_scores(formation_id);
CREATE INDEX IF NOT EXISTS idx_formation_matching_score ON formation_matching_scores(match_score DESC);

CREATE TABLE IF NOT EXISTS matching_scores (
    match_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    match_type TEXT NOT NULL CHECK (match_type IN ('experience', 'project')),
    exp_id TEXT,
    project_id TEXT,
    match_score DOUBLE PRECISION NOT NULL CHECK (match_score >= 0.0 AND match_score <= 1.0),
    reasoning TEXT NOT NULL,
    model_version TEXT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE,
    FOREIGN KEY (exp_id) REFERENCES my_experiences(exp_id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES my_projects(project_id) ON DELETE SET NULL,
    CHECK (
        (match_type = 'experience' AND exp_id IS NOT NULL AND project_id IS NULL)
        OR
        (match_type = 'project' AND project_id IS NOT NULL AND exp_id IS NULL)
    )
);
CREATE INDEX IF NOT EXISTS idx_matching_scores_offer ON matching_scores(offer_id);
CREATE INDEX IF NOT EXISTS idx_matching_scores_score ON matching_scores(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_matching_scores_type ON matching_scores(match_type);

CREATE TABLE IF NOT EXISTS generations (
    generation_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('cv', 'letter', 'thank_you', 'email', 'report', 'thesis')),
    language TEXT NOT NULL CHECK (language IN ('fr', 'en')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed')),
    artifact_path TEXT,
    artifact_hash TEXT,
    file_size_bytes INTEGER,
    generation_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    top_matches_json TEXT,
    render_duration_ms INTEGER,
    error_message TEXT,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_generations_offer ON generations(offer_id);
CREATE INDEX IF NOT EXISTS idx_generations_channel ON generations(channel_type);
CREATE INDEX IF NOT EXISTS idx_generations_status ON generations(status);

CREATE TABLE IF NOT EXISTS archive_manifest (
    archive_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    tier TEXT NOT NULL CHECK (tier IN ('tier-1', 'tier-2', 'tier-3')),
    country TEXT NOT NULL,
    company TEXT NOT NULL,
    cv_generation_id TEXT,
    letter_generation_id TEXT,
    archive_created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMPTZ,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE,
    FOREIGN KEY (cv_generation_id) REFERENCES generations(generation_id),
    FOREIGN KEY (letter_generation_id) REFERENCES generations(generation_id)
);
CREATE INDEX IF NOT EXISTS idx_archive_manifest_offer ON archive_manifest(offer_id);
CREATE INDEX IF NOT EXISTS idx_archive_manifest_year_month ON archive_manifest(year, month);
CREATE INDEX IF NOT EXISTS idx_archive_manifest_tier ON archive_manifest(tier);
CREATE INDEX IF NOT EXISTS idx_archive_manifest_country ON archive_manifest(country);
CREATE INDEX IF NOT EXISTS idx_archive_manifest_company ON archive_manifest(company);

COMMIT;