# Test README

## Running Tests

### Install test dependencies
```bash
pip install -r requirements-test.txt
```

Or with `uv`:
```bash
uv pip install -r requirements-test.txt
```

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/src_test/app/test_api.py
```

### Run specific test class
```bash
pytest tests/src_test/app/test_api.py::TestAPIInitialization
```

### Run specific test function
```bash
pytest tests/src_test/app/test_api.py::TestAPIInitialization::test_api_app_exists
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

This generates coverage report in `htmlcov/index.html`

### Run only marked tests
```bash
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests
pytest -m api           # Only API tests
pytest -m streamlit     # Only Streamlit tests
pytest -m orchestration # Only orchestration tests
pytest -m channels     # Only channel tests
```

### Run tests with specific Python version (using tox)
```bash
pip install tox
tox
```

## Test Structure

The test suite mirrors the `src/` directory structure:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration
└── src_test/
    ├── app/
    │   ├── models/
    │   │   ├── test_offer.py
    │   │   └── test_generation.py
    │   ├── routes/
    │   │   ├── test_offers.py
    │   │   ├── test_matching.py
    │   │   └── test_generate.py
    │   └── streamlit/
    │       ├── components/
    │       │   └── test_widgets.py
    │       ├── domain/
    │       │   └── test_tab_service.py
    │       ├── pages/
    │       │   ├── test_base_page.py
    │       │   └── test_pages.py
    │       ├── services/
    │       │   └── test_api_client.py
    │       ├── test_app.py
    │       └── test_utils_functions.py
    ├── channels/
    │   └── test_channels.py
    ├── orchestration/
    │   └── test_orchestration.py
    └── cvrepo/
        └── test_cvrepo.py
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Test Coverage Goals

- Unit tests: >= 80% coverage
- Integration tests: >= 60% coverage
- Overall: >= 75% coverage

Current coverage can be viewed in `htmlcov/index.html` after running:
```bash
pytest --cov=src --cov-report=html
```

## Troubleshooting

### Import errors
Ensure `PYTHONPATH` includes `src/`:
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
pytest
```

### Streamlit tests failing
Some Streamlit tests may require mocking. Check `conftest.py` for `mock_streamlit_session` fixture.

### Database tests
Database tests use mocks by default. For integration tests against real SQLite:
```bash
pytest -m integration
```

## Test Markers

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests with external services
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.streamlit` - Streamlit UI tests
- `@pytest.mark.orchestration` - Orchestration logic tests
- `@pytest.mark.channels` - Output channel tests
- `@pytest.mark.cvrepo` - CVRepo module tests
