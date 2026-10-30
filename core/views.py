from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Event, Invitation
from .serializers import EventSerializer, InvitationSerializer, RSVPSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def perform_create(self, serializer):
        # The logged-in user is always the host
        serializer.save(host=self.request.user)

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

        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
