"""Orchestrator for assessment session grading and report generation."""

from __future__ import annotations

import logging
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import (
    AssessmentInvitation,
    AssessmentQuestion,
    AssessmentReport,
    Problem,
    Submission,
)
from apps.leaderboard.services import LeaderboardService
from .mcq_engine import MCQScoringEngine
from .fib_engine import FIBScoringEngine
from .coding_engine import CodingScoringEngine

logger = logging.getLogger(__name__)
User = get_user_model()


class AssessmentEvaluator:
    """Evaluates candidate submissions and generates final assessment reports."""

    @staticmethod
    def grade_submission(submission: Submission) -> float:
        if submission.score is not None and submission.status == Submission.Status.COMPLETED:
            return float(submission.score)

        problem = submission.problem
        aq = submission.assessment_question
        if aq is None and problem.assessment_id is not None:
            aq = AssessmentQuestion.objects.filter(
                assessment_id=problem.assessment_id,
                problem=problem,
            ).first()
            if aq is None:
                aq = AssessmentQuestion.objects.create(
                    assessment_id=problem.assessment_id,
                    problem=problem,
                    display_order=problem.display_order,
                    marks=problem.max_score,
                    weight=1.0,
                )

        if aq is None:
            raise ValueError("AssessmentQuestion is required to grade a submission.")

        if problem.question_type == problem.QuestionType.MCQ:
            score = MCQScoringEngine.grade(submission, aq)
        elif problem.question_type == problem.QuestionType.FIB:
            score = FIBScoringEngine.grade(submission, aq)
        else:
            score = CodingScoringEngine.grade(submission, aq)

        submission.assessment_question = aq
        submission.score = score
        submission.status = Submission.Status.COMPLETED
        submission.completed_at = timezone.now()
        submission.save(update_fields=["assessment_question", "score", "status", "completed_at"])
        return score

    @staticmethod
    def grade_assessment_session(invitation: AssessmentInvitation) -> AssessmentReport:
        if invitation.user is None:
            invitation.user = User.objects.filter(email__iexact=invitation.email).first()
            if invitation.user:
                invitation.save(update_fields=["user"])

        if invitation.user is None:
            raise ValueError("Candidate user must exist to grade the assessment session.")

        assessment = invitation.assessment
        assessment_questions = list(
            assessment.assessment_questions.select_related("problem").all()
        )
        legacy_submissions = None
        if not assessment_questions:
            assessment_questions = [
                AssessmentQuestion(
                    assessment=assessment,
                    problem=problem,
                    marks=problem.max_score,
                    weight=1.0,
                    display_order=problem.display_order,
                )
                for problem in assessment.problems.all()
            ]
            legacy_submissions = Submission.objects.filter(
                candidate=invitation.user,
                problem__assessment=assessment,
                score__isnull=False,
            ).select_related("problem")
        else:
            legacy_submissions = Submission.objects.filter(
                candidate=invitation.user,
                assessment_question__in=[aq.pk for aq in assessment_questions if aq.pk],
                score__isnull=False,
            ).select_related("assessment_question", "problem")

        best_submission_by_aq: dict[int, Submission] = {}
        best_submission_by_problem_id: dict[int, Submission] = {}

        if assessment_questions and all(aq.pk for aq in assessment_questions):
            for submission in legacy_submissions.order_by("assessment_question_id", "-score"):
                if submission.assessment_question_id not in best_submission_by_aq:
                    best_submission_by_aq[submission.assessment_question_id] = submission
        else:
            for submission in legacy_submissions.order_by("problem_id", "-score"):
                if submission.problem_id not in best_submission_by_problem_id:
                    best_submission_by_problem_id[submission.problem_id] = submission

        section_scores: dict[str, float] = defaultdict(float)
        total_weighted = 0.0
        max_weighted = 0.0
        mcq_question_count = 0
        mcq_correct_count = 0

        for aq in assessment_questions:
            max_weighted += float(aq.marks) * float(aq.weight)
            best_submission = (
                best_submission_by_aq.get(aq.pk)
                if aq.pk
                else best_submission_by_problem_id.get(aq.problem_id)
            )
            score = 0.0
            if best_submission is not None:
                score = AssessmentEvaluator.grade_submission(best_submission)
            weighted = score * float(aq.weight)
            total_weighted += weighted
            section_scores[aq.section_name] += weighted

            if aq.problem.question_type == aq.problem.QuestionType.MCQ:
                mcq_question_count += 1
                if score >= float(aq.marks):
                    mcq_correct_count += 1

        percentage = (total_weighted / max_weighted * 100.0) if max_weighted else 0.0
        passed = percentage >= assessment.pass_threshold_percentage
        time_spent_seconds = 0
        if invitation.started_at and invitation.completed_at:
            time_spent_seconds = int(
                (invitation.completed_at - invitation.started_at).total_seconds()
            )

        with transaction.atomic():
            report, _ = AssessmentReport.objects.update_or_create(
                invitation=invitation,
                defaults={
                    "assessment": assessment,
                    "candidate": invitation.user,
                    "total_score": total_weighted,
                    "section_scores": section_scores,
                    "mcq_accuracy": (
                        mcq_correct_count / mcq_question_count
                        if mcq_question_count
                        else 0.0
                    ),
                    "time_spent_seconds": time_spent_seconds,
                    "proctoring_violations_count": 0,
                    "plagiarism_score": 0.0,
                    "passed": passed,
                },
            )

        try:
            LeaderboardService.upsert_entry(assessment.id, invitation.user.id)
        except Exception as exc:
            logger.warning("Leaderboard update failed during session grading: %s", exc)

        return report
