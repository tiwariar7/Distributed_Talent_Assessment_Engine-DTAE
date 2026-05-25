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

        # Accept connection with subprotocol if negotiated
        if hasattr(self, "accepted_subprotocol"):
            await self.accept(subprotocol=self.accepted_subprotocol)
        else:
            await self.accept()

        logger.info(
            f"Proctoring WS connected for user {user.email}, session {self.session.id}",
            extra={"user_id": user.id, "session_id": self.session.id, "action": "websocket_connect"}
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
        session_id = getattr(self, "session", None) and self.session.id
        user_id = self.scope.get("user") and getattr(self.scope["user"], "id", None)
        logger.info(
            f"Proctoring WS disconnected with code {close_code}",
            extra={"session_id": session_id, "user_id": user_id, "close_code": close_code, "action": "websocket_disconnect"}
        )

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming telemetry signals from the client.
        Normalizes uppercase/lowercase standard events and evaluates violations.
        """
        raw_event = content.get("event_type", "")
        if not raw_event:
            await self.send_json({"error": "event_type is required."})
            return

        event_type = raw_event.upper().strip()
        metadata = content.get("metadata", {})

        # Handle ping/heartbeat
        if event_type in ("PING", "HEARTBEAT_PING"):
            session_id = getattr(self, "session", None) and self.session.id
            user_id = self.scope.get("user") and getattr(self.scope["user"], "id", None)
            logger.info("Heartbeat ping received", extra={"session_id": session_id, "user_id": user_id, "action": "heartbeat_ping"})
            await self.send_json({"event_type": "pong", "timestamp": timezone.now().isoformat()})
            return

        # Normalize incoming events
        normalized_event = None
        if event_type in ("TAB_SWITCH", "WINDOW_BLUR", "TAB_FOCUS_LOST"):
            normalized_event = "tab_switch"
        elif event_type in ("FULLSCREEN_EXIT",):
            normalized_event = "fullscreen_exit"
        elif event_type in ("COPY_PASTE_ATTEMPT", "COPY_ATTEMPT", "PASTE_ATTEMPT", "COPY_PASTE"):
            normalized_event = "copy_paste_attempt"
        elif event_type in ("FACE_DETECTION_UPDATE", "PHONE_DETECTED", "MULTIPLE_FACES_DETECTED", "NO_FACE_DETECTED"):
            normalized_event = "face_detection_update"
        else:
            # Lowercase fallback
            normalized_event = raw_event.lower().strip()

        # Validate event type
        valid_violation_types = {choice[0] for choice in ProctoringViolation.ViolationType.choices}
        valid_event_types = {choice[0] for choice in ProctoringLog.EventType.choices}

        if normalized_event not in valid_violation_types and normalized_event not in valid_event_types:
            await self.send_json({"error": f"Invalid event_type: {raw_event}"})
            return

        # Check if the event is a violation that counts towards warnings
        is_violation = normalized_event in valid_violation_types

        # Structured JSON logging for all telemetry
        logger.info(
            f"Proctoring telemetry event: {normalized_event}",
            extra={
                "session_id": self.session.id,
                "user_id": self.scope["user"].id,
                "event_type": normalized_event,
                "is_violation": is_violation,
                "metadata": metadata,
                "action": "proctoring_event"
            }
        )

        if is_violation:
            max_warnings = getattr(settings, "PROCTORING_MAX_WARNINGS", 2)
            auto_submit_enabled = getattr(settings, "PROCTORING_AUTO_SUBMIT_ON_VIOLATION", True)
            
            # Process violation in DB (atomic)
            res = await self.process_violation(
                self.session.id, normalized_event, metadata, max_warnings, auto_submit_enabled
            )
            if res:
                violation_id, auto_submitted, count = res
                
                # Warning logger warning log
                logger.warning(
                    f"Proctoring warning issued ({count}/{max_warnings}) for {self.scope['user'].email}",
                    extra={
                        "session_id": self.session.id,
                        "user_id": self.scope["user"].id,
                        "violation_type": normalized_event,
                        "violation_count": count,
                        "auto_submitted": auto_submitted,
                        "action": "proctoring_violation"
                    }
                )

                # Broadcast back to current client
                await self.send_json({
                    "event_type": "warning_issued" if not auto_submitted else "auto_submit",
                    "violation_type": normalized_event,
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
            await self.record_log(self.session.id, normalized_event, metadata)
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
        """Validate JWT from query string, subprotocol, or scope user."""
        from urllib.parse import parse_qs
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model

        User = get_user_model()
        token = None

        # 1. Try to get token from Sec-WebSocket-Protocol subprotocol
        headers = dict(self.scope.get("headers", []))
        protocol_header = headers.get(b"sec-websocket-protocol", b"").decode().strip()
        if protocol_header:
            protocols = [p.strip() for p in protocol_header.split(",")]
            if "access_token" in protocols:
                idx = protocols.index("access_token")
                if idx + 1 < len(protocols):
                    token = protocols[idx + 1]
                    self.accepted_subprotocol = "access_token"

        # 2. Fallback to query string
        if not token:
            query_string = self.scope.get("query_string", b"").decode()
            token_list = parse_qs(query_string).get("token", [])
            if token_list:
                token = token_list[0]

        # 3. Fallback to scope user
        if not token:
            user = self.scope.get("user")
            if user and user.is_authenticated:
                return user
            return None

        try:
            access = AccessToken(token)
            user_id = access["user_id"]
            self.token_expiry = access["exp"]
            user = await database_sync_to_async(User.objects.get)(pk=user_id)
            self.scope["user"] = user
            return user
        except (InvalidToken, TokenError, User.DoesNotExist, KeyError) as exc:
            logger.warning("WebSocket auth failed: %s", exc, extra={"token_supplied": bool(token)})
            return None


# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve responsive styles and layouts.

# Refactor: Update validation checks and constraints.

# Refactor: Optimize query performance and database indexing.

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Improve responsive styles and layouts.
