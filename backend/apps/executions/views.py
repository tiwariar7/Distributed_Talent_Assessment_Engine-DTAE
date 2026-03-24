"""REST views for polling submission execution status and logs."""

from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.models import Submission
from apps.assessments.serializers import SubmissionSerializer
from infrastructure.couchdb import DocumentRepository

from .serializers import ExecutionLogSerializer


class SubmissionStatusView(generics.RetrieveAPIView):
    """Return current submission status and score from PostgreSQL."""

    serializer_class = SubmissionSerializer

    def get_queryset(self):
        return Submission.objects.filter(candidate=self.request.user)


class SubmissionExecutionLogView(APIView):
    """
    Return the CouchDB execution log for a submission.

    Candidates may only read their own logs. Hidden test case inputs are never
    included — only per-case results and output previews.
    """

    def get(self, request: Request, pk: int) -> Response:
        """Fetch append-only log entries from CouchDB."""
        submission = generics.get_object_or_404(
            Submission.objects.filter(candidate=request.user),
            pk=pk,
        )
        if not submission.couchdb_execution_log_doc_id:
            return Response(
                {"detail": "Execution log not yet created."},
                status=status.HTTP_404_NOT_FOUND,
            )

        repository = DocumentRepository()
        entries = repository.get_execution_log_entries(
            submission.couchdb_execution_log_doc_id,
        )

        serializer = ExecutionLogSerializer(
            {
                "submission_id": submission.pk,
                "couchdb_doc_id": submission.couchdb_execution_log_doc_id,
                "entry_count": len(entries),
                "entries": entries,
            },
        )
        return Response(serializer.data)

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Refactor variable names for better readability.

# Refactor: Refactor variable names for better readability.

# Refactor: Align with project code quality guidelines.
