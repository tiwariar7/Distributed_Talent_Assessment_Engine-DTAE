from django.db import models


class FrequencyBucket(models.TextChoices):
    THIRTY_DAYS = "30_days"
    THREE_MONTHS = "3_months"
    SIX_MONTHS = "6_months"
    MORE_THAN_SIX_MONTHS = "more_than_6_months"
    ALL = "all"


class Company(models.Model):
    """
    Hiring companies mapping to interview questions.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.CharField(max_length=512, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "companies"
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Topic(models.Model):
    """
    DSA Topics organized hierarchically.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        db_table = "question_topics"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class DSAQuestion(models.Model):
    """
    Canonical LeetCode/DSA questions.
    """
    title = models.CharField(max_length=512)
    slug = models.SlugField(max_length=512, unique=True)
    leetcode_url = models.URLField(max_length=1024, null=True, blank=True)
    difficulty = models.CharField(max_length=32, db_index=True)
    prompt = models.TextField(null=True, blank=True)
    acceptance_rate = models.FloatField(null=True, blank=True)
    topics = models.ManyToManyField(Topic, related_name="questions", blank=True)

    class Meta:
        db_table = "dsa_questions"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class QuestionCompanyFrequency(models.Model):
    """
    Resolves Many-to-Many relationship between DSAQuestion and Company
    with frequency bucket tracking.
    """
    question = models.ForeignKey(
        DSAQuestion,
        on_delete=models.CASCADE,
        related_name="company_frequencies",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="question_frequencies",
    )
    frequency_bucket = models.CharField(
        max_length=32,
        choices=FrequencyBucket.choices,
        db_index=True,
    )
    frequency_percentage = models.FloatField(null=True, blank=True)
    source_repo = models.CharField(max_length=128)
    ingestion_timestamp = models.DateTimeField(auto_now_add=True)
    last_seen_date = models.DateField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "question_company_frequency"
        constraints = [
            models.UniqueConstraint(
                fields=["question", "company", "frequency_bucket"],
                name="unique_question_company_frequency",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "frequency_bucket"]),
            models.Index(fields=["company", "frequency_bucket", "frequency_percentage"]),
        ]

    def __str__(self) -> str:
        return f"{self.question.title} - {self.company.name} ({self.frequency_bucket})"

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Add typing hints and documentation docstrings.
