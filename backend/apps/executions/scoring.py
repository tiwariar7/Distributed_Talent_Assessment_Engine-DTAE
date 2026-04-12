"""
Points Engine — determines how many leaderboard points a submission earns.

Scoring formula:
  base_points  = difficulty_base * (passed_cases / total_cases)
  speed_bonus  = floor(difficulty_base * 0.20 * speed_factor)   [only on full pass]
  total        = base_points + speed_bonus

Difficulty bases:
  Easy   → 100 pts
  Medium → 200 pts
  Hard   → 300 pts

Speed bonus:
  Awarded only when ALL test cases pass.
  speed_factor = max(0, 1 - elapsed_seconds / time_budget_seconds)
  time_budget  = problem.time_limit_ms * total_cases / 1000   (capped at 60s)

This module is pure-Python with no I/O so it is trivially unit-testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

DIFFICULTY_BASE: dict[str, int] = {
    "easy":   100,
    "medium": 200,
    "hard":   300,
}

DEFAULT_BASE = 100   # fallback if difficulty unknown
SPEED_BONUS_FRACTION = 0.20   # 20% of base as max speed bonus
MIN_TIME_BUDGET_SECONDS = 5.0
MAX_TIME_BUDGET_SECONDS = 60.0


@dataclass(frozen=True)
class ScoringResult:
    base_points: int
    speed_bonus: int
    total_points: int
    passed_cases: int
    total_cases: int
    difficulty: str
    perfect: bool


def calculate_score(
    *,
    difficulty: str,           # "easy" / "medium" / "hard" (case-insensitive)
    passed_cases: int,
    total_cases: int,
    elapsed_seconds: float,
    time_limit_ms: int = 2000, # per-test-case time limit from Problem model
    max_score_override: int | None = None,  # if set, use problem.max_score directly
) -> ScoringResult:
    """
    Compute the final score for a submission.

    Parameters
    ----------
    difficulty        : Problem difficulty label.
    passed_cases      : Number of test cases that passed.
    total_cases       : Total test cases evaluated.
    elapsed_seconds   : Wall-clock time the full evaluation took.
    time_limit_ms     : Per-case time limit (ms) from the Problem model.
    max_score_override: If the problem has a custom max_score, use it as the base.
    """
    total_cases = max(total_cases, 1)

    # Determine base
    if max_score_override is not None:
        base = max_score_override
    else:
        base = DIFFICULTY_BASE.get(difficulty.lower(), DEFAULT_BASE)

    # Partial credit proportional to cases passed
    pass_ratio = passed_cases / total_cases
    base_points = math.floor(base * pass_ratio)

    # Speed bonus — only on perfect run
    speed_bonus = 0
    perfect = passed_cases == total_cases
    if perfect and elapsed_seconds >= 0:
        # time budget = total_cases * per_case_limit, clamped
        time_budget = total_cases * (time_limit_ms / 1000.0)
        time_budget = max(MIN_TIME_BUDGET_SECONDS, min(time_budget, MAX_TIME_BUDGET_SECONDS))
        speed_factor = max(0.0, 1.0 - elapsed_seconds / time_budget)
        speed_bonus = math.floor(base * SPEED_BONUS_FRACTION * speed_factor)

    total_points = base_points + speed_bonus

    return ScoringResult(
        base_points=base_points,
        speed_bonus=speed_bonus,
        total_points=total_points,
        passed_cases=passed_cases,
        total_cases=total_cases,
        difficulty=difficulty.lower(),
        perfect=perfect,
    )

# Refactor: Refactor variable names for better readability.

# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.
