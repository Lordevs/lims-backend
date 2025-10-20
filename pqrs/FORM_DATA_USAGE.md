# PQR Form Data API Usage Guide

## Overview
The PQR (Procedure Qualification Record) API now accepts **form data** instead of JSON for POST and PUT requests. The `joint_design_sketch` field accepts **actual image files** (multiple files supported).

## Model Changes
- `joint_design_sketch`: Changed from `StringField` to `ListField(StringField)` to support multiple image file paths

## API Endpoints

### 1. Create PQR (POST)
**Endpoint:** `POST /api/pqrs/`

**Content-Type:** `multipart/form-data`

**Required Fields:**
- `type` (string)
- `welder_card_id` (ObjectId string)
- `mechanical_testing_conducted_by` (string)
- `lab_test_no` (string)
- `law_name` (string)

**Optional Fields (JSON strings):**
- `basic_info` (JSON string)
- `joints` (JSON string)
- `base_metals` (JSON string)
- `filler_metals` (JSON string)
- `positions` (JSON string)
- `preheat` (JSON string)
- `post_weld_heat_treatment` (JSON string)
- `gas` (JSON string)
- `electrical_characteristics` (JSON string)
- `techniques` (JSON string)
- `welding_parameters` (JSON string)
- `tensile_test` (JSON string)
- `guided_bend_test` (JSON string)
- `toughness_test` (JSON string)
- `fillet_weld_test` (JSON string)
- `other_tests` (JSON string)
- `signatures` (JSON string)
- `is_active` (string: 'true'/'false')

**File Upload:**
- `joint_design_sketch` - Multiple image files

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/pqrs/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "type=WPS" \
  -F "welder_card_id=60f7b3b3b3b3b3b3b3b3b3b3" \
  -F "mechanical_testing_conducted_by=John Doe" \
  -F "lab_test_no=LT-2024-001" \
  -F "law_name=ASME IX" \
  -F 'basic_info={"project_name":"Test Project","date":"2024-01-01"}' \
  -F 'joints={"joint_type":"butt","thickness":"10mm"}' \
  -F "joint_design_sketch=@/path/to/image1.jpg" \
  -F "joint_design_sketch=@/path/to/image2.jpg" \
  -F "is_active=true"
```

**Example using Postman:**
1. Set method to POST
2. Set URL to `http://localhost:8000/api/pqrs/`
3. Go to "Body" tab
4. Select "form-data"
5. Add key-value pairs:
   - `type`: WPS
   - `welder_card_id`: 60f7b3b3b3b3b3b3b3b3b3b3
   - `mechanical_testing_conducted_by`: John Doe
   - `lab_test_no`: LT-2024-001
   - `law_name`: ASME IX
   - `basic_info`: {"project_name":"Test Project"}
   - `joint_design_sketch`: (change type to "File" and select image files - you can add multiple rows with same key)

**Response:**
```json
{
  "status": "success",
  "message": "PQR created successfully",
  "data": {
    "id": "60f7b3b3b3b3b3b3b3b3b3b3",
    "type": "WPS",
    "lab_test_no": "LT-2024-001",
    "law_name": "ASME IX",
    "joint_design_sketch": [
      "pqrs/60f7b3b3b3b3b3b3b3b3b3b3/joint_sketch_2024-01-15_14-30-25_a1b2c3d4.jpg",
      "pqrs/60f7b3b3b3b3b3b3b3b3b3b3/joint_sketch_2024-01-15_14-30-26_b2c3d4e5.jpg"
    ]
  }
}
```

### 2. Update PQR (PUT)
**Endpoint:** `PUT /api/pqrs/<object_id>/`

**Content-Type:** `multipart/form-data`

**Fields:** Same as POST (all optional)

**Example using cURL:**
```bash
curl -X PUT "http://localhost:8000/api/pqrs/60f7b3b3b3b3b3b3b3b3b3b3/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "type=Updated WPS" \
  -F "joint_design_sketch=@/path/to/new_image1.jpg" \
  -F "joint_design_sketch=@/path/to/new_image2.jpg"
```

**Response:**
```json
{
  "status": "success",
  "message": "PQR updated successfully",
  "data": {
    "id": "60f7b3b3b3b3b3b3b3b3b3b3",
    "type": "Updated WPS",
    "lab_test_no": "LT-2024-001",
    "joint_design_sketch": [
      "pqrs/60f7b3b3b3b3b3b3b3b3b3b3/joint_sketch_2024-01-15_15-45-30_c3d4e5f6.jpg",
      "pqrs/60f7b3b3b3b3b3b3b3b3b3b3/joint_sketch_2024-01-15_15-45-31_d4e5f6g7.jpg"
    ],
    "updated_at": "2024-01-15T15:45:30.123456"
  }
}
```

### 3. Get PQR (GET)
**Endpoint:** `GET /api/pqrs/<object_id>/`

**Response includes:**
- All PQR fields
- `joint_design_sketch` as array of file paths
- Welder card and welder information

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "id": "60f7b3b3b3b3b3b3b3b3b3b3",
    "type": "WPS",
    "basic_info": {...},
    "joints": {...},
    "joint_design_sketch": [
      "pqrs/60f7b3b3b3b3b3b3b3b3b3b3/joint_sketch_2024-01-15_14-30-25_a1b2c3d4.jpg"
    ],
    "welder_card_info": {...},
    ...
  }
}
```

## File Storage
- **Directory:** `media/pqrs/[pqr-id]/`
- **Filename Format:** `joint_sketch_YYYY-MM-DD_HH-MM-SS_<uuid>.ext`
- **Access:** Files are accessible via Django's media URL: `/media/pqrs/[pqr-id]/<filename>`
- **Organization:** Each PQR has its own dedicated folder identified by its ObjectId

### 4. Delete PQR (DELETE)
**Endpoint:** `DELETE /api/pqrs/<object_id>/`

**Permanently Deletes PQR and Image Folder:**
```bash
curl -X DELETE "http://localhost:8000/api/pqrs/60f7b3b3b3b3b3b3b3b3b3b3/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "PQR permanently deleted successfully",
  "data": {
    "id": "60f7b3b3b3b3b3b3b3b3b3b3",
    "deleted_at": "2024-01-15T16:00:00.123456"
  }
}
```

**⚠️ Warning:** This is a permanent deletion. The PQR document and all associated images in `media/pqrs/[pqr-id]/` will be permanently removed.

## Important Notes
1. **Multiple Files:** You can upload multiple images by adding multiple `joint_design_sketch` fields in form data
2. **JSON Fields:** Complex fields (basic_info, joints, etc.) must be passed as JSON strings in form data
3. **File Replacement:** When updating with new files, the old files are NOT deleted automatically
4. **File Size:** No explicit size limit is set, but Django's default settings apply
5. **Supported Formats:** Any image format is supported (jpg, png, gif, etc.)
6. **Folder Structure:** Each PQR gets its own folder in `media/pqrs/[pqr-id]/`
7. **Permanent Deletion:** DELETE requests permanently remove the PQR and its entire image folder

## Frontend Integration (React/JavaScript Example)

```javascript
const formData = new FormData();
formData.append('type', 'WPS');
formData.append('welder_card_id', '60f7b3b3b3b3b3b3b3b3b3b3');
formData.append('mechanical_testing_conducted_by', 'John Doe');
formData.append('lab_test_no', 'LT-2024-001');
formData.append('law_name', 'ASME IX');
formData.append('basic_info', JSON.stringify({ project_name: 'Test Project' }));

// Add multiple files
const files = document.getElementById('fileInput').files;
for (let i = 0; i < files.length; i++) {
  formData.append('joint_design_sketch', files[i]);
}

fetch('http://localhost:8000/api/pqrs/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```
