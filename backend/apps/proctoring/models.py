from django.db import models
from django.conf import settings


class ProctoringSession(models.Model):
    """
    Tracks a complete proctoring session for a candidate taking an assessment.
    Created when the candidate enters the assessment environment and ends
    when the assessment is completed or auto-submitted.
    """

    class SessionStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        WARNED = "warned", "Warned"
        SUSPENDED = "suspended", "Suspended"
        COMPLETED = "completed", "Completed"
        AUTO_SUBMITTED = "auto_submitted", "Auto-Submitted"

    invitation = models.ForeignKey(
        "assessments.AssessmentInvitation",
        on_delete=models.CASCADE,
        related_name="proctoring_sessions",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proctoring_sessions",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    violation_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    is_camera_active = models.BooleanField(default=False)
    is_mic_active = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE,
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Browser info, screen resolution, user agent, etc.",
    )

    class Meta:
        db_table = "proctoring_sessions"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Session for {self.candidate} - {self.invitation.assessment.title}"


class ProctoringViolation(models.Model):
    """
    Individual violation event within a proctoring session.
    Each violation is tracked with severity and timestamp for audit purposes.
    """

    class ViolationType(models.TextChoices):
        TAB_SWITCH = "tab_switch", "Tab Switch"
        WINDOW_BLUR = "window_blur", "Window Blur"
        WINDOW_MINIMIZE = "window_minimize", "Window Minimize"
        SCREEN_CHANGE = "screen_change", "Screen Change"
        COPY_ATTEMPT = "copy_attempt", "Copy Attempt"
        PASTE_ATTEMPT = "paste_attempt", "Paste Attempt"
        RIGHT_CLICK = "right_click", "Right Click"
        FULLSCREEN_EXIT = "fullscreen_exit", "Fullscreen Exit"
        CAMERA_BLOCKED = "camera_blocked", "Camera Blocked"
        MIC_BLOCKED = "mic_blocked", "Microphone Blocked"
        IDLE_TIMEOUT = "idle_timeout", "Idle Timeout"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    session = models.ForeignKey(
        ProctoringSession,
        on_delete=models.CASCADE,
        related_name="violations",
    )
    violation_type = models.CharField(max_length=32, choices=ViolationType.choices)
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    warning_shown = models.BooleanField(default=False)
    auto_submitted = models.BooleanField(
        default=False,
        help_text="True if this violation triggered an auto-submit.",
    )

    class Meta:
        db_table = "proctoring_violations"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.violation_type} violation ({self.severity}) in session {self.session_id}"


class ProctoringLog(models.Model):
    """Telemetry events emitted by candidate workspace during assessment execution.
    Captures anti-cheating signals such as tab focus loss, copy‑paste, fullscreen exit,
    device changes and idle timeouts.
    """

    class EventType(models.TextChoices):
        TAB_FOCUS_LOST = "tab_focus_lost", "Tab Focus Lost"
        COPY_PASTE = "copy_paste", "Copy‑Paste Detected"
        DEVICE_CHANGE = "device_change", "Device Source Changed"
        IDLE_TIMEOUT = "idle_timeout", "Idle Timeout"
        WINDOW_BLUR = "window_blur", "Window Blur"
        WINDOW_MINIMIZE = "window_minimize", "Window Minimize"
        SCREEN_CHANGE = "screen_change", "Screen Change"
        COPY_ATTEMPT = "copy_attempt", "Copy Attempt"
        PASTE_ATTEMPT = "paste_attempt", "Paste Attempt"
        RIGHT_CLICK = "right_click", "Right Click Blocked"
        FULLSCREEN_EXIT = "fullscreen_exit", "Fullscreen Exit"
        CAMERA_BLOCKED = "camera_blocked", "Camera Access Blocked"
        MIC_BLOCKED = "mic_blocked", "Microphone Access Blocked"
        WARNING_ISSUED = "warning_issued", "Warning Issued"
        AUTO_SUBMIT = "auto_submit", "Auto Submit Triggered"

    session = models.ForeignKey(
        ProctoringSession,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
    )
    # Legacy FK — kept for backward compatibility
    submission = models.ForeignKey(
        "assessments.Submission",
        on_delete=models.CASCADE,
        related_name="proctoring_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event data such as viewport size, keystroke count, paste length, etc.",
    )

    class Meta:
        db_table = "proctoring_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"
