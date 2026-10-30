import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass")


def login(client, password="pass"):
    return client.post("/api/auth/token/", {"username": "alice", "password": password}, format="json")


def test_login_returns_access_and_refresh_token(user):
    response = login(APIClient())

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


def test_wrong_password_is_rejected(user):
    response = login(APIClient(), password="wrong")

    assert response.status_code == 401


def test_api_needs_a_token(db):
    response = APIClient().get("/api/events/")

    assert response.status_code == 401


def test_bearer_token_gives_access(user):
    client = APIClient()
    access = login(client).data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = client.get("/api/events/")

    assert response.status_code == 200


def test_refresh_token_gives_new_access_token(user):
    client = APIClient()
    refresh = login(client).data["refresh"]

    response = client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")

    assert response.status_code == 200
    assert "access" in response.data
