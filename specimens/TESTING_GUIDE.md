# Specimens Module - Postman Testing Guide

This guide provides a comprehensive walkthrough for testing the **Specimens** module of your LIMS backend using Postman. It covers all available API endpoints, required input data, and sample responses for each operation.

---

## Table of Contents
1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
    - [List All Specimens](#1-list-all-specimens)
    - [Create a New Specimen](#2-create-a-new-specimen)
    - [Get Specimen Details](#3-get-specimen-details)
    - [Update a Specimen](#4-update-a-specimen)
    - [Delete a Specimen](#5-delete-a-specimen)
    - [Search Specimens](#6-search-specimens)
    - [Specimen Statistics](#7-specimen-statistics)
    - [Bulk Delete Specimens](#8-bulk-delete-specimens)
5. [Sample Data](#sample-data)
6. [Troubleshooting](#troubleshooting)

---

## Overview
The Specimens module manages laboratory specimens, each with a unique `specimen_id`. This guide helps you test all CRUD and search operations using Postman.

## Base URL
```
http://<your-server>/specimens/
```
Replace `<your-server>` with your actual server address (e.g., `localhost:8000`).

## Authentication
*If your API requires authentication, add the necessary headers or tokens in Postman. (Not covered here if not required.)*

---

## Endpoints

### 1. List All Specimens
- **Endpoint:** `GET /specimens/`
- **Description:** Returns all specimens.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/specimens/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6531e2...",
      "specimen_id": "SP-001",
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 2. Create a New Specimen
- **Endpoint:** `POST /specimens/`
- **Description:** Creates a new specimen. `specimen_id` must be unique.
- **Required Fields:** `specimen_id`
- **Sample Request:**
    - Method: POST
    - URL: `http://localhost:8000/specimens/`
    - Body (JSON):
```json
{
  "specimen_id": "SP-002"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Specimen created successfully",
  "data": {
    "id": "6531e3...",
    "specimen_id": "SP-002",
    "created_at": "2025-09-25T10:05:00"
  }
}
```
- **Error Response (duplicate):**
```json
{
  "status": "error",
  "message": "Specimen with ID \"SP-002\" already exists. Specimen IDs must be unique."
}
```

---

### 3. Get Specimen Details
- **Endpoint:** `GET /specimens/<object_id>/`
- **Description:** Returns details for a specific specimen.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/specimens/6531e3.../`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6531e3...",
    "specimen_id": "SP-002",
    "created_at": "2025-09-25T10:05:00",
    "updated_at": "2025-09-25T10:05:00"
  }
}
```

---

### 4. Update a Specimen
- **Endpoint:** `PUT /specimens/<object_id>/`
- **Description:** Updates fields for a specific specimen (can update `specimen_id`, must remain unique).
- **Sample Request:**
    - Method: PUT
    - URL: `http://localhost:8000/specimens/6531e3.../`
    - Body (JSON):
```json
{
  "specimen_id": "SP-002-UPDATED"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Specimen updated successfully",
  "data": {
    "id": "6531e3...",
    "specimen_id": "SP-002-UPDATED",
    "created_at": "2025-09-25T10:05:00",
    "updated_at": "2025-09-25T10:10:00"
  }
}
```
- **Error Response (duplicate):**
```json
{
  "status": "error",
  "message": "Specimen with ID \"SP-002-UPDATED\" already exists. Specimen IDs must be unique."
}
```

---

### 5. Delete a Specimen
- **Endpoint:** `DELETE /specimens/<object_id>/`
- **Description:** Deletes a specimen.
- **Sample Request:**
    - Method: DELETE
    - URL: `http://localhost:8000/specimens/6531e3.../`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Specimen deleted successfully",
  "data": {
    "id": "6531e3...",
    "specimen_id": "SP-002-UPDATED",
    "deleted_at": "2025-09-25T10:15:00"
  }
}
```

---

### 6. Search Specimens
- **Endpoint:** `GET /specimens/search/?specimen_id=`
- **Description:** Search specimens by `specimen_id` (case-insensitive partial match).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/specimens/search/?specimen_id=SP-002`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6531e3...",
      "specimen_id": "SP-002-UPDATED",
      "created_at": "2025-09-25T10:05:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "specimen_id": "SP-002"
  }
}
```

---

### 7. Specimen Statistics
- **Endpoint:** `GET /specimens/stats/`
- **Description:** Returns statistics on specimens (total count).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/specimens/stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_specimens": 2
  }
}
```

---

### 8. Bulk Delete Specimens
- **Endpoint:** `DELETE /specimens/bulk-delete/`
- **Description:** Bulk delete multiple specimens by `specimen_id`.
- **Sample Request:**
    - Method: DELETE
    - URL: `http://localhost:8000/specimens/bulk-delete/`
    - Body (JSON):
```json
{
  "specimen_ids": ["SP-001", "SP-002-UPDATED"]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Bulk delete completed. Deleted 2 specimens.",
  "results": {
    "requested_ids": ["SP-001", "SP-002-UPDATED"],
    "total_requested": 2,
    "total_deleted": 2,
    "not_found_count": 0
  }
}
```

---

## Sample Data
- **specimen_id:** Must be unique for each specimen.

### Example Specimen Document
```json
{
  "specimen_id": "SP-001"
}
```

---

## Troubleshooting
- **Validation Errors:** Ensure all required fields are provided and IDs are valid.
- **Unique Constraint:** `specimen_id` must be unique.
- **Date Fields:** Dates are in ISO format.

---

*For any issues, check the API error messages for details. If you need more help, review the backend code or contact the development team.*
