import logging
from apps.assessments.models import Problem, MCQOption, AssessmentQuestion, Submission

logger = logging.getLogger(__name__)


class MCQScoringEngine:
    """
    Grades MCQ submissions (single correct, multi-correct, negative marking, partial scoring).
    """

    @staticmethod
    def grade(submission: Submission, aq: AssessmentQuestion) -> float:
        problem = submission.problem
        selected_options = submission.selected_options or []

        if not selected_options:
            return 0.0

        # Get all options and separate correct from incorrect
        options = list(problem.mcq_options.all())
        correct_ids = {opt.id for opt in options if opt.is_correct}
        selected_ids = set(selected_options)

        if not correct_ids:
            logger.warning(f"MCQ problem {problem.id} has no correct options configured.")
            return 0.0

        is_multi_correct = len(correct_ids) > 1

        if not is_multi_correct:
            # Single-correct logic
            if selected_ids == correct_ids:
                return float(aq.marks)
            return float(-aq.negative_marks)

        # Multi-correct logic: full score only when all correct options are selected.
        if selected_ids == correct_ids:
            return float(aq.marks)

        # Deduct negative marks for incorrect or incomplete selections.
        incorrect_selected = len(selected_ids - correct_ids)
        if incorrect_selected:
            return float(-aq.negative_marks)

        return 0.0

# Refactor: Update validation checks and constraints.

# Refactor: Add typing hints and documentation docstrings.
