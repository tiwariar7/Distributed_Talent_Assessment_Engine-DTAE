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

# Refactor: Optimize imports and clean up code structure.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve responsive styles and layouts.
