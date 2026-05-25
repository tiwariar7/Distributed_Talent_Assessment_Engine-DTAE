import requests

BASE_URL = "http://localhost"

def test_generation():
    print("Logging in recruiter...")
    session = requests.Session()
    login_url = f"{BASE_URL}/api/v1/auth/login/"
    payload = {
        "email": "recruiter@demo.test",
        "password": "DemoPass123!"
    }
    
    response = session.post(login_url, json=payload)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
        
    cookies = session.cookies.get_dict()
    print("Logged in successfully. Cookies:", cookies)
    
    resp_data = response.json().get("data") or {}
    access_token = resp_data.get("access")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-CSRFToken": cookies.get("csrftoken")
    }
    
    # Let's check company list first
    print("\nFetching companies...")
    comp_resp = session.get(f"{BASE_URL}/api/v1/dsa-intelligence/companies/", headers=headers)
    print("Companies status:", comp_resp.status_code)
    comp_json = comp_resp.json()
    companies = comp_json.get("data") or []
    print(f"Found {len(companies)} companies.")
    if not companies:
        print("No companies found in response data:", comp_json)
        return
        
    target_comp = companies[0]
    print(f"Selected target company: {target_comp['name']} (slug: {target_comp['slug']})")
    
    # Generate assessment
    gen_url = f"{BASE_URL}/api/v1/dsa-intelligence/assessments/generate/"
    gen_payload = {
        "company_slug": target_comp['slug'],
        "frequency_bucket": "all",
        "easy_count": 1,
        "medium_count": 1,
        "hard_count": 1,
        "title": f"Test Gen {target_comp['name']}"
    }
    
    print("\nCalling Smart Assessment Generator...")
    gen_resp = session.post(gen_url, json=gen_payload, headers=headers)
    print("Generator status:", gen_resp.status_code)
    print("Generator response:", gen_resp.text)

if __name__ == "__main__":
    test_generation()
