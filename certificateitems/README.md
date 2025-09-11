# Certificate Items API Documentation

## Overview

The Certificate Items system provides comprehensive CRUD operations for managing detailed test results against certificates. Each certificate item represents specimen testing data with detailed test results, equipment information, and environmental conditions.

## Key Features

### Data Structure Analysis
- **Certificate Items**: Detailed test results for specific specimens against certificates
- **Multiple Items per Certificate**: One certificate can have multiple items for different tests/specimens
- **Complex Test Data**: JSON-formatted test results with flexible data structure
- **Image Support**: Multiple images per specimen with captions
- **Strong Relationships**: Validated references to certificates and specimens
- **Environmental Data**: Temperature, humidity, equipment calibration details

### Relationships
- **Certificate Items ↔ Certificates**: Many-to-One (multiple items can share same certificate_id)
- **Certificate Items ↔ Specimens**: Many-to-Many through specimen_sections
- **Specimen Sections ↔ Images**: One-to-Many embedded relationship

## API Endpoints

### Base URL
All endpoints are prefixed with: `/api/certificate-items/`

### 1. List/Create Certificate Items
**Endpoint**: `GET/POST /api/certificate-items/`

#### GET - List Certificate Items
Returns all active certificate items with relationship data and test result summaries.

**Query Parameters**:
- `certificate_id` (optional): Filter by specific certificate ID
- `material_grade` (optional): Filter by material grade (partial match)

**Response Example**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "68c2ea3a89096bba01165a4b",
      "certificate_id": "CERT-2025-0195",
      "certificate_info": {
        "certificate_id": "CERT-2025-0195",
        "issue_date": "2025-09-11",
        "customers_name_no": "AL-USAIMI STEEL CO - 001"
      },
      "sample_preparation_method": "Cutting & Milling",
      "material_grade": "ASTM A333 Gr.6",
      "temperature": "25",
      "humidity": "31",
      "equipment_name": "Charpy Impact Testing Machine",
      "specimen_sections": [
        {
          "specimen_info": {
            "specimen_id": "68be975f38b66424c8eeebfd",
            "specimen_name": "1000"
          },
          "test_results_count": 1,
          "test_results_summary": [
            {
              "sample_id": "646",
              "test_parameters": [
                "Energy Absorbed Specimen-3 (J)",
                "Dimension",
                "Test Method",
                "Min Requirement",
                "Energy Absorbed Specimen-1 (J)"
              ]
            }
          ],
          "images_count": 1
        }
      ],
      "total_specimens": 1,
      "comments": "Updated: Results are Acceptable as per ASTM A333",
      "created_at": "2025-09-11T15:26:50.357000",
      "updated_at": "2025-09-11T15:28:59.941000"
    }
  ],
  "total": 1,
  "filters_applied": {
    "certificate_id": null,
    "material_grade": null
  }
}
```

#### POST - Create Certificate Item
Creates a new certificate item with specimen testing data.

**Required Fields**:
- `certificate_id`: Must reference existing certificate
- `specimen_sections`: Array of specimen test data

**Request Example**:
```json
{
  "certificate_id": "CERT-2025-0195",
  "sample_preparation_method": "Cutting & Milling",
  "material_grade": "ASTM A333 Gr.6",
  "temperature": "24",
  "humidity": "31",
  "po": "POY 253400601",
  "mtc_no": "NA",
  "heat_no": "037890",
  "comments": "Results are Acceptable as per ASTM A333 and 01-SAMSS-43",
  "equipment_name": "Charpy Impact Testing Machine",
  "equipment_calibration": "2025-12-01",
  "specimen_sections": [
    {
      "test_results": "[{\"data\": {\"Energy Absorbed Specimen-3 (J)\": \"301\", \"Dimension\": \"10*10*55 MM\", \"Test Method\": \"A/SA333 & 01-SAMSS-043\", \"Min Requirement\": \"34 J\", \"Energy Absorbed Specimen-1 (J)\": \"300\", \"Energy Absorbed Specimen-2 (J)\": \"301\", \"Position\": \"Longitudinal\", \"Average (J)\": \"300.6\", \"Test Temp (°C)\": \"-45\", \"Sample ID\": \"646\"}}]",
      "specimen_id": "68be975f38b66424c8eeebfd",
      "images_list": [
        {
          "image_url": "https://example.com/test-image.jpg",
          "caption": "Test result image"
        }
      ]
    }
  ]
}
```

### 2. Certificate Item Details
**Endpoint**: `GET/PUT/DELETE /api/certificate-items/{item_id}/`

#### GET - Get Certificate Item Details
Returns complete certificate item data with full test results and relationship information.

**Response Example**:
```json
{
  "status": "success",
  "data": {
    "id": "68c2ea3a89096bba01165a4b",
    "certificate_id": "CERT-2025-0195",
    "certificate_info": {
      "certificate_id": "CERT-2025-0195",
      "issue_date": "2025-09-11",
      "customers_name_no": "AL-USAIMI STEEL CO - 001",
      "date_of_sampling": "2025-07-07",
      "date_of_testing": "2025-09-10"
    },
    "sample_preparation_method": "Cutting & Milling",
    "material_grade": "ASTM A333 Gr.6",
    "temperature": "24",
    "humidity": "31",
    "po": "POY 253400601",
    "mtc_no": "NA",
    "heat_no": "037890",
    "comments": "Results are Acceptable as per ASTM A333 and 01-SAMSS-43",
    "specimen_sections": [
      {
        "specimen_info": {
          "specimen_id": "68be975f38b66424c8eeebfd",
          "specimen_name": "1000"
        },
        "test_results": [
          {
            "data": {
              "Energy Absorbed Specimen-3 (J)": "301",
              "Dimension": "10*10*55 MM",
              "Test Method": "A/SA333 & 01-SAMSS-043",
              "Min Requirement": "34 J",
              "Energy Absorbed Specimen-1 (J)": "300",
              "Energy Absorbed Specimen-2 (J)": "301",
              "Position": "Longitudinal",
              "Average (J)": "300.6",
              "Test Temp (°C)": "-45",
              "Sample ID": "646"
            }
          }
        ],
        "images_list": [
          {
            "image_url": "https://example.com/test-image.jpg",
            "caption": "Test result image"
          }
        ]
      }
    ],
    "equipment_name": "Charpy Impact Testing Machine",
    "equipment_calibration": "2025-12-01",
    "total_specimens": 1,
    "created_at": "2025-09-11T15:26:50.357000",
    "updated_at": "2025-09-11T15:26:50.357000"
  }
}
```

#### PUT - Update Certificate Item
Updates certificate item basic information. Note: specimen_sections cannot be updated via PUT.

**Updateable Fields**:
- Basic info: `sample_preparation_method`, `material_grade`, `temperature`, `humidity`
- Business info: `po`, `mtc_no`, `heat_no`, `comments`
- Equipment info: `equipment_name`, `equipment_calibration`
- `certificate_id` (with validation)

#### DELETE - Delete Certificate Item
Performs soft delete by setting `is_active` to false.

### 3. Search Certificate Items
**Endpoint**: `GET /api/certificate-items/search/`

**Query Parameters**:
- `certificate_id`: Exact match on certificate ID
- `material_grade`: Partial match on material grade
- `equipment_name`: Partial match on equipment name
- `specimen_id`: Exact match on specimen ID within sections

### 4. Certificate Items by Certificate
**Endpoint**: `GET /api/certificate-items/certificate/{certificate_id}/`

Returns all certificate items for a specific certificate with summary data.

### 5. Certificate Items Statistics
**Endpoint**: `GET /api/certificate-items/stats/`

**Response Example**:
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
      {"_id": "SA 312 TP 316 L", "count": 1},
      {"_id": "ASTM A333 Gr.6", "count": 1}
    ]
  }
}
```

## Data Validation

### Certificate Validation
- Certificate ID must exist in certificates collection
- Strong referential integrity maintained

### Specimen Validation
- All specimen IDs in specimen_sections must exist
- Individual specimen validation per section

### Test Results Validation
- test_results field must contain valid JSON
- Flexible structure to accommodate various test types

### Image Validation
- Optional images_list with URL and caption
- Multiple images supported per specimen section

## Error Handling

### Common Error Responses
- **400 Bad Request**: Validation errors, invalid JSON, missing required fields
- **404 Not Found**: Invalid certificate/specimen references, item not found
- **500 Internal Server Error**: Database or system errors

### Example Error Response
```json
{
  "status": "error",
  "message": "Certificate with ID INVALID-CERT-ID not found"
}
```

## Advanced Features

### Duplicate Certificate Support
- Multiple certificate items can share the same certificate_id
- Useful for different test types on same certificate
- Different specimens, equipment, or test conditions

### Complex Test Data Structure
- JSON-formatted test_results support any test type
- Flexible schema accommodates various testing standards
- Nested data structures for complex measurements

### Relationship Data Resolution
- Automatic resolution of certificate information
- Specimen name lookup and validation
- Equipment and environmental condition tracking

### Soft Delete Pattern
- Items marked as inactive rather than deleted
- Maintains audit trail and referential integrity
- Can be restored if needed

## Testing Examples

The system has been thoroughly tested with:
- **Material Types**: ASTM A333 Gr.6, ASTM A358 TP 316/316L, SA 312 TP 316 L
- **Test Types**: Charpy Impact, Tensile Testing, Hardness Testing
- **Multiple Specimens**: 2-3 specimens per certificate item
- **Image Attachments**: URL-based image storage with captions
- **Equipment Tracking**: Various testing machines with calibration dates

## Performance Considerations

### Indexing Strategy
- `certificate_id`: Fast lookup by certificate
- `material_grade`: Efficient material-based searches
- `specimen_sections.specimen_id`: Quick specimen-based queries
- `created_at`, `is_active`: Timeline and active record queries

### Data Size Optimization
- Test results stored as JSON strings (efficient storage)
- Image references stored as URLs (not binary data)
- Pagination support for large datasets

This Certificate Items system provides a robust, flexible foundation for managing detailed laboratory test results while maintaining strong data integrity and comprehensive relationship tracking.