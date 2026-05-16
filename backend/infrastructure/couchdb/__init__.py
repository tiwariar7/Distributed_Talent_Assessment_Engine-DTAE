"""CouchDB document store with MVCC optimistic concurrency."""

from .client import CouchDBClient, DocumentConflictError
from .repository import DocumentRepository

__all__ = ("CouchDBClient", "DocumentConflictError", "DocumentRepository")

# Refactor: Enhance component rendering performance.

# Refactor: Improve error handling and exception logging.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Update validation checks and constraints.
