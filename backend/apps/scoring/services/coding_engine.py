"""Scoring engine wrapper for coding submissions."""

from apps.assessments.models import Submission, AssessmentQuestion


class CodingScoringEngine:
    """Resolves coding submission scores into assessment-weighted points."""

    @staticmethod
    def grade(submission: Submission, aq: AssessmentQuestion) -> float:
        if submission.score is None:
            return 0.0

        score = float(submission.score)
        return min(score, float(aq.marks) if aq.marks else score)
