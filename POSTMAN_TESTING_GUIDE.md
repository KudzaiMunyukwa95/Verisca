# Verisca API Testing Guide - Postman

## 📋 Overview

This guide will walk you through testing the Verisca API endpoints using Postman, with a focus on **PDF Report Generation** and **Sync Endpoints**.

---

## 🚀 Getting Started

### Prerequisites

1. **Backend Server Running**
   ```powershell
   cd c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca
   .\venv\Scripts\Activate
   cd backend
   uvicorn app.main:app --reload
   ```
   
   ✅ Verify: Open http://127.0.0.1:8000 in browser - should see `{"message": "Verisca API", ...}`

2. **Postman Installed**
   - Download from: https://www.postman.com/downloads/
   - Or use Postman Web: https://web.postman.com/

3. **Test Data Created**
   ```powershell
   # Run this once to create test user
   cd backend
   ..\venv\Scripts\python.exe create_test_user.py
   ```

---

## 📥 Import Postman Collection

### Option 1: Import from File

1. Open Postman
2. Click **Import** button (top left)
3. Select **File** tab
4. Choose: `c:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca\Verisca_API_Collection.postman_collection.json`
5. Click **Import**

### Option 2: Drag and Drop

- Drag the `Verisca_API_Collection.postman_collection.json` file into Postman window

---

## 🧪 Testing Workflow

### Step 1: Authentication

**Endpoint**: `1. Authentication > Login`

1. Open the **Login** request
2. Click **Send**
3. ✅ **Expected Result**:
   - Status: `200 OK`
   - Response contains `access_token`
   - Token automatically saved to collection variable

**Credentials**:
- Username: `admin`
- Password: `password123`

---

### Step 2: Create Test Farm

**Endpoint**: `2. Farms & Fields > Create Farm`

1. Open the **Create Farm** request
2. Review the JSON body (pre-filled with test data)
3. Click **Send**
4. ✅ **Expected Result**:
   - Status: `201 Created`
   - Response contains farm details with `id`
   - Farm ID automatically saved to collection variable

**What to Check**:
- `farm_code`: Unique identifier
- `farm_name`: Farm name
- `total_farm_area`: Total area in hectares
- `farm_location`: GPS coordinates

---

### Step 3: Create Test Field

**Endpoint**: `2. Farms & Fields > Create Field`

1. Open the **Create Field** request
2. Note: Uses `{{farm_id}}` variable from previous step
3. Click **Send**
4. ✅ **Expected Result**:
   - Status: `201 Created`
   - Response contains field details with calculated area
   - Field ID automatically saved

**What to Check**:
- `field_area`: Calculated from boundary coordinates (in hectares)
- `field_boundary`: Polygon geometry
- `field_center`: Center point coordinates

---

### Step 4: Create Test Claim

**Endpoint**: `3. Claims & Assessments > Create Claim`

1. Open the **Create Claim** request
2. Uses `{{farm_id}}` and `{{field_id}}` variables
3. Click **Send**
4. ✅ **Expected Result**:
   - Status: `201 Created`
   - Response contains `claim_number` (e.g., `CLM-2025-00001`)
   - Claim ID automatically saved

**What to Check**:
- `claim_number`: Auto-generated unique number
- `status`: Should be `REPORTED`
- `peril_type`: Type of loss (hail, drought, etc.)

---

### Step 5: Create Assessment Session

**Endpoint**: `3. Claims & Assessments > Create Assessment Session`

1. Open the **Create Assessment Session** request
2. Uses `{{claim_id}}` variable
3. Click **Send**
4. ✅ **Expected Result**:
   - Status: `201 Created`
   - Session ID automatically saved
   - Claim status updated to `IN_PROGRESS`

**What to Check**:
- `assessment_method`: Method used (hail_damage, stand_reduction, etc.)
- `growth_stage`: Crop growth stage (VT, R1, etc.)
- `status`: Should be `IN_PROGRESS`

---

### Step 6: Add Sample Points

**Endpoints**: 
- `3. Claims & Assessments > Add Sample Point 1`
- `3. Claims & Assessments > Add Sample Point 2`
- `3. Claims & Assessments > Add Sample Point 3`

1. Open **Add Sample Point 1** request
2. Click **Send**
3. Repeat for Sample Points 2 and 3
4. ✅ **Expected Result** (for each):
   - Status: `200 OK`
   - Response contains sample data with GPS location

**What to Check**:
- `sample_number`: Sequential number
- `sample_location`: WKT format GPS point
- `measurements`: JSON object with field measurements
- `gps_accuracy_meters`: GPS accuracy

---

## 📄 TESTING PDF REPORT GENERATION

### Step 7: Generate PDF Report

**Endpoint**: `4. PDF Report (TEST THIS) > Generate PDF Report`

This is the **main test** for PDF functionality!

#### How to Test:

1. Open the **Generate PDF Report** request
2. **Important**: Click the dropdown arrow next to "Send"
3. Select **"Send and Download"** (NOT just "Send")
4. Choose where to save the PDF file
5. ✅ **Expected Result**:
   - Status: `200 OK`
   - Content-Type: `application/pdf`
   - PDF file downloads to your computer

#### Verify PDF Contents:

Open the downloaded PDF and check for:

- ✅ **Title**: "Loss Assessment Report: CLM-2025-XXXXX"
- ✅ **Claim Details Table**:
  - Status
  - Date of Loss
  - Peril Type
  - Farm/Field IDs
- ✅ **Assessment Session Section**:
  - Date Started
  - Assessment Method
  - Final Appraisal Results
- ✅ **Field Samples Table**:
  - Sample numbers (1, 2, 3)
  - GPS locations
  - Measurements
  - Notes

#### Common Issues:

❌ **If you get an error**:
- Check that samples were added successfully in Step 6
- Verify claim_id variable is set correctly
- Check backend logs for detailed error

❌ **If PDF is empty or corrupted**:
- Check that `reportlab` is installed: `pip install reportlab`
- Verify session has samples attached

---

## 🔄 TESTING SYNC ENDPOINTS

### Step 8: Sync Down (Download Claims)

**Endpoint**: `5. Sync Endpoints (TEST THESE) > Sync Down - Download Claims`

This endpoint simulates a mobile app downloading claims for offline work.

#### How to Test:

1. Open the **Sync Down - Download Claims** request
2. Click **Send**
3. ✅ **Expected Result**:
   - Status: `200 OK`
   - Response contains:
     ```json
     {
       "timestamp": "2025-12-06T12:00:00",
       "claims": [...],
       "farms": [...],
       "fields": [...]
     }
     ```

#### What to Verify:

- ✅ **Claims Array**: Should contain the claim you created
- ✅ **Farms Array**: Should contain the related farm
- ✅ **Fields Array**: Should contain the related field
- ✅ **Timestamp**: Current server time

**Note**: By default, this returns claims assigned to the current user. Since we're using admin, it may return empty arrays if no claims are assigned. To test properly:

1. First assign the claim to the admin user (you may need to add an assignment endpoint)
2. Or modify the sync logic to return all claims for testing

---

### Step 9: Incremental Sync

**Endpoint**: `5. Sync Endpoints (TEST THESE) > Sync Down - Incremental (with last_sync)`

This tests downloading only data modified since a specific time.

#### How to Test:

1. Open the **Sync Down - Incremental** request
2. Note the `last_sync` query parameter
3. **Modify the timestamp**:
   - Set to 1 hour ago: `2025-12-06T11:00:00`
   - Or set to yesterday to get all recent data
4. Click **Send**
5. ✅ **Expected Result**:
   - Status: `200 OK`
   - Only returns claims updated after the specified time

#### Testing Scenarios:

**Scenario 1**: Recent sync (1 hour ago)
```
?last_sync=2025-12-06T11:00:00
```
- Should return claims created in the last hour

**Scenario 2**: Old sync (1 week ago)
```
?last_sync=2025-11-29T00:00:00
```
- Should return all recent claims

**Scenario 3**: No parameter
```
(remove the query parameter)
```
- Should return all assigned claims

---

### Step 10: Sync Up (Upload Assessment Data)

**Endpoint**: `5. Sync Endpoints (TEST THESE) > Sync Up - Upload Assessment Data`

This simulates a mobile app uploading offline assessment data to the server.

#### How to Test:

1. Open the **Sync Up - Upload Assessment Data** request
2. Review the JSON body:
   ```json
   {
     "sessions": [
       {
         "id": "550e8400-e29b-41d4-a716-446655440000",
         "claim_id": "{{claim_id}}",
         "assessment_method": "stand_reduction",
         ...
       }
     ],
     "samples": []
   }
   ```
3. **Important**: Generate a new UUID for the session `id`
   - Visit: https://www.uuidgenerator.net/
   - Copy a new UUID
   - Replace the `id` value in the request body
4. Click **Send**
5. ✅ **Expected Result**:
   - Status: `200 OK`
   - Response: `{"status": "success", "synced": {"sessions": [...], "samples": [...]}}`

#### What to Verify:

- ✅ **Status**: Should be "success"
- ✅ **Synced Sessions**: Should contain the session ID you uploaded
- ✅ **Database**: Session should now exist in the database

#### Testing Scenarios:

**Scenario 1**: Upload new session (new UUID)
- Should create a new assessment session

**Scenario 2**: Upload existing session (reuse UUID from Step 5)
- Should update the existing session

**Scenario 3**: Upload with samples
- Modify the `samples` array to include sample data
- Should create both session and samples

---

## 🎯 Complete Test Checklist

Run through all endpoints in order:

- [ ] 1. Login ✅
- [ ] 2. Get Current User ✅
- [ ] 3. Create Farm ✅
- [ ] 4. Create Field ✅
- [ ] 5. Create Claim ✅
- [ ] 6. Create Assessment Session ✅
- [ ] 7. Add Sample Point 1 ✅
- [ ] 8. Add Sample Point 2 ✅
- [ ] 9. Add Sample Point 3 ✅
- [ ] 10. **Generate PDF Report** 📄 ← **MAIN TEST**
- [ ] 11. **Sync Down** 🔄 ← **MAIN TEST**
- [ ] 12. **Sync Down - Incremental** 🔄 ← **MAIN TEST**
- [ ] 13. **Sync Up** 🔄 ← **MAIN TEST**

---

## 🐛 Troubleshooting

### PDF Generation Issues

**Error**: `500 Internal Server Error`
- Check backend logs for detailed error
- Verify `reportlab` is installed: `pip list | findstr reportlab`
- Ensure samples exist for the session

**Error**: `404 Not Found`
- Verify `claim_id` variable is set correctly
- Check that the claim exists: `GET /claims/{{claim_id}}`

**PDF is blank or incomplete**
- Verify samples were added successfully
- Check that session has `calculated_result` data

### Sync Issues

**Error**: `401 Unauthorized`
- Token may have expired - re-run the Login request
- Check Authorization header is set correctly

**Empty arrays in sync response**
- Claims may not be assigned to current user
- Check claim `assigned_assessor_id` field
- Modify sync logic for testing if needed

**Sync Up fails**
- Verify UUID format is correct
- Check `claim_id` exists
- Ensure JSON body is valid

---

## 📊 Expected Test Results

### PDF Report Test
✅ **Success Criteria**:
- Status: `200 OK`
- Content-Type: `application/pdf`
- File size: > 5 KB
- PDF opens without errors
- Contains all claim and assessment data

### Sync Down Test
✅ **Success Criteria**:
- Status: `200 OK`
- Response has `timestamp`, `claims`, `farms`, `fields`
- Arrays contain expected data
- Response time: < 2 seconds

### Sync Up Test
✅ **Success Criteria**:
- Status: `200 OK`
- Response: `{"status": "success", ...}`
- Session created/updated in database
- No data loss or corruption

---

## 🎉 Next Steps

After completing these tests:

1. ✅ **Document Results**: Note any failures or issues
2. 🔧 **Fix Issues**: Address any bugs found during testing
3. 📝 **Update Collection**: Add more test cases as needed
4. 🚀 **Proceed with Implementation Plan**: Continue with remaining endpoints

---

## 💡 Tips

- **Use Collection Variables**: The collection automatically saves IDs between requests
- **Check Tests Tab**: Each request has automated tests - review the results
- **Save Responses**: Use "Save Response" to keep examples for documentation
- **Environment Variables**: Consider creating separate environments for dev/staging/production
- **Collection Runner**: Use Postman's Collection Runner to run all tests automatically

---

## 📞 Support

If you encounter issues:
1. Check the backend logs in the terminal
2. Verify all prerequisites are met
3. Review the error messages in Postman
4. Check the database state using pgAdmin

---

**Happy Testing! 🚀**
