# Déploiement - CI/CD et Render

## Vue d'ensemble

Le projet deploie sur **Render.com** via **GitHub Actions** avec CI/CD automatique.

---

## 1. CI/CD Pipeline (GitHub Actions)

### Fichier: `.github/workflows/ci.yml`

```yaml
name: CI - Test & Lint

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: uv sync
      
      - name: Lint with Pylance
        run: uv run pylint src/
      
      - name: Run tests
        run: uv run pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image (test)
        run: docker build -t recruitment-app:test .
```

### Fichier: `.github/workflows/deploy-render.yml`

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Trigger Render deployment
        run: |
          curl -X POST \
            https://api.render.com/deploy/srv-${RENDER_SERVICE_ID}?key=${RENDER_API_KEY}
        env:
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
      
      - name: Wait for deployment
        run: sleep 60
      
      - name: Health check
        run: |
          curl --fail https://recruitment-app.onrender.com/api/health \
            || exit 1
```

### Fichier: `.github/workflows/db-backup.yml`

```yaml
name: Database Backup

on:
  schedule:
    - cron: "0 2 * * *"  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Download DB from Render
        run: |
          # Fetch DB via API (si exposed) ou SSH
          # Example: scp render:/app/db/recruitment_assistant.db ./backup/
          echo "Backup implementation pending"
      
      - name: Upload to GitHub Releases
        uses: softprops/action-gh-release@v1
        with:
          files: backup/recruitment_assistant.db.gz
```

---

## 2. Déploiement sur Render

### Runtime multi-base et bascule PostgreSQL

Le runtime supporte désormais SQLite et PostgreSQL via la variable d'environnement DATABASE_URL.

Règles de fonctionnement:
- SQLite local par défaut si DATABASE_URL n'est pas défini
- PostgreSQL activé dès que DATABASE_URL pointe vers postgresql://...
- Le service API applique automatiquement le schéma PostgreSQL sur Render via preDeployCommand
- Le workflow GitHub Actions applique aussi le schéma initial via le job migrate-db

Artifacts ajoutés pour cette transition:
- `db/schema_postgres.sql`
- `src/orchestration/database.py`
- `scripts/init_postgres_db.sh`
- `scripts/mirror_sqlite_to_postgres.sh`
- `python -m orchestration.postgres_mirror`

Exemple local:

```bash
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/recruitment_assistant bash scripts/init_postgres_db.sh
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/recruitment_assistant bash scripts/mirror_sqlite_to_postgres.sh
```

Activation locale PostgreSQL avec Docker Compose:

```bash
COMPOSE_PROFILES=postgres \
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/recruitment_assistant \
docker-compose up -d postgres api app runner
```

Initialisation du schéma local PostgreSQL:

```bash
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/recruitment_assistant bash scripts/init_postgres_db.sh
```

Miroir optionnel SQLite vers PostgreSQL:

```bash
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/recruitment_assistant bash scripts/mirror_sqlite_to_postgres.sh
```

### Render Service Configuration

**Fichier: `render.yaml`** (root)

Le blueprint Render est maintenant configuré pour:
- créer une base Render Postgres `recruitment-db`
- injecter DATABASE_URL depuis `fromDatabase.connectionString`
- exécuter `bash scripts/init_postgres_db.sh` avant chaque déploiement API
- exposer la santé API sur `/api/health`

### Étapes Manuelles (First Time)

1. **Créer projet Render:**
   ```bash
   # Via Render Dashboard:
   # 1. New → Web Service
   # 2. Connect GitHub repo
   # 3. Branch: main
   # 4. Root dir: .
   # 5. Runtime: Python 3.11
   # 6. Build: uv sync
   # 7. Start: uvicorn src.app.api:app --host 0.0.0.0 --port $PORT
   ```

2. **Configurer Environment Variables:**
   ```
   PYTHONUNBUFFERED=1
   LLM_API_KEY=<your-key>
   ENVIRONMENT=production
   ```

3. **Secrets GitHub / Render pour PostgreSQL:**
  ```
  RENDER_POSTGRES_DSN=<external postgres url for CI migration job>
  OPENAI_API_KEY=<your-key>
  CLAUDE_API_KEY=<your-key>
  ```

4. **Test:**
   ```bash
   curl https://recruitment-app.onrender.com/api/health
   # Expected: {"status": "healthy", ...}
   ```

---

## 3. Structure des Secrets GitHub

**Settings → Secrets → Actions**

```
RENDER_SERVICE_ID       = srv-1a2b3c4d5e6f7g
RENDER_API_KEY          = rnd_abcdefghijklmnop
RENDER_POSTGRES_DSN     = postgresql://...
OPENAI_API_KEY          = sk-proj-...
CLAUDE_API_KEY          = claude-...
CODECOV_TOKEN           = (optional)
```

---

## 4. Rollback & Versioning

### Tagging et Releases

```bash
# Create release tag
git tag -a v0.2.0 -m "Release v0.2.0 - Level 2 LLM Integration"
git push origin v0.2.0

# Render auto-deploys from main
# Rollback via GitHub Actions: Re-run workflow for previous commit
```

### Emergency Rollback

```bash
# If deployment broken:
git revert <bad-commit>
git push origin main
# GitHub Actions auto-triggers → Render redeploys
```

---

## 5. Monitoring & Logging

### Render Logs

- Accessible via Render Dashboard
- Streaming logs: `https://dashboard.render.com/services/<service-id>`

### Application Logs

```python
# src/app/api.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/offers")
def upload_offer(data: dict):
    logger.info(f"Offer upload: {data['company_name']}")
    # ...
```

### Database Backups

- Manual: `sqlite3 db/recruitment_assistant.db .dump > backup.sql`
- Automated: via `.github/workflows/db-backup.yml`

---

## 6. Alternative: Déploiement à Distance (SSH)

Si Render indisponible, déployer sur serveur perso via SSH:

```bash
#!/bin/bash
# scripts/deploy_ssh.sh

HOST="user@myserver.com"
REMOTE_PATH="/opt/recruitment-assistant"

ssh $HOST "cd $REMOTE_PATH && git pull origin main"
ssh $HOST "cd $REMOTE_PATH && uv sync && systemctl restart recruitment-api"
echo "Deployment complete"
```

---

## 7. Performance & Scalabilité

**Render Tier Actuel:**
- Pro tier: 0.05 USD/hour
- 512MB RAM, 1 CPU
- Sufficient pour MVP

**Upgrade si needed:**
- Standard tier: 0.50 USD/hour
- 1GB RAM, 2 CPU
- Recommended si > 1000 offers/month

**Caching:**
- Render: Built-in varnish cache (optionnel)
- App: Redis cache pour LLM results (future)

---

## 8. Checklist Déploiement

- [ ] Repository bien configuré (public ou privé selon besoin)
- [ ] Secrets GitHub ajoutés (`RENDER_SERVICE_ID`, `RENDER_API_KEY`, etc.)
- [ ] Render account créé + GitHub connecté
- [ ] `.github/workflows/` fichiers un place
- [ ] `render.yaml` à la racine + reviewed
- [ ] Database init script testé localement
- [ ] Health check endpoint (`/api/health`) fonctionnel
- [ ] Logs accessible + monitoring setup
- [ ] Rollback procedure documentée et testée
- [ ] Backup automatique configuré (optionnel mais recommandé)
