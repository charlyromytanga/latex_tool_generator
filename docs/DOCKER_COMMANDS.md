# Docker & Docker Compose Commands

## Quick Start with Docker Compose

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Build All Services

```bash
# Build all Docker images
docker-compose build

# Build specific service
docker-compose build api
docker-compose build app
docker-compose build runner
```

### 3. Start All Services

```bash
# Start all services in background
docker-compose up -d

# Start with logs output
docker-compose up

# Start specific service
docker-compose up -d api
docker-compose up -d app
docker-compose up -d runner
```

### 4. Check Service Status

```bash
# View running services
docker-compose ps

# View logs
docker-compose logs -f api      # FastAPI logs
docker-compose logs -f app      # Streamlit logs
docker-compose logs -f runner   # Runner logs
docker-compose logs -f db       # Database logs

# Watch all logs
docker-compose logs -f
```

### 5. Access Services

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **App (Streamlit):** http://localhost:8501
- **Database:** `/db/recruitment_assistant.db`

### 6. Database Management

```bash
# Initialize database (automatic on first run)
docker-compose run runner python -m src.orchestration.ingest --init-db

# Backup database
docker container run --rm -v latex_tool_db_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/db_backup_$(date +%Y%m%d).tar.gz -C /data .

# Restore database
docker container run --rm -v latex_tool_db_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/db_backup.tar.gz -C /data
```

### 7. Run Commands Inside Containers

```bash
# Execute in api container
docker-compose exec api python -m src.app.api

# Execute in runner container
docker-compose exec runner python -m src.orchestration.orchestrator --help

# Interactive shell
docker-compose exec api bash
docker-compose exec runner ash
```

### 8. Stop & Cleanup

```bash
# Stop all services (keep data)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers & volumes
docker-compose down -v

# Remove dangling images
docker image prune -f
```

---

## Individual Docker Commands

### Build Images

```bash
# Build API image
docker build -f Dockerfile.api -t latex-tool-api:latest .

# Build App image
docker build -f Dockerfile.app -t latex-tool-app:latest .

# Build Runner image
docker build -f Dockerfile.runner -t latex-tool-runner:latest .

# Build with specific tag
docker build -f Dockerfile.api -t latex-tool-api:v0.1.0 .
```

### Run Containers Manually

```bash
# Run API
docker run -d --name api -p 8000:8000 \
  -v $(pwd)/db:/app/db \
  -v $(pwd)/runs:/app/runs \
  -e DATABASE_URL="sqlite:////app/db/recruitment_assistant.db" \
  latex-tool-api:latest

# Run Streamlit App
docker run -d --name app -p 8501:8501 \
  -v $(pwd)/templates:/app/templates \
  -e API_URL="http://api:8000" \
  latex-tool-app:latest

# Run Runner
docker run -d --name runner \
  -v $(pwd)/db:/app/db \
  -v $(pwd)/runs:/app/runs \
  -e DATABASE_URL="sqlite:////app/db/recruitment_assistant.db" \
  latex-tool-runner:latest
```

### View Container Logs

```bash
# Real-time logs
docker logs -f api

# Last 50 lines
docker logs --tail 50 api

# Logs with timestamps
docker logs -t api

# Since specific time
docker logs --since 10m api
```

---

## Docker Compose Networking

All services communicate via internal `latex-network`:

```
API Service (8000)
     ↓
App Service (8501)
     ↓
Runner Service
     ↓
DB Service
```

To test connectivity between containers:

```bash
# From app container, ping api
docker-compose exec app curl http://api:8000/api/v1/health

# From runner, test database
docker-compose exec runner sqlite3 /app/db/recruitment_assistant.db "SELECT COUNT(*) FROM offers_raw;"
```

---

## Development with Docker

### Live Code Reload (Hot Reload)

API (FastAPI automatically reloads):
```bash
docker-compose up -d api
# Edit src/app/api.py
# Changes apply automatically (uvicorn --reload)
```

App (Streamlit auto-reruns on file change):
```bash
docker-compose up -d app
# Edit src/app/streamlit_app.py
# Changes apply automatically
```

### Build & Test Locally Before Pushing

```bash
# Build
docker build -f Dockerfile.api -t latex-tool-api:local .

# Run test
docker run --rm latex-tool-api:local python -m pytest tests/

# Inspect image size
docker images | grep latex-tool-api

# Inspect layers
docker history latex-tool-api:local
```

---

## Production Deployment

### Push to Registry (Docker Hub)

```bash
# Login to Docker Hub
docker login

# Tag images
docker tag latex-tool-api:latest yourusername/latex-tool-api:latest
docker tag latex-tool-app:latest yourusername/latex-tool-app:latest

# Push
docker push yourusername/latex-tool-api:latest
docker push yourusername/latex-tool-app:latest
```

### Deploy to Render

Services defined in `render.yaml`:

```bash
# Deploy via GitHub (automatic on push to main)
# Or manually trigger via GitHub Actions
```

### Security Best Practices

```bash
# Run as non-root user in Dockerfile
# Use .dockerignore to exclude secrets
# Never commit .env files
# Use GitHub Secrets for sensitive data
# Scan images for vulnerabilities
docker scan latex-tool-api:latest
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Container Exits Immediately

```bash
# Check container logs
docker-compose logs api

# Run in foreground to see errors
docker-compose up api
```

### Database Lock Issues

```bash
# Check if database is locked
docker-compose exec runner sqlite3 /app/db/recruitment_assistant.db ".mode list"

# Restart services
docker-compose restart
```

### Memory Issues

```bash
# Check memory usage
docker stats

# Limit memory per service (in docker-compose.yml)
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
```

---

## Monitoring & Health Checks

```bash
# Check service health
docker-compose exec api curl http://localhost:8000/api/v1/health

# View health check history
docker inspect api | jq '.State.Health'

# Monitor resource usage
docker stats --no-stream

# View container process tree
docker top api

# Check disk usage
docker system df
```

---

## Useful References

- Docker Documentation: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Multi-stage builds: https://docs.docker.com/build/building/multi-stage/
