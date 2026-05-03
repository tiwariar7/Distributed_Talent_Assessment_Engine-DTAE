"""Unit tests for CouchDB MVCC conflict handling."""

from unittest.mock import MagicMock

import pytest
import responses

from infrastructure.couchdb.client import CouchDBClient, DocumentConflictError


@pytest.fixture
def couch_client() -> CouchDBClient:
    """Client pointed at a mock CouchDB base URL."""
    return CouchDBClient(
        base_url="http://couchdb.test:5984",
        database="test_db",
        username="admin",
        password="secret",
    )


@responses.activate
def test_append_execution_log_retries_on_conflict(couch_client: CouchDBClient) -> None:
    """A 409 on PUT triggers a re-read and successful retry."""
    doc_id = "execution_log_99"
    base = couch_client.db_url

    responses.add(
        responses.GET,
        f"{base}/{doc_id}",
        json={"_id": doc_id, "_rev": "1-aaa", "type": "execution_log", "entries": []},
        status=200,
    )
    responses.add(
        responses.PUT,
        f"{base}/{doc_id}",
        json={"error": "conflict", "reason": "Document update conflict"},
        status=409,
    )
    responses.add(
        responses.GET,
        f"{base}/{doc_id}",
        json={
            "_id": doc_id,
            "_rev": "1-bbb",
            "type": "execution_log",
            "entries": [{"event": "prior"}],
        },
        status=200,
    )
    responses.add(
        responses.PUT,
        f"{base}/{doc_id}",
        json={"_id": doc_id, "_rev": "2-ccc", "ok": True},
        status=201,
    )

    result = couch_client.append_to_execution_log(
        doc_id,
        {"event": "worker-1"},
        max_retries=3,
    )

    assert result["ok"] is True
    assert len(responses.calls) == 4


@responses.activate
def test_update_document_raises_after_max_retries(couch_client: CouchDBClient) -> None:
    """Exhausted retries surface DocumentConflictError."""
    doc_id = "leaderboard_1_2"
    base = couch_client.db_url

    for _ in range(6):
        responses.add(
            responses.GET,
            f"{base}/{doc_id}",
            json={"_id": doc_id, "_rev": "1-x", "total_score": 10},
            status=200,
        )
        responses.add(
            responses.PUT,
            f"{base}/{doc_id}",
            json={"error": "conflict"},
            status=409,
        )

    with pytest.raises(DocumentConflictError):
        couch_client.update_document(doc_id, {"total_score": 20}, max_retries=2)


def test_create_document_on_409_delegates_to_update(couch_client: CouchDBClient) -> None:
    """Creating an existing document falls back to MVCC update."""
    couch_client.session = MagicMock()
    put_response = MagicMock(status_code=409)
    couch_client.session.put.return_value = put_response
    couch_client.update_document = MagicMock(return_value={"ok": True})

    result = couch_client.create_document("doc-1", {"type": "test"})

    assert result == {"ok": True}
    couch_client.update_document.assert_called_once()

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.
