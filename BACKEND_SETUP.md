# Backend Setup and Testing Guide

## ✅ What's Done
- Database created on Render with PostGIS
- Schema loaded (30+ tables)
- Seed data loaded (roles, crops, growth stages, test user)
- Backend code created
- `.env` file configured with database connection

## 🚀 Next: Install Dependencies and Run Backend

### Step 1: Open PowerShell

1. Press `Windows + X`
2. Select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to Project and Create Virtual Environment

```powershell
# Navigate to Verisca folder
cd c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate
```

**You should see `(venv)` appear in your prompt**

### Step 3: Install Dependencies

```powershell
# Navigate to backend folder
cd backend

# Install all dependencies (this takes 2-3 minutes)
pip install -r requirements.txt
```

**Wait for all packages to install...**

### Step 4: Run the Backend Server

```powershell
# Start the server
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['c:\\Users\\kmunyukwa.AONZWARSHRE\\Downloads\\Verisca\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 5: Test the API

**Open your web browser and go to:**

1. **Root endpoint**: http://127.0.0.1:8000
   - Should see: `{"message": "Verisca API", "version": "1.0.0", "status": "operational"}`

2. **API Documentation**: http://127.0.0.1:8000/api/docs
   - Should see interactive Swagger UI with all endpoints

3. **Test Login** (in Swagger UI):
   - Click on `POST /api/v1/auth/login`
   - Click "Try it out"
   - Enter:
     ```json
     {
       "username": "demo_assessor",
       "password": "password123",
       "tenant_code": "DEMO"
     }
     ```
   - Click "Execute"
   - Should get back an access token!

---

## 🎉 Success!

If you see the API running and can login, you've successfully:
- ✅ Set up PostgreSQL with PostGIS on Render
- ✅ Loaded complete database schema
- ✅ Configured backend with database connection
- ✅ Started FastAPI server
- ✅ Tested authentication

---

## 🐛 Troubleshooting

### "python: command not found"
- Try `python3` instead of `python`
- Or install Python from python.org

### "pip: command not found"
- Make sure virtual environment is activated (you should see `(venv)`)
- Try `python -m pip install -r requirements.txt`

### Database connection error
- Check `.env` file has correct DATABASE_URL
- Verify database is "Available" in Render dashboard
- Check firewall isn't blocking connection

### Port 8000 already in use
- Try different port: `uvicorn app.main:app --reload --port 8001`

---

## 📝 Test Credentials

**Tenant Code:** DEMO  
**Username:** demo_assessor  
**Password:** password123  
**Email:** assessor@demo.com

---

Let me know when the backend is running! 🚀
