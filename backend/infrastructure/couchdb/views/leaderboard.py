"""
MapReduce view definitions for the assessment leaderboard.

Scores are pre-aggregated in CouchDB to avoid expensive SQL JOINs at query time.
"""

LEADERBOARD_BY_ASSESSMENT_MAP = """
function(doc) {
  if (doc.type === 'leaderboard_entry' && doc.assessment_id && doc.candidate_id) {
    emit([doc.assessment_id, -doc.total_score, doc.candidate_id], {
      candidate_id: doc.candidate_id,
      total_score: doc.total_score,
      problems_solved: doc.problems_solved || 0
    });
  }
}
"""

LEADERBOARD_VIEWS = {
    "by_assessment": {
        "map": LEADERBOARD_BY_ASSESSMENT_MAP,
        "reduce": "_count",
    },
    "scores_by_assessment": {
        "map": LEADERBOARD_BY_ASSESSMENT_MAP,
    },
}

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Optimize query performance and database indexing.

# Refactor: Update validation checks and constraints.

# Refactor: Improve responsive styles and layouts.

# Refactor: Optimize query performance and database indexing.
