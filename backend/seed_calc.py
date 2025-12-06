import requests
import json

# Local server URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def seed_data():
    try:
        response = requests.post(f"{BASE_URL}/calculations/seed-tables")
        if response.status_code in [200, 201]:
            print("Success:", response.json())
        else:
            print("Failed:", response.status_code, response.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    seed_data()
