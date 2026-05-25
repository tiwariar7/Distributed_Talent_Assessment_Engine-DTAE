"""DRF serializers for assessment domain objects."""

from rest_framework import serializers
from .models import Assessment, Problem, Submission, AssessmentInvitation, MCQOption, SubmissionDraft


class MCQOptionSerializer(serializers.ModelSerializer):
    """Option for MCQ problem, excluding the is_correct field for candidates."""

    class Meta:
        model = MCQOption
        fields = ("id", "option_text", "display_order")


class ProblemSerializer(serializers.ModelSerializer):
    """Public problem metadata — excludes CouchDB test case references, includes sample test cases & MCQ options."""

    mcq_options = MCQOptionSerializer(many=True, read_only=True)
    is_multiple_choice = serializers.SerializerMethodField()
    sample_test_cases = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = (
            "id",
            "title",
            "prompt",
            "question_type",
            "language",
            "difficulty",
            "max_score",
            "time_limit_ms",
            "memory_limit_mb",
            "display_order",
            "mcq_options",
            "is_multiple_choice",
            "sample_test_cases",
        )

    def get_is_multiple_choice(self, obj) -> bool:
        if obj.question_type == Problem.QuestionType.MCQ:
            return obj.mcq_options.filter(is_correct=True).count() > 1
        return False

    def get_sample_test_cases(self, obj) -> list:
        if obj.question_type == Problem.QuestionType.CODING and obj.couchdb_test_cases_doc_id:
            from infrastructure.couchdb import DocumentRepository
            try:
                all_cases = DocumentRepository().get_test_cases(obj.couchdb_test_cases_doc_id)
                return [tc for tc in all_cases if tc.get("is_sample", False)]
            except Exception:
                pass
        return []


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
    """Payload for a new submission (supports MCQ, FIB, and Coding)."""

    source_code = serializers.CharField(required=False, allow_blank=True, default="")
    selected_options = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    submitted_text = serializers.CharField(required=False, allow_blank=True, default="")


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
            "selected_options",
            "submitted_text",
        )
        read_only_fields = fields


class SubmissionDraftSerializer(serializers.ModelSerializer):
    """Submission draft response returned to the client."""

    class Meta:
        model = SubmissionDraft
        fields = (
            "id",
            "problem",
            "source_code",
            "selected_options",
            "submitted_text",
            "updated_at",
        )
        read_only_fields = ("id", "problem", "updated_at")


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

# Refactor: Improve responsive styles and layouts.

# Refactor: Align with project code quality guidelines.

# Refactor: Align with project code quality guidelines.

# Refactor: Align with project code quality guidelines.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.
