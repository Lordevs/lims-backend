# Sample Lots Module - Postman Testing Guide

This guide provides a comprehensive walkthrough for testing the **Sample Lots** module of your LIMS backend using Postman. It covers all available API endpoints, required input data, and sample responses for each operation.

---

## Table of Contents
1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
    - [List All Sample Lots](#1-list-all-sample-lots)
    - [Create a New Sample Lot](#2-create-a-new-sample-lot)
    - [Get Sample Lot Details](#3-get-sample-lot-details)
    - [Update a Sample Lot](#4-update-a-sample-lot)
    - [Delete a Sample Lot](#5-delete-a-sample-lot)
    - [Search Sample Lots](#6-search-sample-lots)
    - [Sample Lot Statistics](#7-sample-lot-statistics)
    - [Get Sample Lots by Job](#8-get-sample-lots-by-job)
5. [Sample Data](#sample-data)
6. [Troubleshooting](#troubleshooting)

---

## Overview
The Sample Lots module manages laboratory sample lots, each associated with a job and multiple test methods. This guide helps you test all CRUD and search operations using Postman.

## Base URL
```
http://<your-server>/samplelots/
```
Replace `<your-server>` with your actual server address (e.g., `localhost:8000`).

## Authentication
*If your API requires authentication, add the necessary headers or tokens in Postman. (Not covered here if not required.)*

---

## Endpoints

### 1. List All Sample Lots
- **Endpoint:** `GET /samplelots/`
- **Description:** Returns all active sample lots with job and test method info.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplelots/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511e2...",
      "job_id": "6511e1...",
      "job_info": { "job_id": "JOB-001", "project_name": "Project X" },
      "item_no": "ITEM-001",
      "sample_type": "cs",
      "material_type": "plate",
      "condition": "GOOD",
      "heat_no": "H1234",
      "description": "Sample lot description",
      "mtc_no": "MTC-001",
      "storage_location": "Shelf A",
      "test_methods_count": 2,
      "test_methods": ["Tensile", "Hardness"],
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 2. Create a New Sample Lot
- **Endpoint:** `POST /samplelots/`
- **Description:** Creates a new sample lot.
- **Required Fields:** `job_id`, `item_no`, `description`
- **Optional Fields:** `sample_type`, `material_type`, `condition`, `heat_no`, `mtc_no`, `storage_location`, `test_method_oids` (list of test method IDs)
- **Sample Request:**
    - Method: POST
    - URL: `http://localhost:8000/samplelots/`
    - Body (JSON):
```json
{
  "job_id": "6511e1...",
  "item_no": "ITEM-002",
  "sample_type": "stainless steel",
  "material_type": "pipe",
  "condition": "HEAT TREATED",
  "heat_no": "H5678",
  "description": "Second sample lot",
  "mtc_no": "MTC-002",
  "storage_location": "Shelf B",
  "test_method_oids": ["6511e3...", "6511e4..."]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Sample lot created successfully",
  "data": {
    "id": "6511e5...",
    "item_no": "ITEM-002",
    "job_id": "JOB-001",
    "project_name": "Project X"
  }
}
```
- **Error Response (missing required field):**
```json
{
  "status": "error",
  "message": "Validation error: ..."
}
```

---

### 3. Get Sample Lot Details
- **Endpoint:** `GET /samplelots/<sample_lot_id>/`
- **Description:** Returns details for a specific sample lot.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplelots/6511e5.../`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6511e5...",
    "job_id": "6511e1...",
    "job_info": { "job_id": "JOB-001", "project_name": "Project X" },
    "item_no": "ITEM-002",
    "sample_type": "stainless steel",
    "material_type": "pipe",
    "condition": "HEAT TREATED",
    "heat_no": "H5678",
    "description": "Second sample lot",
    "mtc_no": "MTC-002",
    "storage_location": "Shelf B",
    "test_methods": [
      { "id": "6511e3...", "name": "Tensile" },
      { "id": "6511e4...", "name": "Hardness" }
    ],
    "created_at": "2025-09-25T10:00:00",
    "updated_at": "2025-09-25T10:00:00"
  }
}
```

---

### 4. Update a Sample Lot
- **Endpoint:** `PUT /samplelots/<sample_lot_id>/`
- **Description:** Updates fields for a specific sample lot (partial update supported).
- **Sample Request:**
    - Method: PUT
    - URL: `http://localhost:8000/samplelots/6511e5.../`
    - Body (JSON):
```json
{
  "condition": "GOOD",
  "storage_location": "Shelf C"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Sample lot updated successfully"
}
```

---

### 5. Delete a Sample Lot
- **Endpoint:** `DELETE /samplelots/<sample_lot_id>/`
- **Description:** Soft deletes a sample lot (sets `is_active` to false).
- **Sample Request:**
    - Method: DELETE
    - URL: `http://localhost:8000/samplelots/6511e5.../`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Sample lot deleted successfully"
}
```

---

### 6. Search Sample Lots
- **Endpoint:** `GET /samplelots/search/?job_id=&sample_type=&material_type=&item_no=`
- **Description:** Search sample lots by job, sample type, material type, or item number (partial match).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplelots/search/?sample_type=cs&material_type=plate`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511e2...",
      "job_id": "6511e1...",
      "job_info": { "job_id": "JOB-001", "project_name": "Project X" },
      "item_no": "ITEM-001",
      "sample_type": "cs",
      "material_type": "plate",
      "description": "Sample lot description",
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "job_id": "",
    "sample_type": "cs",
    "material_type": "plate",
    "item_no": ""
  }
}
```

---

### 7. Sample Lot Statistics
- **Endpoint:** `GET /samplelots/stats/`
- **Description:** Returns statistics on sample lots (total, by sample type, by material type).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplelots/stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_sample_lots": 2,
    "sample_type_distribution": [
      { "_id": "cs", "count": 1 },
      { "_id": "stainless steel", "count": 1 }
    ],
    "material_type_distribution": [
      { "_id": "plate", "count": 1 },
      { "_id": "pipe", "count": 1 }
    ]
  }
}
```

---

### 8. Get Sample Lots by Job
- **Endpoint:** `GET /samplelots/job/<job_id>/`
- **Description:** Returns all sample lots for a specific job.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplelots/job/6511e1.../`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6511e2...",
      "item_no": "ITEM-001",
      "sample_type": "cs",
      "material_type": "plate",
      "description": "Sample lot description",
      "test_methods_count": 2,
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "job_info": {
    "job_id": "JOB-001",
    "project_name": "Project X",
    "client_id": "6511e0..."
  }
}
```

---

## Sample Data
- **job_id:** Use a valid Job ObjectId from your database.
- **test_method_oids:** Use valid TestMethod ObjectIds.
- **item_no:** Must be unique for each sample lot.

### Example Job Document
```json
{
  "_id": "6511e1...",
  "job_id": "JOB-001",
  "project_name": "Project X",
  "client_id": "6511e0..."
}
```

### Example TestMethod Document
```json
{
  "_id": "6511e3...",
  "name": "Tensile"
}
```

---

## Troubleshooting
- **Validation Errors:** Ensure all required fields are provided and IDs are valid ObjectIds.
- **Unique Constraint:** `item_no` must be unique.
- **Legacy Data:** Endpoints support legacy records without `is_active` field.
- **Date Fields:** Dates are in ISO format.

---

*For any issues, check the API error messages for details. If you need more help, review the backend code or contact the development team.*
