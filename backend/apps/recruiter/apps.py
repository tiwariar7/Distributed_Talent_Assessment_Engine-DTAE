"""Django app configuration for recruiter dashboard APIs."""

from django.apps import AppConfig


class RecruiterConfig(AppConfig):
    """Registers the recruiter application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recruiter"
    verbose_name = "Recruiter Dashboard"

# Refactor: Align with project code quality guidelines.

# Refactor: Improve error handling and exception logging.
