# API Specification - FastAPI

## Statut actuel

Ce document decrit la cible d'API.

- Etat du code: `src/app/api.py` et les routes associees ne sont pas encore implementes dans cette phase.
- Usage: contrat fonctionnel pour la future Phase 4 (API + UI), apres finalisation des phases ingestion et LLM.

## Vue d'ensemble

L'API expose les fonctionnalités d'orchestration en 3 niveaux via endpoints REST JSON.

**Base URL:**
- Local: `http://localhost:8000`
- Production (Render): `https://recruitment-app.onrender.com`

**Authentification:** À définir (token JWT ou API key)

**Format réponse:** JSON + HTTP status codes standard

---

## Endpoints

### 1. Health & Status

#### `GET /api/health`

Vérification santé de l'API.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T10:30:00Z",
  "db_connected": true,
  "llm_available": true
}
```

---

### 2. Offers Management

#### `POST /api/offers`

Ingest une nouvelle offre (Markdown).

**Request:**
```json
{
  "markdown_content": "# Senior Backend Engineer\n...",
  "source_file": "offer.md",
  "ingestion_date": "2026-04-05"
}
```

**Response (201):**
```json
{
  "status": "ingested",
  "offer_id": "offer-20260405-xyz123",
  "company_name": "Acme Corp",
  "tier": "tier-2",
  "country": "France",
  "sections_detected": {
    "title": "Senior Backend Engineer",
    "company": "Acme Corp",
    "responsibilities": ["...", "..."],
    "skills": ["Python", "FastAPI", "..."]
  }
}
```

**Error (400):**
```json
{
  "error": "Invalid Markdown format",
  "details": "Missing required section: Tier"
}
```

#### `GET /api/offers/{offer_id}`

Récupérer offre depuis DB (avec keywords + matching results).

**Response (200):**
```json
{
  "offer_id": "offer-20260405-xyz123",
  "company_name": "Acme Corp",
  "tier": "tier-2",
  "country": "France",
  "raw_text": "# Offer...",
  "sections": { "title": "...", "skills": [...] },
  "keywords_extracted": {
    "technical": ["Python", "FastAPI"],
    "soft_skills": ["Leadership", "Communication"],
    "domain": "FinTech",
    "seniority": "Senior"
  },
  "matching_results": {
    "confidence": 0.78,
    "top_experiences": [
      {
        "exp_id": "exp-001",
        "company": "OldStartup",
        "role": "Lead Dev",
        "score": 0.85,
        "reasoning": "Experience matching 5/7 tech keywords"
      }
    ],
    "top_projects": [
      {
        "project_id": "proj-001",
        "repo_name": "my-api-framework",
        "score": 0.72,
        "reasoning": "Project uses FastAPI, 3/4 tech keywords match"
      }
    ]
  },
  "recommendation": "GO_TO_LEVEL3"  // GO / REVIEW / SKIP
}
```

---

### 3. Matching & Analysis

#### `GET /api/matching/{offer_id}`

Résultats détaillés du matching LLM (Level 2).

**Query params:**
- `threshold` (default: 0.5): Score minimum pour inclusion
- `limit` (default: 10): Nombre de résultats max

**Response (200):**
```json
{
  "offer_id": "offer-20260405-xyz123",
  "matching_computed_at": "2026-04-05T10:35:00Z",
  "model_version": "gpt-4-turbo-2024-04",
  "overall_confidence": 0.78,
  "experiences": [
    {
      "rank": 1,
      "exp_id": "exp-001",
      "company": "OldStartup",
      "role": "Lead Backend Engineer",
      "score": 0.85,
      "matching_keywords": ["Python", "FastAPI", "System Design"],
      "reasoning": "Excellent match: 6/7 key technical skills + leadership experience"
    }
  ],
  "projects": [
    {
      "rank": 1,
      "project_id": "proj-001",
      "repo_name": "my-api-framework",
      "languages": ["Python"],
      "scores": 0.72,
      "matching_keywords": ["FastAPI"],
      "reasoning": "Demonstrates FastAPI expertise, relevant for API design role"
    }
  ]
}
```

---

### 4. Generation (Level 3)

#### `POST /api/generate/cv_letter`

Trigger génération CV + Lettre pour une offre (gated par threshold).

**Request:**
```json
{
  "offer_id": "offer-20260405-xyz123",
  "language": "fr",  // fr | en
  "force": false,    // Override confidence threshold
  "use_top_matches": true,
  "custom_experiences_ids": ["exp-001", "exp-003"],  // Override auto-select
  "custom_projects_ids": ["proj-001"]
}
```

**Response (202 - Accepted):**
```json
{
  "status": "generation_in_progress",
  "generation_id": "gen-20260405-abc789",
  "offer_id": "offer-20260405-xyz123",
  "estimated_duration_seconds": 30
}
```

#### Polling Generation Status

`GET /api/generate/{generation_id}`

**Response (200) - Still rendering:**
```json
{
  "status": "rendering",
  "progress": 75,
  "message": "Rendering LaTeX to PDF..."
}
```

**Response (200) - Complete:**
```json
{
  "status": "completed",
  "generation_id": "gen-20260405-abc789",
  "artifacts": {
    "cv": {
      "id": "cv-gen-001",
      "format": "pdf",
      "path": "runs/run_cv/2026/04/tier-2/france/acme_corp/cv_offer-xyz123.pdf",
      "size_bytes": 245000,
      "generated_at": "2026-04-05T10:40:00Z"
    },
    "letter": {
      "id": "lm-gen-001",
      "format": "pdf",
      "path": "runs/run_cv/2026/04/tier-2/france/acme_corp/lm_offer-xyz123.pdf",
      "size_bytes": 178000
    }
  },
  "render_duration_ms": 12000,
  "used_experiences": ["exp-001"],
  "used_projects": ["proj-001"]
}
```

---

### 5. Preview & Download

#### `GET /api/preview/{generation_id}`

Récupère preview (base64) pour affichage dans app Streamlit.

**Response (200):**
```json
{
  "generation_id": "gen-20260405-abc789",
  "artifacts": {
    "cv": {
      "format": "base64_png",
      "pages": [
        "iVBORw0KGgoAAAANSUhEUg...",  // Page 1
        "iVBORw0KGgoAAAANSUhEUg..."   // Page 2
      ],
      "page_count": 2
    },
    "letter": {
      "format": "base64_png",
      "pages": ["iVBORw0KGgoAAAANSUhEUg..."],
      "page_count": 1
    }
  }
}
```

#### `GET /api/download/{generation_id}/{artifact_type}`

Télécharge PDF directement.

**Params:**
- `artifact_type`: `cv` | `letter`

**Response (200):**
- Content-Type: `application/pdf`
- Fichier binaire

---

### 6. Integration

#### `POST /api/integrate/submit`

Submit candidature via intégration externe (si applicable).

**Request:**
```json
{
  "generation_id": "gen-20260405-abc789",
  "integration": "linkedin",  // linkedin | other_job_board
  "offer_url": "https://www.linkedin.com/jobs/view/...",
  "metadata": {}
}
```

**Response (202):**
```json
{
  "status": "submitted",
  "submission_id": "sub-20260405-def999",
  "offer_url": "https://...",
  "timestamp": "2026-04-05T11:00:00Z"
}
```

---

## Error Handling

Tous les endpoints retournent les codes HTTP standard:

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 202 | Accepted (async) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Internal Server Error |

**Exemple erreur (400):**
```json
{
  "error": "BAD_REQUEST",
  "message": "Offer ID not found",
  "timestamp": "2026-04-05T10:30:00Z"
}
```

---

## Rate Limiting

- Local: Pas de limites
- Production: À définir (ex. 100 req/min)

---

## Authentication

À implémenter (JWT token ou API key dans header):

```
Authorization: Bearer <token>
```

---

## Déploiement sur Render

Fichier service: `render.yaml` (à la racine)

```yaml
services:
  - type: web
    name: recruitment-api
    runtime: python311
    buildCommand: uv sync && python -m src.app.api
    startCommand: uvicorn src.app.api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        value: sqlite:///db/recruitment_assistant.db
      - key: LLM_API_KEY
        fromService:
          type: env
          property: LLM_API_KEY
```
