# Clients Module API Testing Guide (Postman)

This guide provides a step-by-step workflow for testing the Clients module using Postman. It covers all main endpoints, required inputs, and sample responses.

---

## Base URL
Replace `{{baseUrl}}` with your server's base URL, e.g., `http://localhost:8000/api/clients/`

---

## 1. List All Clients
- **Endpoint:** `GET {{baseUrl}}`
- **Description:** Returns all clients.
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
      "client_name": "ABC Industries",
      "company_name": "ABC Group",
      "email": "abc@example.com",
      "phone": "+1234567890",
      "address": "123 Main St, City",
      "contact_person": "John Doe",
      "is_active": true,
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

## 2. Create a New Client
- **Endpoint:** `POST {{baseUrl}}`
- **Description:** Creates a new client. `client_id` is optional and auto-generated if not provided.
- **Request:**
  - Method: POST
  - URL: `{{baseUrl}}`
  - Body (JSON):
```json
{
  "client_name": "XYZ Corp",
  "company_name": "XYZ Holdings",
  "email": "xyz@example.com",
  "phone": "+1987654321",
  "address": "456 Market St, City",
  "contact_person": "Jane Smith"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Client created successfully",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d1",
    "client_id": 2,
    "client_name": "XYZ Corp",
    "email": "xyz@example.com"
  }
}
```

---

## 3. Get Client Details
- **Endpoint:** `GET {{baseUrl}}<object_id>/`
- **Description:** Get details of a specific client by ObjectId.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d1/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d1",
    "client_name": "XYZ Corp",
    "company_name": "XYZ Holdings",
    "email": "xyz@example.com",
    "phone": "+1987654321",
    "address": "456 Market St, City",
    "contact_person": "Jane Smith",
    "is_active": true,
    "created_at": "2025-09-25T10:05:00",
    "updated_at": "2025-09-25T10:05:00"
  }
}
```

---

## 4. Update Client
- **Endpoint:** `PUT {{baseUrl}}<object_id>/`
- **Description:** Update an existing client (partial update allowed).
- **Request:**
  - Method: PUT
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d1/`
  - Body (JSON):
```json
{
  "company_name": "XYZ Group",
  "phone": "+1122334455"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Client updated successfully",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d1",
    "client_name": "XYZ Corp",
    "company_name": "XYZ Group",
    "email": "xyz@example.com",
    "phone": "+1122334455",
    "address": "456 Market St, City",
    "contact_person": "Jane Smith",
    "is_active": true,
    "created_at": "2025-09-25T10:05:00",
    "updated_at": "2025-09-25T10:10:00"
  }
}
```

---

## 5. Delete Client
- **Endpoint:** `DELETE {{baseUrl}}<object_id>/`
- **Description:** Delete a client by ObjectId.
- **Request:**
  - Method: DELETE
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d1/`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Client deleted successfully"
}
```

---

## 6. Search Clients
- **Endpoint:** `GET {{baseUrl}}search/?name=xyz&active=true`
- **Description:** Search clients by name, email, company, or active status.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}search/?name=xyz&active=true`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511a1b2c3d4e5f6a7b8c9d1",
      "client_id": 2,
      "client_name": "XYZ Corp",
      "company_name": "XYZ Holdings",
      "email": "xyz@example.com",
      "phone": "+1987654321",
      "is_active": true
    }
  ],
  "total": 1,
  "filters_applied": {
    "name": "xyz",
    "email": "",
    "company": "",
    "active": "true"
  }
}
```

---

## 7. Client Statistics
- **Endpoint:** `GET {{baseUrl}}stats/`
- **Description:** Get statistics about clients.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_clients": 10,
    "active_clients": 8,
    "inactive_clients": 2,
    "activity_rate": 80.0
  }
}
```

---

## Notes
- All endpoints return JSON responses.
- For POST/PUT, set the request body to `raw` and select `JSON` in Postman.
- Use valid ObjectIds for `<object_id>`.
- If you get a 404 or error, check the input and ensure the resource exists.

---

For any questions or issues, check the API error messages or contact the backend developer.
