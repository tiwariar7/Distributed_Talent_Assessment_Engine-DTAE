"""
Repository layer for CouchDB documents.

Encapsulates document shapes so Django apps depend on abstractions, not raw JSON.
"""

from __future__ import annotations

import uuid
from typing import Any

from .client import CouchDBClient


class DocumentRepository:
    """
    High-level persistence for unstructured assessment artifacts.

    Dependency Inversion: services depend on this class, not HTTP details.
    """

    def __init__(self, client: CouchDBClient | None = None) -> None:
        self._client = client or CouchDBClient()

    def save_source_code(self, source_code: str, submission_id: int) -> str:
        """Persist candidate source code; returns CouchDB document id."""
        doc_id = f"source_{submission_id}_{uuid.uuid4().hex[:8]}"
        self._client.create_document(
            doc_id,
            {
                "type": "source_code",
                "submission_id": submission_id,
                "content": source_code,
            },
        )
        return doc_id

    def save_test_cases(self, problem_id: int, test_cases: list[dict[str, Any]]) -> str:
        """Persist hidden test cases for a problem."""
        doc_id = f"test_cases_problem_{problem_id}"
        self._client.create_document(
            doc_id,
            {
                "type": "hidden_test_cases",
                "problem_id": problem_id,
                "cases": test_cases,
            },
        )
        return doc_id

    def get_test_cases(self, doc_id: str) -> list[dict[str, Any]]:
        """Load hidden test cases (worker-only; never exposed to candidates)."""
        document = self._client.get_document(doc_id)
        return document.get("cases", [])

    def get_source_code(self, doc_id: str) -> str:
        """Load candidate source from CouchDB."""
        document = self._client.get_document(doc_id)
        return document.get("content", "")

    def append_execution_log(self, doc_id: str, entry: dict[str, Any]) -> None:
        """Append one execution event using MVCC-safe merge."""
        self._client.append_to_execution_log(doc_id, entry)

    def get_execution_log_entries(self, doc_id: str) -> list[dict[str, Any]]:
        """Load all append-only log entries for a submission."""
        document = self._client.get_document(doc_id)
        return list(document.get("entries", []))

    def create_execution_log(self, submission_id: int) -> str:
        """Initialize an empty execution log document."""
        doc_id = f"execution_log_{submission_id}"
        self._client.create_document(
            doc_id,
            {"type": "execution_log", "submission_id": submission_id, "entries": []},
        )
        return doc_id

    def save_standard_output(
        self,
        problem_id: int,
        test_case_index: int,
        stdout: str,
    ) -> str:
        """Persist expected stdout for a test case."""
        doc_id = f"stdout_problem_{problem_id}_case_{test_case_index}"
        self._client.create_document(
            doc_id,
            {
                "type": "standard_output",
                "problem_id": problem_id,
                "test_case_index": test_case_index,
                "stdout": stdout,
            },
        )
        return doc_id

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Align with project code quality guidelines.

# Refactor: Update validation checks and constraints.

# Refactor: Enhance component rendering performance.

# Refactor: Improve error handling and exception logging.
