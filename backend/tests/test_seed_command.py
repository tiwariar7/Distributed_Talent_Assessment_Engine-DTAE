"""Tests for the demo seed management command."""

from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from apps.accounts.models import Membership, Role
from apps.assessments.models import Assessment, Problem
from apps.organizations.models import Organization


@pytest.mark.django_db
@patch("apps.executions.management.commands.seed_demo_data.DocumentRepository")
@patch("apps.executions.management.commands.seed_demo_data.CouchDBClient")
def test_seed_demo_data_is_idempotent(mock_couch_client, mock_repository) -> None:
    """Running the seed command twice does not duplicate core entities."""
    mock_couch_client.return_value = MagicMock()
    mock_repository.return_value.save_test_cases.side_effect = (
        lambda problem_id, _: f"test_cases_problem_{problem_id}"
    )

    call_command("seed_demo_data")
    call_command("seed_demo_data")

    assert Organization.objects.filter(slug="acme-corp").count() == 1
    assert Role.objects.filter(code="candidate").exists()
    assert Assessment.objects.filter(title="Backend Engineering Screen").count() == 1
    assert Problem.objects.filter(assessment__organization__slug="acme-corp").count() == 2
    assert Membership.objects.filter(user__email="candidate@demo.test").exists()

# Refactor: Align with project code quality guidelines.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.

# Refactor: Enhance component rendering performance.
