from django.conf import settings
from django.db import models


class Event(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        FRIENDS = "friends", "Friends"
        PUBLIC = "public", "Public"

    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    # Empty capacity means "no limit"
    capacity = models.PositiveIntegerField(null=True, blank=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    # Cancelled events are kept, so invitees can still see what happened
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return self.title

    def is_host_or_cohost(self, user):
        if self.host == user:
            return True
        return self.invitations.filter(invitee=user, is_cohost=True).exists()


class Invitation(models.Model):
    """One row per invited user. It also stores their RSVP answer."""

    class RSVP(models.TextChoices):
        PENDING = "pending", "Pending"  # invited but has not answered yet
        GOING = "going", "Going"
        MAYBE = "maybe", "Maybe"
        DECLINED = "declined", "Declined"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="invitations")
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitations")
    rsvp = models.CharField(max_length=10, choices=RSVP.choices, default=RSVP.PENDING)
    # A co-host can edit and cancel the event, same as the host
    is_cohost = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "invitee"], name="unique_invite_per_event"),
        ]

    def __str__(self):
        return f"{self.invitee} -> {self.event} ({self.rsvp})"
