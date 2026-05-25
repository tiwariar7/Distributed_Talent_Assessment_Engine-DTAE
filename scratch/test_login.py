import requests

BASE_URL = "http://localhost"

def test_login(email, password, expected_role, dashboard_endpoint):
    print(f"\n--- Testing login for {email} ({expected_role}) ---")
    session = requests.Session()
    
    # 1. Login Request
    login_url = f"{BASE_URL}/api/v1/auth/login/"
    payload = {
        "email": email,
        "password": password
    }
    
    response = session.post(login_url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
        return False
        
    response_json = response.json()
    resp_data = response_json.get("data") or {}
    
    # Verify cookies
    cookies = session.cookies.get_dict()
    print("Set Cookies:", cookies)
    
    has_refresh_cookie = "dtae_refresh" in cookies
    has_csrf_cookie = "csrftoken" in cookies
    
    print(f"Contains 'dtae_refresh' cookie: {has_refresh_cookie}")
    print(f"Contains 'csrftoken' cookie: {has_csrf_cookie}")
    
    if not has_refresh_cookie or not has_csrf_cookie:
        print("FAIL: Missing expected cookies!")
        return False
        
    access_token = resp_data.get("access")
    if not access_token:
        print("FAIL: Access token not found in response data!")
        return False
        
    print(f"Received access token: {access_token[:15]}...")
    
    # Authenticate requests using the Bearer token in the header
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # 2. Test Dashboard Data Request
    print(f"\n--- Fetching dashboard data from {dashboard_endpoint} ---")
    dash_response = session.get(f"{BASE_URL}{dashboard_endpoint}", headers=headers)
    print(f"Dashboard Status Code: {dash_response.status_code}")
    if dash_response.status_code != 200:
        print(f"Dashboard Error Response: {dash_response.text}")
        return False
        
    dash_json = dash_response.json()
    dash_data = dash_json.get("data") if "data" in dash_json else dash_json
    print(f"Dashboard data keys/length: {len(dash_data) if isinstance(dash_data, list) else list(dash_data.keys())}")
    
    # 3. Test Refresh Request (using the refresh token cookie + CSRF verification)
    print("\n--- Testing token refresh with cookies ---")
    refresh_url = f"{BASE_URL}/api/v1/auth/refresh/"
    
    # Prepare CSRF header as required by the backend validate_csrf
    csrf_token = cookies.get("csrftoken")
    refresh_headers = {
        "X-CSRFToken": csrf_token
    }
    
    refresh_response = session.post(refresh_url, json={}, headers=refresh_headers)
    print(f"Refresh Status Code: {refresh_response.status_code}")
    if refresh_response.status_code != 200:
        print(f"Refresh Error Response: {refresh_response.text}")
        return False
        
    refresh_json = refresh_response.json()
    refresh_data = refresh_json.get("data") or {}
    new_access_token = refresh_data.get("access")
    if not new_access_token:
        print("FAIL: New access token not found in refresh response data!")
        return False
        
    print(f"Received new access token: {new_access_token[:15]}...")
    print("SUCCESS!")
    return True

if __name__ == "__main__":
    c_ok = test_login(
        "candidate@demo.test", 
        "DemoPass123!", 
        "Candidate", 
        "/api/v1/assessments/candidate/invitations/"
    )
    r_ok = test_login(
        "recruiter@demo.test", 
        "DemoPass123!", 
        "Recruiter", 
        "/api/v1/recruiter/assessments/"
    )
    
    if c_ok and r_ok:
        print("\nAll login, dashboard access, and cookie verification tests PASSED!")
    else:
        print("\nSome tests FAILED!")
