# Test Method Module API Testing Guide (Postman)

This guide provides a step-by-step workflow for testing the Test Method module using Postman. It covers all main endpoints, required inputs, and sample responses.

---

## Base URL
Replace `{{baseUrl}}` with your server's base URL, e.g., `http://localhost:8000/api/testmethods/`

---

## 1. List All Test Methods
- **Endpoint:** `GET {{baseUrl}}`
- **Description:** Returns all test methods.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511a1b2c3d4e5f6a7b8c9d0",
      "test_name": "Tensile Strength",
      "test_description": "Measures tensile strength.",
      "test_columns": ["Load", "Elongation"],
      "hasImage": false,
      "createdAt": "2025-09-25T10:00:00",
      "updatedAt": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

## 2. Create a New Test Method
- **Endpoint:** `POST {{baseUrl}}`
- **Description:** Creates a new test method.
- **Request:**
  - Method: POST
  - URL: `{{baseUrl}}`
  - Body (JSON):
```json
{
  "test_name": "Hardness Test",
  "test_description": "Measures material hardness.",
  "test_columns": ["Indentation", "Force"],
  "hasImage": true
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Test method created successfully",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d1",
    "test_name": "Hardness Test"
  }
}
```

---

## 3. Get Test Method Details
- **Endpoint:** `GET {{baseUrl}}<test_method_id>/`
- **Description:** Get details of a specific test method.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d1/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d1",
    "test_name": "Hardness Test",
    "test_description": "Measures material hardness.",
    "test_columns": ["Indentation", "Force"],
    "hasImage": true,
    "createdAt": "2025-09-25T10:05:00",
    "updatedAt": "2025-09-25T10:05:00"
  }
}
```

---

## 4. Update Test Method
- **Endpoint:** `PUT {{baseUrl}}<test_method_id>/`
- **Description:** Update an existing test method.
- **Request:**
  - Method: PUT
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d1/`
  - Body (JSON):
```json
{
  "test_description": "Updated description.",
  "test_columns": ["Indentation", "Force", "Depth"]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Test method updated successfully",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d1",
    "test_name": "Hardness Test",
    "updatedAt": "2025-09-25T10:10:00"
  }
}
```

---

## 5. Delete Test Method (Soft Delete)
- **Endpoint:** `DELETE {{baseUrl}}<test_method_id>/`
- **Description:** Soft deletes a test method.
- **Request:**
  - Method: DELETE
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d1/`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Test method deleted successfully"
}
```

---

## 6. Search Test Methods
- **Endpoint:** `GET {{baseUrl}}search/?test_name=Hardness&hasImage=true`
- **Description:** Search test methods by name, description, or image support.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}search/?test_name=Hardness&hasImage=true`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511a1b2c3d4e5f6a7b8c9d1",
      "test_name": "Hardness Test",
      "test_description": "Measures material hardness.",
      "hasImage": true,
      "createdAt": "2025-09-25T10:05:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "test_name": "Hardness",
    "test_description": "",
    "hasImage": "true"
  }
}
```

---

## 7. Test Method Statistics
- **Endpoint:** `GET {{baseUrl}}stats/`
- **Description:** Get statistics about test methods.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_test_methods": 5,
    "image_support_distribution": [
      {"_id": true, "count": 3},
      {"_id": false, "count": 2}
    ],
    "monthly_creation_stats": [
      {"_id": {"year": 2025, "month": 9}, "count": 5}
    ]
  }
}
```

---

## Notes
- All endpoints return JSON responses.
- For POST/PUT, set the request body to `raw` and select `JSON` in Postman.
- Use valid ObjectIds for `<test_method_id>`.
- If you get a 404 or error, check the input and ensure the resource exists.

---

For any questions or issues, check the API error messages or contact the backend developer.
