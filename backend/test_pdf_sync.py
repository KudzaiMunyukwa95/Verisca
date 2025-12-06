"""
Test script for PDF Report Generation and Sync Endpoints
Run this after the backend is running: uvicorn app.main:app --reload
"""

import requests
import json
from datetime import datetime, timedelta
from uuid import uuid4

# Configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "admin"
PASSWORD = "password123"

# Global variables
token = None
headers = {}
test_data = {}

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")

def login():
    """Step 1: Login and get token"""
    print_section("STEP 1: Authentication")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        global token, headers
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print_result("Login", True, f"Token: {token[:20]}...")
        return True
    else:
        print_result("Login", False, f"Status: {response.status_code}, Error: {response.text}")
        return False

def create_test_farm():
    """Step 2: Create a test farm"""
    print_section("STEP 2: Create Test Farm")
    
    farm_data = {
        "farm_code": f"FARM-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "farm_name": "Test Farm for PDF Report",
        "farmer_name": "John Doe",
        "farmer_contact": "+263771234567",
        "farm_address": "Harare, Zimbabwe",
        "total_farm_area": 100.5,
        "operational_area": 95.0,
        "farm_location": {
            "lat": -17.8252,
            "lng": 31.0335
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/farms/",
        headers=headers,
        json=farm_data
    )
    
    if response.status_code == 201:
        farm = response.json()
        test_data["farm_id"] = farm["id"]
        print_result("Create Farm", True, f"Farm ID: {farm['id']}")
        print(f"    Farm Code: {farm['farm_code']}")
        return True
    else:
        print_result("Create Farm", False, f"Status: {response.status_code}, Error: {response.text}")
        return False

def create_test_field():
    """Step 3: Create a test field"""
    print_section("STEP 3: Create Test Field")
    
    # Simple polygon boundary (rectangle)
    field_data = {
        "field_code": "FIELD-001",
        "field_name": "Maize Field A",
        "boundary_coordinates": [
            {"lat": -17.8250, "lng": 31.0330},
            {"lat": -17.8250, "lng": 31.0340},
            {"lat": -17.8260, "lng": 31.0340},
            {"lat": -17.8260, "lng": 31.0330},
            {"lat": -17.8250, "lng": 31.0330}  # Close the polygon
        ],
        "irrigation_type": "rainfed",
        "elevation_meters": 1500
    }
    
    response = requests.post(
        f"{BASE_URL}/farms/{test_data['farm_id']}/fields",
        headers=headers,
        json=field_data
    )
    
    if response.status_code == 201:
        field = response.json()
        test_data["field_id"] = field["id"]
        print_result("Create Field", True, f"Field ID: {field['id']}")
        print(f"    Field Area: {field['field_area']} hectares")
        return True
    else:
        print_result("Create Field", False, f"Status: {response.status_code}, Error: {response.text}")
        return False

def create_test_claim():
    """Step 4: Create a test claim"""
    print_section("STEP 4: Create Test Claim")
    
    claim_data = {
        "farm_id": test_data["farm_id"],
        "field_id": test_data["field_id"],
        "peril_type": "hail",
        "date_of_loss": (datetime.now() - timedelta(days=7)).isoformat(),
        "loss_description": "Severe hail damage to maize crop at VT stage"
    }
    
    response = requests.post(
        f"{BASE_URL}/claims/",
        headers=headers,
        json=claim_data
    )
    
    if response.status_code == 201:
        claim = response.json()
        test_data["claim_id"] = claim["id"]
        print_result("Create Claim", True, f"Claim ID: {claim['id']}")
        print(f"    Claim Number: {claim['claim_number']}")
        return True
    else:
        print_result("Create Claim", False, f"Status: {response.status_code}, Error: {response.text}")
        return False

def create_assessment_session():
    """Step 5: Create assessment session"""
    print_section("STEP 5: Create Assessment Session")
    
    session_data = {
        "assessment_method": "hail_damage",
        "growth_stage": "VT",
        "weather_conditions": "Clear, sunny, 25°C",
        "crop_conditions": "Moderate hail damage visible on leaves",
        "assessor_notes": "Assessment conducted 7 days after hail event"
    }
    
    response = requests.post(
        f"{BASE_URL}/claims/{test_data['claim_id']}/sessions",
        headers=headers,
        json=session_data
    )
    
    if response.status_code == 201:
        session = response.json()
        test_data["session_id"] = session["id"]
        print_result("Create Session", True, f"Session ID: {session['id']}")
        return True
    else:
        print_result("Create Session", False, f"Status: {response.status_code}, Error: {response.text}")
        return False

def add_sample_points():
    """Step 6: Add sample points to session"""
    print_section("STEP 6: Add Sample Points")
    
    # Sample data for hail damage assessment
    samples = [
        {
            "sample_number": 1,
            "lat": -17.8252,
            "lng": 31.0332,
            "gps_accuracy_meters": 2.5,
            "measurements": {
                "plants_per_row_ft": 3.2,
                "leaf_defoliation_pct": 25,
                "stalk_breakage": 0,
                "ear_damage_pct": 15
            },
            "notes": "Light to moderate leaf damage"
        },
        {
            "sample_number": 2,
            "lat": -17.8254,
            "lng": 31.0334,
            "gps_accuracy_meters": 1.8,
            "measurements": {
                "plants_per_row_ft": 3.1,
                "leaf_defoliation_pct": 35,
                "stalk_breakage": 2,
                "ear_damage_pct": 20
            },
            "notes": "Moderate damage, some stalk breakage"
        },
        {
            "sample_number": 3,
            "lat": -17.8256,
            "lng": 31.0336,
            "gps_accuracy_meters": 2.1,
            "measurements": {
                "plants_per_row_ft": 3.0,
                "leaf_defoliation_pct": 30,
                "stalk_breakage": 1,
                "ear_damage_pct": 18
            },
            "notes": "Moderate leaf damage throughout"
        }
    ]
    
    success_count = 0
    for sample in samples:
        response = requests.post(
            f"{BASE_URL}/claims/sessions/{test_data['session_id']}/samples",
            headers=headers,
            json=sample
        )
        
        if response.status_code == 200:
            success_count += 1
            print_result(f"Add Sample {sample['sample_number']}", True)
        else:
            print_result(f"Add Sample {sample['sample_number']}", False, 
                        f"Status: {response.status_code}")
    
    return success_count == len(samples)

def test_pdf_generation():
    """Step 7: Test PDF Report Generation"""
    print_section("STEP 7: Test PDF Report Generation")
    
    response = requests.get(
        f"{BASE_URL}/claims/{test_data['claim_id']}/report",
        headers=headers
    )
    
    if response.status_code == 200:
        # Save PDF to file
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print_result("Generate PDF Report", True, f"Saved as: {filename}")
        print(f"    File size: {len(response.content)} bytes")
        print(f"    Content-Type: {response.headers.get('content-type')}")
        return True
    else:
        print_result("Generate PDF Report", False, 
                    f"Status: {response.status_code}, Error: {response.text}")
        return False

def test_sync_down():
    """Step 8: Test Sync Down (Download Claims)"""
    print_section("STEP 8: Test Sync Down (Download Claims)")
    
    response = requests.get(
        f"{BASE_URL}/sync/down",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_result("Sync Down", True)
        print(f"    Claims downloaded: {len(data.get('claims', []))}")
        print(f"    Farms downloaded: {len(data.get('farms', []))}")
        print(f"    Fields downloaded: {len(data.get('fields', []))}")
        print(f"    Timestamp: {data.get('timestamp')}")
        
        # Store for sync up test
        test_data["sync_data"] = data
        return True
    else:
        print_result("Sync Down", False, 
                    f"Status: {response.status_code}, Error: {response.text}")
        return False

def test_sync_up():
    """Step 9: Test Sync Up (Upload Assessment Data)"""
    print_section("STEP 9: Test Sync Up (Upload Assessment Data)")
    
    # Simulate offline session data
    offline_session = {
        "id": str(uuid4()),
        "claim_id": test_data["claim_id"],
        "assessment_method": "stand_reduction",
        "growth_stage": "V6",
        "date_completed": datetime.now().isoformat(),
        "calculated_result": {
            "loss_percentage": 15.5,
            "average_potential_yield_pct": 84.5
        },
        "created_at": datetime.now().isoformat()
    }
    
    sync_payload = {
        "sessions": [offline_session],
        "samples": []
    }
    
    response = requests.post(
        f"{BASE_URL}/sync/up",
        headers=headers,
        json=sync_payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print_result("Sync Up", True)
        print(f"    Status: {result.get('status')}")
        print(f"    Synced sessions: {len(result.get('synced', {}).get('sessions', []))}")
        return True
    else:
        print_result("Sync Up", False, 
                    f"Status: {response.status_code}, Error: {response.text}")
        return False

def test_incremental_sync():
    """Step 10: Test Incremental Sync with last_sync parameter"""
    print_section("STEP 10: Test Incremental Sync")
    
    # Test with a timestamp from 1 hour ago
    last_sync = (datetime.now() - timedelta(hours=1)).isoformat()
    
    response = requests.get(
        f"{BASE_URL}/sync/down",
        headers=headers,
        params={"last_sync": last_sync}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_result("Incremental Sync", True)
        print(f"    Claims since {last_sync[:19]}: {len(data.get('claims', []))}")
        return True
    else:
        print_result("Incremental Sync", False, 
                    f"Status: {response.status_code}, Error: {response.text}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "VERISCA PDF & SYNC ENDPOINT TESTS" + " "*15 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("Login", login),
        ("Create Farm", create_test_farm),
        ("Create Field", create_test_field),
        ("Create Claim", create_test_claim),
        ("Create Assessment Session", create_assessment_session),
        ("Add Sample Points", add_sample_points),
        ("PDF Generation", test_pdf_generation),
        ("Sync Down", test_sync_down),
        ("Sync Up", test_sync_up),
        ("Incremental Sync", test_incremental_sync)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            if not success and test_name in ["Login", "Create Farm", "Create Field", "Create Claim"]:
                print(f"\n⚠️  Stopping tests - {test_name} failed (prerequisite)")
                break
        except Exception as e:
            print_result(test_name, False, f"Exception: {str(e)}")
            results.append((test_name, False))
            if test_name in ["Login", "Create Farm", "Create Field", "Create Claim"]:
                break
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed! PDF and Sync endpoints are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")

if __name__ == "__main__":
    run_all_tests()
