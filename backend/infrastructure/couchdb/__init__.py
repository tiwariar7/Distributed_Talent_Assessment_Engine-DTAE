"""CouchDB document store with MVCC optimistic concurrency."""

from .client import CouchDBClient, DocumentConflictError
from .repository import DocumentRepository

__all__ = ("CouchDBClient", "DocumentConflictError", "DocumentRepository")
