# Pytest Assignment

Four pytest exercises: parametrization + exceptions, a module-scoped fixture
with teardown, a custom `--env` CLI flag, and monkeypatching an external API.

## Setup

```bash
python3.14 -m venv env
./env/bin/pip install pytest requests
```

## Run

```bash
./env/bin/pytest                 # default: --env=dev
./env/bin/pytest --env=staging   # Task 3: run against staging
```

## Layout

| File | Task |
| --- | --- |
| `app.py` | code under test: `safe_divide`, `connect_database`, `fetch_user` |
| `conftest.py` | Task 2 `db_conn` fixture, Task 3 `pytest_addoption` + `env` fixture |
| `tests/test_safe_divide.py` | Task 1: `@pytest.mark.parametrize` + `pytest.raises(ZeroDivisionError)` |
| `tests/test_db_conn.py` | Task 2: `@pytest.fixture(scope="module")` yielding a mock connection |
| `tests/test_env_option.py` | Task 3: reads `request.config.getoption("--env")` |
| `tests/test_fetch_user.py` | Task 4: `monkeypatch.setattr(requests, "get", ...)` |
