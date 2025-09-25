# Sample Preparation Module - Postman Testing Guide

This guide provides a comprehensive walkthrough for testing the **Sample Preparation** module of your LIMS backend using Postman. It covers all available API endpoints, required input data, and sample responses for each operation.

---

## Table of Contents
1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
    - [List All Sample Preparations](#1-list-all-sample-preparations)
    - [Create a New Sample Preparation](#2-create-a-new-sample-preparation)
    - [Get Sample Preparation Details](#3-get-sample-preparation-details)
    - [Update a Sample Preparation](#4-update-a-sample-preparation)
    - [Delete a Sample Preparation](#5-delete-a-sample-preparation)
    - [Search Sample Preparations](#6-search-sample-preparations)
    - [Sample Preparation Statistics](#7-sample-preparation-statistics)
5. [Sample Data](#sample-data)
6. [Troubleshooting](#troubleshooting)

---

## Overview
The Sample Preparation module manages laboratory sample preparations, linking sample lots, test methods, and specimens. This guide helps you test all CRUD and search operations using Postman.

## Base URL
```
http://<your-server>/samplepreperation/
```
Replace `<your-server>` with your actual server address (e.g., `localhost:8000`).

## Authentication
*If your API requires authentication, add the necessary headers or tokens in Postman. (Not covered here if not required.)*

---

## Endpoints

### 1. List All Sample Preparations
- **Endpoint:** `GET /samplepreperation/`
- **Description:** Returns all sample preparations with related data.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplepreperation/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6521e2...",
      "request_no": "REQ-2025-0001",
      "sample_lots": [
        {
          "item_description": "Lot 1 desc",
          "planned_test_date": "2025-09-25",
          "dimension_spec": "10x10x10",
          "request_by": "John Doe",
          "remarks": "Urgent",
          "sample_lot_id": "6511e2...",
          "test_method_oid": "6511e3...",
          "specimen_oids": ["6511e7...", "6511e8..."]
        }
      ],
      "sample_lots_count": 1,
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 2. Create a New Sample Preparation
- **Endpoint:** `POST /samplepreperation/`
- **Description:** Creates a new sample preparation. `request_no` is auto-generated if not provided.
- **Required Fields:** `sample_lots` (array of sample lot info)
- **Sample Request:**
    - Method: POST
    - URL: `http://localhost:8000/samplepreperation/`
    - Body (JSON):
```json
{
  "sample_lots": [
    {
      "item_description": "Lot 1 desc",
      "planned_test_date": "2025-09-25",
      "dimension_spec": "10x10x10",
      "request_by": "John Doe",
      "remarks": "Urgent",
      "sample_lot_id": "6511e2...",
      "test_method_oid": "6511e3...",
      "specimen_oids": ["6511e7...", "6511e8..."]
    }
  ]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Sample preparation created successfully",
  "data": {
    "id": "6521e2...",
    "request_no": "REQ-2025-0002",
    "sample_lots_count": 1
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

### 3. Get Sample Preparation Details
- **Endpoint:** `GET /samplepreperation/<object_id>/`
- **Description:** Returns details for a specific sample preparation, including related sample lots, test methods, and specimens.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplepreperation/6521e2.../`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6521e2...",
    "request_no": "REQ-2025-0002",
    "sample_lots": [
      {
        "sample_lot_id": "6511e2...",
        "item_no": "ITEM-001",
        "sample_type": "cs",
        "material_type": "plate",
        "job_id": "6511e1...",
        "test_method_oid": "6511e3...",
        "test_name": "Tensile",
        "test_description": "Tensile test desc",
        "specimens": [
          { "id": "6511e7...", "specimen_no": "SP-001" },
          { "id": "6511e8...", "specimen_no": "SP-002" }
        ]
      }
    ],
    "sample_lots_count": 1,
    "total_specimens": 2,
    "created_at": "2025-09-25T10:00:00",
    "updated_at": "2025-09-25T10:00:00"
  }
}
```

---

### 4. Update a Sample Preparation
- **Endpoint:** `PUT /samplepreperation/<object_id>/`
- **Description:** Updates fields for a specific sample preparation (partial update supported).
- **Sample Request:**
    - Method: PUT
    - URL: `http://localhost:8000/samplepreperation/6521e2.../`
    - Body (JSON):
```json
{
  "sample_lots": [
    {
      "item_description": "Lot 1 desc updated",
      "planned_test_date": "2025-09-26",
      "dimension_spec": "12x12x12",
      "request_by": "Jane Doe",
      "remarks": "Updated remarks",
      "sample_lot_id": "6511e2...",
      "test_method_oid": "6511e3...",
      "specimen_oids": ["6511e7...", "6511e8..."]
    }
  ]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Sample preparation updated successfully"
}
```

---

### 5. Delete a Sample Preparation
- **Endpoint:** `DELETE /samplepreperation/<object_id>/`
- **Description:** Deletes a sample preparation.
- **Sample Request:**
    - Method: DELETE
    - URL: `http://localhost:8000/samplepreperation/6521e2.../`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Sample preparation deleted successfully",
  "data": {
    "id": "6521e2...",
    "request_no": "REQ-2025-0002",
    "deleted_at": "2025-09-25T10:10:00"
  }
}
```

---

### 6. Search Sample Preparations
- **Endpoint:** `GET /samplepreperation/search/?request_no=&request_by=`
- **Description:** Search sample preparations by request number or requester name (partial match).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplepreperation/search/?request_no=REQ-2025&request_by=John`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6521e2...",
      "request_no": "REQ-2025-0002",
      "sample_lots_count": 1,
      "total_specimens": 2,
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "request_no": "REQ-2025",
    "request_by": "John"
  }
}
```

---

### 7. Sample Preparation Statistics
- **Endpoint:** `GET /samplepreperation/stats/`
- **Description:** Returns statistics on sample preparations (total, sample lots, specimens, averages).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/samplepreperation/stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_preparations": 2,
    "total_sample_lots": 3,
    "total_specimens_used": 6,
    "avg_sample_lots_per_preparation": 1.5,
    "avg_specimens_per_preparation": 3.0
  }
}
```

---

## Sample Data
- **sample_lot_id:** Use a valid SampleLot ObjectId from your database.
- **test_method_oid:** Use a valid TestMethod ObjectId.
- **specimen_oids:** Use valid Specimen ObjectIds (array).

### Example SampleLotInfo
```json
{
  "item_description": "Lot 1 desc",
  "planned_test_date": "2025-09-25",
  "dimension_spec": "10x10x10",
  "request_by": "John Doe",
  "remarks": "Urgent",
  "sample_lot_id": "6511e2...",
  "test_method_oid": "6511e3...",
  "specimen_oids": ["6511e7...", "6511e8..."]
}
```

---

## Troubleshooting
- **Validation Errors:** Ensure all required fields are provided and IDs are valid ObjectIds.
- **Unique Constraint:** `request_no` must be unique (auto-generated if not provided).
- **Array Fields:** `sample_lots` must be a non-empty array.
- **Date Fields:** Dates are in ISO format.

---

*For any issues, check the API error messages for details. If you need more help, review the backend code or contact the development team.*
