"""
Recruiter dashboard API — create assessments, problems, and upload test cases.
"""

from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.throttles import RecruiterAPIRateThrottle
from apps.assessments.models import Assessment, Problem
from apps.recruiter.permissions import get_recruiter_organization

from .permissions import IsRecruiter, IsRecruiterForAssessment
from .serializers import (
    RecruiterAssessmentCreateSerializer,
    RecruiterAssessmentSerializer,
    RecruiterProblemCreateSerializer,
    RecruiterProblemSerializer,
    TestCasesUploadSerializer,
)
from .services import RecruiterAssessmentService


class RecruiterAssessmentListCreateView(generics.ListCreateAPIView):
    """
    List assessments for the recruiter's organization or create a draft.

    Use ``?organization=<slug>`` when the user belongs to multiple orgs.
    """

    permission_classes = [IsRecruiter]
    throttle_classes = [RecruiterAPIRateThrottle]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RecruiterAssessmentCreateSerializer
        return RecruiterAssessmentSerializer

    def get_queryset(self):
        organization = get_recruiter_organization(self.request)
        if organization is None:
            return Assessment.objects.none()
        return Assessment.objects.filter(
            organization=organization,
        ).prefetch_related("problems")

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create assessment under the recruiter's organization."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = get_recruiter_organization(request)
        assessment = RecruiterAssessmentService.create_assessment(
            organization=organization,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            duration_minutes=serializer.validated_data.get("duration_minutes", 60),
        )
        output = RecruiterAssessmentSerializer(assessment)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class RecruiterAssessmentDetailView(generics.RetrieveAPIView):
    """Retrieve a single assessment with metadata for recruiters."""

    permission_classes = [IsRecruiterForAssessment]
    serializer_class = RecruiterAssessmentSerializer
    throttle_classes = [RecruiterAPIRateThrottle]

    def get_queryset(self):
        organization = get_recruiter_organization(self.request)
        if organization is None:
            return Assessment.objects.none()
        return Assessment.objects.filter(organization=organization).prefetch_related("problems")


class RecruiterAssessmentPublishView(APIView):
    """Transition a draft assessment to published status."""

    permission_classes = [IsRecruiterForAssessment]
    throttle_classes = [RecruiterAPIRateThrottle]

    def post(self, request: Request, pk: int) -> Response:
        """Validate and publish the assessment."""
        assessment = generics.get_object_or_404(
            Assessment.objects.select_related("organization"),
            pk=pk,
        )
        try:
            published = RecruiterAssessmentService.publish_assessment(assessment)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RecruiterAssessmentSerializer(published)
        return Response(serializer.data)


class RecruiterProblemCreateView(generics.CreateAPIView):
    """Add a coding problem to an assessment."""

    permission_classes = [IsRecruiterForAssessment]
    serializer_class = RecruiterProblemCreateSerializer
    throttle_classes = [RecruiterAPIRateThrottle]

    def perform_create(self, serializer) -> None:
        assessment = generics.get_object_or_404(Assessment, pk=self.kwargs["assessment_id"])
        serializer.instance = RecruiterAssessmentService.create_problem(
            assessment,
            **serializer.validated_data,
        )


class RecruiterProblemDetailView(generics.RetrieveAPIView):
    """Retrieve problem metadata (includes CouchDB test case doc id)."""

    permission_classes = [IsRecruiterForAssessment]
    serializer_class = RecruiterProblemSerializer
    throttle_classes = [RecruiterAPIRateThrottle]

    def get_queryset(self):
        return Problem.objects.filter(
            assessment_id=self.kwargs["assessment_id"],
        )


class RecruiterTestCasesUploadView(APIView):
    """Upload hidden test cases to CouchDB for a problem."""

    permission_classes = [IsRecruiterForAssessment]
    throttle_classes = [RecruiterAPIRateThrottle]

    def put(self, request: Request, assessment_id: int, problem_id: int) -> Response:
        """Replace all hidden test cases for the problem."""
        problem = generics.get_object_or_404(
            Problem,
            pk=problem_id,
            assessment_id=assessment_id,
        )
        serializer = TestCasesUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_id = RecruiterAssessmentService.upload_test_cases(
            problem,
            serializer.validated_data["test_cases"],
        )
        return Response(
            {
                "problem_id": problem.pk,
                "couchdb_test_cases_doc_id": doc_id,
                "test_case_count": len(serializer.validated_data["test_cases"]),
            },
        )

# Refactor: Improve error handling and exception logging.

# Refactor: Enhance component rendering performance.
