"""
Recruiter views for candidate assessment invitation management.
"""

import uuid

from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AuditLog, User, Membership, Role
from apps.accounts.throttles import RecruiterAPIRateThrottle
from apps.assessments.models import Assessment, AssessmentInvitation

from .invitation_serializers import InviteCandidatesSerializer, InvitationDetailSerializer
from .permissions import IsRecruiter, IsRecruiterForAssessment, get_recruiter_organization


class InviteCandidatesView(APIView):
    """
    Invite candidates to an assessment via email.
    Creates AssessmentInvitation records and generates unique access tokens.
    """

    permission_classes = [IsRecruiterForAssessment]
    throttle_classes = [RecruiterAPIRateThrottle]

    def post(self, request: Request, assessment_id: int) -> Response:
        assessment = Assessment.objects.filter(pk=assessment_id).first()
        if not assessment:
            return Response(
                {"detail": "Assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if assessment.status != Assessment.Status.PUBLISHED:
            return Response(
                {"detail": "Only published assessments can have invitations."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InviteCandidatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emails = [e.lower().strip() for e in serializer.validated_data["emails"]]
        deadline = serializer.validated_data.get("deadline") or (
            timezone.now() + timedelta(days=7)
        )
        instructions = serializer.validated_data.get("instructions", "")
        proctoring_required = serializer.validated_data.get("proctoring_required", True)
        invitation_message = serializer.validated_data.get("invitation_message", "")

        created_invitations = []
        skipped_emails = []

        for email in emails:
            # Check if invitation already exists
            existing = AssessmentInvitation.objects.filter(
                email=email, assessment=assessment
            ).first()

            if existing:
                skipped_emails.append(email)
                continue

            token = uuid.uuid4().hex
            invitation = AssessmentInvitation.objects.create(
                assessment=assessment,
                email=email,
                token=token,
                expires_at=deadline,
                instructions=instructions,
                proctoring_required=proctoring_required,
                invitation_message=invitation_message,
                status=AssessmentInvitation.InvitationStatus.PENDING,
            )

            # Auto-link if user already exists with this email
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user:
                invitation.user = existing_user
                invitation.save(update_fields=["user"])

                # Ensure candidate membership in the org
                candidate_role = Role.objects.filter(code="candidate").first()
                if candidate_role:
                    Membership.objects.get_or_create(
                        user=existing_user,
                        organization=assessment.organization,
                        role=candidate_role,
                    )

            created_invitations.append(invitation)

            # Print link to server logs (dev mode)
            print("\n" + "=" * 60)
            print(f"CANDIDATE ASSESSMENT LINK: http://localhost:3000/assessment/{token}")
            print(f"  Email: {email}")
            print(f"  Assessment: {assessment.title}")
            print(f"  Deadline: {deadline}")
            print("=" * 60 + "\n")

        # Audit log
        AuditLog.objects.create(
            user=request.user,
            action=f"invited_{len(created_invitations)}_candidates_to_{assessment.title}",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        output = InvitationDetailSerializer(created_invitations, many=True)

        response_data = {
            "message": f"Successfully invited {len(created_invitations)} candidate(s).",
            "invitations": output.data,
        }

        if skipped_emails:
            response_data["skipped"] = {
                "count": len(skipped_emails),
                "emails": skipped_emails,
                "reason": "Already invited to this assessment.",
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class InvitationListView(generics.ListAPIView):
    """List all invitations for a specific assessment."""

    permission_classes = [IsRecruiterForAssessment]
    serializer_class = InvitationDetailSerializer
    throttle_classes = [RecruiterAPIRateThrottle]
    pagination_class = None

    def get_queryset(self):
        assessment_id = self.kwargs.get("assessment_id")
        return (
            AssessmentInvitation.objects.filter(assessment_id=assessment_id)
            .select_related("assessment")
            .order_by("-expires_at")
        )


class RevokeInvitationView(APIView):
    """Revoke (deactivate) a pending assessment invitation."""

    permission_classes = [IsRecruiter]
    throttle_classes = [RecruiterAPIRateThrottle]

    def post(self, request: Request, invitation_id: str) -> Response:
        try:
            invitation = AssessmentInvitation.objects.select_related(
                "assessment__organization"
            ).get(pk=invitation_id)
        except AssessmentInvitation.DoesNotExist:
            return Response(
                {"detail": "Invitation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify recruiter owns this assessment's org
        org = get_recruiter_organization(request)
        if not org or invitation.assessment.organization_id != org.pk:
            return Response(
                {"detail": "Not authorized for this invitation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not invitation.is_active:
            return Response(
                {"detail": "Invitation is already inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.is_active = False
        invitation.status = AssessmentInvitation.InvitationStatus.EXPIRED
        invitation.save(update_fields=["is_active", "status"])

        AuditLog.objects.create(
            user=request.user,
            action=f"revoked_invitation:{invitation.email}:{invitation.assessment.title}",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        return Response(
            {"message": f"Invitation for {invitation.email} has been revoked."},
            status=status.HTTP_200_OK,
        )


class CandidateInvitationDetailView(APIView):
    """
    Public endpoint for candidates to view invitation details via token.
    No authentication required — token serves as credential.
    """

    from rest_framework.permissions import AllowAny
    permission_classes = [AllowAny]

    def get(self, request: Request, token: str) -> Response:
        try:
            invitation = AssessmentInvitation.objects.select_related(
                "assessment__organization"
            ).get(token=token)
        except AssessmentInvitation.DoesNotExist:
            return Response(
                {"detail": "Invalid invitation token."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Allow active OR in-progress (started) invitations through
        # Only block if explicitly expired or completed
        if invitation.status in (
            AssessmentInvitation.InvitationStatus.EXPIRED,
            AssessmentInvitation.InvitationStatus.COMPLETED,
        ) and not invitation.is_active:
            return Response(
                {"detail": "This invitation has expired or been revoked."},
                status=status.HTTP_410_GONE,
            )

        if invitation.expires_at < timezone.now():
            invitation.is_active = False
            invitation.status = AssessmentInvitation.InvitationStatus.EXPIRED
            invitation.save(update_fields=["is_active", "status"])
            return Response(
                {"detail": "This invitation has expired."},
                status=status.HTTP_410_GONE,
            )

        from apps.assessments.serializers import AssessmentSerializer

        return Response(
            {
                "invitation_id": str(invitation.pk),
                "email": invitation.email,
                "status": invitation.status,
                "assessment": AssessmentSerializer(invitation.assessment).data,
                "instructions": invitation.instructions,
                "proctoring_required": invitation.proctoring_required,
                "invitation_message": invitation.invitation_message,
                "expires_at": invitation.expires_at,
                "started_at": invitation.started_at,
            },
            status=status.HTTP_200_OK,
        )

# Refactor: Update validation checks and constraints.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Align with project code quality guidelines.
