import os
import sys
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ajoute src/ au path pour les imports absolus depuis core/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core.utils.cv_pipeline import CV, IntegrationService  # noqa: E402
from .routes.offers import router  # noqa: E402

DATA_DIR = os.getenv("DATA_DIR", "./data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Chargement du pipeline CV...")
    cv = CV(data_dir=DATA_DIR)
    cv_base_fr, cv_base_en = cv.cv_base_in_all()
    app.state.integration_service = IntegrationService(
        cv_base_fr=cv_base_fr,
        cv_base_en=cv_base_en,
        n8n_webhook_url=os.getenv("N8N_WEBHOOK_URL", ""),
    )
    logger.info("Pipeline CV chargé — API prête.")
    yield


app = FastAPI(
    title="LaTeX Tool Generator API",
    version="0.1.0",
    description="Pipeline de génération de CV ATS-optimisés",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}
