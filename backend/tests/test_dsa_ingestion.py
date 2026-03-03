import pytest
from apps.dsa_intelligence.management.commands.ingest_dsa_questions import Command


def test_title_normalization():
    cmd = Command()
    assert cmd.normalize_title("Two Sum") == "two-sum"
    assert cmd.normalize_title("two-sum") == "two-sum"
    assert cmd.normalize_title("Two Sum LC") == "two-sum"
    assert cmd.normalize_title("Two Sum LeetCode") == "two-sum"
    assert cmd.normalize_title("Longest Substring Without Repeating Characters (Medium)") == "longest-substring-without-repeating-characters-medium"
    assert cmd.normalize_title("  3Sum   ") == "3sum"


def test_float_parsing():
    cmd = Command()
    assert cmd.parse_float("57.1%") == 57.1
    assert cmd.parse_float("0.557769903") == 0.557769903
    assert cmd.parse_float("100.0%") == 100.0
    assert cmd.parse_float("0.0") == 0.0
    assert cmd.parse_float("") == 0.0

# Refactor: Enhance component rendering performance.

# Refactor: Optimize imports and clean up code structure.
