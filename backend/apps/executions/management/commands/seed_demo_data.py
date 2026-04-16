"""
Seed demo organization, users, assessment, and CouchDB test cases.

Usage: python manage.py seed_demo_data
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Membership, Role
from apps.assessments.models import Assessment, Problem
from apps.organizations.models import Organization
from infrastructure.couchdb import CouchDBClient, DocumentRepository
from infrastructure.couchdb.views.leaderboard import LEADERBOARD_VIEWS

User = get_user_model()

DEMO_ORG_SLUG = "acme-corp"
DEMO_PASSWORD = "DemoPass123!"


class Command(BaseCommand):
    """Populate PostgreSQL and CouchDB with a walkthrough-ready demo dataset."""

    help = "Seed roles, organization, users, assessment, problems, and CouchDB test cases."

    def handle(self, *args, **options) -> None:
        client = CouchDBClient()
        client.ensure_database()
        client.upsert_design_document("leaderboard", LEADERBOARD_VIEWS)

        with transaction.atomic():
            organization, _ = Organization.objects.get_or_create(
                slug=DEMO_ORG_SLUG,
                defaults={"name": "Acme Corp", "is_active": True},
            )

            roles = {}
            for code, description in [
                ("candidate", "Assessment participant"),
                ("recruiter", "Hiring team member"),
                ("admin", "Platform administrator"),
            ]:
                roles[code], _ = Role.objects.get_or_create(
                    code=code,
                    defaults={"description": description},
                )

            candidate = self._ensure_user(
                email="candidate@demo.test",
                first_name="Casey",
                last_name="Candidate",
            )
            recruiter = self._ensure_user(
                email="recruiter@demo.test",
                first_name="Riley",
                last_name="Recruiter",
            )

            self._ensure_membership(candidate, organization, roles["candidate"])
            self._ensure_membership(recruiter, organization, roles["recruiter"])

            assessment, _ = Assessment.objects.get_or_create(
                organization=organization,
                title="Backend Engineering Screen",
                defaults={
                    "description": (
                        "Two Python challenges demonstrating the DTAE execution "
                        "pipeline, CouchDB MVCC logs, and MapReduce leaderboard."
                    ),
                    "status": Assessment.Status.PUBLISHED,
                    "duration_minutes": 90,
                    "pass_threshold_percentage": 40,
                },
            )
            if assessment.status != Assessment.Status.PUBLISHED:
                assessment.status = Assessment.Status.PUBLISHED
                assessment.save(update_fields=["status"])

        repository = DocumentRepository()
        problems = self._seed_problems(assessment, repository)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write(f"  Organization : {organization.slug}")
        self.stdout.write(f"  Assessment   : {assessment.id} — {assessment.title}")
        for problem in problems:
            self.stdout.write(f"  Problem      : {problem.id} — {problem.title}")
        self.stdout.write("")
        self.stdout.write("  Login credentials (JWT via /api/v1/auth/login/):")
        self.stdout.write(f"    candidate@demo.test / {DEMO_PASSWORD}")
        self.stdout.write(f"    recruiter@demo.test / {DEMO_PASSWORD}")

    def _ensure_user(self, email: str, first_name: str, last_name: str) -> User:
        """Create or update a demo user with a known password."""
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        if created:
            self.stdout.write(f"  Created user: {email}")
        return user

    def _ensure_membership(self, user: User, organization: Organization, role: Role) -> None:
        """Attach user to organization if not already a member."""
        Membership.objects.get_or_create(
            user=user,
            organization=organization,
            role=role,
        )

    def _seed_problems(
        self,
        assessment: Assessment,
        repository: DocumentRepository,
    ) -> list[Problem]:
        """Create demo problems and persist hidden test cases to CouchDB."""
        specs = [
            {
                "title": "Hello, World",
                "prompt": (
                    "Write a Python program that prints exactly:\n\n"
                    "    Hello, World!\n"
                ),
                "display_order": 1,
                "test_cases": [
                    {"stdin": "", "expected_stdout": "Hello, World!"},
                ],
                "reference_solution": 'print("Hello, World!")',
            },
            {
                "title": "Sum Two Numbers",
                "prompt": (
                    "Read two integers from stdin (one per line) and print their sum."
                ),
                "display_order": 2,
                "test_cases": [
                    {"stdin": "2\n3\n", "expected_stdout": "5"},
                    {"stdin": "10\n-4\n", "expected_stdout": "6"},
                ],
                "reference_solution": (
                    "a = int(input())\n"
                    "b = int(input())\n"
                    "print(a + b)"
                ),
            },
        ]

        problems: list[Problem] = []
        for spec in specs:
            problem, created = Problem.objects.get_or_create(
                assessment=assessment,
                title=spec["title"],
                defaults={
                    "prompt": spec["prompt"],
                    "language": Problem.Language.PYTHON,
                    "max_score": 100,
                    "display_order": spec["display_order"],
                },
            )
            test_doc_id = repository.save_test_cases(problem.pk, spec["test_cases"])
            problem.couchdb_test_cases_doc_id = test_doc_id
            problem.save(update_fields=["couchdb_test_cases_doc_id"])
            problems.append(problem)
            if created:
                self.stdout.write(f"  Created problem: {problem.title}")

        return problems

# Refactor: Enhance component rendering performance.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Improve responsive styles and layouts.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.
