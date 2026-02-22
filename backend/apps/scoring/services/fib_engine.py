"""Scoring engine for Fill-in-the-Blank submissions."""

import logging
import re

from apps.assessments.models import Submission, AssessmentQuestion

logger = logging.getLogger(__name__)


class FIBScoringEngine:
    """Evaluates Fill in the Blank text inputs against configured rules."""

    @staticmethod
    def grade(submission: Submission, aq: AssessmentQuestion) -> float:
        if not submission.submitted_text:
            return 0.0

        response = submission.submitted_text.strip()
        if not response:
            return 0.0

        rules = list(submission.problem.fib_rules.all())
        if not rules:
            logger.warning(
                "FIB problem %s has no grading rules configured.",
                submission.problem_id,
            )
            return 0.0

        for rule in rules:
            acceptable = rule.acceptable_answer.strip()
            if rule.use_regex:
                try:
                    if re.fullmatch(acceptable, response):
                        return float(aq.marks)
                except re.error as exc:
                    logger.warning(
                        "Invalid regex for FIB rule %s: %s",
                        rule.pk,
                        exc,
                    )
                    continue
            else:
                if rule.case_sensitive:
                    matched = response == acceptable
                else:
                    matched = response.lower() == acceptable.lower()
                if matched:
                    return float(aq.marks)

        return float(-aq.negative_marks) if aq.negative_marks else 0.0

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.
