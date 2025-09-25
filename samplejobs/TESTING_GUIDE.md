# SampleJobs Module API Testing Guide (Postman)

This guide provides a step-by-step workflow for testing the SampleJobs module using Postman. It covers all main endpoints, required inputs, and sample responses.

---

## Base URL
Replace `{{baseUrl}}` with your server's base URL, e.g., `http://localhost:8000/api/samplejobs/`

---

## 1. List All Jobs
- **Endpoint:** `GET {{baseUrl}}`
- **Description:** Returns all jobs with client information.
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
      "job_id": "MTL-2025-0001",
      "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
      "client_name": "ABC Industries",
      "project_name": "Bridge Project",
      "end_user": "Govt Dept",
      "receive_date": "2025-09-25T10:00:00",
      "received_by": "John Doe",
      "remarks": "Urgent",
      "job_created_at": "2025-09-25T10:00:00",
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

## 2. Create a New Job
- **Endpoint:** `POST {{baseUrl}}`
- **Description:** Creates a new job. `job_id` is optional and auto-generated if not provided.
- **Request:**
  - Method: POST
  - URL: `{{baseUrl}}`
  - Body (JSON):
```json
{
  "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
  "project_name": "Bridge Project",
  "end_user": "Govt Dept",
  "receive_date": "2025-09-25T10:00:00",
  "received_by": "John Doe",
  "remarks": "Urgent"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Job created successfully",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d0",
    "job_id": "MTL-2025-0001",
    "project_name": "Bridge Project",
    "client_name": "ABC Industries"
  }
}
```

---

## 3. Get Job Details
- **Endpoint:** `GET {{baseUrl}}<object_id>/`
- **Description:** Get details of a specific job by ObjectId.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d0/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d0",
    "job_id": "MTL-2025-0001",
    "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
    "client_info": {
      "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
      "client_name": "ABC Industries",
      "company_name": "ABC Group",
      "email": "abc@example.com",
      "phone": "+1234567890"
    },
    "project_name": "Bridge Project",
    "end_user": "Govt Dept",
    "receive_date": "2025-09-25T10:00:00",
    "received_by": "John Doe",
    "remarks": "Urgent",
    "job_created_at": "2025-09-25T10:00:00",
    "created_at": "2025-09-25T10:00:00",
    "updated_at": "2025-09-25T10:00:00"
  }
}
```

---

## 4. Update Job
- **Endpoint:** `PUT {{baseUrl}}<object_id>/`
- **Description:** Update an existing job (partial update allowed).
- **Request:**
  - Method: PUT
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d0/`
  - Body (JSON):
```json
{
  "project_name": "Bridge Project Phase 2",
  "remarks": "Updated remarks"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Job updated successfully",
  "data": {
    "id": "6511a1b2c3d4e5f6a7b8c9d0",
    "job_id": "MTL-2025-0001",
    "project_name": "Bridge Project Phase 2",
    "end_user": "Govt Dept",
    "receive_date": "2025-09-25T10:00:00",
    "received_by": "John Doe",
    "remarks": "Updated remarks",
    "job_created_at": "2025-09-25T10:00:00",
    "created_at": "2025-09-25T10:00:00",
    "updated_at": "2025-09-25T10:10:00"
  }
}
```

---

## 5. Delete Job
- **Endpoint:** `DELETE {{baseUrl}}<object_id>/`
- **Description:** Delete a job by ObjectId (with cascading soft delete for related sample lots).
- **Request:**
  - Method: DELETE
  - URL: `{{baseUrl}}6511a1b2c3d4e5f6a7b8c9d0/`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Job \"MTL-2025-0001\" deleted successfully. Also affected 2 related records.",
  "cascaded_deletions": {"sample_lots": 2},
  "job_details": {
    "id": "6511a1b2c3d4e5f6a7b8c9d0",
    "job_id": "MTL-2025-0001",
    "project_name": "Bridge Project",
    "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
    "deleted_at": "2025-09-25T10:15:00"
  },
  "summary": {
    "total_records_affected": 3,
    "job_deleted": true,
    "cascading_successful": true
  }
}
```

---

## 6. Search Jobs
- **Endpoint:** `GET {{baseUrl}}search/?project=bridge&client_id=6511a1b2c3d4e5f6a7b8c9d1`
- **Description:** Search jobs by project name, client ID, or received_by.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}search/?project=bridge&client_id=6511a1b2c3d4e5f6a7b8c9d1`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511a1b2c3d4e5f6a7b8c9d0",
      "job_id": "MTL-2025-0001",
      "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
      "client_name": "ABC Industries",
      "project_name": "Bridge Project",
      "receive_date": "2025-09-25T10:00:00",
      "received_by": "John Doe"
    }
  ],
  "total": 1,
  "filters_applied": {
    "project": "bridge",
    "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
    "received_by": ""
  }
}
```

---

## 7. Job Statistics
- **Endpoint:** `GET {{baseUrl}}stats/`
- **Description:** Get statistics about jobs.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_jobs": 5
  }
}
```

---

## 8. Get Jobs by Client
- **Endpoint:** `GET {{baseUrl}}client/<object_id>/`
- **Description:** Get all jobs for a specific client by client ObjectId.
- **Request:**
  - Method: GET
  - URL: `{{baseUrl}}client/6511a1b2c3d4e5f6a7b8c9d1/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511a1b2c3d4e5f6a7b8c9d0",
      "job_id": "MTL-2025-0001",
      "project_name": "Bridge Project",
      "receive_date": "2025-09-25T10:00:00",
      "received_by": "John Doe",
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "client_info": {
    "client_id": "6511a1b2c3d4e5f6a7b8c9d1",
    "client_name": "ABC Industries",
    "company_name": "ABC Group"
  }
}
```

---

## 9. Bulk Delete Jobs
- **Endpoint:** `DELETE {{baseUrl}}bulk-delete/`
- **Description:** Bulk delete multiple jobs (with cascading delete for related sample lots).
- **Request:**
  - Method: DELETE
  - URL: `{{baseUrl}}bulk-delete/`
  - Body (JSON):
```json
{
  "job_ids": ["MTL-2025-0001", "MTL-2025-0002"]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Bulk delete completed. Deleted 2 jobs with 3 related records.",
  "results": {
    "deleted_jobs": [
      {
        "job_id": "MTL-2025-0001",
        "project_name": "Bridge Project",
        "cascaded_deletions": {"sample_lots": 2}
      }
    ],
    "total_jobs_deleted": 2,
    "total_cascaded_records": 3,
    "errors": []
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
