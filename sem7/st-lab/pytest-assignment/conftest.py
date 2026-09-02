"""Shared fixtures and CLI options for the pytest assignment."""

import pytest

from app import connect_database


# --- Task 3: custom CLI flag --------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="target environment for the test run (e.g. dev, staging, prod)",
    )


@pytest.fixture
def env(request):
    """Expose the value passed to --env."""
    return request.config.getoption("--env")


# --- Task 2: module-scoped fixture with teardown ----------------------------
@pytest.fixture(scope="module")
def db_conn():
    conn = connect_database()
    yield conn
    conn.close()
