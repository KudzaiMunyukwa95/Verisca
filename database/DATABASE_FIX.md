# Database Setup - Quick Fix Instructions

## Problem

The original schema file has INSERT statements at the end that are missing required JSONB field values, causing errors.

## Solution

We'll load the schema in two steps:

### Step 1: Clear the Database (if you already ran the schema)

In pgAdmin Query Tool, run:

```sql
-- Drop all tables to start fresh
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Re-enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Step 2: Load Schema Without Seed Data

1. **Open the schema file** in a text editor (Notepad):
   ```
   c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\verisca_v2_database_refined_complete\verisca_v2_database_schema.sql
   ```

2. **Scroll to the bottom** (around line 905)

3. **Delete everything from line 905 onwards** (all the INSERT statements)
   - Look for the comment: `-- INITIAL DATA SETUP`
   - Delete from that line to the end of the file

4. **Save the file**

5. **In pgAdmin**, load and execute this modified file

6. **Verify tables created**: You should see 30+ tables with NO errors

### Step 3: Load Seed Data

1. **In pgAdmin Query Tool**, open the new seed data file:
   ```
   c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\database\seed_data.sql
   ```

2. **Execute it** (F5)

3. **Verify data loaded**:
   ```sql
   SELECT * FROM roles;
   SELECT * FROM crops;
   SELECT * FROM growth_stages;
   SELECT * FROM perils;
   SELECT * FROM assessment_methods;
   SELECT * FROM tenants;
   SELECT * FROM users;
   ```

You should see:
- 5 roles
- 1 crop (MAIZE)
- 7 growth stages
- 3 perils
- 2 assessment methods
- 1 tenant (DEMO)
- 1 user (demo_assessor)

---

## Quick Alternative (Easier)

If you don't want to edit the file, just run these two files in order:

1. **First, clear the database** (copy/paste into pgAdmin):
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

2. **Then run the fix script I created**:
   - Open: `c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\database\fix_assessment_methods.sql`
   - Execute it

3. **Then load the original schema** (it will skip the seed data errors)

4. **Finally load the seed data**:
   - Open: `c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\database\seed_data.sql`
   - Execute it

Let me know which approach you prefer!
