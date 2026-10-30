import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Event, Invitation


@pytest.fixture
def host(db):
    return User.objects.create_user(username="host", password="pass")


@pytest.fixture
def stranger(db):
    return User.objects.create_user(username="stranger", password="pass")


@pytest.fixture
def guest(db):
    return User.objects.create_user(username="guest", password="pass")


@pytest.fixture
def private_event(host):
    return Event.objects.create(
        host=host,
        title="Secret party",
        start_time="2030-01-10T18:00:00Z",
        end_time="2030-01-10T21:00:00Z",
        visibility="private",
    )


@pytest.fixture
def public_event(host):
    return Event.objects.create(
        host=host,
        title="Open picnic",
        start_time="2030-01-10T18:00:00Z",
        end_time="2030-01-10T21:00:00Z",
        visibility="public",
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# --- Only participants can see a private event ---


def test_non_participant_cannot_read_private_event(stranger, private_event):
    client = client_for(stranger)

    response = client.get(f"/api/events/{private_event.id}/")
    missing = client.get("/api/events/999999/")

    # Same answer as an event that does not exist, so the stranger
    # cannot tell the private event is there
    assert response.status_code == 404
    assert response.data == missing.data
    assert "Secret party" not in response.content.decode()


def test_private_event_is_not_in_the_list(stranger, private_event):
    response = client_for(stranger).get("/api/events/")

    assert response.status_code == 200
    assert response.data == []


def test_host_can_read_private_event(host, private_event):
    response = client_for(host).get(f"/api/events/{private_event.id}/")

    assert response.status_code == 200


def test_invitee_can_read_private_event(guest, private_event):
    Invitation.objects.create(event=private_event, invitee=guest)

    response = client_for(guest).get(f"/api/events/{private_event.id}/")

    assert response.status_code == 200


def test_anyone_logged_in_can_read_public_event(stranger, public_event):
    response = client_for(stranger).get(f"/api/events/{public_event.id}/")

    assert response.status_code == 200


# --- Only the host or a co-host can edit or cancel ---


def test_host_can_edit(host, public_event):
    response = client_for(host).patch(f"/api/events/{public_event.id}/", {"title": "New title"}, format="json")

    assert response.status_code == 200
    assert response.data["title"] == "New title"


def test_cohost_can_edit_and_cancel(guest, private_event):
    Invitation.objects.create(event=private_event, invitee=guest, is_cohost=True)
    client = client_for(guest)

    edit = client.patch(f"/api/events/{private_event.id}/", {"location": "Rooftop"}, format="json")
    cancel = client.post(f"/api/events/{private_event.id}/cancel/")

    assert edit.status_code == 200
    assert cancel.status_code == 200
    assert cancel.data["is_cancelled"] is True


def test_invitee_cannot_edit_or_cancel(guest, private_event):
    Invitation.objects.create(event=private_event, invitee=guest)
    client = client_for(guest)

    edit = client.patch(f"/api/events/{private_event.id}/", {"title": "Mine now"}, format="json")
    cancel = client.post(f"/api/events/{private_event.id}/cancel/")

    # They can see the event already, so 403 does not leak anything
    assert edit.status_code == 403
    assert cancel.status_code == 403


def test_stranger_cannot_edit_public_event(stranger, public_event):
    response = client_for(stranger).patch(f"/api/events/{public_event.id}/", {"title": "Hacked"}, format="json")

    assert response.status_code == 403


def test_stranger_cannot_edit_or_cancel_private_event(stranger, private_event):
    client = client_for(stranger)

    edit = client.patch(f"/api/events/{private_event.id}/", {"title": "Hacked"}, format="json")
    cancel = client.post(f"/api/events/{private_event.id}/cancel/")

    assert edit.status_code == 404
    assert cancel.status_code == 404
    private_event.refresh_from_db()
    assert private_event.title == "Secret party"
    assert private_event.is_cancelled is False


def test_only_host_can_add_a_cohost(guest, stranger, private_event):
    Invitation.objects.create(event=private_event, invitee=guest, is_cohost=True)

    response = client_for(guest).post(
        f"/api/events/{private_event.id}/invite/", {"invitee": stranger.id, "is_cohost": True}, format="json"
    )

    assert response.status_code == 403
