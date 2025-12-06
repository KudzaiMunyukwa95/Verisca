import sys
import os
from datetime import datetime

# Add the current directory to the path so we can import app
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.tenant import Tenant, User
from app.models.spatial import Farm, Field
from app.models.claims import Claim, ClaimStatus
from geoalchemy2.elements import WKTElement
import uuid

def create_test_claim():
    db = SessionLocal()
    try:
        print("Starting Test Claim Creation...")
        
        # 1. Get Tenant and User
        tenant = db.query(Tenant).filter(Tenant.tenant_code == "TEST001").first()
        if not tenant:
            print("ERROR: Tenant TEST001 not found. Run create_test_user.py first.")
            return

        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("ERROR: User admin not found. Run create_test_user.py first.")
            return

        print(f"Assigning to User: {user.username} (ID: {user.id})")

        # 2. Get or Create Farm
        farm = db.query(Farm).filter(Farm.farm_code == "DEMO_FARM_01").first()
        if not farm:
            print("Creating Demo Farm...")
            farm = Farm(
                tenant_id=tenant.id,
                farm_code="DEMO_FARM_01",
                farm_name="Verisca Demo Farm",
                farmer_name="John Doe",
                total_farm_area=100.0,
                operational_area=80.0
            )
            db.add(farm)
            db.commit()
            db.refresh(farm)
        else:
            print(f"Found existing Farm: {farm.farm_name}")

        # 3. Get or Create Field
        field = db.query(Field).filter(Field.field_code == "FIELD-A").first()
        if not field:
            print("Creating Demo Field...")
            # Simple square polygon around (0 0) for testing, or realistic coords
            # Using roughly central Zimbabwe coords (Harare) for realism: -17.82, 31.05
            wkt_polygon = "POLYGON((-17.82 31.05, -17.82 31.06, -17.83 31.06, -17.83 31.05, -17.82 31.05))"
            
            field = Field(
                farm_id=farm.id,
                field_code="FIELD-A",
                field_name="North Field",
                field_boundary=wkt_polygon, # Direct WKT string often works with GeoAlchemy2 if handle properly, else WKTElement
                field_area=10.5
            )
            db.add(field)
            db.commit()
            db.refresh(field)
        else:
            print(f"Found existing Field: {field.field_name}")

        # 4. Create Claim (Assigned to User)
        claim_number = f"CLM-{datetime.now().year}-TEST001"
        claim = db.query(Claim).filter(Claim.claim_number == claim_number).first()
        
        if not claim:
            print("Creating Test Claim...")
            claim = Claim(
                tenant_id=tenant.id,
                claim_number=claim_number,
                farm_id=farm.id,
                field_id=field.id,
                peril_type="hail",
                date_of_loss=datetime.now(),
                loss_description="Severe hail damage observed on maize crop.",
                status=ClaimStatus.ASSIGNED, # Crucial: Must be ASSIGNED or REPORTED
                assigned_assessor_id=user.id, # CRITICAL: Assign to the logged-in user
                created_by_user_id=user.id
            )
            db.add(claim)
            db.commit()
            print(f"SUCCESS: Claim {claim_number} created and assigned to {user.username}.")
        else:
            print(f"Claim {claim_number} already exists.")
            # Ensure it is assigned correctly if it exists
            if claim.assigned_assessor_id != user.id:
                print("Updating assignment to current admin user...")
                claim.assigned_assessor_id = user.id
                db.commit()

    except Exception as e:
        print(f"[ERROR] Failed to create claim: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_claim()
