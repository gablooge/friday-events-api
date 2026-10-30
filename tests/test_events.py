import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Event, Invitation


@pytest.fixture
def host(db):
    return User.objects.create_user(username="host", password="pass")


@pytest.fixture
def guest(db):
    return User.objects.create_user(username="guest", password="pass")


@pytest.fixture
def event(host):
    return Event.objects.create(
        host=host,
        title="Friday drinks",
        start_time="2030-01-10T18:00:00Z",
        end_time="2030-01-10T21:00:00Z",
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_create_event(host):
    response = client_for(host).post(
        "/api/events/",
        {
            "title": "Board games",
            "start_time": "2030-01-10T18:00:00Z",
            "end_time": "2030-01-10T21:00:00Z",
            "visibility": "public",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["host"] == host.id
    assert response.data["capacity"] is None


def test_end_time_must_be_after_start_time(host):
    response = client_for(host).post(
        "/api/events/",
        {"title": "Oops", "start_time": "2030-01-10T18:00:00Z", "end_time": "2030-01-10T17:00:00Z"},
        format="json",
    )

    assert response.status_code == 400
    assert "end_time" in response.data


def test_host_invites_a_user(host, guest, event):
    response = client_for(host).post(f"/api/events/{event.id}/invite/", {"invitee": guest.id}, format="json")

    assert response.status_code == 201
    assert response.data["rsvp"] == "pending"


def test_cannot_invite_the_same_user_twice(host, guest, event):
    Invitation.objects.create(event=event, invitee=guest)

    response = client_for(host).post(f"/api/events/{event.id}/invite/", {"invitee": guest.id}, format="json")

    assert response.status_code == 400


@pytest.mark.parametrize("answer", ["going", "maybe", "declined"])
def test_invitee_can_rsvp(guest, event, answer):
    Invitation.objects.create(event=event, invitee=guest)

    response = client_for(guest).post(f"/api/events/{event.id}/rsvp/", {"rsvp": answer}, format="json")

    assert response.status_code == 200
    assert Invitation.objects.get(invitee=guest).rsvp == answer


def test_not_invited_user_cannot_rsvp(guest, event):
    # Public, so the guest can see it but is still not invited
    event.visibility = "public"
    event.save()

    response = client_for(guest).post(f"/api/events/{event.id}/rsvp/", {"rsvp": "going"}, format="json")

    assert response.status_code == 400


def test_cannot_rsvp_going_when_event_is_full(host, guest, event):
    event.capacity = 1
    event.save()
    first = User.objects.create_user(username="first", password="pass")
    Invitation.objects.create(event=event, invitee=first, rsvp="going")
    Invitation.objects.create(event=event, invitee=guest)

    response = client_for(guest).post(f"/api/events/{event.id}/rsvp/", {"rsvp": "going"}, format="json")

    assert response.status_code == 400
