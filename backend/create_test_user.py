import sys
import os

# Add the current directory to the path so we can import app
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.tenant import Tenant, User, Role
from app.core.security import get_password_hash
import uuid

def create_test_data():
    db = SessionLocal()
    try:
        print("Checking for existing test data...")
        
        # 1. Create Tenant
        tenant = db.query(Tenant).filter(Tenant.tenant_code == "TEST001").first()
        if not tenant:
            print("Creating test tenant...")
            tenant = Tenant(
                tenant_code="TEST001",
                tenant_name="Test Insurance Co",
                tenant_type="insurer",
                contact_email="test@verisca.com",
                is_active=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        else:
            print("Test tenant already exists.")

        # 2. Create Role
        role = db.query(Role).filter(Role.role_name == "admin").first()
        if not role:
            print("Creating admin role...")
            role = Role(
                role_name="admin",
                role_description="Administrator",
                permissions=["all"],
                is_system_role=True
            )
            db.add(role)
            db.commit()
            db.refresh(role)
        else:
            print("Admin role already exists.")

        # 3. Create User
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("Creating admin user...")
            user = User(
                tenant_id=tenant.id,
                role_id=role.id,
                username="admin",
                email="admin@verisca.com",
                password_hash=get_password_hash("password123"),
                first_name="Admin",
                last_name="User",
                is_active=True,
                email_verified=True
            )
            db.add(user)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
            # Update password just in case
            user.password_hash = get_password_hash("password123")
            db.commit()
            print("Admin user password reset to 'password123'.")

        print("\n---------------------------------------------------")
        print("✅ Test Data Ready")
        print("---------------------------------------------------")
        print(f"Tenant Code: {tenant.tenant_code}")
        print(f"Username:    admin")
        print(f"Password:    password123")
        print("---------------------------------------------------")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
