"""Access-control tests for the admin section (Actividad 3, Opción B)."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.auth import hash_password

PASSWORD = "secret123"


ADMIN = {
    "id": 1,
    "username": "admin@rentek.com",
    "email": "admin@rentek.com",
    "display_name": "Admin Rentek",
    "role": "admin",
}

CLIENTE = {
    "id": 2,
    "username": "cliente@rentek.com",
    "email": "cliente@rentek.com",
    "display_name": "Cliente",
    "role": "cliente",
}


class FakeCursor:
    def __init__(self, users):
        self.users = users
        self._rows = []
        self._row = None
        self.last_query = ""
        self.last_params = None

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params
        if "FROM users" in query and "ORDER BY" in query:
            self._rows = [
                (
                    u["id"],
                    u["username"],
                    u["email"],
                    u["display_name"],
                    u["role"],
                    u["blocked"],
                    u["blocked_at"],
                    u["created_at"],
                    u["last_login"],
                )
                for u in self.users
            ]
        elif "password_hash" in query:
            identifier = params[0]
            target = next(
                (
                    u
                    for u in self.users
                    if u["email"] == identifier or u["username"] == identifier
                ),
                None,
            )
            self._row = (
                (
                    target["id"],
                    target["password_hash"],
                    target["display_name"],
                    target["role"],
                    target["username"],
                    target["email"],
                    target["blocked"],
                )
                if target
                else None
            )
        elif "SELECT blocked FROM users WHERE id" in query:
            target = next((u for u in self.users if u["id"] == params[0]), None)
            self._row = (target["blocked"],) if target else None
        elif "display_name" in query and "FROM users WHERE id" in query:
            target = next((u for u in self.users if u["id"] == params[0]), None)
            self._row = (
                (
                    target["id"],
                    target["username"],
                    target["email"],
                    target["display_name"],
                    target["role"],
                    target["blocked"],
                )
                if target
                else None
            )
        elif "FROM users WHERE id" in query:
            target = next((u for u in self.users if u["id"] == params[0]), None)
            self._row = (
                (target["id"], target["username"], target["role"], target["blocked"])
                if target
                else None
            )
        elif query.strip().startswith("UPDATE users"):
            target = next((u for u in self.users if u["id"] == params[0]), None)
            if target and "blocked = TRUE" in query:
                target["blocked"] = True
            elif target and "blocked = FALSE" in query:
                target["blocked"] = False

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._row

    def close(self):
        pass


class FakeConnection:
    def __init__(self, users):
        self.cursor_obj = FakeCursor(users)

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def close(self):
        pass


def _user(uid, role, username):
    return {
        "id": uid,
        "username": username,
        "email": username,
        "password_hash": hash_password(PASSWORD),
        "display_name": username,
        "role": role,
        "blocked": False,
        "blocked_at": None,
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
        "last_login": None,
    }


@pytest.fixture()
def users():
    return [
        _user(1, "admin", "admin@rentek.com"),
        _user(2, "cliente", "cliente@rentek.com"),
        _user(3, "admin", "otro-admin@rentek.com"),
    ]


@pytest.fixture()
def client(api_module, monkeypatch, users):
    fake_conn = FakeConnection(users)
    monkeypatch.setattr(api_module.database, "get_conn", lambda: fake_conn)
    return TestClient(api_module.app)


def _login_as(api_module, monkeypatch, user):
    monkeypatch.setattr(api_module, "get_current_user_details", lambda request: user)


def test_admin_users_requires_authentication(api_module, monkeypatch, client):
    _login_as(api_module, monkeypatch, None)

    response = client.get("/api/admin/users")

    assert response.status_code == 401


def test_admin_users_rejects_cliente_role(api_module, monkeypatch, client):
    _login_as(api_module, monkeypatch, CLIENTE)

    response = client.get("/api/admin/users")

    assert response.status_code == 403


def test_admin_users_returns_users_without_password_hash(
    api_module, monkeypatch, client
):
    _login_as(api_module, monkeypatch, ADMIN)

    response = client.get("/api/admin/users")

    assert response.status_code == 200
    body = response.json()
    assert len(body["users"]) == 3
    assert body["users"][0]["email"] == "admin@rentek.com"
    assert all("password_hash" not in user for user in body["users"])


def test_admin_cannot_block_own_account(api_module, monkeypatch, client):
    _login_as(api_module, monkeypatch, ADMIN)

    response = client.post("/api/admin/users/1/block")

    assert response.status_code == 400


def test_admin_cannot_block_another_admin(api_module, monkeypatch, client):
    _login_as(api_module, monkeypatch, ADMIN)

    response = client.post("/api/admin/users/3/block")

    assert response.status_code == 400


def test_admin_can_block_cliente(api_module, monkeypatch, client, users):
    _login_as(api_module, monkeypatch, ADMIN)

    response = client.post("/api/admin/users/2/block")

    assert response.status_code == 200
    assert users[1]["blocked"] is True


def test_blocking_unknown_user_returns_404(api_module, monkeypatch, client):
    _login_as(api_module, monkeypatch, ADMIN)

    response = client.post("/api/admin/users/99/block")

    assert response.status_code == 404


def test_blocked_user_cannot_use_token(api_module, client, users):
    users[1]["blocked"] = True
    token = api_module.create_token(2, "cliente@rentek.com")

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_blocked_user_cannot_read_chats(api_module, client, users):
    users[1]["blocked"] = True
    token = api_module.create_token(2, "cliente@rentek.com")

    response = client.get(
        "/api/chats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_blocked_user_cannot_login(api_module, client, users):
    users[1]["blocked"] = True

    response = client.post(
        "/api/auth/login",
        json={"email": "cliente@rentek.com", "password": PASSWORD},
    )

    assert response.status_code == 403


def test_default_admin_is_not_seeded_unless_enabled(api_module, monkeypatch):
    monkeypatch.delenv("SEED_DEFAULT_ADMIN", raising=False)
    calls = []

    def fake_get_conn():
        calls.append(True)
        return None

    monkeypatch.setattr(api_module.database, "get_conn", fake_get_conn)

    api_module.seed_default_admin()

    assert calls == []

