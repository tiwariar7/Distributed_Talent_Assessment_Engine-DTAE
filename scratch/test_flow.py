import requests

BASE_URL = "http://localhost"

def test_recruiter_flow():
    # 1. Login as recruiter
    login_url = f"{BASE_URL}/api/v1/auth/login/"
    login_data = {
        "email": "recruiter@demo.test",
        "password": "DemoPass123!"
    }
    print(f"Logging in to {login_url}...")
    response = requests.post(login_url, json=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    res_json = response.json()
    assert res_json["success"] is True
    access_token = res_json["data"]["access"]
    print("Logged in successfully! Token received.")
    
    # Header for authenticated requests
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. Get topics to ensure endpoint works
    topics_url = f"{BASE_URL}/api/v1/dsa-intelligence/topics/"
    print(f"Fetching topics from {topics_url}...")
    response = requests.get(topics_url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch topics: {response.text}"
    print("Topics fetched successfully!")

    # 3. Call assessments generate API
    generate_url = f"{BASE_URL}/api/v1/dsa-intelligence/assessments/generate/"
    generate_payload = {
        "company_slug": "google",
        "frequency_bucket": "all",
        "easy_count": 1,
        "medium_count": 1,
        "hard_count": 1,
        "topic_slug": "array",
        "title": "Google Array Assessment via Script"
    }
    print(f"Generating assessment via {generate_url}...")
    response = requests.post(generate_url, json=generate_payload, headers=headers)
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    assert response.status_code == 201, f"Failed to generate assessment: {response.text}"
    
    gen_data = response.json()
    assert gen_data["success"] is True
    assessment_id = gen_data["data"]["assessment_id"]
    print(f"Successfully generated assessment! ID: {assessment_id}")
    print(f"Title: {gen_data['data']['title']}")
    print(f"Duration: {gen_data['data']['duration_minutes']} mins")
    print(f"Problems Count: {gen_data['data']['problems_count']}")
    for prob in gen_data["data"]["problems"]:
        print(f"  - Problem ID {prob['id']}: {prob['title']} ({prob['difficulty']})")

    # 4. Fetch assessments list
    assessments_url = f"{BASE_URL}/api/v1/recruiter/assessments/"
    print(f"Fetching assessments from {assessments_url}...")
    response = requests.get(assessments_url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch assessments: {response.text}"
    
    ass_json = response.json()
    assert ass_json["success"] is True
    print("Assessments list:")
    
    # Check if results is a list under data or directly paginated
    data = ass_json["data"]
    results = data if isinstance(data, list) else data.get("results", [])
    
    for ass in results:
        print(f"  - Assessment ID {ass['id']}: {ass['title']} (status: {ass['status']})")
        for prob in ass.get("problems", []):
            print(f"    * Problem: {prob['title']} ({prob['language']})")

if __name__ == "__main__":
    test_recruiter_flow()
