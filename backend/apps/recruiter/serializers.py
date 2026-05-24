"""Serializers for recruiter assessment management."""

from rest_framework import serializers

from apps.assessments.models import Assessment, Problem


class TestCaseSerializer(serializers.Serializer):
    """A single hidden test case stored in CouchDB."""

    stdin = serializers.CharField(allow_blank=True, default="")
    expected_stdout = serializers.CharField()


class RecruiterAssessmentSerializer(serializers.ModelSerializer):
    """Assessment with nested problem count for recruiter dashboards."""

    organization = serializers.CharField(source="organization.slug", read_only=True)
    problem_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = (
            "id",
            "title",
            "description",
            "status",
            "duration_minutes",
            "organization",
            "problem_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "organization", "created_at", "updated_at")

    def get_problem_count(self, assessment: Assessment) -> int:
        """Return number of problems in this assessment."""
        return assessment.problems.count()


class RecruiterAssessmentCreateSerializer(serializers.ModelSerializer):
    """Payload for creating a draft assessment."""

    organization_slug = serializers.SlugField(write_only=True)

    class Meta:
        model = Assessment
        fields = (
            "title",
            "description",
            "duration_minutes",
            "organization_slug",
        )

    def validate_organization_slug(self, value: str) -> str:
        """Ensure the recruiter belongs to the target organization."""
        request = self.context["request"]
        from apps.recruiter.permissions import get_recruiter_organization

        organization = get_recruiter_organization(request)
        if organization is None or organization.slug != value:
            raise serializers.ValidationError(
                "You are not a recruiter for this organization.",
            )
        return value


class RecruiterProblemSerializer(serializers.ModelSerializer):
    """Problem definition for recruiter authoring."""

    class Meta:
        model = Problem
        fields = (
            "id",
            "title",
            "prompt",
            "language",
            "max_score",
            "time_limit_ms",
            "memory_limit_mb",
            "display_order",
            "couchdb_test_cases_doc_id",
        )
        read_only_fields = ("id", "couchdb_test_cases_doc_id")


class RecruiterProblemCreateSerializer(serializers.ModelSerializer):
    """Create a problem under an assessment."""

    class Meta:
        model = Problem
        fields = (
            "title",
            "prompt",
            "language",
            "max_score",
            "time_limit_ms",
            "memory_limit_mb",
            "display_order",
        )


class TestCasesUploadSerializer(serializers.Serializer):
    """Upload or replace hidden test cases for a problem."""

    test_cases = TestCaseSerializer(many=True, min_length=1)
