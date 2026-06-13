"""Orchestration package for ingestion, matching and generation workflows."""

from .experiences_orchestrator import ExperiencesBootstrapOrchestrator
from .jobs_ingestor import JobsIngestionOrchestrator
from .llm_extractors import OfferLLMOrchestrator
from .orchestrator import OfferPipelineOrchestrator
from .projects_orchestrator import ProjectBootstrapOrchestrator

# Alias pour compatibilité arrière
OfferIngestionOrchestrator = JobsIngestionOrchestrator

__all__ = [
    "ProjectBootstrapOrchestrator",
    "ExperiencesBootstrapOrchestrator",
    "JobsIngestionOrchestrator",
    "OfferIngestionOrchestrator",  # Alias de compatibilité
    "OfferLLMOrchestrator",
    "OfferPipelineOrchestrator",
]
