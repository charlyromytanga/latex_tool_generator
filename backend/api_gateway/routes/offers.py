from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict

from ..auth import require_api_key

router = APIRouter(prefix="/api/v1", tags=["offers"])


class OfferInputRequest(BaseModel):
    offer_text: str


class OfferUpgradeRequest(BaseModel):
    structured_offer: Dict[str, Any]
    offer_text: str


class ScoreRequest(BaseModel):
    full_offer: Dict[str, Any]


@router.post("/offer_input", summary="Extraction et structuration d'une offre texte")
def offer_input(body: OfferInputRequest, request: Request, _: str = Depends(require_api_key)):
    """
    Reçoit une offre texte brut.
    Retourne l'offre structurée (première moitié de job_offer) + le texte original.
    """
    svc = request.app.state.integration_service
    result = svc.extract_and_structure_offer(body.offer_text)
    if not result:
        raise HTTPException(status_code=500, detail="Échec extraction offre")
    return result


@router.post("/offer_upgrade_by_llm", summary="Enrichissement LLM de l'offre avec cv_base")
def offer_upgrade_by_llm(body: OfferUpgradeRequest, request: Request, _: str = Depends(require_api_key)):
    """
    Reçoit l'offre structurée + le texte de l'offre.
    Enrichit avec les sections LLM croisées avec cv_base_in_all et sauvegarde en base.
    Retourne l'offre job complète avec toutes les sections.
    """
    svc = request.app.state.integration_service
    result = svc.enrich_offer_with_cv(body.structured_offer, body.offer_text)
    if not result:
        raise HTTPException(status_code=500, detail="Échec enrichissement offre")
    return result


@router.post("/score_and_cv_lm_generated_or_not", summary="Scoring ATS + génération CV/LM si score ≥ 70 %")
def score_and_cv_lm(body: ScoreRequest, request: Request, _: str = Depends(require_api_key)):
    """
    Reçoit l'offre enrichie complète.
    Calcule le score ATS. Si score >= 0.70 : génère CV et LM en texte et sauvegarde dans candidature_tracking.
    Retourne le score, les détails et les documents générés (ou null si score insuffisant).
    """
    svc = request.app.state.integration_service
    result = svc.score_and_generate(body.full_offer)
    if not result:
        raise HTTPException(status_code=500, detail="Échec scoring")
    return result
