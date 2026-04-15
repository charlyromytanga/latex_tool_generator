# API Specification - FastAPI

## Statut actuel (implémentation réelle)

Ce document décrit le contrat effectivement implémenté dans les routes FastAPI et validé contre la base SQLite locale.

- Entrypoint API: `src/app/api/api.py`
- Routes: `src/app/api/routes/*.py`
- Schéma DB local: `db/recruitment_assistant.db`

## Vue d'ensemble

Base URL:
- Local: `http://localhost:8000`

Format:
- JSON pour les endpoints applicatifs
- Binaire PDF pour le téléchargement

Authentification:
- Non implémentée actuellement

## Cohérence API <-> DB (points clés)

### Ingestion d'offre

Payload d'entrée API:
```json
{
  "markdown_content": "# ...",
  "source_file": "api_upload.md",
  "ingestion_date": "2026-04-05"
}
```

Persistance réelle en DB (`offers_raw`):
- `raw_text` reçoit `markdown_content`
- `source_file` est persisté
- `ingestion_timestamp` est généré par SQLite (DEFAULT CURRENT_TIMESTAMP)
- `extracted_at` est généré côté orchestrateur

Important:
- `ingestion_date` est accepté par le modèle API mais n'est pas utilisé par la route, ni persisté tel quel.

### Matching

L'endpoint lit:
- `matching_scores` (expériences/projets)
- `formation_matching_scores` (formations)

La réponse API contient des champs calculés (`overall_confidence`, `matching_computed_at`) et ne reflète pas 1:1 les colonnes des tables.

### Génération

`POST /api/generate/cv_letter` crée une ligne dans `generations` avec:
- `channel_type = "cv"`
- `status = "pending"`
- `top_matches_json` sérialisé depuis le payload

## Endpoints

### 1) Health

#### `GET /api/health`

Response `200`:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T10:30:00Z",
  "db_connected": true,
  "llm_available": true
}
```

### 2) Offers

#### `POST /api/offers`

Request:
```json
{
  "markdown_content": "# Senior Backend Engineer\n...",
  "source_file": "offer.md",
  "ingestion_date": "2026-04-05"
}
```

Notes:
- `source_file` est optionnel (défaut: `api_upload.md`)
- `ingestion_date` est optionnel et ignoré actuellement

Response `201`:
```json
{
  "status": "ingested",
  "offer_id": "offer-20260405103000-ab12cd34",
  "company_name": "Acme Corp",
  "tier": "tier-2",
  "country": "France",
  "sections_detected": {
    "company": "Acme Corp",
    "tier": "tier-2",
    "country": "France"
  }
}
```

#### `GET /api/offers/{offer_id}`

Response `200`:
```json
{
  "offer_id": "offer-20260405103000-ab12cd34",
  "company_name": "Acme Corp",
  "tier": "tier-2",
  "country": "France",
  "raw_text": "# Offer...",
  "sections": {
    "title": "Senior Backend Engineer",
    "company": "Acme Corp",
    "location": "Paris, France",
    "country": "France",
    "tier": "tier-2",
    "description": "...",
    "responsibilities": ["..."],
    "skills": ["Python", "FastAPI"],
    "qualifications": ["..."],
    "benefits": ["..."]
  },
  "keywords_extracted": {
    "technical": ["Python"]
  },
  "matching_results": {
    "confidence": 0.78,
    "top_experiences": [
      {
        "exp_id": "exp-001",
        "score": 0.85,
        "reasoning": "..."
      }
    ],
    "top_projects": [
      {
        "project_id": "proj-001",
        "score": 0.72,
        "reasoning": "..."
      }
    ]
  },
  "recommendation": "GO_TO_LEVEL3"
}
```

`recommendation` est calculé via les seuils de config:
- `GO_TO_LEVEL3` si `confidence >= go_threshold`
- `REVIEW` si `review_threshold <= confidence < go_threshold`
- `SKIP` sinon

### 3) Matching

#### `GET /api/matching/{offer_id}`

Query params:
- `threshold` (défaut: `0.0`, attendu entre `0.0` et `1.0`)
- `limit` (défaut: `10`, attendu entre `1` et `100`)

Response `200`:
```json
{
  "offer_id": "offer-20260405103000-ab12cd34",
  "matching_computed_at": "2026-04-05T10:35:00Z",
  "model_version": "heuristic-v0",
  "overall_confidence": 0.78,
  "experiences": [
    {
      "rank": 1,
      "exp_id": "exp-001",
      "score": 0.85,
      "reasoning": "...",
      "computed_at": "2026-04-05 10:34:10",
      "model_version": "heuristic-v0"
    }
  ],
  "projects": [
    {
      "rank": 1,
      "project_id": "proj-001",
      "score": 0.72,
      "reasoning": "...",
      "computed_at": "2026-04-05 10:34:10",
      "model_version": "heuristic-v0"
    }
  ],
  "formations": [
    {
      "formation_id": "form-001",
      "score": 0.68,
      "reasoning": "...",
      "computed_at": "2026-04-05 10:34:10",
      "model_version": "heuristic-v0"
    }
  ]
}
```

### 4) Generation

#### `POST /api/generate/cv_letter`

Request:
```json
{
  "offer_id": "offer-20260405103000-ab12cd34",
  "language": "fr",
  "force": false,
  "use_top_matches": true,
  "custom_experiences_ids": ["exp-001"],
  "custom_projects_ids": ["proj-001"]
}
```

Response `202`:
```json
{
  "status": "generation_in_progress",
  "generation_id": "gen-20260405104000-ef56gh78",
  "offer_id": "offer-20260405103000-ab12cd34",
  "estimated_duration_seconds": 30,
  "message": "Generation started",
  "progress": null,
  "render_duration_ms": null,
  "artifacts": null,
  "used_experiences": [],
  "used_projects": []
}
```

#### `GET /api/generate/{generation_id}`

Response `200` (en cours):
```json
{
  "status": "rendering",
  "generation_id": "gen-20260405104000-ef56gh78",
  "offer_id": "offer-20260405103000-ab12cd34",
  "progress": 75,
  "message": "Rendering LaTeX to PDF...",
  "render_duration_ms": 0,
  "used_experiences": [],
  "used_projects": []
}
```

Response `200` (terminé):
```json
{
  "status": "completed",
  "generation_id": "gen-20260405104000-ef56gh78",
  "offer_id": "offer-20260405103000-ab12cd34",
  "progress": 100,
  "message": "Generation completed",
  "render_duration_ms": 12000,
  "used_experiences": ["exp-001"],
  "used_projects": ["proj-001"]
}
```

### 5) Preview & Download

#### `GET /api/preview/{generation_id}`

Si un PDF existe pour `artifact_path`, l'API retourne:
```json
{
  "generation_id": "gen-20260405104000-ef56gh78",
  "artifacts": {
    "cv": {
      "format": "base64_pdf",
      "pages": ["JVBERi0xLjQK..."],
      "page_count": 1
    }
  }
}
```

Sinon, fallback:
```json
{
  "generation_id": "gen-20260405104000-ef56gh78",
  "artifacts": {
    "cv": {
      "format": "base64_png",
      "pages": [],
      "page_count": 0
    },
    "letter": {
      "format": "base64_png",
      "pages": [],
      "page_count": 0
    }
  }
}
```

#### `GET /api/download/{generation_id}/{artifact_type}`

`artifact_type` accepté: `cv` ou `letter`

Response `200`:
- Content-Type: `application/pdf`
- Corps binaire

### 6) Integration

#### `POST /api/integrate/submit`

Request:
```json
{
  "generation_id": "gen-20260405104000-ef56gh78",
  "integration": "linkedin",
  "offer_url": "https://www.linkedin.com/jobs/view/...",
  "metadata": {}
}
```

Response `202`:
```json
{
  "status": "submitted",
  "generation_id": "gen-20260405104000-ef56gh78",
  "integration": "linkedin",
  "offer_url": "https://www.linkedin.com/jobs/view/...",
  "submitted_at": "2026-04-05T11:00:00Z",
  "metadata": {}
}
```

## Erreurs

Format d'erreur FastAPI (effectif):
```json
{
  "detail": "Offer not found: offer-xxx"
}
```

Codes observés selon les routes:
- `200`, `201`, `202`
- `400`, `404`, `422`, `500`

## Schéma DB validé localement

Tables présentes:
- `offers_raw`
- `offer_keywords`
- `matching_scores`
- `formation_matching_scores`
- `generations`
- `archive_manifest`
- `my_experiences`
- `my_projects`
- `formations`

Champs importants de cohérence:
- `offers_raw.raw_text` (contenu markdown)
- `offers_raw.source_file`
- `offers_raw.ingestion_timestamp`
- `offers_raw.extracted_at`
- `generations.top_matches_json`
