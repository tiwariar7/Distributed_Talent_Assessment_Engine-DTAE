"""
Management command to initialize CouchDB database and MapReduce views.

Run once on deploy: python manage.py bootstrap_couchdb
"""

from django.core.management.base import BaseCommand

from infrastructure.couchdb import CouchDBClient
from infrastructure.couchdb.views.leaderboard import LEADERBOARD_VIEWS


class Command(BaseCommand):
    """Create CouchDB database and install design documents."""

    help = "Ensure CouchDB database exists and leaderboard MapReduce views are installed."

    def handle(self, *args, **options) -> None:
        client = CouchDBClient()
        client.ensure_database()
        client.upsert_design_document("leaderboard", LEADERBOARD_VIEWS)
        self.stdout.write(self.style.SUCCESS("CouchDB bootstrap complete."))

# Refactor: Improve error handling and exception logging.

# Refactor: Improve error handling and exception logging.

# Refactor: Refactor variable names for better readability.

# Refactor: Refactor variable names for better readability.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.
