# Step-by-Step Instructions for Setting Up Verisca

## Part 1: PostgreSQL Database Setup on Render

### Step 1: Create PostgreSQL Database

1. **Go to Render**: https://render.com
2. **Sign in** or create a new account
3. **Click "New +"** button in the top right
4. **Select "PostgreSQL"**
5. **Fill in the form:**
   - Name: `verisca-db`
   - Database: `verisca`
   - User: (leave default or use `verisca_user`)
   - Region: Choose closest to you
   - PostgreSQL Version: **15** or higher
   - Plan: **Free** (for development)
6. **Click "Create Database"**
7. **Wait 2-3 minutes** for database to be created

### Step 2: Get Connection Details

1. **Click on your database** in the Render dashboard
2. **Copy and save these details** (you'll need them):
   - **Internal Database URL** (starts with `postgresql://`)
   - **External Database URL** (for pgAdmin)
   - **Hostname**
   - **Port** (usually 5432)
   - **Database** (verisca)
   - **Username**
   - **Password**

### Step 3: Enable PostGIS Extension

1. **In Render dashboard**, click on your database
2. **Click "Shell" tab** at the top
3. **Run these commands** (copy and paste):
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```
4. **Verify PostGIS** is installed:
   ```sql
   SELECT PostGIS_version();
   ```
   - You should see version info like "3.3 USE_GEOS=1..."

---

## Part 2: Connect with pgAdmin

### Step 1: Install pgAdmin

1. **Download pgAdmin**: https://www.pgadmin.org/download/
2. **Install** for Windows
3. **Open pgAdmin**

### Step 2: Add Render Database

1. **Right-click "Servers"** in left panel
2. **Select "Register" → "Server"**
3. **General Tab:**
   - Name: `Verisca Render DB`
4. **Connection Tab:**
   - Host: (paste hostname from Render)
   - Port: `5432`
   - Maintenance database: `verisca`
   - Username: (paste from Render)
   - Password: (paste from Render)
   - ✅ Check "Save password"
5. **SSL Tab:**
   - SSL Mode: `Require`
6. **Click "Save"**

### Step 3: Load Database Schema

1. **In pgAdmin**, expand: Servers → Verisca Render DB → Databases → verisca
2. **Right-click on "verisca"** → Select "Query Tool"
3. **Click "Open File" icon** (folder icon in toolbar)
4. **Navigate to:**
   ```
   c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\verisca_v2_database_refined_complete\verisca_v2_database_schema.sql
   ```
5. **Click "Open"**
6. **Click "Execute/Refresh"** button (▶ play icon) or press **F5**
7. **Wait 30-60 seconds** for execution
8. **Check "Messages" tab** for success (should say "Query returned successfully")

### Step 4: Verify Tables Created

1. **In left panel**, expand: verisca → Schemas → public → Tables
2. **You should see 30+ tables** including:
   - tenants
   - users
   - roles
   - crops
   - claims
   - assessment_sessions
   - sample_points
   - etc.

---

## Part 3: Backend Setup

### Step 1: Create .env File

1. **Navigate to backend folder:**
   ```
   c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\backend
   ```
2. **Copy `.env.example` to `.env`**
3. **Edit `.env` file** and update:
   ```env
   DATABASE_URL=postgresql://username:password@hostname:5432/verisca
   SECRET_KEY=your-secret-key-change-this-to-something-random
   ```
   - Replace `username`, `password`, `hostname` with values from Render
   - Generate a random SECRET_KEY (can use any long random string)

### Step 2: Create Virtual Environment

1. **Open PowerShell**
2. **Navigate to Verisca folder:**
   ```powershell
   cd c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca
   ```
3. **Create virtual environment:**
   ```powershell
   python -m venv venv
   ```
4. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate
   ```
   - You should see `(venv)` in your prompt

### Step 3: Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

This will install all required packages (may take 2-3 minutes).

### Step 4: Test Backend Server

```powershell
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 5: Test API

1. **Open browser** and go to: http://127.0.0.1:8000
   - Should see: `{"message": "Verisca API", "version": "1.0.0", "status": "operational"}`

2. **Test API docs**: http://127.0.0.1:8000/api/docs
   - Should see interactive API documentation

---

## Next Steps

After completing these steps, you should have:
- ✅ PostgreSQL database running on Render
- ✅ PostGIS extension enabled
- ✅ Database schema loaded (30+ tables)
- ✅ Backend API running locally
- ✅ API documentation accessible

**Next, we'll:**
1. Create seed data (test tenant, user, crops, etc.)
2. Test authentication endpoint
3. Create claims management endpoints
4. Build assessment and sampling features

---

## Troubleshooting

### Can't connect to Render database in pgAdmin
- Check SSL mode is set to "Require"
- Verify you're using External Database URL hostname
- Check firewall isn't blocking port 5432

### Backend won't start
- Make sure virtual environment is activated
- Check DATABASE_URL in .env is correct
- Verify all dependencies installed: `pip list`

### Import errors
- Make sure you're in the backend directory
- Check all __init__.py files exist
- Try: `pip install -e .`
