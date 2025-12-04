# Simple Database Setup - Step by Step

## The Problem
The original schema file has errors in the INSERT statements at the end. We need to load just the table structures first, then add the data separately.

## Solution: Run These 3 Scripts in Order

### Script 1: Clear and Prepare Database
**Copy/paste this into pgAdmin Query Tool and run it:**

```sql
-- Clear everything
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Script 2: Load Clean Schema (Tables Only)
**Open this file in pgAdmin and run it:**
```
c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\database\schema_clean.sql
```

This creates all 30+ tables WITHOUT the problematic INSERT statements.

### Script 3: Load Seed Data
**Open this file in pgAdmin and run it:**
```
c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\database\seed_data.sql
```

This adds the test data (roles, crops, users, etc.)

### Script 4: Verify Everything Worked
**Run this to check:**

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check data loaded
SELECT * FROM roles;
SELECT * FROM crops;
SELECT * FROM growth_stages;
SELECT * FROM tenants;
SELECT * FROM users;
```

**Expected Results:**
- 30+ tables listed
- 5 roles
- 1 crop (MAIZE)
- 7 growth stages  
- 1 tenant (DEMO)
- 1 user (demo_assessor)

---

## If You Get Stuck

Just run Script 1 again to start fresh, then try Scripts 2 and 3 again.
