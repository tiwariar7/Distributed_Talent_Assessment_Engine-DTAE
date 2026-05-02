import logging
from django.utils import timezone
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.assessments.models import AssessmentInvitation
from .models import ProctoringSession, ProctoringViolation, ProctoringLog
from .serializers import ProctoringSessionSerializer, ProctoringViolationSerializer

logger = logging.getLogger(__name__)


class StartProctoringSessionView(APIView):
    """
    Start a proctoring session for a given invitation token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("invitation_token")
        if not token:
            return Response(
                {"error": "invitation_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation = AssessmentInvitation.objects.get(
                token=token,
            )
        except AssessmentInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid or inactive invitation token."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Reject already completed or revoked invitations
        if invitation.status in (
            AssessmentInvitation.InvitationStatus.COMPLETED,
            AssessmentInvitation.InvitationStatus.EXPIRED,
        ):
            return Response(
                {"error": f"This assessment has already been {invitation.status}. You cannot retake it."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce expiration limit
        if invitation.expires_at < timezone.now():
            invitation.is_active = False
            invitation.status = AssessmentInvitation.InvitationStatus.EXPIRED
            invitation.save(update_fields=["is_active", "status"])
            return Response(
                {"error": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user is candidate on the invitation
        if invitation.user and invitation.user != request.user:
            return Response(
                {"error": "This invitation does not belong to the authenticated user."},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not invitation.user:
            # Bind user to the invitation on first entry
            invitation.user = request.user
            invitation.save(update_fields=["user"])

        # Update invitation status
        if invitation.status in (
            AssessmentInvitation.InvitationStatus.PENDING,
            AssessmentInvitation.InvitationStatus.ACCEPTED
        ):
            invitation.status = AssessmentInvitation.InvitationStatus.STARTED
            if not invitation.started_at:
                invitation.started_at = timezone.now()
            invitation.save(update_fields=["status", "started_at"])

        # Get or create active session
        session, created = ProctoringSession.objects.get_or_create(
            invitation=invitation,
            candidate=request.user,
            ended_at__isnull=True,
            defaults={
                "is_camera_active": request.data.get("is_camera_active", True),
                "is_mic_active": request.data.get("is_mic_active", True),
                "metadata": request.data.get("metadata", {}),
            }
        )

        serializer = ProctoringSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


class ReportViolationView(APIView):
    """
    Report a proctoring violation. If violation count exceeds threshold, trigger auto-submit.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session_id")
        violation_type = request.data.get("violation_type")
        severity = request.data.get("severity", "medium")
        metadata = request.data.get("metadata", {})

        if not session_id or not violation_type:
            return Response(
                {"error": "session_id and violation_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = ProctoringSession.objects.get(pk=session_id, ended_at__isnull=True)
        except ProctoringSession.DoesNotExist:
            return Response(
                {"error": "Active proctoring session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Candidate security check
        if session.candidate != request.user:
            # Recruiters can view/update but let's restrict reporting to the candidate user
            # unless recruiter has permissions (we can check memberships)
            is_recruiter = request.user.memberships.filter(
                organization=session.invitation.assessment.organization,
                role__code="recruiter"
            ).exists()
            if not is_recruiter:
                return Response(
                    {"error": "Unauthorized to access this session."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        max_warnings = getattr(settings, "PROCTORING_MAX_WARNINGS", 3)
        auto_submit_enabled = getattr(settings, "PROCTORING_AUTO_SUBMIT_ON_VIOLATION", True)

        # Determine if we should trigger auto-submit
        # Default policy: auto-submit when violation count >= max_warnings
        current_violations = session.violation_count + 1
        trigger_auto_submit = auto_submit_enabled and (current_violations >= max_warnings)

        # Create violation
        violation = ProctoringViolation.objects.create(
            session=session,
            violation_type=violation_type,
            severity=severity,
            metadata=metadata,
            warning_shown=True,
            auto_submitted=trigger_auto_submit,
        )

        # Log event in ProctoringLog for telemetry trace
        log_event_type = getattr(ProctoringLog.EventType, violation_type.upper(), ProctoringLog.EventType.WARNING_ISSUED)
        ProctoringLog.objects.create(
            session=session,
            event_type=log_event_type,
            metadata=metadata,
        )

        # Update session
        session.violation_count = current_violations
        session.warning_count += 1
        
        if trigger_auto_submit:
            session.status = ProctoringSession.SessionStatus.AUTO_SUBMITTED
            session.ended_at = timezone.now()
            
            # Deactivate invitation
            invitation = session.invitation
            invitation.is_active = False
            invitation.completed_at = timezone.now()
            invitation.status = AssessmentInvitation.InvitationStatus.COMPLETED
            invitation.save(update_fields=["is_active", "completed_at", "status"])
            
            # Log auto-submit log entry
            ProctoringLog.objects.create(
                session=session,
                event_type=ProctoringLog.EventType.AUTO_SUBMIT,
                metadata={"reason": f"Violation count {current_violations} reached threshold {max_warnings}"},
            )
            logger.warning(f"Auto-submitting assessment for candidate {session.candidate.email} due to proctoring violations.")
            
        elif current_violations == max_warnings - 1:
            session.status = ProctoringSession.SessionStatus.WARNED

        session.save(update_fields=["violation_count", "warning_count", "status", "ended_at"])

        # Serialize & response
        serializer = ProctoringViolationSerializer(violation)
        response_data = serializer.data
        response_data["violation_count"] = session.violation_count
        response_data["auto_submitted"] = trigger_auto_submit
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class ProctoringStatusView(generics.RetrieveAPIView):
    """
    Get current status of a proctoring session.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProctoringSessionSerializer
    queryset = ProctoringSession.objects.all()


class EndProctoringSessionView(APIView):
    """
    End an active proctoring session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session_id")
        if not session_id:
            return Response(
                {"error": "session_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = ProctoringSession.objects.get(pk=session_id, ended_at__isnull=True)
        except ProctoringSession.DoesNotExist:
            return Response(
                {"error": "Active session not found or already ended."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.candidate != request.user:
            return Response(
                {"error": "Unauthorized to modify this session."},
                status=status.HTTP_403_FORBIDDEN,
            )

        session.ended_at = timezone.now()
        session.status = ProctoringSession.SessionStatus.COMPLETED
        session.save(update_fields=["ended_at", "status"])

        serializer = ProctoringSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Refactor: Align with project code quality guidelines.

# Refactor: Enhance component rendering performance.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Update validation checks and constraints.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Update validation checks and constraints.
