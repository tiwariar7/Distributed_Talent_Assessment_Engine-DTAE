"""
Recruiter assessment management service.

Coordinates PostgreSQL metadata with CouchDB unstructured test case documents.
"""

from __future__ import annotations

from django.db import transaction

from apps.assessments.models import Assessment, Problem
from apps.organizations.models import Organization
from infrastructure.couchdb import DocumentRepository


class RecruiterAssessmentService:
    """
    Application service for recruiters to author and publish assessments.

    Single Responsibility: recruiter write operations on assessments/problems.
    """

    @staticmethod
    def create_assessment(
        organization: Organization,
        title: str,
        description: str,
        duration_minutes: int,
    ) -> Assessment:
        """Create a draft assessment for the organization."""
        return Assessment.objects.create(
            organization=organization,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            status=Assessment.Status.DRAFT,
        )

    @staticmethod
    def create_problem(assessment: Assessment, **fields) -> Problem:
        """Add a coding problem to a draft assessment."""
        if assessment.status == Assessment.Status.ARCHIVED:
            raise ValueError("Cannot add problems to an archived assessment.")
        return Problem.objects.create(assessment=assessment, **fields)

    @staticmethod
    def upload_test_cases(problem: Problem, test_cases: list[dict]) -> str:
        """
        Persist hidden test cases to CouchDB and link the document id.

        Overwrites any existing test case document for the problem.
        """
        repository = DocumentRepository()
        doc_id = repository.save_test_cases(problem.pk, test_cases)
        problem.couchdb_test_cases_doc_id = doc_id
        problem.save(update_fields=["couchdb_test_cases_doc_id"])
        return doc_id

    @staticmethod
    @transaction.atomic
    def publish_assessment(assessment: Assessment) -> Assessment:
        """
        Publish an assessment after validating it has problems with test cases.

        Raises ValueError when preconditions are not met.
        """
        if assessment.status == Assessment.Status.PUBLISHED:
            return assessment

        problems = list(assessment.problems.all())
        if not problems:
            raise ValueError("Assessment must have at least one problem before publishing.")

        missing_tests = [
            problem.title
            for problem in problems
            if not problem.couchdb_test_cases_doc_id
        ]
        if missing_tests:
            raise ValueError(
                f"Problems missing test cases: {', '.join(missing_tests)}",
            )

        assessment.status = Assessment.Status.PUBLISHED
        assessment.save(update_fields=["status", "updated_at"])
        return assessment

# Refactor: Refactor variable names for better readability.

# Refactor: Improve responsive styles and layouts.

# Refactor: Update validation checks and constraints.
