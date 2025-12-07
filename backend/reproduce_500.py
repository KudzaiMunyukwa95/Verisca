import urllib.request
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@verisca.com"
ADMIN_PASS = "password123"

def post(url, data, token=None):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise

def patch(url, data, token):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='PATCH'
    )
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise

def main():
    print("1. Logging in...")
    login_resp = post(f"{BASE_URL}/auth/login", {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    token = login_resp['access_token']
    print("   Logged in.")

    print("2. Creating Claim...")
    # Need existing farm/field. Assuming some exist or we can default?
    # Actually, let's use the 'assigned' logic to find existing or just create new if we know IDs.
    # To be safe, let's LIST claims and use one if available, or create if none.
    
    req = urllib.request.Request(f"{BASE_URL}/claims/", headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as response:
        claims = json.loads(response.read().decode('utf-8'))
    
    if claims:
        claim = claims[0]
        claim_id = claim['id']
        print(f"   Using existing claim: {claim_id}")
    else:
        # Create new claim (might fail if farm_id not known)
        print("   No claims found. Cannot proceed without known farm_id.")
        return

    print("3. Creating Session...")
    session_data = {
        "assessment_method": "hail",
        "growth_stage": "V10",
        "assessor_notes": "Debug session"
    }
    session = post(f"{BASE_URL}/claims/{claim_id}/sessions", session_data, token)
    session_id = session['id']
    print(f"   Created session: {session_id}")

    print("4. Patching Session (Simulating Completion)...")
    # Simulate result from hail calculation
    calculated_result = {
        "loss_percentage": 65.0,
        "damage_breakdown": {
            "stand": 45.0,
            "defoliation": 20.0
        },
        "sample_details": [
            {
                "sample_number": 1,
                "total_loss": 65.0
            }
        ]
    }
    
    patch_data = {
        "status": "completed",
        "calculated_result": calculated_result,
        "date_completed": datetime.now().isoformat()
    }
    
    print(f"   Sending PATCH to: {BASE_URL}/claims/{claim_id}/sessions/{session_id}")
    try:
        updated_session = patch(f"{BASE_URL}/claims/{claim_id}/sessions/{session_id}", patch_data, token)
        print("   SUCCESS! Session updated.")
        print(updated_session)
    except Exception as e:
        print("   FAILED!")

if __name__ == "__main__":
    main()
