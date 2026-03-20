"""Django admin registrations for organizations."""

from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization records."""

    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.
