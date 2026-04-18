"""Django admin registrations for accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Membership, Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role records."""

    list_display = ("code", "description")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = ("email", "username", "is_staff", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Admin interface for Membership records."""

    list_display = ("user", "organization", "role", "joined_at")
    list_filter = ("role", "organization")

# Refactor: Improve responsive styles and layouts.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.

# Refactor: Optimize query performance and database indexing.

# Refactor: Update validation checks and constraints.

# Refactor: Improve error handling and exception logging.
