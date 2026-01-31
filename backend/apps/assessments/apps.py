"""Django app configuration for assessments."""

from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    """Registers the assessments application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.assessments"
    verbose_name = "Assessments"
