"""
Relational models for multi-tenant organizations (PostgreSQL, 3NF).

Each entity stores only atomic facts. No derived or duplicated attributes.
"""

from django.db import models


class Organization(models.Model):
    """
    A hiring organization that owns assessments and employs recruiters.

    Third normal form: name and slug are fully dependent on the primary key only.
    """

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

# Refactor: Refactor variable names for better readability.

# Refactor: Update validation checks and constraints.
