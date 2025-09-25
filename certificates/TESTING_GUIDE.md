# Certificates Module - Postman Testing Guide

This guide provides a comprehensive walkthrough for testing the **Certificates** module of your LIMS backend using Postman. It covers all available API endpoints, required input data, and sample responses for each operation.

---

## Table of Contents
1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
    - [List All Certificates](#1-list-all-certificates)
    - [Create a New Certificate](#2-create-a-new-certificate)
    - [Get Certificate Details](#3-get-certificate-details)
    - [Update a Certificate](#4-update-a-certificate)
    - [Delete a Certificate](#5-delete-a-certificate)
    - [Search Certificates](#6-search-certificates)
    - [Certificate Statistics](#7-certificate-statistics)
    - [Get Certificates by Request](#8-get-certificates-by-request)
5. [Sample Data](#sample-data)
6. [Troubleshooting](#troubleshooting)

---

## Overview
The Certificates module manages laboratory test certificates, each linked to a sample preparation request. This guide helps you test all CRUD and search operations using Postman.

## Base URL
```
http://<your-server>/certificates/
```
Replace `<your-server>` with your actual server address (e.g., `localhost:8000`).

## Authentication
*If your API requires authentication, add the necessary headers or tokens in Postman. (Not covered here if not required.)*

---

## Endpoints

### 1. List All Certificates
- **Endpoint:** `GET /certificates/`
- **Description:** Returns all certificates with sample preparation info.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificates/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6541e2...",
      "certificate_id": "CERT-2025-0001",
      "date_of_sampling": "2025-09-20",
      "date_of_testing": "2025-09-22",
      "issue_date": "2025-09-25",
      "revision_no": "1",
      "customers_name_no": "Acme Corp",
      "atten": "QA Manager",
      "customer_po": "PO-1234",
      "tested_by": "John Doe",
      "reviewed_by": "Jane Smith",
      "request_info": {
        "request_id": "6521e2...",
        "request_no": "REQ-2025-0002",
        "sample_lots_count": 1,
        "total_specimens": 2,
        "sample_lots": [],
        "specimens": []
      },
      "created_at": "2025-09-25T10:00:00",
      "updated_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 2. Create a New Certificate
- **Endpoint:** `POST /certificates/`
- **Description:** Creates a new certificate. `certificate_id` is auto-generated if not provided.
- **Required Fields:** `request_id` (ObjectId of SamplePreparation)
- **Optional Fields:** `date_of_sampling`, `date_of_testing`, `issue_date`, `revision_no`, `customers_name_no`, `atten`, `customer_po`, `tested_by`, `reviewed_by`
- **Sample Request:**
    - Method: POST
    - URL: `http://localhost:8000/certificates/`
    - Body (JSON):
```json
{
  "request_id": "6521e2...",
  "date_of_sampling": "2025-09-20",
  "date_of_testing": "2025-09-22",
  "issue_date": "2025-09-25",
  "revision_no": "1",
  "customers_name_no": "Acme Corp",
  "atten": "QA Manager",
  "customer_po": "PO-1234",
  "tested_by": "John Doe",
  "reviewed_by": "Jane Smith"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Certificate created successfully",
  "data": {
    "id": "6541e2...",
    "certificate_id": "CERT-2025-0002",
    "request_no": "REQ-2025-0002",
    "customers_name_no": "Acme Corp"
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

### 3. Get Certificate Details
- **Endpoint:** `GET /certificates/<certificate_id>/`
- **Description:** Returns details for a specific certificate, including sample preparation info.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificates/CERT-2025-0002/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "id": "6541e2...",
    "certificate_id": "CERT-2025-0002",
    "date_of_sampling": "2025-09-20",
    "date_of_testing": "2025-09-22",
    "issue_date": "2025-09-25",
    "revision_no": "1",
    "customers_name_no": "Acme Corp",
    "atten": "QA Manager",
    "customer_po": "PO-1234",
    "tested_by": "John Doe",
    "reviewed_by": "Jane Smith",
    "request_info": {
      "request_id": "6521e2...",
      "request_no": "REQ-2025-0002",
      "sample_lots_count": 1,
      "total_specimens": 2,
      "sample_lots": [],
      "specimens": []
    },
    "created_at": "2025-09-25T10:00:00",
    "updated_at": "2025-09-25T10:00:00"
  }
}
```

---

### 4. Update a Certificate
- **Endpoint:** `PUT /certificates/<certificate_id>/`
- **Description:** Updates fields for a specific certificate (partial update supported).
- **Sample Request:**
    - Method: PUT
    - URL: `http://localhost:8000/certificates/CERT-2025-0002/`
    - Body (JSON):
```json
{
  "revision_no": "2",
  "reviewed_by": "Dr. Jane Smith"
}
```
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Certificate updated successfully"
}
```

---

### 5. Delete a Certificate
- **Endpoint:** `DELETE /certificates/<certificate_id>/`
- **Description:** Deletes a certificate.
- **Sample Request:**
    - Method: DELETE
    - URL: `http://localhost:8000/certificates/CERT-2025-0002/`
- **Sample Response:**
```json
{
  "status": "success",
  "message": "Certificate deleted successfully",
  "data": {
    "certificate_id": "CERT-2025-0002",
    "deleted_at": "2025-09-25T10:15:00"
  }
}
```

---

### 6. Search Certificates
- **Endpoint:** `GET /certificates/search/?certificate_id=&customers_name_no=&tested_by=&issue_date=`
- **Description:** Search certificates by certificate ID, customer name/number, tester, or issue date.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificates/search/?certificate_id=CERT-2025&customers_name_no=Acme&tested_by=John&issue_date=2025-09-25`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6541e2...",
      "certificate_id": "CERT-2025-0002",
      "customers_name_no": "Acme Corp",
      "issue_date": "2025-09-25",
      "tested_by": "John Doe",
      "reviewed_by": "Jane Smith",
      "request_no": "REQ-2025-0002",
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "filters_applied": {
    "certificate_id": "CERT-2025",
    "customers_name_no": "Acme",
    "tested_by": "John",
    "issue_date": "2025-09-25"
  }
}
```

---

### 7. Certificate Statistics
- **Endpoint:** `GET /certificates/stats/`
- **Description:** Returns statistics on certificates (total, by month, by tester).
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificates/stats/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": {
    "total_certificates": 2,
    "monthly_issue_stats": [
      { "_id": "2025-09", "count": 2 }
    ],
    "tester_distribution": [
      { "_id": "John Doe", "count": 2 }
    ]
  }
}
```

---

### 8. Get Certificates by Request
- **Endpoint:** `GET /certificates/request/<request_no>/`
- **Description:** Returns all certificates for a specific sample preparation request.
- **Sample Request:**
    - Method: GET
    - URL: `http://localhost:8000/certificates/request/REQ-2025-0002/`
- **Sample Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "6541e2...",
      "certificate_id": "CERT-2025-0002",
      "issue_date": "2025-09-25",
      "customers_name_no": "Acme Corp",
      "tested_by": "John Doe",
      "reviewed_by": "Jane Smith",
      "created_at": "2025-09-25T10:00:00"
    }
  ],
  "total": 1,
  "request_info": {
    "request_no": "REQ-2025-0002",
    "sample_lots_count": 1,
    "total_specimens": 2
  }
}
```

---

## Sample Data
- **request_id:** Use a valid SamplePreparation ObjectId from your database.
- **certificate_id:** Must be unique if provided (auto-generated if not).

### Example Certificate Document
```json
{
  "certificate_id": "CERT-2025-0002",
  "request_id": "6521e2...",
  "date_of_sampling": "2025-09-20",
  "date_of_testing": "2025-09-22",
  "issue_date": "2025-09-25",
  "customers_name_no": "Acme Corp"
}
```

---

## Troubleshooting
- **Validation Errors:** Ensure all required fields are provided and IDs are valid ObjectIds.
- **Unique Constraint:** `certificate_id` must be unique (auto-generated if not provided).
- **Date Fields:** Dates are in ISO format (YYYY-MM-DD).

---

*For any issues, check the API error messages for details. If you need more help, review the backend code or contact the development team.*
