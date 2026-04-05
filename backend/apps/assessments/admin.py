"""Django admin registrations for assessments."""

from django.contrib import admin

from .models import Assessment, Problem, Submission, AssessmentInvitation


class ProblemInline(admin.TabularInline):
    """Inline editor for problems within an assessment."""

    model = Problem
    extra = 0
    fields = ("title", "language", "difficulty", "max_score", "time_limit_ms", "display_order")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Admin interface for Assessment records."""

    list_display = ("title", "organization", "status", "duration_minutes")
    list_filter = ("status", "organization")
    inlines = [ProblemInline]


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    """Admin interface for Problem records."""

    list_display = ("title", "assessment", "language", "difficulty", "max_score")
    list_filter = ("language", "difficulty")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin interface for Submission records."""

    list_display = ("id", "problem", "candidate", "status", "score")
    list_filter = ("status",)


@admin.register(AssessmentInvitation)
class AssessmentInvitationAdmin(admin.ModelAdmin):
    """Admin interface for AssessmentInvitation records."""

    list_display = ("id", "assessment", "email", "user", "expires_at", "is_active")
    list_filter = ("is_active", "assessment")
    search_fields = ("email", "token")

# Refactor: Improve error handling and exception logging.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Improve responsive styles and layouts.
