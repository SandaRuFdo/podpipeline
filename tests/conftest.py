# tests/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end (playwright)")
    config.addinivalue_line("markers", "api: marks tests as API tests (requests)")
