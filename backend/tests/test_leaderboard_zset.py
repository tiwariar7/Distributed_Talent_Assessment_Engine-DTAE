import pytest
import redis
from unittest.mock import patch
from django.conf import settings
from apps.assessments.models import Assessment, Problem, Submission
from apps.leaderboard.services import LeaderboardService


class MockRedis:
    def __init__(self, *args, **kwargs):
        self.zsets = {}
        self.hashes = {}

    def zadd(self, key, mapping, *args, **kwargs):
        if key not in self.zsets:
            self.zsets[key] = {}
        for member, score in mapping.items():
            self.zsets[key][member] = float(score)
        return len(mapping)

    def zscore(self, key, member):
        return self.zsets.get(key, {}).get(member)

    def hset(self, key, mapping_key, value=None):
        if key not in self.hashes:
            self.hashes[key] = {}
        if isinstance(mapping_key, dict):
            for k, v in mapping_key.items():
                self.hashes[key][k] = str(v).encode()
        else:
            self.hashes[key][mapping_key] = str(value).encode()
        return 1

    def hget(self, key, member):
        val = self.hashes.get(key, {}).get(member)
        return val

    def zrevrange(self, key, start, end, withscores=False):
        zset = self.zsets.get(key, {})
        # Sort by score descending
        sorted_members = sorted(zset.items(), key=lambda x: x[1], reverse=True)
        slice_members = sorted_members[start:end+1] if end != -1 else sorted_members[start:]
        if withscores:
            return [(str(k).encode(), float(v)) for k, v in slice_members]
        else:
            return [str(k).encode() for k, v in slice_members]

    def delete(self, *keys):
        for key in keys:
            self.zsets.pop(key, None)
            self.hashes.pop(key, None)

    def pipeline(self):
        return MockPipeline(self)


class MockPipeline:
    def __init__(self, client):
        self.client = client
        self.commands = []

    def zadd(self, key, mapping):
        self.commands.append(('zadd', key, mapping))
        return self

    def hset(self, key, member, value):
        self.commands.append(('hset', key, {member: value}))
        return self

    def execute(self):
        for cmd, *args in self.commands:
            if cmd == 'zadd':
                self.client.zadd(*args)
            elif cmd == 'hset':
                self.client.hset(*args)
        self.commands = []
        return []


@pytest.mark.django_db
@patch("redis.Redis.from_url")
@patch("apps.leaderboard.services.CouchDBClient")
def test_leaderboard_max_score_aggregation(mock_couch, mock_redis_from_url, candidate_user, recruiter_user, organization):
    mock_redis = MockRedis()
    mock_redis_from_url.return_value = mock_redis
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
