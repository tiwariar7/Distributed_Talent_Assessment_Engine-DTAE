from rest_framework import serializers
from .models import ProctoringSession, ProctoringViolation, ProctoringLog


class ProctoringViolationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringViolation
        fields = (
            "id",
            "session",
            "violation_type",
            "severity",
            "timestamp",
            "metadata",
            "warning_shown",
            "auto_submitted",
        )
        read_only_fields = ("id", "timestamp")


class ProctoringSessionSerializer(serializers.ModelSerializer):
    violations = ProctoringViolationSerializer(many=True, read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    assessment_title = serializers.CharField(source="invitation.assessment.title", read_only=True)

    class Meta:
        model = ProctoringSession
        fields = (
            "id",
            "invitation",
            "candidate",
            "candidate_email",
            "assessment_title",
            "started_at",
            "ended_at",
            "violation_count",
            "warning_count",
            "is_camera_active",
            "is_mic_active",
            "status",
            "metadata",
            "violations",
        )
        read_only_fields = ("id", "started_at", "violation_count", "warning_count")


class ProctoringLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringLog
        fields = (
            "id",
            "session",
            "submission",
            "event_type",
            "timestamp",
            "metadata",
        )
        read_only_fields = ("id", "timestamp")

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve responsive styles and layouts.

# Refactor: Align with project code quality guidelines.

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve error handling and exception logging.

# Refactor: Enhance component rendering performance.
