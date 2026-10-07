import requests

from app import fetch_user


def test_fetch_user(monkeypatch):
    class MockResponse:
        status_code = 200

        def json(self):
            return {"status": "active"}

    monkeypatch.setattr(requests, "get", lambda url: MockResponse())

    assert fetch_user(1) == {"status": "active"}
