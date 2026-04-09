"""
Low-level CouchDB HTTP client with MVCC conflict handling.

Race conditions on concurrent log appends are resolved via _rev tokens and
exponential backoff retries — no PostgreSQL or application-level locks.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings
from opentelemetry import trace

tracer = trace.get_tracer("dtae.couchdb")

logger = logging.getLogger(__name__)


class DocumentConflictError(Exception):
    """Raised when CouchDB returns HTTP 409 after all retry attempts."""


class CouchDBClient:
    """
    Thin wrapper around CouchDB REST API.

    Single Responsibility: transport and MVCC semantics only.
    """

    CONFLICT_STATUS = 409
    DEFAULT_MAX_RETRIES = 5
    BASE_BACKOFF_SECONDS = 0.05

    def __init__(
        self,
        base_url: str | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.COUCHDB_URL).rstrip("/")
        self.database = database or settings.COUCHDB_DATABASE
        self.session = requests.Session()
        self.session.auth = (
            username or settings.COUCHDB_USER,
            password or settings.COUCHDB_PASSWORD,
        )

    @property
    def db_url(self) -> str:
        """Fully qualified database URL."""
        return f"{self.base_url}/{self.database}"

    def ensure_database(self) -> None:
        """Create the database if it does not exist."""
        response = self.session.put(self.db_url)
        if response.status_code not in (201, 412):
            response.raise_for_status()

    def get_document(self, doc_id: str) -> dict[str, Any]:
        """Fetch a document including its current _rev."""
        with tracer.start_as_current_span("couchdb.get_document") as span:
            span.set_attribute("db.system", "couchdb")
            span.set_attribute("db.operation", "get")
            span.set_attribute("db.couchdb.document_id", doc_id)
            response = self.session.get(f"{self.db_url}/{doc_id}")
            response.raise_for_status()
            return response.json()

    def create_document(self, doc_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Create a new document with a server-assigned or client-provided id."""
        with tracer.start_as_current_span("couchdb.create_document") as span:
            span.set_attribute("db.system", "couchdb")
            span.set_attribute("db.operation", "create")
            span.set_attribute("db.couchdb.document_id", doc_id)
            payload = {**body, "_id": doc_id}
            response = self.session.put(f"{self.db_url}/{doc_id}", json=payload)
            if response.status_code == 409:
                return self.update_document(doc_id, body, rev=None)
            response.raise_for_status()
            return response.json()

    def update_document(
        self,
        doc_id: str,
        body: dict[str, Any],
        rev: str | None = None,
        max_retries: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a document using MVCC _rev, retrying on 409 Conflict.

        Multiple worker threads may append to the same execution log; each
        conflict triggers a re-read and merge before retry.
        """
        with tracer.start_as_current_span("couchdb.update_document") as span:
            span.set_attribute("db.system", "couchdb")
            span.set_attribute("db.operation", "update")
            span.set_attribute("db.couchdb.document_id", doc_id)
            retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
            attempt = 0
            
            while attempt <= retries:
                current_rev = rev
                if current_rev is None:
                    existing = self.get_document(doc_id)
                    current_rev = existing["_rev"]
                    merged_body = {**existing, **body}
                else:
                    merged_body = body

                merged_body["_id"] = doc_id
                merged_body["_rev"] = current_rev
                response = self.session.put(
                    f"{self.db_url}/{doc_id}",
                    json=merged_body,
                )

                if response.status_code != self.CONFLICT_STATUS:
                    response.raise_for_status()
                    return response.json()

                attempt += 1
                rev = None
                sleep_seconds = self.BASE_BACKOFF_SECONDS * (2**attempt)
                try:
                    from config.prometheus_middleware import COUCHDB_CONFLICT_RETRIES
                    COUCHDB_CONFLICT_RETRIES.inc()
                except Exception:
                    pass
                logger.warning(
                    "CouchDB 409 conflict on doc=%s attempt=%s; retrying in %.3fs",
                    doc_id,
                    attempt,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)

            raise DocumentConflictError(
                f"Exceeded {retries} retries for document '{doc_id}' due to MVCC conflicts."
            )

    def append_to_execution_log(
        self,
        doc_id: str,
        entry: dict[str, Any],
        max_retries: int | None = None,
    ) -> dict[str, Any]:
        """
        Append a structured log entry to an execution log document.

        Uses read-merge-write with _rev retry — the core concurrency pattern.
        """
        with tracer.start_as_current_span("couchdb.append_to_execution_log") as span:
            span.set_attribute("db.system", "couchdb")
            span.set_attribute("db.operation", "append_log")
            span.set_attribute("db.couchdb.document_id", doc_id)
            retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
            attempt = 0

            while attempt <= retries:
                try:
                    document = self.get_document(doc_id)
                except requests.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == 404:
                        return self.create_document(
                            doc_id,
                            {"type": "execution_log", "entries": [entry]},
                        )
                    raise

                entries = list(document.get("entries", []))
                entries.append(entry)
                update_body = {"entries": entries}

                response = self.session.put(
                    f"{self.db_url}/{doc_id}",
                    json={
                        **{k: v for k, v in document.items() if k.startswith("_")},
                        **update_body,
                    },
                )

                if response.status_code != self.CONFLICT_STATUS:
                    response.raise_for_status()
                    return response.json()

                attempt += 1
                try:
                    from config.prometheus_middleware import COUCHDB_CONFLICT_RETRIES
                    COUCHDB_CONFLICT_RETRIES.inc()
                except Exception:
                    pass
                time.sleep(self.BASE_BACKOFF_SECONDS * (2**attempt))

            raise DocumentConflictError(
                f"Log append failed for '{doc_id}' after {retries} conflict retries."
            )

    def query_view(
        self,
        design_doc: str,
        view_name: str,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Query a MapReduce view and return row objects."""
        with tracer.start_as_current_span("couchdb.query_view") as span:
            span.set_attribute("db.system", "couchdb")
            span.set_attribute("db.operation", "query")
            span.set_attribute("db.couchdb.design_document", design_doc)
            span.set_attribute("db.couchdb.view", view_name)
            url = f"{self.db_url}/_design/{design_doc}/_view/{view_name}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json().get("rows", [])

    def upsert_design_document(self, design_doc_id: str, views: dict[str, Any]) -> None:
        """Install or update a design document containing MapReduce views."""
        doc_id = f"_design/{design_doc_id}"
        body = {"views": views}
        try:
            existing = self.get_document(doc_id)
            body["_rev"] = existing["_rev"]
        except requests.HTTPError as exc:
            if exc.response is None or exc.response.status_code != 404:
                raise
        response = self.session.put(f"{self.db_url}/{doc_id}", json=body)
        response.raise_for_status()

# Refactor: Refactor variable names for better readability.
