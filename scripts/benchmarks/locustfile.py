import random
import string
from locust import HttpUser, task, between

class DtaeUser(HttpUser):
    """Simulates a candidate participating in a coding assessment."""

    wait_time = between(1, 3)

    def on_start(self):
        """Register a unique candidate user and log in to obtain JWT tokens."""
        # Generate random email to avoid collision
        rand_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.email = f"candidate_{rand_str}@example.com"
        self.password = "Secr3t_P@ssword!"
        self.org_slug = "demo-org"
        self.headers = {}
        self.access_token = None

        # 1. Register candidate
        response = self.client.post(
            "/api/v1/auth/register/",
            json={
                "email": self.email,
                "password": self.password,
                "first_name": "LoadTest",
                "last_name": "User",
                "organization_slug": self.org_slug,
                "role": "candidate",
            }
        )
        
        if response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access")
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            # Try to log in if registration failed (e.g. database pre-seeded)
            response = self.client.post(
                "/api/v1/auth/login/",
                json={
                    "email": self.email,
                    "password": self.password,
                }
            )
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get("access")
                self.headers = {"Authorization": f"Bearer {self.access_token}"}

    @task(3)
    def view_assessments(self):
        """Simulate candidate checking the assessment dashboard."""
        if self.headers:
            self.client.get("/api/v1/assessments/", headers=self.headers)

    @task(2)
    def check_problem_details(self):
        """Simulate candidate viewing problem statement details."""
        if self.headers:
            # Assuming problem ID 1 exists (pre-seeded)
            self.client.get("/api/v1/assessments/problems/1/", headers=self.headers)

    @task(1)
    def submit_code_solution(self):
        """Simulate candidate submitting code for execution."""
        if self.headers:
            source_code = (
                "import sys\n"
                "line = sys.stdin.read().strip()\n"
                "print(f'Hello {line}')\n"
            )
            # Assuming problem ID 1 exists
            response = self.client.post(
                "/api/v1/assessments/problems/1/submissions/",
                json={"source_code": source_code},
                headers=self.headers
            )
            if response.status_code == 202:
                submission = response.json()
                sub_id = submission.get("id")
                # Poll status a few times
                if sub_id:
                    for _ in range(3):
                        self.client.get(
                            f"/api/v1/executions/submissions/{sub_id}/status/",
                            headers=self.headers
                        )
