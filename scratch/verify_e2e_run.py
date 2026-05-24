import sys
import os
import django
import time
import uuid
import redis

def run():
    print("======================================================================")
    print("🚀 STARTING E2E VERIFICATION OF DTAE ECOSYSTEM AND STABILITY UPGRADE")
    print("======================================================================")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    from django.conf import settings
    settings.ALLOWED_HOSTS.append("testserver")

    # Import after Django setup
    from rest_framework.test import APIClient
    from apps.accounts.models import User, Role, Membership, VerificationToken, UserSession, AuditLog
    from apps.organizations.models import Organization
    from apps.assessments.models import Assessment, Problem, Submission
    from apps.dsa_intelligence.models import Company, Topic, DSAQuestion, QuestionCompanyFrequency, FrequencyBucket
    from apps.leaderboard.services import LeaderboardService

    # 1. Initialize Roles if not present
    candidate_role, _ = Role.objects.get_or_create(code="candidate", defaults={"description": "Candidate"})
    recruiter_role, _ = Role.objects.get_or_create(code="recruiter", defaults={"description": "Recruiter"})

    # Ensure unique emails
    recruiter_email = f"recruiter_{uuid.uuid4().hex[:6]}@e2etest.com"
    candidate_email = f"candidate_{uuid.uuid4().hex[:6]}@e2etest.com"
    org_name = f"E2E Corp {uuid.uuid4().hex[:6]}"

    print(f"Using Recruiter email: {recruiter_email}")
    print(f"Using Candidate email: {candidate_email}")
    print(f"Using Organization name: {org_name}")

    client = APIClient()

    # Step 1: Register Recruiter & Create Organization
    print("\n[Step 1] Registering recruiter account...")
    reg_data = {
        "email": recruiter_email,
        "password": "SecurePassword123!",
        "first_name": "E2E",
        "last_name": "Recruiter",
        "organization_name": org_name,
        "role": "recruiter",
    }
    response = client.post("/api/v1/auth/register/", reg_data, format="json")
    assert response.status_code == 201, f"Failed recruiter registration: {response.data}"
    print(f"✅ Recruiter registered successfully: {response.data['message']}")

    # Verify Recruiter Email
    recruiter_user = User.objects.get(email=recruiter_email)
    verify_token = VerificationToken.objects.get(user=recruiter_user, token_type=VerificationToken.TokenType.VERIFICATION)
    print(f"Verification token: {verify_token.token}")
    response = client.post("/api/v1/auth/verify-email/", {"token": verify_token.token}, format="json")
    assert response.status_code == 200, f"Email verification failed: {response.data}"
    recruiter_user.refresh_from_db()
    assert recruiter_user.is_email_verified is True, "User should be verified now"
    print("✅ Recruiter email verified successfully.")

    # Step 2: Recruiter Login
    print("\n[Step 2] Logging in as Recruiter...")
    response = client.post("/api/v1/auth/login/", {"email": recruiter_email, "password": "SecurePassword123!"}, format="json")
    assert response.status_code == 200, f"Login failed: {response.data}"
    recruiter_jwt_access = response.data["access"]
    print("✅ Login successful. Obtained JWT Access Token.")

    # Verify active sessions & audit logs
    sessions = UserSession.objects.filter(user=recruiter_user)
    assert sessions.exists(), "Recruiter session should be active"
    print(f"✅ Session audit active: device_info={sessions.first().device_info}, ip_address={sessions.first().ip_address}")
    audit_logs = AuditLog.objects.filter(user=recruiter_user)
    assert audit_logs.filter(action="login_success").exists(), "Audit log should track login success"
    print(f"✅ Audit Log matches: {list(audit_logs.values_list('action', flat=True))}")

    # Step 3: Register Candidate & Verify
    print("\n[Step 3] Registering candidate account...")
    reg_cand_data = {
        "email": candidate_email,
        "password": "SecurePassword123!",
        "first_name": "E2E",
        "last_name": "Candidate",
        "role": "candidate",
    }
    response = client.post("/api/v1/auth/register/", reg_cand_data, format="json")
    assert response.status_code == 201, f"Failed candidate registration: {response.data}"
    candidate_user = User.objects.get(email=candidate_email)
    cand_verify_token = VerificationToken.objects.get(user=candidate_user, token_type=VerificationToken.TokenType.VERIFICATION)
    response = client.post("/api/v1/auth/verify-email/", {"token": cand_verify_token.token}, format="json")
    assert response.status_code == 200
    candidate_user.refresh_from_db()
    assert candidate_user.is_email_verified is True
    print("✅ Candidate registered and email verified successfully.")

    # Candidate Login
    response = client.post("/api/v1/auth/login/", {"email": candidate_email, "password": "SecurePassword123!"}, format="json")
    assert response.status_code == 200
    candidate_jwt_access = response.data["access"]
    print("✅ Candidate logged in successfully.")

    # Step 4: Verify DSA Database Ingested questions count
    print("\n[Step 4] Checking ingested company DSA database...")
    companies_count = Company.objects.count()
    questions_count = DSAQuestion.objects.count()
    mappings_count = QuestionCompanyFrequency.objects.count()
    print(f"Database contains {companies_count} companies, {questions_count} questions, and {mappings_count} frequency mappings.")
    assert companies_count > 0, "No companies ingested! Ingestion pipeline has not been seeded."
    assert questions_count > 0, "No questions ingested!"

    # Step 5: Recruiter Smart Assessment Generation
    print("\n[Step 5] Recruiter generating a smart mock assessment round for Google...")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {recruiter_jwt_access}")
    company_slug = "google"
    google_comp = Company.objects.filter(slug=company_slug).first()
    if not google_comp:
        google_comp = Company.objects.create(name="Google", slug=company_slug)
        print("Google company model auto-created for generation fallback.")
    gen_payload = {
        "company_slug": company_slug,
        "frequency_bucket": "all",
        "easy_count": 1,
        "medium_count": 1,
        "hard_count": 0,
        "title": f"Google Mock E2E Round {uuid.uuid4().hex[:6]}",
    }
    response = client.post("/api/v1/dsa-intelligence/assessments/generate/", gen_payload, format="json")
    assert response.status_code == 201, f"Failed to generate assessment: {response.data}"
    assessment_id = response.data["assessment_id"]
    assessment_title = response.data["title"]
    print(f"✅ Generated Assessment ID: {assessment_id}, Title: '{assessment_title}'")

    # Step 6: Verify assessment and problems were created
    assessment_obj = Assessment.objects.get(pk=assessment_id)
    problems = list(assessment_obj.problems.all().order_by('display_order'))
    print(f"Assessment contains {len(problems)} problems:")
    for prob in problems:
        print(f"  - Problem ID {prob.id}: {prob.title} (Language: {prob.language}, Max Score: {prob.max_score})")
    assert len(problems) > 0, "No problems generated for the assessment!"

    # Add Candidate to organization
    recruiter_org = recruiter_user.memberships.first().organization
    Membership.objects.get_or_create(user=candidate_user, organization=recruiter_org, role=candidate_role)
    print(f"Candidate added to organization '{recruiter_org.name}'.")

    # Step 7: Candidate submits code to the assessment problems
    print("\n[Step 7] Candidate submitting solutions to problems...")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {candidate_jwt_access}")
    p1 = problems[0]
    print(f"Submitting code for Problem {p1.id} ({p1.title})...")
    source_code_correct = """
import sys
for line in sys.stdin:
    if line.strip():
        parts = line.strip().split()
        if len(parts) == 2:
            print(int(parts[0]) + int(parts[1]))
"""
    response = client.post(f"/api/v1/assessments/problems/{p1.id}/submissions/", {"source_code": source_code_correct}, format="json")
    assert response.status_code == 202, f"Failed to submit: {response.data}"
    submission_id = response.data["id"]
    print(f"✅ Submission created. ID: {submission_id}, Status: {response.data['status']}")

    # Wait for Celery worker
    print("Waiting for Celery worker docker sandbox evaluation...")
    sub_obj = Submission.objects.get(pk=submission_id)
    max_wait = 15
    while sub_obj.status in (Submission.Status.QUEUED, Submission.Status.RUNNING) and max_wait > 0:
        time.sleep(1)
        sub_obj.refresh_from_db()
        max_wait -= 1
    print(f"Evaluation complete. Final status: {sub_obj.status}, Score: {sub_obj.score}")
    assert sub_obj.status == Submission.Status.COMPLETED, f"Submission failed with status: {sub_obj.status}. Check worker logs."
    assert sub_obj.score == 100, f"Expected 100 points, got {sub_obj.score}."
    print("✅ Correct solution evaluated successfully with full score (100).")

    # Step 8: Incorrect solution submission
    print("\n[Step 8] Submitting an incorrect solution to verify max-score logic...")
    source_code_wrong = "print('wrong')"
    response = client.post(f"/api/v1/assessments/problems/{p1.id}/submissions/", {"source_code": source_code_wrong}, format="json")
    assert response.status_code == 202
    sub_wrong_id = response.data["id"]
    sub_wrong_obj = Submission.objects.get(pk=sub_wrong_id)
    max_wait = 15
    while sub_wrong_obj.status in (Submission.Status.QUEUED, Submission.Status.RUNNING) and max_wait > 0:
        time.sleep(1)
        sub_wrong_obj.refresh_from_db()
        max_wait -= 1
    print(f"Wrong submission complete. Final status: {sub_wrong_obj.status}, Score: {sub_wrong_obj.score}")
    assert sub_wrong_obj.status == Submission.Status.FAILED, "Expected failed status"
    assert sub_wrong_obj.score == 0, f"Expected 0 points, got {sub_wrong_obj.score}."

    # Step 9: Verify Leaderboard correctness
    print("\n[Step 9] Verifying real-time Leaderboard caching and correctness...")
    response = client.get(f"/api/v1/leaderboard/{assessment_id}/")
    assert response.status_code == 200, f"Leaderboard API failed: {response.data}"
    rankings = response.data
    print("Leaderboard API Response:")
    for rank in rankings:
        print(f"  Rank {rank['rank']}: Candidate #{rank['candidate_id']} - Total Score: {rank['total_score']} - Problems Solved: {rank['problems_solved']}")
    assert len(rankings) == 1
    assert rankings[0]["candidate_id"] == candidate_user.id
    assert rankings[0]["total_score"] == 100
    assert rankings[0]["problems_solved"] == 1
    print("✅ Leaderboard correctly aggregated max score of 100 and solved count 1.")

    # Check Redis cache directly
    r = redis.Redis.from_url(settings.REDIS_URL)
    zset_key = f"leaderboard:zset:{assessment_id}"
    solved_key = f"leaderboard:solved:{assessment_id}"
    redis_score = r.zscore(zset_key, str(candidate_user.id))
    redis_solved = int(r.hget(solved_key, str(candidate_user.id)) or 0)
    print(f"Redis cache values -> Score: {redis_score}, Solved: {redis_solved}")
    assert redis_score == 100, f"Expected score 100 in Redis, found {redis_score}"
    assert redis_solved == 1, f"Expected solved count 1 in Redis, found {redis_solved}"
    print("✅ Redis Sorted Set cache mirrors PostgreSQL truth successfully.")

    print("\n======================================================================")
    print("🎉 ALL E2E VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    run()
