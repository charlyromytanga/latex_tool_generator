"""Pytest configuration and shared fixtures for all tests."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_api_client():
    """Provide a mock API client for testing."""
    client = Mock()
    client.health_check.return_value = True
    client.create_offer.return_value = {"offer_id": "test-offer-123"}
    client.get_offer.return_value = {
        "offer_id": "test-offer-123",
        "title": "Test Offer",
        "company": "Test Company",
        "description": "Test description",
        "keywords": ["test"],
        "created_at": "2025-04-05T00:00:00Z"
    }
    client.get_matching.return_value = {
        "offer_id": "test-offer-123",
        "overall_confidence": 0.5,
        "experience_matches": [],
        "project_matches": [],
        "formation_matches": []
    }
    client.generate_cv_letter.return_value = {"generation_id": "test-gen-123"}
    client.get_generation_status.return_value = {
        "generation_id": "test-gen-123",
        "status": "completed"
    }
    return client


@pytest.fixture
def mock_streamlit_session():
    """Provide mock streamlit session state."""
    session = MagicMock()
    session.offer_id = None
    session.generation_id = None
    session.theme = "light"
    session.language = "en"
    session.threshold = 0.5
    return session


@pytest.fixture
def mock_database_connection():
    """Provide mock database connection."""
    conn = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.execute.return_value = cursor
    conn.cursor.return_value = cursor
    conn.commit.return_value = None
    conn.close.return_value = None
    return conn


@pytest.fixture
def sample_markdown_offer():
    """Provide sample markdown offer for testing."""
    return """# Senior Python Developer

## Company
TechCorp International

## Location
Berlin, Germany (Remote possible)

## Salary
€70,000 - €90,000/year

## Description
We are looking for an experienced Python developer to join our growing platform team.

## Requirements
- 5+ years Python experience
- FastAPI or Django knowledge
- PostgreSQL expertise
- Docker proficiency
- CI/CD pipeline understanding

## Nice to have
- Kubernetes experience
- Microservices architecture knowledge
- Cloud platform experience (AWS/GCP/Azure)

## Contract
Full-time, permanent position
"""


@pytest.fixture
def sample_offer_data():
    """Provide sample offer data structure."""
    return {
        "offer_id": "offer-123",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "description": "We are looking for...",
        "keywords": ["python", "fastapi", "docker", "postgresql"],
        "location": "Berlin",
        "salary_range": "70k-90k",
        "contract_type": "Permanent",
        "created_at": "2025-04-05T10:00:00Z",
        "source_url": "https://example.com/offers/123"
    }


@pytest.fixture
def sample_matching_result():
    """Provide sample matching result."""
    return {
        "offer_id": "offer-123",
        "overall_confidence": 0.82,
        "experience_matches": [
            {
                "entity_id": "exp-1",
                "match_score": 0.95,
                "entity_type": "experience",
                "title": "Backend Developer at Company A"
            },
            {
                "entity_id": "exp-2",
                "match_score": 0.78,
                "entity_type": "experience",
                "title": "Python Developer at Company B"
            }
        ],
        "project_matches": [
            {
                "entity_id": "proj-1",
                "match_score": 0.85,
                "entity_type": "project",
                "title": "E-commerce Platform"
            }
        ],
        "formation_matches": [
            {
                "entity_id": "form-1",
                "match_score": 0.90,
                "entity_type": "formation",
                "title": "Computer Science Degree"
            }
        ]
    }


@pytest.fixture
def sample_generation_output():
    """Provide sample generation output."""
    return {
        "generation_id": "gen-123",
        "offer_id": "offer-123",
        "status": "completed",
        "cv_content": "# Curriculum Vitae\n\n## Personal Information\n...",
        "letter_content": "# Cover Letter\n\nDear Hiring Manager,\n...",
        "cv_pdf_url": "/artifacts/gen-123/cv.pdf",
        "letter_pdf_url": "/artifacts/gen-123/letter.pdf",
        "created_at": "2025-04-05T10:00:00Z",
        "completed_at": "2025-04-05T10:05:00Z"
    }


@pytest.fixture(autouse=True)
def reset_imports():
    """Reset imports before each test to avoid cross-test pollution."""
    yield


# Markers for test categorization
def pytest_configure(config):
    """Register pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "streamlit: Streamlit tests")
    config.addinivalue_line("markers", "orchestration: Orchestration tests")
    config.addinivalue_line("markers", "channels: Channel tests")
    config.addinivalue_line("markers", "cvrepo: CVRepo tests")
