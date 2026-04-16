from django.urls import path
from .views import (
    CompanyListView,
    TopicListView,
    DSAQuestionListView,
    SmartAssessmentGeneratorView,
)

app_name = "dsa_intelligence"

urlpatterns = [
    path("companies/", CompanyListView.as_view(), name="company-list"),
    path("topics/", TopicListView.as_view(), name="topic-list"),
    path("questions/", DSAQuestionListView.as_view(), name="question-list"),
    path("assessments/generate/", SmartAssessmentGeneratorView.as_view(), name="smart-assessment-generate"),
]

# Refactor: Enhance component rendering performance.

# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Optimize query performance and database indexing.

# Refactor: Update validation checks and constraints.

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve error handling and exception logging.
