from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)

from .models import Assessment, Problem, Submission, AssessmentInvitation, SubmissionDraft
from .serializers import (
    AssessmentSerializer,
    ProblemSerializer,
    SubmissionSerializer,
    SubmissionCreateSerializer,
    AssessmentInvitationSerializer,
    SubmissionDraftSerializer,
)
from apps.executions.tasks import run_submission_evaluation
from ..accounts.permissions import IsRecruiterUser, IsCandidateUser
from .throttles import SubmissionRateThrottle
from .permissions import IsCandidateForProblem


def verify_assessment_timer(user, assessment) -> AssessmentInvitation | None:
    """
    Enforces the assessment session timer on the backend.
    Checks if the user has an active invitation, if they have started,
    and if they are still within the duration limits (+ 2 min grace period).
    """
    invitation = AssessmentInvitation.objects.filter(
        user=user,
        assessment=assessment,
    ).first()
    if not invitation:
        return None

    # Check if assessment is started and currently active
    if invitation.status == AssessmentInvitation.InvitationStatus.PENDING or not invitation.started_at:
        return None

    if invitation.status == AssessmentInvitation.InvitationStatus.COMPLETED or not invitation.is_active:
        return None

    elapsed = timezone.now() - invitation.started_at
    allowed_duration = timedelta(minutes=assessment.duration_minutes)
    grace_period = timedelta(minutes=2)

    if elapsed > allowed_duration + grace_period:
        # Auto-finalize expired invitation
        invitation.is_active = False
        invitation.status = AssessmentInvitation.InvitationStatus.COMPLETED
        invitation.completed_at = invitation.started_at + allowed_duration
        invitation.save(update_fields=["is_active", "status", "completed_at"])
        return None

    return invitation


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

    def perform_update(self, serializer):
        assessment = serializer.save()
        cache.delete(f"assessment_detail:{assessment.id}")

    def perform_destroy(self, instance):
        cache.delete(f"assessment_detail:{instance.id}")
        super().perform_destroy(instance)

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

    def retrieve(self, request, *args, **kwargs):
        """Cache assessment details lookup."""
        assessment_id = kwargs.get("pk")
        cache_key = f"assessment_detail:{assessment_id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)  # 5 minutes
        return response

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
        
        # Enforce that the user hasn't already completed/expired the assessment
        if invitation.status == AssessmentInvitation.InvitationStatus.COMPLETED:
            return Response({'detail': 'Assessment has already been completed.'}, status=status.HTTP_400_BAD_REQUEST)

        invitation.started_at = timezone.now()
        invitation.status = AssessmentInvitation.InvitationStatus.STARTED
        invitation.save(update_fields=['started_at', 'status'])
        return Response({'detail': 'Assessment started.'})

    @action(detail=True, methods=['post'], url_path='finish')
    def finish_assessment(self, request, pk=None):
        """Mark assessment as completed for the candidate."""
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
        
        # Verify timer is not expired on backend
        assessment = invitation.assessment
        inv = verify_assessment_timer(request.user, assessment)
        if not inv:
            return Response({'detail': 'Assessment time limit has expired.'}, status=status.HTTP_403_FORBIDDEN)

        # Mark invitation as completed
        invitation.is_active = False
        invitation.completed_at = timezone.now()
        invitation.status = AssessmentInvitation.InvitationStatus.COMPLETED
        invitation.save(update_fields=['is_active', 'completed_at', 'status'])
        
        # Trigger scoring task (reuse existing evaluation task)
        try:
            run_submission_evaluation.delay(invitation.id)
            result = {"status": "scoring_triggered"}
        except Exception as e:
            logger.error(f"Failed to dispatch evaluation task for invitation {invitation.id}: {e}")
            result = {"status": "scoring_failed", "error": str(e)}
        return Response({'detail': 'Assessment finished.', 'result': result}, status=status.HTTP_200_OK)


class ProblemSubmissionView(APIView):
    """Candidate submits a solution to a problem or retrieves submission history."""
    permission_classes = [IsAuthenticated, IsCandidateUser, IsCandidateForProblem]
    throttle_classes = [SubmissionRateThrottle]

    def get(self, request, problem_id):
        """Retrieve versioned submission history for this problem and candidate."""
        submissions = Submission.objects.filter(
            problem_id=problem_id,
            candidate=request.user,
        ).order_by("-submitted_at")

        data = []
        from infrastructure.couchdb import DocumentRepository
        repo = DocumentRepository()

        for sub in submissions:
            sub_data = SubmissionSerializer(sub).data
            if sub.couchdb_source_doc_id:
                try:
                    sub_data["source_code"] = repo.get_source_code(sub.couchdb_source_doc_id)
                except Exception:
                    sub_data["source_code"] = ""
            data.append(sub_data)

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, problem_id):
        try:
            problem = Problem.objects.select_related("assessment").get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({"detail": "Problem not found."}, status=status.HTTP_404_NOT_FOUND)

        # Enforce that the assessment is published
        if problem.assessment.status != problem.assessment.Status.PUBLISHED:
            return Response({"detail": "Assessment not published."}, status=status.HTTP_403_FORBIDDEN)

        # Enforce assessment session timer limit checks
        inv = verify_assessment_timer(request.user, problem.assessment)
        if not inv:
            return Response({"detail": "Assessment session timer expired. Submission closed."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if problem.question_type == Problem.QuestionType.MCQ:
            selected_options = serializer.validated_data.get("selected_options", [])
            # Evaluate MCQ
            correct_opts = set(problem.mcq_options.filter(is_correct=True).values_list("id", flat=True))
            candidate_opts = set(selected_options)

            score = problem.max_score if candidate_opts == correct_opts else 0

            submission = Submission.objects.create(
                problem=problem,
                candidate=request.user,
                status=Submission.Status.COMPLETED,
                score=score,
                selected_options=selected_options,
                completed_at=timezone.now(),
            )
            
            # Update leaderboard points asynchronously
            from apps.leaderboard.services import LeaderboardService
            try:
                LeaderboardService.upsert_entry(
                    assessment_id=problem.assessment_id,
                    candidate_id=request.user.id,
                    score_delta=score,
                    problems_solved_delta=1 if score > 0 else 0,
                )
            except Exception as e:
                logger.error(f"Failed to update leaderboard: {e}")

            return Response(SubmissionSerializer(submission).data, status=status.HTTP_200_OK)

        elif problem.question_type == Problem.QuestionType.FIB:
            submitted_text = serializer.validated_data.get("submitted_text", "").strip()
            
            # Evaluate FIB
            rules = problem.fib_rules.all()
            matched = False
            for rule in rules:
                val = rule.acceptable_answer.strip()
                if rule.use_regex:
                    import re
                    flags = re.IGNORECASE if not rule.case_sensitive else 0
                    if re.match(val, submitted_text, flags):
                        matched = True
                        break
                else:
                    if rule.case_sensitive:
                        if submitted_text == val:
                            matched = True
                            break
                    else:
                        if submitted_text.lower() == val.lower():
                            matched = True
                            break

            score = problem.max_score if matched else 0

            submission = Submission.objects.create(
                problem=problem,
                candidate=request.user,
                status=Submission.Status.COMPLETED,
                score=score,
                submitted_text=submitted_text,
                completed_at=timezone.now(),
            )

            # Update leaderboard
            from apps.leaderboard.services import LeaderboardService
            try:
                LeaderboardService.upsert_entry(
                    assessment_id=problem.assessment_id,
                    candidate_id=request.user.id,
                    score_delta=score,
                    problems_solved_delta=1 if score > 0 else 0,
                )
            except Exception as e:
                logger.error(f"Failed to update leaderboard: {e}")

            return Response(SubmissionSerializer(submission).data, status=status.HTTP_200_OK)

        else:
            # Coding question
            source_code = serializer.validated_data.get("source_code")
            if not source_code:
                return Response({"detail": "source_code is required for coding questions."}, status=status.HTTP_400_BAD_REQUEST)

            from apps.executions.services import SubmissionService
            submission = SubmissionService.create_and_queue(
                problem=problem,
                candidate=request.user,
                source_code=source_code,
            )

            serializer_out = SubmissionSerializer(submission)
            return Response(serializer_out.data, status=status.HTTP_202_ACCEPTED)


class ProblemAutosaveView(APIView):
    """Endpoint for candidate to autosave and load answer drafts for a problem."""
    permission_classes = [IsAuthenticated, IsCandidateUser, IsCandidateForProblem]

    def get(self, request, problem_id):
        """Retrieve the current autosaved draft for the problem."""
        draft = SubmissionDraft.objects.filter(
            candidate=request.user,
            problem_id=problem_id,
        ).first()

        if not draft:
            return Response(
                {
                    "problem": problem_id,
                    "source_code": "",
                    "selected_options": [],
                    "submitted_text": "",
                },
                status=status.HTTP_200_OK,
            )

        return Response(SubmissionDraftSerializer(draft).data, status=status.HTTP_200_OK)

    def post(self, request, problem_id):
        """Save a new autosave draft. Enforces assessment timer."""
        try:
            problem = Problem.objects.select_related("assessment").get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({"detail": "Problem not found."}, status=status.HTTP_404_NOT_FOUND)

        # Enforce timer
        inv = verify_assessment_timer(request.user, problem.assessment)
        if not inv:
            return Response({"detail": "Assessment session timer expired. Autosave closed."}, status=status.HTTP_403_FORBIDDEN)

        draft, created = SubmissionDraft.objects.update_or_create(
            candidate=request.user,
            problem_id=problem_id,
            defaults={
                "source_code": request.data.get("source_code", ""),
                "selected_options": request.data.get("selected_options", []),
                "submitted_text": request.data.get("submitted_text", ""),
            },
        )

        return Response(SubmissionDraftSerializer(draft).data, status=status.HTTP_200_OK)

# Refactor: Enhance component rendering performance.

# Refactor: Enhance component rendering performance.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Update validation checks and constraints.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.
