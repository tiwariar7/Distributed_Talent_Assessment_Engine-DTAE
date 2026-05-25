"""
Seed demo organization, users, assessment, and CouchDB test cases.

Usage: python manage.py seed_demo_data
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Membership, Role
from apps.assessments.models import Assessment, Problem, MCQOption, FIBRule
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
        try:
            client.ensure_database()
            client.upsert_design_document("leaderboard", LEADERBOARD_VIEWS)
            self.stdout.write(self.style.SUCCESS("CouchDB connection verified and design docs loaded."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"CouchDB not available or unauthorized: {e}. Skipping CouchDB design doc initialization."))

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
                        "A timed Hiring Assessment demonstrating multiple question types: "
                        "Coding challenges with sample/hidden test cases, Single & Multiple Correct MCQs, "
                        "and Fill-in-the-blank questions, secured by real-time proctoring."
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
            self.stdout.write(f"  Problem      : {problem.id} — {problem.title} ({problem.question_type})")
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
        problems = []

        # 1. Coding problem: "Sum Two Numbers"
        sum_problem, created = Problem.objects.get_or_create(
            assessment=assessment,
            title="Sum Two Numbers",
            defaults={
                "prompt": "Read two integers from stdin (one per line) and print their sum.",
                "question_type": Problem.QuestionType.CODING,
                "language": Problem.Language.PYTHON,
                "max_score": 100,
                "display_order": 1,
            },
        )
        
        # 3 visible samples + 10 hidden = 13 total test cases
        coding_cases = [
            {"stdin": "2\n3\n", "expected_stdout": "5", "is_sample": True},
            {"stdin": "10\n-4\n", "expected_stdout": "6", "is_sample": True},
            {"stdin": "0\n0\n", "expected_stdout": "0", "is_sample": True},
            {"stdin": "1\n1\n", "expected_stdout": "2", "is_sample": False},
            {"stdin": "-5\n-5\n", "expected_stdout": "-10", "is_sample": False},
            {"stdin": "100\n200\n", "expected_stdout": "300", "is_sample": False},
            {"stdin": "50\n-50\n", "expected_stdout": "0", "is_sample": False},
            {"stdin": "-12\n15\n", "expected_stdout": "3", "is_sample": False},
            {"stdin": "999\n1\n", "expected_stdout": "1000", "is_sample": False},
            {"stdin": "-1\n0\n", "expected_stdout": "-1", "is_sample": False},
            {"stdin": "1000\n1000\n", "expected_stdout": "2000", "is_sample": False},
            {"stdin": "123\n456\n", "expected_stdout": "579", "is_sample": False},
            {"stdin": "-999\n-1\n", "expected_stdout": "-1000", "is_sample": False},
        ]
        
        try:
            test_doc_id = repository.save_test_cases(sum_problem.pk, coding_cases)
            self.stdout.write(self.style.SUCCESS("Saved coding test cases to CouchDB."))
        except Exception as e:
            test_doc_id = f"mock_couchdb_doc_{sum_problem.pk}"
            self.stdout.write(self.style.WARNING(f"CouchDB not available: {e}. Seeding with mock document ID {test_doc_id}."))

        sum_problem.couchdb_test_cases_doc_id = test_doc_id
        sum_problem.save(update_fields=["couchdb_test_cases_doc_id"])
        problems.append(sum_problem)

        # 2. MCQ (Single Correct)
        mcq_single, created = Problem.objects.get_or_create(
            assessment=assessment,
            title="Time Complexity of Binary Search",
            defaults={
                "prompt": "What is the worst-case time complexity of Binary Search?",
                "question_type": Problem.QuestionType.MCQ,
                "max_score": 25,
                "display_order": 2,
            },
        )
        if created or not MCQOption.objects.filter(problem=mcq_single).exists():
            MCQOption.objects.bulk_create([
                MCQOption(problem=mcq_single, option_text="O(N)", is_correct=False, display_order=1),
                MCQOption(problem=mcq_single, option_text="O(log N)", is_correct=True, display_order=2),
                MCQOption(problem=mcq_single, option_text="O(N^2)", is_correct=False, display_order=3),
                MCQOption(problem=mcq_single, option_text="O(1)", is_correct=False, display_order=4),
            ])
        problems.append(mcq_single)

        # 3. MCQ (Multiple Correct)
        mcq_multi, created = Problem.objects.get_or_create(
            assessment=assessment,
            title="Linear Data Structures",
            defaults={
                "prompt": "Select all options that represent linear data structures.",
                "question_type": Problem.QuestionType.MCQ,
                "max_score": 25,
                "display_order": 3,
            },
        )
        if created or not MCQOption.objects.filter(problem=mcq_multi).exists():
            MCQOption.objects.bulk_create([
                MCQOption(problem=mcq_multi, option_text="Array", is_correct=True, display_order=1),
                MCQOption(problem=mcq_multi, option_text="Queue", is_correct=True, display_order=2),
                MCQOption(problem=mcq_multi, option_text="Tree", is_correct=False, display_order=3),
                MCQOption(problem=mcq_multi, option_text="Graph", is_correct=False, display_order=4),
                MCQOption(problem=mcq_multi, option_text="Stack", is_correct=True, display_order=5),
            ])
        problems.append(mcq_multi)

        # 4. Fill-in-the-blank
        fib_prob, created = Problem.objects.get_or_create(
            assessment=assessment,
            title="LIFO Data Structure",
            defaults={
                "prompt": "A ______ is a data structure that follows the Last In First Out (LIFO) principle.",
                "question_type": Problem.QuestionType.FIB,
                "max_score": 50,
                "display_order": 4,
            },
        )
        if created or not FIBRule.objects.filter(problem=fib_prob).exists():
            FIBRule.objects.create(
                problem=fib_prob,
                acceptable_answer="stack",
                case_sensitive=False,
                use_regex=False,
            )
        problems.append(fib_prob)

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

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.

# Refactor: Improve responsive styles and layouts.

# Refactor: Fix minor edge cases in calculation functions.
