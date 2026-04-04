# DATABASE SCHEMA - SQLite

## Initialisation

Fichier: `db/schema_init.sql`

Execution locale:

```bash
bash scripts/init_db.sh
```

Ou via Makefile:

```bash
make db-init
```

```sql
-- ============================================================================
-- TABLE: offers_raw
-- Définition: Stockage offres brutes + sections extraites
-- ============================================================================
CREATE TABLE IF NOT EXISTS offers_raw (
    offer_id TEXT PRIMARY KEY,                -- UUID
    company_name TEXT NOT NULL,
    location TEXT NOT NULL,                   -- Ville, Pays
    country TEXT NOT NULL,
    tier TEXT NOT NULL CHECK(tier IN ('tier-1', 'tier-2', 'tier-3')),
    raw_text TEXT NOT NULL,                   -- Markdown brut
    sections_json TEXT NOT NULL,              -- JSON: {title, company, tier, responsibilities[], skills[], qualifications[]}
    ingestion_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_file TEXT NOT NULL,
    extracted_at DATETIME
);
CREATE INDEX idx_offers_raw_company ON offers_raw(company_name);
CREATE INDEX idx_offers_raw_country ON offers_raw(country);
CREATE INDEX idx_offers_raw_tier ON offers_raw(tier);

-- ============================================================================
-- TABLE: offer_keywords
-- Définition: Keywords extraits par LLM Model 1
-- ============================================================================
CREATE TABLE IF NOT EXISTS offer_keywords (
    keyword_id TEXT PRIMARY KEY,              -- UUID
    offer_id TEXT NOT NULL,
    keywords_json TEXT NOT NULL,              -- JSON: {technical[], soft_skills[], domain[], seniority}
    model_version TEXT NOT NULL,              -- ex. "gpt-4-turbo-2024-04"
    extraction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE
);
CREATE INDEX idx_offer_keywords_offer ON offer_keywords(offer_id);

-- ============================================================================
-- TABLE: my_experiences
-- Définition: Expériences personnelles (pour matching)
-- ============================================================================
CREATE TABLE IF NOT EXISTS my_experiences (
    exp_id TEXT PRIMARY KEY,                  -- UUID
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    duration_months INTEGER,
    description TEXT NOT NULL,                -- Description libre en Markdown
    skills_json TEXT NOT NULL,                -- JSON: [skill1, skill2, ...]
    achievements_json TEXT NOT NULL,          -- JSON: [achievement1, achievement2, ...]
    start_date DATE,
    end_date DATE,
    tags_json TEXT,                           -- JSON: ["tag1", "tag2"] pour recherche rapide
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_my_experiences_role ON my_experiences(role);
CREATE INDEX idx_my_experiences_company ON my_experiences(company);

-- ============================================================================
-- TABLE: my_projects
-- Définition: Projets Git personnels (README + metadata)
-- ============================================================================
CREATE TABLE IF NOT EXISTS my_projects (
    project_id TEXT PRIMARY KEY,              -- UUID
    repo_name TEXT NOT NULL UNIQUE,
    repo_url TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,                -- README ou résumé
    languages_json TEXT NOT NULL,             -- JSON: ["Python", "JavaScript", ...]
    technologies_json TEXT NOT NULL,          -- JSON: ["React", "FastAPI", ...]
    readme_full_text TEXT,                    -- README complet pour matching LLM
    stars INTEGER,
    last_updated DATE,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_my_projects_repo ON my_projects(repo_name);

-- ============================================================================
-- TABLE: matching_scores
-- Définition: Résultats matching offre vs expériences/projets
-- ============================================================================
CREATE TABLE IF NOT EXISTS matching_scores (
    match_id TEXT PRIMARY KEY,                -- UUID
    offer_id TEXT NOT NULL,
    match_type TEXT NOT NULL CHECK(match_type IN ('experience', 'project')),
    exp_id TEXT,                              -- NULL si match_type='project'
    project_id TEXT UNIQUE,                   -- NULL si match_type='experience'
    match_score REAL NOT NULL CHECK(match_score >= 0.0 AND match_score <= 1.0),
    reasoning TEXT NOT NULL,                  -- Résumé LLM: pourquoi ce match
    model_version TEXT NOT NULL,              -- ex. "gpt-4-turbo-2024-04"
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE,
    FOREIGN KEY (exp_id) REFERENCES my_experiences(exp_id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES my_projects(project_id) ON DELETE SET NULL
);
CREATE INDEX idx_matching_scores_offer ON matching_scores(offer_id);
CREATE INDEX idx_matching_scores_score ON matching_scores(match_score DESC);

-- ============================================================================
-- TABLE: generations
-- Définition: Traces CV/LM générés + metadata
-- ============================================================================
CREATE TABLE IF NOT EXISTS generations (
    generation_id TEXT PRIMARY KEY,           -- UUID
    offer_id TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK(channel_type IN ('cv', 'letter', 'thank_you', 'email', 'report', 'thesis')),
    language TEXT NOT NULL CHECK(language IN ('fr', 'en')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'success', 'failed')),
    artifact_path TEXT,                       -- Chemin PDF/HTML généré
    artifact_hash TEXT,                       -- SHA256 du fichier généré
    file_size_bytes INTEGER,
    generation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    top_matches_json TEXT,                    -- JSON: [exp1, exp2, proj1] utilisés dans génération
    render_duration_ms INTEGER,               -- Durée render LaTeX/HTML
    error_message TEXT,                       -- Si status='failed'
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE
);
CREATE INDEX idx_generations_offer ON generations(offer_id);
CREATE INDEX idx_generations_channel ON generations(channel_type);
CREATE INDEX idx_generations_status ON generations(status);

-- ============================================================================
-- TABLE: archive_manifest
-- Définition: Manifest d'archive (index)
-- ============================================================================
CREATE TABLE IF NOT EXISTS archive_manifest (
    archive_id TEXT PRIMARY KEY,              -- UUID
    offer_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
    tier TEXT NOT NULL CHECK(tier IN ('tier-1', 'tier-2', 'tier-3')),
    country TEXT NOT NULL,
    company TEXT NOT NULL,
    cv_generation_id TEXT,
    letter_generation_id TEXT,
    archive_created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived_at DATETIME,
    FOREIGN KEY (offer_id) REFERENCES offers_raw(offer_id) ON DELETE CASCADE,
    FOREIGN KEY (cv_generation_id) REFERENCES generations(generation_id),
    FOREIGN KEY (letter_generation_id) REFERENCES generations(generation_id)
);
CREATE INDEX idx_archive_manifest_offer ON archive_manifest(offer_id);
CREATE INDEX idx_archive_manifest_year_month ON archive_manifest(year, month);
CREATE INDEX idx_archive_manifest_tier ON archive_manifest(tier);
CREATE INDEX idx_archive_manifest_country ON archive_manifest(country);
CREATE INDEX idx_archive_manifest_company ON archive_manifest(company);
```

---

## Requêtes Utiles

### Ajouter une nouvelle offre

```sql
INSERT INTO offers_raw (offer_id, company_name, location, country, tier, raw_text, sections_json, source_file)
VALUES (
    'offer-20260405-123456',
    'Acme Corp',
    'Paris, France',
    'France',
    'tier-2',
    '# Offer Text...',
    '{"title": "...", "skills": [...]}',
    'data/offers/2026/Q2/tier-2/france/acme_corp/offer.md'
);
```

### Récupérer offre + keywords + matching

```sql
SELECT 
    o.offer_id,
    o.company_name,
    o.tier,
    k.keywords_json,
    GROUP_CONCAT(m.match_id || '|' || m.exp_id || '|' || m.match_score) as matches
FROM offers_raw o
LEFT JOIN offer_keywords k ON o.offer_id = k.offer_id
LEFT JOIN matching_scores m ON o.offer_id = m.offer_id AND m.match_score >= 0.5
WHERE o.offer_id = 'offer-20260405-123456'
GROUP BY o.offer_id;
```

### Lister CV générés par année/mois/tier

```sql
SELECT 
    am.year,
    am.month,
    am.tier,
    am.country,
    am.company,
    COUNT(*) as count,
    SUM(g.file_size_bytes) as total_size_bytes
FROM archive_manifest am
LEFT JOIN generations g ON am.cv_generation_id = g.generation_id
WHERE am.year = 2026
GROUP BY am.year, am.month, am.tier, am.country, am.company
ORDER BY am.year DESC, am.month DESC;
```

### Trouver top matching experiences pour une offre

```sql
SELECT 
    m.match_id,
    exp.company,
    exp.role,
    m.match_score,
    m.reasoning
FROM matching_scores m
JOIN my_experiences exp ON m.exp_id = exp.exp_id
WHERE m.offer_id = 'offer-20260405-123456'
  AND m.match_type = 'experience'
ORDER BY m.match_score DESC
LIMIT 5;
```

### DB Size Monitoring

```sql
-- Taille par table
SELECT 
    name,
    (SELECT COUNT(*) FROM offers_raw) as offers_count,
    (SELECT COUNT(*) FROM generations) as generations_count,
    (SELECT COUNT(*) FROM my_experiences) as experiences_count,
    (SELECT COUNT(*) FROM my_projects) as projects_count,
    (SELECT COUNT(*) FROM matching_scores) as matching_count;

-- Taille fichier DB
SELECT 
    'recruitment_assistant.db' as filename,
    ROUND(page_count * page_size / 1024.0 / 1024.0, 2) as size_mb
FROM pragma_page_count(), pragma_page_size();
```

---

## Migrations Futures

**Fichier:** `db/migrations/001_initial_schema.sql`

À maintenir au fur et à mesure d'évolutions (versioning).
