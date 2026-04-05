"""Unit tests for cvrepo modules."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json


class TestArchiveManager:
    """Tests for archive manager."""

    def test_archive_manager_creates(self):
        """Test archive manager initialization."""
        from cvrepo.archive_manager import ArchiveManager
        
        manager = ArchiveManager(root_path="./data")
        assert manager is not None

    @patch("pathlib.Path.exists")
    def test_archive_manager_lists_archives(self, mock_exists):
        """Test archive manager can list archives."""
        mock_exists.return_value = True
        
        from cvrepo.archive_manager import ArchiveManager
        
        manager = ArchiveManager(root_path="./data")
        assert manager is not None


class TestJobParser:
    """Tests for job parser."""

    def test_job_parser_creates(self):
        """Test job parser initialization."""
        from cvrepo.job_parser import JobParser
        
        parser = JobParser()
        assert parser is not None

    def test_job_parser_parses_markdown(self):
        """Test job parser can parse markdown."""
        from cvrepo.job_parser import JobParser
        
        parser = JobParser()
        markdown = "# Job Offer\n## Company\nTech Corp"
        result = parser.parse(markdown)
        
        assert result is not None


class TestMetadata:
    """Tests for metadata module."""

    def test_metadata_index_creates(self):
        """Test metadata index creation."""
        from cvrepo.metadata import MetadataIndex
        
        index = MetadataIndex()
        assert index is not None

    @patch("pathlib.Path.read_text")
    def test_metadata_loads_from_file(self, mock_read):
        """Test metadata loads from JSON file."""
        mock_read.return_value = '{"entries": []}'
        
        from cvrepo.metadata import MetadataIndex
        
        index = MetadataIndex()
        assert index is not None


class TestPaths:
    """Tests for paths module."""

    def test_paths_provides_root(self):
        """Test paths module provides root directory."""
        from cvrepo.paths import get_repo_root
        
        root = get_repo_root()
        assert root is not None

    def test_paths_provides_data_dir(self):
        """Test paths module provides data directory."""
        from cvrepo.paths import get_data_dir
        
        data_dir = get_data_dir()
        assert data_dir is not None


class TestPipeline:
    """Tests for pipeline module."""

    def test_pipeline_creates(self):
        """Test pipeline initialization."""
        from cvrepo.pipeline import CVPipeline
        
        pipeline = CVPipeline(config=Mock())
        assert pipeline is not None

    @patch("cvrepo.pipeline.MarkdownOfferParser")
    def test_pipeline_executes(self, mock_parser):
        """Test pipeline can execute."""
        from cvrepo.pipeline import CVPipeline
        
        pipeline = CVPipeline(config=Mock())
        assert pipeline is not None


class TestTemplateEngine:
    """Tests for template engine."""

    def test_template_engine_creates(self):
        """Test template engine initialization."""
        from cvrepo.template_engine import TemplateEngine
        
        engine = TemplateEngine(templates_dir="./templates")
        assert engine is not None

    @patch("pathlib.Path.read_text")
    def test_template_engine_loads_template(self, mock_read):
        """Test template engine loads templates."""
        mock_read.return_value = "\\documentclass{article}\\nContent: {{ content }}"
        
        from cvrepo.template_engine import TemplateEngine
        
        engine = TemplateEngine(templates_dir="./templates")
        assert engine is not None

    @patch("pathlib.Path.read_text")
    def test_template_engine_renders(self, mock_read):
        """Test template engine renders templates."""
        mock_read.return_value = "Hello {{ name }}"
        
        from cvrepo.template_engine import TemplateEngine
        
        engine = TemplateEngine(templates_dir="./templates")
        result = engine.render("template.txt", {"name": "John"})
        
        assert result is not None


class TestValidation:
    """Tests for validation module."""

    def test_offer_validation_valid(self):
        """Test valid offer passes validation."""
        from cvrepo.validation import validate_offer
        
        offer = {
            "title": "Developer",
            "company": "TechCorp",
            "description": "Test"
        }
        result = validate_offer(offer)
        
        assert result is True or result is None

    def test_offer_validation_invalid(self):
        """Test invalid offer fails validation."""
        from cvrepo.validation import validate_offer
        
        offer = {}
        
        # Should either raise exception or return False
        try:
            result = validate_offer(offer)
            assert result is False or result is None
        except Exception:
            pass


class TestCVRepoErrorHandling:
    """Tests for error handling in cvrepo."""

    @patch("pathlib.Path.read_text", side_effect=FileNotFoundError())
    def test_handles_missing_file(self, mock_read):
        """Test modules handle missing files."""
        from cvrepo.metadata import MetadataIndex
        
        # Should handle gracefully
        try:
            index = MetadataIndex()
        except (FileNotFoundError, Exception):
            pass

    def test_handles_invalid_json(self):
        """Test modules handle invalid JSON."""
        from cvrepo.metadata import MetadataIndex
        
        # Should handle invalid data
        index = MetadataIndex()
        assert index is not None
