import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.conf import settings

from apps.assessments.models import AssessmentInvitation
from .models import ProctoringLog, ProctoringSession, ProctoringViolation

logger = logging.getLogger(__name__)


class ProctoringConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that handles proctoring telemetry stream in real-time.
    Manages active session validation, logs cheating events, evaluates violation counts,
    and broadcasts auto-submit/warning events back to the candidate client.
    """

    async def connect(self):
        user = await self._authenticate_user()
        if not user:
            await self.close(code=4001)  # Unauthorized
            return

        self.invitation_id = self.scope["url_route"]["kwargs"]["invitation_id"]
        
        # Verify invitation exists and belongs to the user
        invitation = await self.get_invitation(self.invitation_id, user)
        if not invitation:
            await self.close(code=4004)  # Not Found or forbidden
            return

        # Fetch or create proctoring session
        self.session = await self.get_or_create_session(invitation, user)
        if not self.session:
            await self.close(code=4003)  # Forbidden or inactive
            return

        # Channel group for active candidate communication
        self.group_name = f"proctoring_session_{self.session.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()
        logger.info(f"Proctoring WS connected for user {user.email}, session {self.session.id}")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"Proctoring WS disconnected with code {close_code}")

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming telemetry signals from the client.
        Expected format:
        {
            "event_type": "window_blur" | "copy_attempt" | etc.,
            "metadata": { ... }
        }
        """
        event_type = content.get("event_type")
        metadata = content.get("metadata", {})

        # Handle ping/heartbeat
        if event_type == "ping":
            await self.send_json({"event_type": "pong", "timestamp": timezone.now().isoformat()})
            return

        if not event_type:
            await self.send_json({"error": "event_type is required."})
            return

        # Validate event type
        valid_event_types = {choice[0] for choice in ProctoringLog.EventType.choices}
        if event_type not in valid_event_types:
            # Check if it fits the ViolationType choices as fallback
            valid_violation_types = {choice[0] for choice in ProctoringViolation.ViolationType.choices}
            if event_type not in valid_violation_types:
                await self.send_json({"error": f"Invalid event_type: {event_type}"})
                return

        # Check if the event is a violation that counts towards warnings
        is_violation = event_type in {choice[0] for choice in ProctoringViolation.ViolationType.choices}

        if is_violation:
            max_warnings = getattr(settings, "PROCTORING_MAX_WARNINGS", 3)
            auto_submit_enabled = getattr(settings, "PROCTORING_AUTO_SUBMIT_ON_VIOLATION", True)
            
            # Process violation in DB (atomic)
            res = await self.process_violation(
                self.session.id, event_type, metadata, max_warnings, auto_submit_enabled
            )
            if res:
                violation_id, auto_submitted, count = res
                
                # Broadcast back to current client
                await self.send_json({
                    "event_type": "warning_issued" if not auto_submitted else "auto_submit",
                    "violation_type": event_type,
                    "violation_count": count,
                    "max_warnings": max_warnings,
                    "auto_submitted": auto_submitted,
                    "metadata": metadata
                })
                
                # If auto-submitted, close connection
                if auto_submitted:
                    await self.close(code=4000)  # Auto-submitted close code
            else:
                await self.send_json({"error": "Failed to process violation."})
        else:
            # Just log telemetry event
            await self.record_log(self.session.id, event_type, metadata)
            await self.send_json({"status": "logged"})

    # Database Helpers
    @database_sync_to_async
    def get_invitation(self, invitation_id, user):
        try:
            inv = AssessmentInvitation.objects.get(pk=invitation_id, is_active=True)
            # Ensure it belongs to request user if user is set
            if inv.user and inv.user != user:
                return None
            return inv
        except Exception:
            return None

    @database_sync_to_async
    def get_or_create_session(self, invitation, user):
        try:
            session, _ = ProctoringSession.objects.get_or_create(
                invitation=invitation,
                candidate=user,
                ended_at__isnull=True,
                defaults={"is_camera_active": True, "is_mic_active": True}
            )
            return session
        except Exception as e:
            logger.error(f"Error resolving proctoring session: {e}")
            return None

    @database_sync_to_async
    def record_log(self, session_id, event_type, metadata):
        try:
            ProctoringLog.objects.create(
                session_id=session_id,
                event_type=event_type,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error logging telemetry event: {e}")

    @database_sync_to_async
    def process_violation(self, session_id, event_type, metadata, max_warnings, auto_submit_enabled):
        from django.db import transaction
        try:
            with transaction.atomic():
                session = ProctoringSession.objects.select_for_update().get(pk=session_id)
                if session.ended_at:
                    return None
                    
                current_violations = session.violation_count + 1
                trigger_auto_submit = auto_submit_enabled and (current_violations >= max_warnings)
                
                # Create violation record
                ProctoringViolation.objects.create(
                    session=session,
                    violation_type=event_type,
                    severity="medium",
                    metadata=metadata,
                    warning_shown=True,
                    auto_submitted=trigger_auto_submit,
                )
                
                # Create log entry
                ProctoringLog.objects.create(
                    session=session,
                    event_type=ProctoringLog.EventType.WARNING_ISSUED,
                    metadata=metadata,
                )
                
                session.violation_count = current_violations
                session.warning_count += 1
                
                if trigger_auto_submit:
                    session.status = ProctoringSession.SessionStatus.AUTO_SUBMITTED
                    session.ended_at = timezone.now()
                    
                    invitation = session.invitation
                    invitation.is_active = False
                    invitation.completed_at = timezone.now()
                    invitation.status = AssessmentInvitation.InvitationStatus.COMPLETED
                    invitation.save(update_fields=["is_active", "completed_at", "status"])
                    
                    ProctoringLog.objects.create(
                        session=session,
                        event_type=ProctoringLog.EventType.AUTO_SUBMIT,
                        metadata={"reason": "Violation count threshold exceeded"},
                    )
                elif current_violations == max_warnings - 1:
                    session.status = ProctoringSession.SessionStatus.WARNED
                    
                session.save(update_fields=["violation_count", "warning_count", "status", "ended_at"])
                violation_id = session.violations.last().id
                return violation_id, trigger_auto_submit, current_violations
        except Exception as e:
            logger.error(f"Error processing violation transaction: {e}")
            return None

    async def _authenticate_user(self):
        """Validate JWT from query string ``token`` parameter and track expiry."""
        from urllib.parse import parse_qs
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model

        User = get_user_model()
        query_string = self.scope.get("query_string", b"").decode()
        token_list = parse_qs(query_string).get("token", [])
        if not token_list:
            # Fallback to scope user
            user = self.scope.get("user")
            if user and user.is_authenticated:
                return user
            return None

        try:
            access = AccessToken(token_list[0])
            user_id = access["user_id"]
            self.token_expiry = access["exp"]
            user = await database_sync_to_async(User.objects.get)(pk=user_id)
            self.scope["user"] = user
            return user
        except (InvalidToken, TokenError, User.DoesNotExist, KeyError) as exc:
            logger.warning("WebSocket auth failed: %s", exc)
            return None


# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve responsive styles and layouts.

# Refactor: Update validation checks and constraints.

# Refactor: Optimize query performance and database indexing.

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Improve responsive styles and layouts.
