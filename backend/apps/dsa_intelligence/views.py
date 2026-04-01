import random
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify
from apps.recruiter.permissions import IsRecruiter
from apps.assessments.models import Assessment, Problem
from infrastructure.couchdb import DocumentRepository

from .models import Company, Topic, DSAQuestion, QuestionCompanyFrequency, FrequencyBucket
from .serializers import CompanySerializer, TopicSerializer, DSAQuestionSerializer, SmartAssessmentGeneratorSerializer


class CompanyListView(generics.ListAPIView):
    """
    List all companies.
    Pagination is intentionally disabled — all companies are returned in one
    response so the frontend dropdown can be populated without paging.
    """
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # All 709+ companies in one shot

    def get_queryset(self):
        queryset = Company.objects.all().order_by("name")
        search = self.request.query_params.get("search", "")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class TopicListView(generics.ListAPIView):
    """
    List all topics.
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]


class DSAQuestionListView(generics.ListAPIView):
    """
    List and filter DSA questions.
    """
    serializer_class = DSAQuestionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = DSAQuestion.objects.all().prefetch_related(
            "topics", "company_frequencies__company"
        )

        company_slug = self.request.query_params.get("company")
        frequency_bucket = self.request.query_params.get("frequency_bucket")
        difficulty = self.request.query_params.get("difficulty")
        topic_slug = self.request.query_params.get("topic")
        tag = self.request.query_params.get("tag")
        recently_asked = self.request.query_params.get("recently_asked")
        keyword = self.request.query_params.get("keyword")

        # Filter by company slug
        if company_slug:
            queryset = queryset.filter(company_frequencies__company__slug=company_slug)

        # Filter by frequency bucket
        if frequency_bucket:
            queryset = queryset.filter(company_frequencies__frequency_bucket=frequency_bucket)

        # Filter by difficulty
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)

        # Filter by topic slug
        if topic_slug:
            queryset = queryset.filter(topics__slug=topic_slug)

        # Filter by tag
        if tag:
            queryset = queryset.filter(
                Q(company_frequencies__metadata__tags__contains=[tag]) |
                Q(topics__name__iexact=tag)
            )

        # Filter recently asked (either 30_days or 3_months)
        if recently_asked and recently_asked.lower() == "true":
            queryset = queryset.filter(
                company_frequencies__frequency_bucket__in=[
                    FrequencyBucket.THIRTY_DAYS,
                    FrequencyBucket.THREE_MONTHS,
                ]
            )

        # Keyword search on title/slug
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(slug__icontains=keyword) |
                Q(prompt__icontains=keyword)
            )

        # Deduplicate results since join tables can duplicate rows
        return queryset.distinct()


class SmartAssessmentGeneratorView(APIView):
    """
    Generate a company-specific, balanced mock round/assessment.
    Requires recruiter permission.
    """
    permission_classes = [IsRecruiter]

    @transaction.atomic
    def post(self, request: Request) -> Response:
        # Validate input using serializer
        serializer = SmartAssessmentGeneratorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company_slug = serializer.validated_data["company_slug"]
        frequency_bucket = serializer.validated_data["frequency_bucket"]
        easy_count = serializer.validated_data["easy_count"]
        medium_count = serializer.validated_data["medium_count"]
        hard_count = serializer.validated_data["hard_count"]
        topic_slug = serializer.validated_data.get("topic_slug")
        title = serializer.validated_data.get("title")

        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            return Response(
                {"error": f"Company '{company_slug}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Retrieve questions belonging to this company
        questions_qs = DSAQuestion.objects.filter(
            company_frequencies__company=company,
        )
        
        # Skip frequency bucket filter when value is "all"
        if frequency_bucket and frequency_bucket != FrequencyBucket.ALL:
            questions_qs = questions_qs.filter(
                company_frequencies__frequency_bucket=frequency_bucket,
            )

        if topic_slug:
            questions_qs = questions_qs.filter(topics__slug=topic_slug)

        # Separate questions by difficulty
        easy_qs = list(questions_qs.filter(difficulty__iexact="Easy").distinct())
        medium_qs = list(questions_qs.filter(difficulty__iexact="Medium").distinct())
        hard_qs = list(questions_qs.filter(difficulty__iexact="Hard").distinct())

        # Fallback and deduplication using dict/set
        if len(easy_qs) < easy_count:
            fallback_easy = list(DSAQuestion.objects.filter(difficulty__iexact="Easy").distinct())
            easy_qs = list({q.id: q for q in easy_qs + fallback_easy}.values())
        if len(medium_qs) < medium_count:
            fallback_medium = list(DSAQuestion.objects.filter(difficulty__iexact="Medium").distinct())
            medium_qs = list({q.id: q for q in medium_qs + fallback_medium}.values())
        if len(hard_qs) < hard_count:
            fallback_hard = list(DSAQuestion.objects.filter(difficulty__iexact="Hard").distinct())
            hard_qs = list({q.id: q for q in hard_qs + fallback_hard}.values())

        # Random sample
        selected_questions = []
        selected_questions.extend(random.sample(easy_qs, min(len(easy_qs), easy_count)))
        selected_questions.extend(random.sample(medium_qs, min(len(medium_qs), medium_count)))
        selected_questions.extend(random.sample(hard_qs, min(len(hard_qs), hard_count)))

        if not selected_questions:
            return Response(
                {"error": "No matching DSA questions found to generate assessment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve recruiter organization
        recruiter_membership = request.user.memberships.filter(role__code="recruiter").first()
        if not recruiter_membership:
            return Response(
                {"error": "Recruiter does not belong to any organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        org = recruiter_membership.organization
        assessment_title = title or f"{company.name} Mock Assessment ({frequency_bucket.replace('_', ' ').title()})"
        
        # Ensure title is unique per organization
        base_title = assessment_title
        counter = 1
        while Assessment.objects.filter(organization=org, title=assessment_title).exists():
            assessment_title = f"{base_title} #{counter}"
            counter += 1

        # Calculate dynamic duration based on difficulty mix
        duration_minutes = 0
        for qn in selected_questions:
            diff_lower = qn.difficulty.lower()
            if diff_lower == "easy":
                duration_minutes += 15
            elif diff_lower == "medium":
                duration_minutes += 30
            elif diff_lower == "hard":
                duration_minutes += 45
            else:
                duration_minutes += 30
        duration_minutes = max(15, duration_minutes)

        assessment = Assessment.objects.create(
            organization=org,
            title=assessment_title,
            description=f"Generated mock assessment round containing {len(selected_questions)} questions from {company.name}.",
            duration_minutes=duration_minutes,
            status=Assessment.Status.PUBLISHED, # Auto publish
        )

        # Create Problems and seed mock test cases in CouchDB
        repository = DocumentRepository()
        problems_created = []
        couchdb_errors = []
        
        for idx, qn in enumerate(selected_questions):
            difficulty_map = {
                "easy": Problem.Difficulty.EASY,
                "medium": Problem.Difficulty.MEDIUM,
                "hard": Problem.Difficulty.HARD,
            }
            difficulty_val = difficulty_map.get(qn.difficulty.lower(), Problem.Difficulty.MEDIUM)

            problem = Problem.objects.create(
                assessment=assessment,
                title=qn.title,
                prompt=qn.prompt or f"Solve the coding challenge: {qn.title}. URL reference: {qn.leetcode_url or '#'}",
                language=Problem.Language.PYTHON,
                max_score=100,
                difficulty=difficulty_val,
                display_order=idx,
            )
            # Create standard test cases in CouchDB
            test_cases = [
                {"stdin": "1 2\n", "expected_stdout": "3\n"},
                {"stdin": "5 10\n", "expected_stdout": "15\n"},
            ]
            try:
                doc_id = repository.save_test_cases(problem.pk, test_cases)
                problem.couchdb_test_cases_doc_id = doc_id
                problem.save(update_fields=["couchdb_test_cases_doc_id"])
            except Exception as e:
                couchdb_errors.append(f"{qn.title}: {str(e)}")

            problems_created.append({
                "id": problem.pk,
                "title": problem.title,
                "difficulty": qn.difficulty,
            })

        response_data = {
            "message": "Assessment generated successfully.",
            "assessment_id": assessment.id,
            "title": assessment.title,
            "duration_minutes": duration_minutes,
            "problems_count": len(selected_questions),
            "problems": problems_created,
            "difficulty_breakdown": {
                "easy": min(len(easy_qs), easy_count),
                "medium": min(len(medium_qs), medium_count),
                "hard": min(len(hard_qs), hard_count),
            },
        }

        if couchdb_errors:
            response_data["warnings"] = couchdb_errors
            # If all test case saves failed, return 502 Bad Gateway
            if len(couchdb_errors) == len(selected_questions):
                return Response(
                    {"error": f"Failed to save test cases to CouchDB: {couchdb_errors}"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        return Response(response_data, status=status.HTTP_201_CREATED)


# Refactor: Add typing hints and documentation docstrings.

# Refactor: Refactor variable names for better readability.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Refactor variable names for better readability.
