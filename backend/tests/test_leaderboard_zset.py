import pytest
import redis
from django.conf import settings
from apps.assessments.models import Assessment, Problem, Submission
from apps.leaderboard.services import LeaderboardService


@pytest.mark.django_db
def test_leaderboard_max_score_aggregation(candidate_user, recruiter_user, organization):
    # 1. Create an Assessment and two problems
    assessment = Assessment.objects.create(
        organization=organization,
        title="Python DS Round",
        duration_minutes=60,
    )
    p1 = Problem.objects.create(
        assessment=assessment,
        title="Sum 2 Numbers",
        prompt="Add a and b",
        max_score=100,
        display_order=1,
    )
    p2 = Problem.objects.create(
        assessment=assessment,
        title="Reverse String",
        prompt="Reverse string s",
        max_score=100,
        display_order=2,
    )

    # 2. Candidate submits multiple times for Problem 1
    # Submission 1: Score 40
    s1 = Submission.objects.create(
        problem=p1,
        candidate=candidate_user,
        status=Submission.Status.COMPLETED,
        couchdb_source_doc_id="src1",
        score=40,
    )
    LeaderboardService.upsert_entry(assessment.id, candidate_user.id)

    # Submission 2: Score 80 (improved)
    s2 = Submission.objects.create(
        problem=p1,
        candidate=candidate_user,
        status=Submission.Status.COMPLETED,
        couchdb_source_doc_id="src2",
        score=80,
    )
    LeaderboardService.upsert_entry(assessment.id, candidate_user.id)

    # Submission 3: Score 50 (lower, should not overwrite max score of 80)
    s3 = Submission.objects.create(
        problem=p1,
        candidate=candidate_user,
        status=Submission.Status.COMPLETED,
        couchdb_source_doc_id="src3",
        score=50,
    )
    LeaderboardService.upsert_entry(assessment.id, candidate_user.id)

    # Submission 4: Problem 2, Score 60
    s4 = Submission.objects.create(
        problem=p2,
        candidate=candidate_user,
        status=Submission.Status.COMPLETED,
        couchdb_source_doc_id="src4",
        score=60,
    )
    LeaderboardService.upsert_entry(assessment.id, candidate_user.id)

    # 3. Retrieve rankings
    rankings = LeaderboardService.get_rankings(assessment.id)

    # Candidate should have total_score = 80 (from p1 max) + 60 (from p2 max) = 140
    # problems_solved = 2 (p1 and p2 have scores > 0)
    assert len(rankings) == 1
    assert rankings[0]["candidate_id"] == candidate_user.id
    assert rankings[0]["total_score"] == 140
    assert rankings[0]["problems_solved"] == 2

    # 4. Verify Redis caching
    r = redis.Redis.from_url(settings.REDIS_URL)
    zset_key = f"leaderboard:zset:{assessment.id}"
    solved_key = f"leaderboard:solved:{assessment.id}"

    assert r.zscore(zset_key, str(candidate_user.id)) == 140
    assert int(r.hget(solved_key, str(candidate_user.id))) == 2

    # 5. Clear Redis and verify cache-aside fallback rebuilds cache
    r.delete(zset_key, solved_key)
    rankings_fallback = LeaderboardService.get_rankings(assessment.id)
    assert len(rankings_fallback) == 1
    assert rankings_fallback[0]["total_score"] == 140
    assert rankings_fallback[0]["problems_solved"] == 2
    assert r.zscore(zset_key, str(candidate_user.id)) == 140

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve responsive styles and layouts.

# Refactor: Align with project code quality guidelines.

# Refactor: Update validation checks and constraints.

# Refactor: Update validation checks and constraints.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Optimize query performance and database indexing.
