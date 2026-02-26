"""DRF serializers for assessment domain objects."""

from rest_framework import serializers
from .models import Assessment, Problem, Submission, AssessmentInvitation


class ProblemSerializer(serializers.ModelSerializer):
    """Public problem metadata — excludes CouchDB test case references."""

    class Meta:
        model = Problem
        fields = (
            "id",
            "title",
            "prompt",
            "language",
            "difficulty",
            "max_score",
            "time_limit_ms",
            "memory_limit_mb",
            "display_order",
        )


class AssessmentSerializer(serializers.ModelSerializer):
    """Published assessment metadata for listing endpoints."""

    organization = serializers.CharField(source="organization.slug", read_only=True)
    problems = ProblemSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = (
            "id",
            "title",
            "description",
            "status",
            "duration_minutes",
            "organization",
            "problems",
            "created_at",
        )
        read_only_fields = fields


class SubmissionCreateSerializer(serializers.Serializer):
    """Payload for a new code submission."""

    source_code = serializers.CharField()


class SubmissionSerializer(serializers.ModelSerializer):
    """Submission status returned to the client."""

    class Meta:
        model = Submission
        fields = (
            "id",
            "problem",
            "status",
            "score",
            "submitted_at",
            "completed_at",
        )
        read_only_fields = fields


class AssessmentInvitationSerializer(serializers.ModelSerializer):
    """Serializer for creating and representing assessment invitations."""

    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    assessment_duration = serializers.IntegerField(source="assessment.duration_minutes", read_only=True)

    class Meta:
        model = AssessmentInvitation
        fields = (
            "id",
            "assessment",
            "assessment_title",
            "assessment_duration",
            "email",
            "token",
            "expires_at",
            "is_active",
            "instructions",
            "proctoring_required",
            "invitation_message",
            "status",
            "started_at",
            "completed_at",
        )
        read_only_fields = ("id", "token", "started_at", "completed_at")


class AssessmentInvitationDetailSerializer(serializers.ModelSerializer):
    """Detailed invitation info for candidates — includes full assessment context."""

    assessment = AssessmentSerializer(read_only=True)

    class Meta:
        model = AssessmentInvitation
        fields = (
            "id",
            "assessment",
            "email",
            "token",
            "expires_at",
            "is_active",
            "instructions",
            "proctoring_required",
            "invitation_message",
            "status",
            "started_at",
            "completed_at",
        )

# Refactor: Improve responsive styles and layouts.

# Refactor: Enhance component rendering performance.

# Refactor: Enhance component rendering performance.
