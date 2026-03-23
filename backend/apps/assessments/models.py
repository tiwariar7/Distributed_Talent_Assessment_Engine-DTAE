"""
Assessment and problem definitions (PostgreSQL, 3NF).

Test cases, stdout, and execution logs are NOT stored here — only CouchDB
document identifiers (opaque keys) are persisted as foreign references.
"""

import uuid
from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class Assessment(models.Model):
    """
    A timed hiring assessment owned by a single organization.

    Status transitions are atomic via PostgreSQL transactions.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    duration_minutes = models.PositiveIntegerField(default=60)
    pass_threshold_percentage = models.PositiveIntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessments"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "title"],
                name="unique_assessment_title_per_org",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.organization.slug})"


class Problem(models.Model):
    """
    A coding problem within an assessment.

    Hidden test cases live in CouchDB; only the document id is stored here.
    """

    class Language(models.TextChoices):
        PYTHON = "python", "Python"
        JAVASCRIPT = "javascript", "JavaScript"
        CPP = "cpp", "C++"
        JAVA = "java", "Java"

    class Difficulty(models.TextChoices):
        EASY   = "easy",   "Easy"
        MEDIUM = "medium", "Medium"
        HARD   = "hard",   "Hard"

    class QuestionType(models.TextChoices):
        CODING = "coding", "Coding"
        MCQ = "mcq", "MCQ"
        FIB = "fib", "Fill in the Blank"

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="problems",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    prompt = models.TextField()
    question_type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
        default=QuestionType.CODING,
    )
    language = models.CharField(
        max_length=16,
        choices=Language.choices,
        default=Language.PYTHON,
        null=True,
        blank=True,
    )
    max_score = models.PositiveIntegerField(default=100)
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        help_text="Problem difficulty — determines base leaderboard points.",
    )
    time_limit_ms = models.PositiveIntegerField(default=2000, null=True, blank=True)
    memory_limit_mb = models.PositiveIntegerField(default=128, null=True, blank=True)
    couchdb_test_cases_doc_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="CouchDB document id for hidden test cases (unstructured).",
    )
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "problems"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return self.title


class Submission(models.Model):
    """
    A candidate's code submission for a problem.

    Source code is stored in CouchDB; PostgreSQL holds only metadata and the
    document reference for ACID-friendly relational queries.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    couchdb_source_doc_id = models.CharField(max_length=128, null=True, blank=True)
    couchdb_execution_log_doc_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="CouchDB document id for append-only execution log.",
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Celery task identifier for execution revocation.",
    )
    score = models.FloatField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # MCQ & FIB fields
    selected_options = models.JSONField(
        blank=True,
        null=True,
        help_text="List of option IDs selected for MCQ",
    )
    submitted_text = models.TextField(
        blank=True,
        null=True,
        help_text="Submitted text for Fill in the Blank",
    )
    assessment_question = models.ForeignKey(
        "AssessmentQuestion",
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "submissions"
        indexes = [
            models.Index(fields=["problem", "candidate"]),
            models.Index(fields=["status"]),
            models.Index(
                fields=["assessment_question", "candidate"],
                name="submissions_assessm_34b9ba_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Submission {self.pk} by {self.candidate_id}"


class AssessmentInvitation(models.Model):
    """
    Cryptographically signed invitation linking a Candidate to a specific Timed Assessment.
    Serves as the gateway for candidate assessment access, enforcing security limits.
    """

    class InvitationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        STARTED = "started", "Started"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessment_invitations",
    )
    token = models.CharField(max_length=64, unique=True)

    # Timing Limits
    scheduled_start = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    # Assessment Details for Candidate
    instructions = models.TextField(
        blank=True,
        default="",
        help_text="Recruiter-specified instructions shown to candidates before starting.",
    )
    proctoring_required = models.BooleanField(
        default=True,
        help_text="Whether this assessment requires camera/mic proctoring.",
    )
    invitation_message = models.TextField(
        blank=True,
        default="",
        help_text="Custom message from recruiter included in the invitation.",
    )

    # Status tracking
    status = models.CharField(
        max_length=16,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )

    # Access Telemetry
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Legacy — kept for backward compatibility, superseded by status
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assessment_invitations"
        constraints = [
            models.UniqueConstraint(
                fields=["email", "assessment"],
                name="unique_email_per_assessment_invite",
            ),
        ]

    def __str__(self) -> str:
        return f"Invite for {self.email} to {self.assessment.title}"


class MCQOption(models.Model):
    """
    An option for a Multiple Choice Question (MCQ).
    """
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="mcq_options",
    )
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "mcq_options"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return f"{self.problem.title} - Option {self.display_order}"


class FIBRule(models.Model):
    """
    A validation rule for a Fill in the Blank (FIB) question.
    """
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="fib_rules",
    )
    acceptable_answer = models.CharField(max_length=255)
    case_sensitive = models.BooleanField(default=False)
    use_regex = models.BooleanField(default=False)

    class Meta:
        db_table = "fib_rules"

    def __str__(self) -> str:
        return f"{self.problem.title} - Rule {self.pk}"


class AssessmentQuestion(models.Model):
    """
    M2M-like model linking an Assessment and a Problem with weight/marks.
    """
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="assessment_questions",
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="assessment_questions",
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    section_name = models.CharField(max_length=100, default="Core")
    marks = models.PositiveIntegerField(default=100)
    negative_marks = models.PositiveIntegerField(default=0)
    weight = models.FloatField(default=1.0)
    is_required = models.BooleanField(default=True)

    class Meta:
        db_table = "assessment_questions"
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "problem"],
                name="unique_assessment_problem",
            )
        ]

    def __str__(self) -> str:
        return f"{self.assessment.title} - {self.problem.title}"


class AssessmentReport(models.Model):
    """
    Report summarizing candidate performance on an assessment.
    """
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_reports",
    )
    invitation = models.OneToOneField(
        AssessmentInvitation,
        on_delete=models.CASCADE,
        related_name="report",
    )
    total_score = models.FloatField(default=0.0)
    section_scores = models.JSONField(default=dict)
    mcq_accuracy = models.FloatField(default=0.0)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    proctoring_violations_count = models.PositiveIntegerField(default=0)
    plagiarism_score = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_reports"

    def __str__(self) -> str:
        return f"Report: {self.candidate.email} - {self.assessment.title}"

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Update validation checks and constraints.

# Refactor: Optimize imports and clean up code structure.
