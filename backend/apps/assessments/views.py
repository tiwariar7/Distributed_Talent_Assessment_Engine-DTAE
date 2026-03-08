import uuid

from datetime import datetime
import logging
logger = logging.getLogger(__name__)


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from datetime import timedelta
from .models import Assessment, Problem, Submission, AssessmentInvitation
from .serializers import AssessmentSerializer, ProblemSerializer, SubmissionSerializer, SubmissionCreateSerializer, AssessmentInvitationSerializer
from apps.executions.tasks import run_submission_evaluation
from ..accounts.permissions import IsRecruiterUser, IsCandidateUser

class RecruiterAssessmentViewSet(viewsets.ModelViewSet):
    """Recruiter CRUD for assessments and problem management."""
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated, IsRecruiterUser]

    def get_queryset(self):
        # Recruiter sees assessments for organizations they belong to
        user = self.request.user
        org_ids = user.memberships.values_list('organization_id', flat=True)
        return Assessment.objects.filter(organization_id__in=org_ids)

    @action(detail=True, methods=['post'], url_path='invite')
    def invite_candidates(self, request, pk=None):
        """Create AssessmentInvitation objects for a list of candidate emails."""
        assessment = self.get_object()
        emails = request.data.get('emails', [])
        if not isinstance(emails, list) or not emails:
            return Response({'detail': 'Emails list required.'}, status=status.HTTP_400_BAD_REQUEST)
        invitations = []
        for email in emails:
            token = uuid.uuid4().hex
            invitation = AssessmentInvitation.objects.create(
                assessment=assessment,
                email=email,
                token=token,
                expires_at=timezone.now() + timedelta(days=7),
                is_active=True,
            )
            invitations.append(invitation)
        serializer = AssessmentInvitationSerializer(invitations, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CandidateAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoints for candidates to retrieve assessment details and submit solutions."""
    queryset = Assessment.objects.filter(status=Assessment.Status.PUBLISHED)
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated, IsCandidateUser]

    @action(detail=False, methods=['get'], url_path='invitations')
    def list_invitations(self, request):
        """List all invitations associated with the authenticated candidate."""
        from django.db.models import Q
        from .serializers import AssessmentInvitationDetailSerializer
        invitations = AssessmentInvitation.objects.filter(
            Q(user=request.user) | Q(email__iexact=request.user.email)
        ).select_related('assessment', 'assessment__organization').order_by('-expires_at')
        serializer = AssessmentInvitationDetailSerializer(invitations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='start')
    def start_assessment(self, request, pk=None):
        """Validate token and mark invitation as started."""
        token = request.data.get('token')
        try:
            invitation = AssessmentInvitation.objects.get(token=token, assessment_id=pk, is_active=True)
        except AssessmentInvitation.DoesNotExist:
            return Response({'detail': 'Invalid or expired invitation token.'}, status=status.HTTP_400_BAD_REQUEST)
        invitation.started_at = timezone.now()
        invitation.save(update_fields=['started_at'])
        return Response({'detail': 'Assessment started.'})

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_solution(self, request, pk=None):
        """Create a new Submission for a problem within the assessment."""
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem_id = request.data.get('problem_id')
        try:
            problem = Problem.objects.get(id=problem_id, assessment_id=pk)
        except Problem.DoesNotExist:
            return Response({'detail': 'Problem not found in this assessment.'}, status=status.HTTP_404_NOT_FOUND)
        submission = Submission.objects.create(
            problem=problem,
            candidate=request.user,
            status=Submission.Status.QUEUED,
        )
        # TODO: enqueue Celery task for execution
        return Response({'submission_id': submission.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], url_path='finish')
    def finish_assessment(self, request, pk=None):
        """Mark assessment as completed for the candidate.

        Validates that the candidate has an active invitation, updates the invitation status,
        triggers scoring via existing Celery task, and returns final results.
        """
        token = request.data.get('token')
        if not token:
            return Response({'detail': 'Token required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            invitation = AssessmentInvitation.objects.get(
                token=token,
                assessment_id=pk,
                is_active=True,
                user=request.user,
            )
        except AssessmentInvitation.DoesNotExist:
            return Response({'detail': 'Invalid invitation.'}, status=status.HTTP_400_BAD_REQUEST)
        # Mark invitation as completed
        invitation.is_active = False
        invitation.completed_at = timezone.now()
        invitation.save(update_fields=['is_active', 'completed_at'])
        # Trigger scoring task (reuse existing evaluation task)
        try:
            run_submission_evaluation.delay(invitation.id)
            result = {"status": "scoring_triggered"}
        except Exception as e:
            logger.error(f"Failed to dispatch evaluation task for invitation {invitation.id}: {e}")
            result = {"status": "scoring_failed", "error": str(e)}
        return Response({'detail': 'Assessment finished.', 'result': result}, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from .throttles import SubmissionRateThrottle
from .permissions import IsCandidateForProblem

class ProblemSubmissionView(APIView):
    """Candidate submits a solution to a problem."""
    permission_classes = [IsAuthenticated, IsCandidateUser, IsCandidateForProblem]
    throttle_classes = [SubmissionRateThrottle]

    def post(self, request, problem_id):
        try:
            problem = Problem.objects.select_related("assessment").get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({"detail": "Problem not found."}, status=status.HTTP_404_NOT_FOUND)

        # Enforce that the assessment is published
        if problem.assessment.status != problem.assessment.Status.PUBLISHED:
            return Response({"detail": "Assessment not published."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source_code = serializer.validated_data.get("source_code")

        from apps.executions.services import SubmissionService
        submission = SubmissionService.create_and_queue(
            problem=problem,
            candidate=request.user,
            source_code=source_code,
        )

        serializer_out = SubmissionSerializer(submission)
        return Response(serializer_out.data, status=status.HTTP_202_ACCEPTED)

# Refactor: Enhance component rendering performance.

# Refactor: Enhance component rendering performance.

# Refactor: Optimize imports and clean up code structure.
