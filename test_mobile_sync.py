import requests
import json
import math
import sys
import time

# CONFIGURATION
# -----------------------------------------------------------------------------
API_BASE_URL = "https://verisca.onrender.com/api/v1"
USERNAME = "admin@verisca.com"  # REPLACE WITH VALID ADMIN EMAIL
PASSWORD = "password"           # REPLACE WITH VALID PASSWORD
# -----------------------------------------------------------------------------

def login():
    """Authenticate and get access token."""
    print(f"🔐 Logging in as {USERNAME}...")
    url = f"{API_BASE_URL}/auth/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Login Successful")
            return response.json()
        else:
            print(f"❌ Login Failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return None

def create_farm(token, user_id):
    """Simulate Farm Sync (SyncService.syncFarmCompleteSchema)."""
    print("\n🏭 Syncing Farm...")
    url = f"{API_BASE_URL}/farms/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    unique_suffix = int(time.time())
    
    farm_data = {
        "farm_code": f"TEST-FARM-{unique_suffix}",
        "farm_name": f"Mobile Sync Test Farm {unique_suffix}",
        "farmer_name": "Test Farmer",
        "farmer_contact": {
          "phone_number": "123456789",
          "email": "farmer@test.com"
        },
        "farm_address": {
          "address": "123 Test Lane, Harare"
        },
        "farm_characteristics": {
          "labor_availability": "Available",
          "power_source": "Grid",
          "notes": "Created via test_mobile_sync.py"
        },
        "total_farm_area": 100.0,
        "operational_area": 80.0,
        "farm_location": { "lat": -17.82, "lng": 31.05 }
    }

    try:
        response = requests.post(url, json=farm_data, headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Farm Synced: ID={data.get('id')} Name='{data.get('farm_name')}'")
            return data
        else:
            print(f"❌ Farm Sync Failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Farm Sync Error: {e}")
        return None

def create_field(token, farm_id):
    """Simulate Field Sync (SyncService.syncFieldCompleteSchemaFIXED100Percent)."""
    print("\n🌱 Syncing Field...")
    url = f"{API_BASE_URL}/farms/{farm_id}/fields"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    unique_suffix = int(time.time())
    
    # Boundary Synthesis Logic (from SyncService.js)
    centerLat = -17.82
    centerLng = 31.05
    areaHectares = 10.0
    
    sideMeters = math.sqrt(areaHectares * 10000)
    halfSide = sideMeters / 2.0
    latOffset = halfSide / 111132.0
    lngOffset = halfSide / (111132.0 * math.cos(centerLat * (math.pi / 180)))
    
    boundary = [
        [centerLng - lngOffset, centerLat - latOffset],
        [centerLng + lngOffset, centerLat - latOffset],
        [centerLng + lngOffset, centerLat + latOffset],
        [centerLng - lngOffset, centerLat + latOffset],
        [centerLng - lngOffset, centerLat - latOffset]
    ]
    
    field_data = {
        "field_code": f"FLD-{unique_suffix}",
        "field_name": f"Test Field {unique_suffix}",
        "boundary_coordinates": boundary,
        "soil_characteristics": {
            "type": "Loam",
            "ph": 6.5,
            "testing_done": 1
        },
        "irrigation_type": "Rainfed",
        "elevation_meters": 1500,
        "slope_characteristics": {
            "gradient": "Flat"
        },
        "land_use_restrictions": {
            "loss_history": {
                "drought": 1,
                "flood": 0
            }
        }
    }
    
    try:
        response = requests.post(url, json=field_data, headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Field Synced: ID={data.get('id')} Name='{data.get('field_name')}'")
            return data
        else:
            print(f"❌ Field Sync Failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Field Sync Error: {e}")
        return None

def main():
    print("🚀 Starting Mobile Backend Sync Verification...")
    print("---------------------------------------------")
    
    auth_data = login()
    if not auth_data:
        print("⚠️  Aborting. Please update USERNAME/PASSWORD in script.")
        sys.exit(1)
        
    token = auth_data['access_token']
    user = auth_data.get('user', {})
    print(f"👤 User: {user.get('email')} (ID: {user.get('id')})")
    
    farm = create_farm(token, user.get('id'))
    if farm:
        field = create_field(token, farm['id'])
        
    print("\n---------------------------------------------")
    print("🏁 Verification Complete")

if __name__ == "__main__":
    main()
