from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsHostOrCoHost(BasePermission):
    """Reading is fine for anyone who can see the event. Changing it needs the host or a co-host.

    Who can see an event is decided in EventViewSet.get_queryset(). Users who
    cannot see it get a 404 before this check runs.
    """

    message = "Only the host or a co-host can change this event."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Answering your own invitation is not changing the event
        if view.action == "rsvp":
            return True
        return obj.is_host_or_cohost(request.user)
