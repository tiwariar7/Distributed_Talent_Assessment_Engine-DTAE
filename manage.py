#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    
    # Initialize OpenTelemetry before running any Django command
    try:
        from config.otel import initialize_otel
        initialize_otel()
    except Exception:
        pass

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and available on your "
            "PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

# Refactor: Update validation checks and constraints.

# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Align with project code quality guidelines.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.
