from rest_framework import serializers

from .models import Event, Invitation


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "host",
            "title",
            "description",
            "start_time",
            "end_time",
            "location",
            "capacity",
            "visibility",
            "is_cancelled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["host", "is_cancelled", "created_at", "updated_at"]

    def validate(self, attrs):
        # On PATCH one of the times may be missing, so use the saved value
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if end_time <= start_time:
            raise serializers.ValidationError({"end_time": ["End time must be after start time."]})
        return attrs


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ["id", "event", "invitee", "is_cohost", "rsvp", "created_at"]
        read_only_fields = ["event", "rsvp", "created_at"]


class RSVPSerializer(serializers.Serializer):
    # "pending" is only the starting state, users cannot answer with it
    rsvp = serializers.ChoiceField(choices=[Invitation.RSVP.GOING, Invitation.RSVP.MAYBE, Invitation.RSVP.DECLINED])


class EventErrorSerializer(serializers.Serializer):
    """Shape of a 400 error for create/update event. Only used for the API docs.

    DRF returns {"field_name": ["message", ...]}, and only for fields that failed.
    """

    title = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.ListField(child=serializers.CharField(), required=False)
    start_time = serializers.ListField(child=serializers.CharField(), required=False)
    end_time = serializers.ListField(child=serializers.CharField(), required=False)
    location = serializers.ListField(child=serializers.CharField(), required=False)
    capacity = serializers.ListField(child=serializers.CharField(), required=False)
    visibility = serializers.ListField(child=serializers.CharField(), required=False)
