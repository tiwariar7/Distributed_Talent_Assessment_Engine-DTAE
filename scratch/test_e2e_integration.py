import os
import sys
import time
import requests

# Add backend root to path so we can query database helper for IDs
sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.assessments.models import Problem, MCQOption, FIBRule, Assessment, AssessmentInvitation
from django.utils import timezone
from datetime import timedelta

BASE_URL = "http://localhost:8000"

def run_e2e_test():
    print("==================================================")
    print("STARTING E2E INTEGRATION WALKTHROUGH TEST")
    print("==================================================")

    # Reset/Seed invitation to Pending state
    print("Resetting/Seeding invitation status to Pending...")
    try:
        user = get_user_model().objects.get(email="candidate@demo.test")
        assessment = Assessment.objects.get(pk=1)
        
        # Clean up any existing invitations or drafts or submissions for clean test
        AssessmentInvitation.objects.filter(email=user.email, assessment=assessment).delete()
        AssessmentInvitation.objects.filter(token="demo-candidate-token").delete()
        
        # Also clean up submissions and drafts for candidate for a clean sheet
        from apps.assessments.models import Submission, SubmissionDraft
        Submission.objects.filter(candidate=user).delete()
        SubmissionDraft.objects.filter(candidate=user).delete()

        demo_invite = AssessmentInvitation.objects.create(
            assessment=assessment,
            email=user.email,
            user=user,
            token="demo-candidate-token",
            expires_at=timezone.now() + timedelta(days=7),
            scheduled_start=timezone.now(),
            instructions="Please complete all sections. Ensure your webcam and screen sharing are active.",
            proctoring_required=True,
            status=AssessmentInvitation.InvitationStatus.PENDING,
            is_active=True
        )
        print("SUCCESS: Invitation reset to Pending.")
    except Exception as e:
        print(f"FAILED: Resetting invitation: {e}")
        return False

    # 1. CANDIDATE LOGIN
    print("\n[Step 1] Logging in as Candidate...")
    session = requests.Session()
    login_payload = {
        "email": "candidate@demo.test",
        "password": "DemoPass123!"
    }
    resp = session.post(f"{BASE_URL}/api/v1/auth/login/", json=login_payload)
    if resp.status_code != 200:
        print(f"FAILED: login status {resp.status_code}, response: {resp.text}")
        return False
    
    login_data = resp.json()
    if not login_data.get("success"):
        print(f"FAILED: success was False: {login_data}")
        return False
    
    access_token = login_data["data"]["access"]
    print("SUCCESS: Candidate logged in.")
    print(f"  Access Token (truncated): {access_token[:50]}...")
    print(f"  Set-Cookie headers: {resp.headers.get('Set-Cookie', 'None')}")

    # Set Auth Header for candidate session
    session.headers.update({"Authorization": f"Bearer {access_token}"})

    # 2. FETCH INVITATIONS
    print("\n[Step 2] Fetching Candidate Invitations...")
    resp = session.get(f"{BASE_URL}/api/v1/assessments/candidate/invitations/")
    if resp.status_code != 200:
        print(f"FAILED: list invitations: {resp.text}")
        return False
    
    invitations_data = resp.json()
    print(f"SUCCESS: Retrieved invitations. Code: {resp.status_code}")
    print(f"  Total invitations: {len(invitations_data['data'])}")
    
    demo_invite_item = None
    for invite in invitations_data["data"]:
        if invite["token"] == "demo-candidate-token":
            demo_invite_item = invite
            break
            
    if not demo_invite_item:
        print("FAILED: demo-candidate-token not found in invitations list.")
        return False
        
    print(f"  Found invitation ID: {demo_invite_item['id']}")
    print(f"  Assessment Title: {demo_invite_item['assessment']['title']}")
    print(f"  Status: {demo_invite_item['status']}")

    assessment_id = demo_invite_item["assessment"]["id"]

    # 3. START ASSESSMENT
    print("\n[Step 3] Starting timed assessment...")
    start_payload = {"token": "demo-candidate-token"}
    resp = session.post(f"{BASE_URL}/api/v1/assessments/candidate/{assessment_id}/start/", json=start_payload)
    if resp.status_code != 200:
        print(f"FAILED: starting assessment: {resp.text}")
        return False
    print("SUCCESS: Started assessment status updated to 'Started'.")

    # 4. FETCH ASSESSMENT DETAILS
    print("\n[Step 4] Fetching assessment details...")
    resp = session.get(f"{BASE_URL}/api/v1/assessments/candidate/{assessment_id}/")
    if resp.status_code != 200:
        print(f"FAILED: fetching assessment details: {resp.text}")
        return False
    
    assessment_details = resp.json()["data"]
    problems = assessment_details["problems"]
    print(f"SUCCESS: Retrieved {len(problems)} problems.")
    
    # 5. ATTEMPT PROBLEMS
    print("\n[Step 5] Auto-saving and submitting answers...")
    for problem in problems:
        p_id = problem["id"]
        p_type = problem["question_type"]
        p_title = problem["title"]
        print(f"\n--- Problem {p_id}: {p_title} ({p_type}) ---")

        if p_type == "mcq":
            # Let's check correctness using django database options
            options = MCQOption.objects.filter(problem_id=p_id)
            correct_option_ids = list(options.filter(is_correct=True).values_list("id", flat=True))
            
            # Save Draft
            draft_payload = {"selected_options": correct_option_ids}
            draft_resp = session.post(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/autosave/", json=draft_payload)
            print(f"  Autosave draft status: {draft_resp.status_code}")
            
            # Submit Answer
            submit_payload = {"selected_options": correct_option_ids}
            submit_resp = session.post(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/submissions/", json=submit_payload)
            if submit_resp.status_code != 200:
                print(f"  FAILED: submission status {submit_resp.status_code}: {submit_resp.text}")
                return False
            
            sub_data = submit_resp.json()["data"]
            print(f"  SUBMISSION SUCCESS. Score: {sub_data['score']} / {problem['max_score']}")

        elif p_type == "fib":
            # Fetch rule acceptable answer
            fib_rule = FIBRule.objects.filter(problem_id=p_id).first()
            ans = fib_rule.acceptable_answer if fib_rule else "stack"

            # Save Draft
            draft_payload = {"submitted_text": ans}
            draft_resp = session.post(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/autosave/", json=draft_payload)
            print(f"  Autosave draft status: {draft_resp.status_code}")

            # Submit Answer
            submit_payload = {"submitted_text": ans}
            submit_resp = session.post(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/submissions/", json=submit_payload)
            if submit_resp.status_code != 200:
                print(f"  FAILED: submission status {submit_resp.status_code}: {submit_resp.text}")
                return False

            sub_data = submit_resp.json()["data"]
            print(f"  SUBMISSION SUCCESS. Score: {sub_data['score']} / {problem['max_score']}")

        elif p_type == "coding":
            # Code to sum two numbers read from stdin
            code = (
                "import sys\n"
                "try:\n"
                "    val1 = int(sys.stdin.readline().strip())\n"
                "    val2 = int(sys.stdin.readline().strip())\n"
                "    print(val1 + val2)\n"
                "except Exception:\n"
                "    pass\n"
            )

            # Save Draft
            draft_payload = {"source_code": code}
            draft_resp = session.post(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/autosave/", json=draft_payload)
            print(f"  Autosave draft status: {draft_resp.status_code}")

            # Submit Solution (Coding gets queued for docker compilation and execution)
            submit_payload = {"source_code": code}
            submit_resp = session.post(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/submissions/", json=submit_payload)
            if submit_resp.status_code != 202:
                print(f"  FAILED: submission status {submit_resp.status_code}: {submit_resp.text}")
                return False

            sub_data = submit_resp.json()["data"]
            sub_id = sub_data["id"]
            print(f"  SUBMISSION ACCEPTED (ID: {sub_id}). Queued status: {sub_data['status']}")

            # Wait for execution evaluation in worker container (poll a few times)
            print("  Waiting for execution worker to evaluate code...")
            for i in range(10):
                time.sleep(2)
                hist_resp = session.get(f"{BASE_URL}/api/v1/assessments/problems/{p_id}/submissions/")
                if hist_resp.status_code == 200:
                    hist_data = hist_resp.json()["data"]
                    matching_sub = next((s for s in hist_data if s["id"] == sub_id), None)
                    if matching_sub:
                        print(f"    Check status: {matching_sub['status']} (Score: {matching_sub['score']})")
                        if matching_sub["status"] in ["completed", "failed"]:
                            print(f"  CODING EVALUATION COMPLETED. Final Score: {matching_sub['score']} / {problem['max_score']}")
                            break
                else:
                    print(f"    Error polling status: {hist_resp.text}")

    # 6. FINISH ASSESSMENT
    print("\n[Step 6] Completing the timed assessment...")
    finish_payload = {"token": "demo-candidate-token"}
    resp = session.post(f"{BASE_URL}/api/v1/assessments/candidate/{assessment_id}/finish/", json=finish_payload)
    if resp.status_code != 200:
        print(f"FAILED: completing assessment: {resp.text}")
        return False
    print("SUCCESS: Finished assessment.")
    print(f"  Response: {resp.json()}")

    # 7. RECRUITER VALIDATION
    print("\n[Step 7] Logging in as Recruiter to verify proctoring & scores...")
    recruiter_session = requests.Session()
    login_payload = {
        "email": "recruiter@demo.test",
        "password": "DemoPass123!"
    }
    resp = recruiter_session.post(f"{BASE_URL}/api/v1/auth/login/", json=login_payload)
    if resp.status_code != 200:
        print(f"FAILED: Recruiter login status {resp.status_code}: {resp.text}")
        return False
    
    rec_login_data = resp.json()
    rec_access_token = rec_login_data["data"]["access"]
    recruiter_session.headers.update({"Authorization": f"Bearer {rec_access_token}"})
    print("SUCCESS: Recruiter logged in.")

    # Fetch recruiter invitations view or submissions
    print("Fetching invitation details from recruiter endpoint...")
    resp = recruiter_session.get(f"{BASE_URL}/api/v1/recruiter/assessments/{assessment_id}/invitations/")
    if resp.status_code == 200:
        print("SUCCESS: Retrieved recruiter invitation dashboard data.")
        invites_list = resp.json()['data']
        matching_invite = next((inv for inv in invites_list if inv['id'] == str(demo_invite.id)), None)
        if matching_invite:
            print(f"  Candidate Email: {matching_invite['email']}")
            print(f"  Completion Status: {matching_invite['status']}")
            print(f"  Webcam / Proctoring required: {matching_invite['proctoring_required']}")
        else:
            print("  Could not find candidate invitation in recruiter list.")
    else:
        print(f"FAILED: recruiter invitations check: {resp.text}")
        return False

    print("\n==================================================")
    print("E2E INTEGRATION WALKTHROUGH COMPLETED SUCCESSFULLY!")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = run_e2e_test()
    if not success:
        sys.exit(1)
