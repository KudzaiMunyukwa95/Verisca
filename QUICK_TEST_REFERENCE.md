# Verisca API - Quick Test Reference (PDF & Sync)

## ✅ Already Tested

Per `verisca_streamlined_implementation.md` checkpoints:
- ✅ Create Farm (Checkpoint 1)
- ✅ Create Field (Checkpoint 2)
- ✅ Generate Sampling Points (Checkpoint 3)
- ✅ Create Claim (Checkpoint 4)
- ✅ USDA Calculations (Checkpoint 5)

## 🎯 What to Test Now

### 1. PDF Report Generation
### 2. Sync Down (Download)
### 3. Sync Up (Upload)

---

## 🚀 Quick Start

### Start Backend
```powershell
cd c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca
.\venv\Scripts\Activate
cd backend
uvicorn app.main:app --reload
```

### Import Collection
File: `Verisca_API_Collection.postman_collection.json`

---

## 📄 TEST 1: PDF Report

**Endpoint**: `GET /api/v1/claims/{claim_id}/report`

**Steps**:
1. Open "Generate PDF Report" request
2. Click dropdown → **"Send and Download"**
3. Save PDF file
4. Open and verify

**Expected**:
- Status: 200 OK
- PDF contains: Claim details, Session info, Samples table

---

## 🔄 TEST 2: Sync Down

**Endpoint**: `GET /api/v1/sync/down`

**Returns**:
```json
{
  "timestamp": "...",
  "claims": [...],
  "farms": [...],
  "fields": [...]
}
```

**Note**: May be empty if no claims assigned to user

---

## 🔄 TEST 3: Sync Up

**Endpoint**: `POST /api/v1/sync/up`

**Before Testing**:
1. Get new UUID from: https://www.uuidgenerator.net/
2. Replace `id` in request body

**Body**:
```json
{
  "sessions": [{
    "id": "NEW-UUID-HERE",
    "claim_id": "{{claim_id}}",
    ...
  }],
  "samples": []
}
```

**Expected**: `{"status": "success", ...}`

---

## ✅ Minimal Checklist

- [ ] Login (get token)
- [ ] PDF Report (Send and Download)
- [ ] Sync Down
- [ ] Sync Up (with new UUID)

---

## 🐛 Quick Fixes

**PDF Error 500**: Add samples first
**Sync Empty**: No assigned claims (normal)
**401 Error**: Re-run Login

---

## 📚 Full Guide
See: `POSTMAN_TESTING_GUIDE.md`

