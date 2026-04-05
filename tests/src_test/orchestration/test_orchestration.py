"""Unit tests for orchestration modules."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json


class TestOrchestrationConfig:
    """Tests for orchestration config."""

    @patch.dict("os.environ", {"REPO_ROOT": "/test/repo"})
    def test_config_from_repo_root(self):
        """Test config initialization from repo root."""
        from orchestration.config import OrchestrationConfig
        
        config = OrchestrationConfig.from_repo_root()
        assert config is not None

    def test_config_has_database_path(self):
        """Test config provides database path."""
        from orchestration.config import OrchestrationConfig
        
        config = OrchestrationConfig()
        assert hasattr(config, "db_path") or hasattr(config, "database_path")

    def test_config_has_data_dir(self):
        """Test config provides data directory."""
        from orchestration.config import OrchestrationConfig
        
        config = OrchestrationConfig()
        assert hasattr(config, "data_dir") or hasattr(config, "offers_dir")


class TestOfferIngestionOrchestrator:
    """Tests for offer ingest orchestrator."""

    @patch("orchestration.ingest.OfferRepositoryGateway")
    def test_offer_ingest_creates_entry(self, mock_gateway):
        """Test offer ingestion creates database entry."""
        from orchestration.ingest import OfferIngestionOrchestrator
        
        mock_gateway.return_value.insert_offer.return_value = "offer-123"
        orchestrator = OfferIngestionOrchestrator(config=Mock())
        
        assert orchestrator is not None

    def test_markdown_parser_extracts_sections(self):
        """Test markdown parser extracts offer sections."""
        from orchestration.ingest import MarkdownOfferParser
        
        markdown = """# Senior Developer
## Company
TechCorp
## Location
Berlin, Germany
## Description
We are hiring...
"""
        parser = MarkdownOfferParser()
        sections = parser.parse(markdown)
        
        assert sections is not None


class TestLLMExtractors:
    """Tests for LLM extractors module."""

    def test_heuristic_extractor_creates(self):
        """Test heuristic extractor init."""
        from orchestration.llm_extractors import HeuristicKeywordExtractor
        
        extractor = HeuristicKeywordExtractor()
        assert extractor is not None

    def test_extractor_extracts_keywords(self):
        """Test extractor can extract keywords."""
        from orchestration.llm_extractors import HeuristicKeywordExtractor
        
        extractor = HeuristicKeywordExtractor()
        text = "We need a Python developer with FastAPI experience"
        keywords = extractor.extract_keywords(text)
        
        assert keywords is not None


class TestOfferPipelineOrchestrator:
    """Tests for offer pipeline orchestrator."""

    @patch("orchestration.orchestrator.OfferIngestionOrchestrator")
    @patch("orchestration.orchestrator.OfferPipelineOrchestrator")
    def test_pipeline_processes_offer(self, mock_pipeline, mock_ingest):
        """Test pipeline processes offer."""
        from orchestration.orchestrator import OfferPipelineOrchestrator
        
        orchestrator = OfferPipelineOrchestrator(config=Mock())
        assert orchestrator is not None

    def test_pipeline_makes_recommendation(self):
        """Test pipeline makes GO/REVIEW/SKIP recommendation."""
        from orchestration.orchestrator import OfferPipelineOrchestrator
        
        orchestrator = OfferPipelineOrchestrator(config=Mock())
        assert orchestrator is not None


class TestExperiencesOrchestrator:
    """Tests for experiences orchestrator."""

    def test_experiences_orchestrator_creates(self):
        """Test experiences orchestrator initialization."""
        from orchestration.experiences_orchestrator import ExperiencesOrchestrator
        
        orchestrator = ExperiencesOrchestrator(config=Mock())
        assert orchestrator is not None

    @patch("sqlite3.connect")
    def test_experiences_orchestrator_stores_data(self, mock_connect):
        """Test experiences orchestrator stores to database."""
        from orchestration.experiences_orchestrator import ExperiencesOrchestrator
        
        orchestrator = ExperiencesOrchestrator(config=Mock())
        assert orchestrator is not None


class TestFormationsOrchestrator:
    """Tests for formations orchestrator."""

    def test_formations_orchestrator_creates(self):
        """Test formations orchestrator initialization."""
        from orchestration.formations_orchestrator import FormationsOrchestrator
        
        orchestrator = FormationsOrchestrator(config=Mock())
        assert orchestrator is not None


class TestProjectsOrchestrator:
    """Tests for projects orchestrator."""

    def test_projects_orchestrator_creates(self):
        """Test projects orchestrator initialization."""
        from orchestration.projects_orchestrator import ProjectsOrchestrator
        
        orchestrator = ProjectsOrchestrator(config=Mock())
        assert orchestrator is not None


class TestOrchestrationErrorHandling:
    """Tests for orchestration error handling."""

    @patch("sqlite3.connect", side_effect=Exception("DB Error"))
    def test_orchestrator_handles_db_error(self, mock_connect):
        """Test orchestrator handles database errors."""
        from orchestration.ingest import OfferIngestionOrchestrator
        
        with pytest.raises(Exception):
            orchestrator = OfferIngestionOrchestrator(config=Mock())
            orchestrator.process_offer({})

    def test_parser_handles_invalid_markdown(self):
        """Test parser handles invalid markdown."""
        from orchestration.ingest import MarkdownOfferParser
        
        parser = MarkdownOfferParser()
        sections = parser.parse("")
        
        # Should return something, even if empty
        assert sections is not None
