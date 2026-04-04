# GitHub Secrets Configuration for CI/CD & Render Deployment

This document outlines all GitHub secrets to configure for automated CI/CD and production deployment.

## Required Secrets for Deployment

Configure these in: **Settings → Secrets and variables → Actions**

### Render Deployment Secrets

```
RENDER_SERVICE_ID_API
  Description: Render service ID for FastAPI backend
  Value: srv-xxxxxxxxxxxxxxxxx (from Render dashboard)
  
RENDER_SERVICE_ID_APP
  Description: Render service ID for Streamlit frontend
  Value: srv-yyyyyyyyyyyyyyyyy (from Render dashboard)
  
RENDER_API_KEY
  Description: Render API authentication token
  Value: rnd_XXXXXXXXXXXXX (from account.render.com → API Keys)
  
RENDER_SERVICE_URL_API
  Description: Deployed API URL
  Value: https://latex-tool-api.onrender.com
  
RENDER_SERVICE_URL_APP
  Description: Deployed app URL
  Value: https://latex-tool-app.onrender.com
```

### LLM API Secrets

```
OPENAI_API_KEY
  Description: OpenAI API key for GPT models
  Value: sk-proj-XXXXXXXXXXXXX (from platform.openai.com → API keys)
  
CLAUDE_API_KEY
  Description: Anthropic Claude API key
  Value: sk-ant-XXXXXXXXXXXXX (from console.anthropic.com → API keys)
```

### GitHub & Social Integrations

```
GITHUB_TOKEN
  Description: GitHub personal access token (for project reports)
  Value: ghp-XXXXXXXXXXXXX (from github.com → Settings → Developer settings → Personal access tokens)
  Scopes: repo, read:user

SLACK_WEBHOOK_URL
  Description: Slack webhook for deployment notifications
  Value: https://hooks.slack.com/services/TXXXXXXXX/BXXXXXXXX/XXXXXXXXXXXXX
  (from Slack workspace → Apps → Incoming WebHooks)
```

### Email Configuration Secrets

```
SMTP_PASSWORD
  Description: App-specific password for email sending
  Value: xxxx xxxx xxxx xxxx (16-char password for Gmail, generated from myaccount.google.com → Security)
```

---

## Setup Instructions

### Step 1: Create Render Account & Services

1. Go to https://render.com
2. Create two web services:
   - **Service 1 (API):**
     - Name: `latex-tool-api`
     - GitHub repo: `your-repo/latex_tool_generator`
     - Branch: `main`
     - Build Command: (use requirements.txt)
     - Start Command: `python -m uvicorn src.app.api:app --host 0.0.0.0...`
   
   - **Service 2 (App):**
     - Name: `latex-tool-app`
     - GitHub repo: `your-repo/latex_tool_generator`
     - Branch: `main`
     - Start Command: `streamlit run src/app/streamlit_app.py...`

3. Note the **Service IDs** (in URL: render.com/services/srv-XXXXX)

### Step 2: Generate API Keys

**Render API Key:**
1. Go to https://account.render.com
2. Settings → API Keys
3. Create new key → copy value

### Step 3: Get OpenAI & Claude Keys

**OpenAI:**
1. Go to https://platform.openai.com/account/api-keys
2. Create new secret key → copy value

**Claude:**
1. Go to https://console.anthropic.com/account/keys
2. Create new API key → copy value

### Step 4: GitHub Integration

**GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Scopes: `repo`, `read:user`
4. Copy token value

### Step 5: Slack Webhook (optional)

1. Go to your Slack workspace
2. Create an app or use existing
3. Enable Incoming WebHooks
4. Create new webhook for #deployments channel
5. Copy Webhook URL

### Step 6: Add Secrets to GitHub

1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret:
   - Name: `RENDER_SERVICE_ID_API`
   - Value: `srv-xxxxx`
4. Repeat for all secrets above

---

## Environment Variables for Render Services

### API Service (.env)

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=${OPENAI_API_KEY}  # From secrets
CLAUDE_API_KEY=${CLAUDE_API_KEY}  # From secrets
LOG_LEVEL=info
LLM_MODEL_EXTRACTION=gpt-4-turbo
LLM_MODEL_MATCHING=gpt-4-turbo
CONFIDENCE_THRESHOLD_SKIP=0.5
CONFIDENCE_THRESHOLD_REVIEW=0.75
CONFIDENCE_THRESHOLD_GO=0.85
```

### App Service (.env)

```
API_URL=https://latex-tool-api.onrender.com
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
```

---

## Deployment Workflows

### Automatic Deployment (on push to main)

`.github/workflows/deploy-render.yml` triggers automatically when code is pushed to `main` branch.

It:
1. Runs tests (pytest)
2. Builds Docker images
3. Pushes to Render via API
4. Verifies health checks (/health endpoints)
5. Sends Slack notification with status

### Manual Deployment

Trigger manually from GitHub Actions:
1. Go to repo → Actions
2. Select "Deploy to Render" workflow
3. Click "Run workflow" button

---

## Verify Secrets are Working

### Check GitHub Actions Logs

1. Go to repo → Actions
2. Click latest workflow run
3. View build/test/deploy logs
4. Confirm secrets are masked (shown as `***`)

### Test API Endpoint

```bash
curl https://latex-tool-api.onrender.com/api/v1/health
# Expected: {"status": "ok"}
```

### Test Streamlit App

1. Navigate to https://latex-tool-app.onrender.com
2. Check that it loads
3. Verify it can reach API (via Settings tab)

---

## Troubleshooting

### Deployment Failed - Invalid API Key

**Solution:**
- Verify RENDER_API_KEY is correct in Render dashboard
- Check it hasn't expired
- Regenerate if needed

### GitHub Actions Won't Trigger

**Solution:**
- Verify `deploy-render.yml` is in `.github/workflows/`
- Check branch protection rules
- Manually trigger via "Run workflow" button

### Render Service Not Updating

**Solution:**
- Check Render dashboard for deployment status
- View build logs: Render → Service → Deployments
- Verify environment variables are set in Render UI

### LLM API Key Errors in Logs

**Solution:**
- Verify OPENAI_API_KEY and CLAUDE_API_KEY are set
- Confirm they're not expired
- Check rate limits on API provider dashboards

---

## Security Best Practices

### ✅ Do's

- ✅ Use GitHub Secrets for all sensitive values
- ✅ Rotate API keys every 90 days
- ✅ Use minimal permissions for access tokens
- ✅ Audit GitHub Actions logs regularly
- ✅ Use different keys for dev/staging/prod

### ❌ Don'ts

- ❌ Commit `.env` files to Git
- ❌ Share secrets in code or documentation
- ❌ Use same API key across multiple services
- ❌ Leave expired secrets in GitHub
- ❌ Commit `render.yaml` with hardcoded secrets

---

## Related Documentation

- [Render Deployment Guide](../docs/DEPLOYMENT.md)
- [CI/CD Workflows](../docs/ARCHITECTURE_COMPLETE.md#ci-cd)
- [Environment Configuration](.env.example)
- [Docker Compose](DOCKER_COMMANDS.md)
