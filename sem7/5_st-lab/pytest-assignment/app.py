import requests

API_BASE = "https://api.example.com"


def safe_divide(a, b):
    return a / b


class DatabaseConnection:
    def __init__(self):
        self.closed = False
        self._rows = {1: {"id": 1, "name": "Ada"}}

    def get(self, row_id):
        return self._rows.get(row_id)

    def close(self):
        self.closed = True


def connect_database():
    return DatabaseConnection()


def fetch_user(user_id):
    response = requests.get(f"{API_BASE}/users/{user_id}")
    return response.json()
