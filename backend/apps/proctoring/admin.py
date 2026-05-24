from django.contrib import admin
from .models import ProctoringSession, ProctoringViolation, ProctoringLog


@admin.register(ProctoringSession)
class ProctoringSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "invitation", "candidate", "status", "violation_count", "started_at")
    list_filter = ("status", "started_at")
    search_fields = ("candidate__email", "invitation__assessment__title")


@admin.register(ProctoringViolation)
class ProctoringViolationAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "violation_type", "severity", "timestamp")
    list_filter = ("violation_type", "severity", "timestamp")


@admin.register(ProctoringLog)
class ProctoringLogAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "event_type", "timestamp")
    list_filter = ("event_type", "timestamp")
