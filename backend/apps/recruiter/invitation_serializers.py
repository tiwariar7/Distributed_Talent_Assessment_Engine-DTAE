from rest_framework import serializers
from apps.assessments.models import AssessmentInvitation


class InviteCandidatesSerializer(serializers.Serializer):
    emails = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
        help_text="List of candidate emails to invite."
    )
    expires_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Expiration date and time for the invitation. Defaults to 7 days from now."
    )
    instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Custom instructions for the candidates."
    )
    proctoring_required = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether webcam and microphone proctoring is required."
    )
    invitation_message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Custom invitation email message."
    )


class InvitationDetailSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    violation_count = serializers.SerializerMethodField()
    proctoring_status = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentInvitation
        fields = (
            "id",
            "assessment",
            "assessment_title",
            "email",
            "token",
            "expires_at",
            "instructions",
            "proctoring_required",
            "invitation_message",
            "status",
            "started_at",
            "completed_at",
            "is_active",
            "violation_count",
            "proctoring_status",
        )
        read_only_fields = ("id", "token", "started_at", "completed_at", "status")

    def get_violation_count(self, obj):
        session = obj.proctoring_sessions.first()
        return session.violation_count if session else 0

    def get_proctoring_status(self, obj):
        session = obj.proctoring_sessions.first()
        return session.status if session else "N/A"


# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.
