from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Event, Invitation
from .permissions import IsHostOrCoHost
from .serializers import EventErrorSerializer, EventSerializer, InvitationSerializer, RSVPSerializer


@extend_schema_view(
    create=extend_schema(
        request=EventSerializer,
        responses={201: EventSerializer, 400: EventErrorSerializer},
    ),
    update=extend_schema(responses={200: EventSerializer, 400: EventErrorSerializer}),
    partial_update=extend_schema(responses={200: EventSerializer, 400: EventErrorSerializer}),
)
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsHostOrCoHost]
    # No DELETE: events are cancelled with POST /events/{id}/cancel/ instead
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        # drf-spectacular calls this without a logged-in user while building the schema
        if getattr(self, "swagger_fake_view", False):
            return Event.objects.none()

        # Public events, plus events you host or are invited to.
        # "friends" is treated like "private" until we have a friends list.
        # Events left out here give a 404 on every endpoint, the same as an id
        # that does not exist, so non-participants cannot tell they exist.
        user = self.request.user
        return Event.objects.filter(
            Q(visibility=Event.Visibility.PUBLIC) | Q(host=user) | Q(invitations__invitee=user)
        ).distinct()

    def perform_create(self, serializer):
        # The logged-in user is always the host
        serializer.save(host=self.request.user)

    @extend_schema(request=None, responses={200: EventSerializer})
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        event = self.get_object()
        event.is_cancelled = True
        event.save()
        return Response(EventSerializer(event).data)

    @extend_schema(request=InvitationSerializer, responses={201: InvitationSerializer})
    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        event = self.get_object()
        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitee = serializer.validated_data["invitee"]
        if invitee == event.host:
            return Response({"invitee": ["The host cannot be invited."]}, status=status.HTTP_400_BAD_REQUEST)
        if event.invitations.filter(invitee=invitee).exists():
            return Response({"invitee": ["This user is already invited."]}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data.get("is_cohost") and event.host != request.user:
            return Response({"detail": "Only the host can add a co-host."}, status=status.HTTP_403_FORBIDDEN)

        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=RSVPSerializer, responses={200: InvitationSerializer})
    @action(detail=True, methods=["post"])
    def rsvp(self, request, pk=None):
        event = self.get_object()
        serializer = RSVPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answer = serializer.validated_data["rsvp"]

        invitation = event.invitations.filter(invitee=request.user).first()
        if invitation is None:
            return Response({"detail": "You are not invited to this event."}, status=status.HTTP_400_BAD_REQUEST)

        if answer == Invitation.RSVP.GOING and event.capacity is not None:
            going = event.invitations.filter(rsvp=Invitation.RSVP.GOING).exclude(id=invitation.id).count()
            if going >= event.capacity:
                return Response({"detail": "This event is full."}, status=status.HTTP_400_BAD_REQUEST)

        invitation.rsvp = answer
        invitation.save()
        return Response(InvitationSerializer(invitation).data)
