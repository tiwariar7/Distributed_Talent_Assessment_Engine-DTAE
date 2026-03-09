"""Serializers for execution log API responses."""

from rest_framework import serializers


class ExecutionLogEntrySerializer(serializers.Serializer):
    """One append-only event from the CouchDB execution log."""

    test_case_index = serializers.IntegerField(required=False)
    passed = serializers.BooleanField(required=False)
    exit_code = serializers.IntegerField(required=False)
    timed_out = serializers.BooleanField(required=False)
    stdout_preview = serializers.CharField(required=False)
    stderr_preview = serializers.CharField(required=False)


class ExecutionLogSerializer(serializers.Serializer):
    """Full execution log document metadata for a submission."""

    submission_id = serializers.IntegerField()
    couchdb_doc_id = serializers.CharField()
    entry_count = serializers.IntegerField()
    entries = ExecutionLogEntrySerializer(many=True)

# Refactor: Align with project code quality guidelines.

# Refactor: Add typing hints and documentation docstrings.
