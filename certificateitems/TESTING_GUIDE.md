# Certificate Items Module - Postman Testing Guide

This guide provides a comprehensive walkthrough for testing the **Certificate Items** module of your LIMS backend using Postman. It covers all available API endpoints, required input data, and sample responses for each operation.

---

## Table of Contents
1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
    - [List All Certificate Items](#1-list-all-certificate-items)
    - [Create a New Certificate Item](#2-create-a-new-certificate-item)
    - [Get Certificate Item Details](#3-get-certificate-item-details)
    - [Update a Certificate Item](#4-update-a-certificate-item)
    - [Delete a Certificate Item](#5-delete-a-certificate-item)
    - [Search Certificate Items](#6-search-certificate-items)
    - [Certificate Item Statistics](#7-certificate-item-statistics)
    - [Get Items by Certificate](#8-get-items-by-certificate)
5. [Sample Data](#sample-data)
6. [Troubleshooting](#troubleshooting)

---

## Overview
The Certificate Items module manages detailed test results for certificates, linking certificates with specimens and storing test data, images, and equipment info. This guide helps you test all CRUD and search operations using Postman.

## Base URL
```
http://<your-server>/certificateitems/
```
Replace `<your-server>` with your actual server address (e.g., `localhost:8000`).

## Authentication
*If your API requires authentication, add the necessary headers or tokens in Postman. (Not covered here if not required.)*

---

## Endpoints

### 1. List All Certificate Items
- **Endpoint:** `GET /certificateitems/`
- **Description:** Returns all active certificate items with related data.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificateitems/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6551e2...",
      "certificate_id": "6531e2...",
      "material_grade": "SS304",
      "specimen_sections": [
        {
          "specimen_id": "6531e3...",
          "test_results": "{\"tensile\": 500}",
          "equipment_name": "Instron 3369",
          "images_list": [
            { "image_url": "http://.../img1.jpg", "caption": "Fracture" }
          ]
        }
      ],
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "certificate_id": null,
    "material_grade": null
  }
}
```

---

### 2. Create a New Certificate Item
- **Endpoint:** `POST /certificateitems/`
- **Description:** Creates a new certificate item.
- **Required Fields:** `certificate_id` (ObjectId), `specimen_sections` (array)
- **Sample Request:**
    - Method: POST
    - URL: `http://localhost:8000/certificateitems/`
    - Body (JSON):
```json
{
  "certificate_id": "6531e2...",
  "sample_preparation_method": "Cut & polish",
  "material_grade": "SS304",
  "temperature": "25C",
  "humidity": "60%",
  "po": "PO-1234",
  "mtc_no": "MTC-001",
  "heat_no": "H1234",
  "comments": "All tests passed",
  "specimen_sections": [
    {
      "specimen_id": "6531e3...",
      "test_results": "{\"tensile\": 500}",
      "equipment_name": "Instron 3369",
      "equipment_calibration": "2025-01-01",
      "images_list": [
        { "image_url": "http://.../img1.jpg", "caption": "Fracture" }
      ]
    }
  ]
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Certificate item created successfully",
  "data": {
    "id": "6551e2...",
    "certificate_id": "6531e2...",
    "specimen_sections_count": 1,
    "material_grade": "SS304"
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

### 3. Get Certificate Item Details
- **Endpoint:** `GET /certificateitems/<item_id>/`
- **Description:** Returns details for a specific certificate item, including specimen sections and certificate info.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificateitems/6551e2.../`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6551e2...",
    "certificate_id": "6531e2...",
    "certificate_info": {
      "certificate_id": "6531e2...",
      "issue_date": "2025-09-25",
      "customers_name_no": "Acme Corp",
      "date_of_sampling": "2025-09-20",
      "date_of_testing": "2025-09-22"
    },
    "sample_preparation_method": "Cut & polish",
    "material_grade": "SS304",
    "temperature": "25C",
    "humidity": "60%",
    "po": "PO-1234",
    "mtc_no": "MTC-001",
    "heat_no": "H1234",
    "comments": "All tests passed",
    "specimen_sections": [
      {
        "specimen_id": "6531e3...",
        "test_results": "{\"tensile\": 500}",
        "equipment_name": "Instron 3369",
        "equipment_calibration": "2025-01-01",
        "images_list": [
          { "image_url": "http://.../img1.jpg", "caption": "Fracture" }
        ]
      }
    ],
    "total_specimens": 1,
    "created_at": "2025-09-25T10:00:00",
    "updated_at": "2025-09-25T10:00:00"
  }
}
```

---

### 4. Update a Certificate Item
- **Endpoint:** `PUT /certificateitems/<item_id>/`
- **Description:** Updates fields for a specific certificate item (partial update supported).
- **Sample Request:**
    - Method: PUT
    - URL: `http://localhost:8000/certificateitems/6551e2.../`
    - Body (JSON):
```json
{
  "comments": "Updated comments"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Certificate item updated successfully"
}
```

---

### 5. Delete a Certificate Item
- **Endpoint:** `DELETE /certificateitems/<item_id>/`
- **Description:** Soft deletes a certificate item (sets `is_active` to false).
- **Sample Request:**
    - Method: DELETE
    - URL: `http://localhost:8000/certificateitems/6551e2.../`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Certificate item deleted successfully",
  "data": {
    "id": "6551e2...",
    "deleted_at": "2025-09-25T10:15:00"
  }
}
```

---

### 6. Search Certificate Items
- **Endpoint:** `GET /certificateitems/search/?certificate_id=&material_grade=&specimen_id=`
- **Description:** Search certificate items by certificate, material grade, or specimen.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificateitems/search/?material_grade=SS304`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6551e2...",
      "certificate_id": "6531e2...",
      "material_grade": "SS304",
      "specimen_count": 1,
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "certificate_id": "",
    "material_grade": "SS304",
    "specimen_id": ""
  }
}
```

---

### 7. Certificate Item Statistics
- **Endpoint:** `GET /certificateitems/stats/`
- **Description:** Returns statistics on certificate items (total, specimens, images, averages, top materials).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificateitems/stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_certificate_items": 2,
    "total_specimens_tested": 3,
    "total_images_attached": 2,
    "avg_specimens_per_item": 1.5,
    "unique_certificates_count": 2,
    "unique_materials_count": 2,
    "top_materials": [
      { "_id": "SS304", "count": 1 },
      { "_id": "SS316", "count": 1 }
    ]
  }
}
```

---

### 8. Get Items by Certificate
- **Endpoint:** `GET /certificateitems/certificate/<certificate_id>/`
- **Description:** Returns all certificate items for a specific certificate.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificateitems/certificate/CERT-2025-0002/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6551e2...",
      "certificate_id": "6531e2...",
      "material_grade": "SS304",
      "specimen_count": 1,
      "images_count": 1,
      "comments": "All tests passed",
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "certificate_id": "CERT-2025-0002"
}
```

---

## Sample Data
- **certificate_id:** Use a valid Certificate ObjectId from your database.
- **specimen_id:** Use a valid Specimen ObjectId.
- **specimen_sections:** Must be a non-empty array.

### Example SpecimenSection
```json
{
  "specimen_id": "6531e3...",
  "test_results": "{\"tensile\": 500}",
  "equipment_name": "Instron 3369",
  "equipment_calibration": "2025-01-01",
  "images_list": [
    { "image_url": "http://.../img1.jpg", "caption": "Fracture" }
  ]
}
```

---

## Troubleshooting
- **Validation Errors:** Ensure all required fields are provided and IDs are valid ObjectIds.
- **Array Fields:** `specimen_sections` must be a non-empty array.
- **Date Fields:** Dates are in ISO format.

---

*For any issues, check the API error messages for details. If you need more help, review the backend code or contact the development team.*
