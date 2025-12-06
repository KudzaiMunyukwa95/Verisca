# Verisca API - Quick Test Reference

## 🚀 Quick Start

### 1. Start Backend
```powershell
cd c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca
.\venv\Scripts\Activate
cd backend
uvicorn app.main:app --reload
```

### 2. Import Postman Collection
File: `Verisca_API_Collection.postman_collection.json`

### 3. Run Tests in Order
1. Login
2. Create Farm
3. Create Field  
4. Create Claim
5. Create Assessment Session
6. Add Sample Points (1, 2, 3)
7. **Generate PDF Report** ← Use "Send and Download"
8. **Sync Down** ← Test offline download
9. **Sync Up** ← Test offline upload

---

## 📄 PDF Report Test

**Endpoint**: `GET /api/v1/claims/{claim_id}/report`

**How to Test**:
1. Click dropdown next to "Send"
2. Select "Send and Download"
3. Save PDF file
4. Open and verify contents

**Expected PDF Contents**:
- Claim number and details
- Assessment session info
- Sample points table
- Measurements and notes

---

## 🔄 Sync Tests

### Sync Down (Download)
**Endpoint**: `GET /api/v1/sync/down`

**Returns**:
```json
{
  "timestamp": "2025-12-06T12:00:00",
  "claims": [...],
  "farms": [...],
  "fields": [...]
}
```

### Sync Up (Upload)
**Endpoint**: `POST /api/v1/sync/up`

**Body**:
```json
{
  "sessions": [{
    "id": "NEW-UUID-HERE",
    "claim_id": "{{claim_id}}",
    "assessment_method": "stand_reduction",
    ...
  }],
  "samples": []
}
```

**Get UUID**: https://www.uuidgenerator.net/

---

## ✅ Success Checklist

- [ ] Backend running on http://127.0.0.1:8000
- [ ] Logged in successfully (token saved)
- [ ] Farm created (ID saved)
- [ ] Field created (ID saved)
- [ ] Claim created (ID saved)
- [ ] Session created (ID saved)
- [ ] 3 samples added
- [ ] PDF generated and downloaded ✅
- [ ] PDF opens and shows data ✅
- [ ] Sync down returns data ✅
- [ ] Sync up succeeds ✅

---

## 🐛 Common Issues

**PDF Error 500**: Check samples exist
**Sync Empty Arrays**: Claims not assigned to user
**401 Unauthorized**: Re-run Login request

---

## 📚 Full Guide
See: `POSTMAN_TESTING_GUIDE.md`
