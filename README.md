# LIMS Backend - Django with MongoDB

A Laboratory Information Management System (LIMS) backend built with Django and MongoDB integration using Djongo and PyMongo.

## Features

- Django REST API endpoints for laboratory data management
- MongoDB integration using Djongo ORM and direct PyMongo connections
- Sample management (create, read, update, delete)
- Test results management
- Laboratory information management
- Database statistics and health check endpoints
- Environment-based configuration

## Project Structure

```
lims-v3/backend/
├── core/                    # Main application
│   ├── models.py           # MongoDB models (Sample, TestResult, Laboratory)
│   ├── views.py            # API endpoints
│   ├── urls.py             # URL routing
│   └── mongodb.py          # Direct MongoDB connection utilities
├── lims_backend/           # Django project settings
│   ├── settings.py         # Django configuration with MongoDB
│   └── urls.py             # Main URL configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .env.example           # Environment variables template
└── manage.py              # Django management script
```

## Installation

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your MongoDB configuration
   ```

4. **Ensure MongoDB is running:**
   - Install MongoDB locally or use MongoDB Atlas
   - Update MONGODB_URI in .env file

5. **Run migrations (if needed):**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Health Check
- `GET /api/` - Health check endpoint

### Samples
- `GET /api/samples/` - List all samples
- `POST /api/samples/` - Create a new sample
- `GET /api/samples/{sample_id}/` - Get sample details
- `PUT /api/samples/{sample_id}/` - Update sample
- `DELETE /api/samples/{sample_id}/` - Delete sample

### Test Results
- `GET /api/test-results/` - List all test results
- `POST /api/test-results/` - Create a new test result

### Statistics
- `GET /api/stats/` - Get database statistics

## Sample API Usage

### Create a Sample
```bash
curl -X POST http://localhost:8000/api/samples/ \
  -H "Content-Type: application/json" \
  -d '{
    "sample_id": "SAMP001",
    "sample_name": "Blood Sample 1",
    "sample_type": "Blood",
    "location": "Lab Room A",
    "collected_by": "Dr. Smith",
    "notes": "Morning collection"
  }'
```

### Get Sample Details
```bash
curl http://localhost:8000/api/samples/SAMP001/
```

### Create a Test Result
```bash
curl -X POST http://localhost:8000/api/test-results/ \
  -H "Content-Type: application/json" \
  -d '{
    "sample_id": "SAMP001",
    "test_name": "Complete Blood Count",
    "test_type": "Hematology",
    "result_value": "Normal",
    "unit": "cells/μL",
    "tested_by": "Lab Tech 1",
    "tested_at": "2023-11-20T10:30:00"
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| MONGODB_URI | MongoDB connection string | mongodb://localhost:27017 |
| MONGODB_NAME | Database name | lims_db |
| MONGODB_USERNAME | MongoDB username | (empty) |
| MONGODB_PASSWORD | MongoDB password | (empty) |
| MONGODB_AUTH_SOURCE | Authentication source | admin |
| SECRET_KEY | Django secret key | (generated) |
| DEBUG | Debug mode | True |

## Models

### Sample
- Sample ID, name, type
- Collection date, location, collector
- Status tracking and notes

### TestResult
- Linked to Sample
- Test name, type, result value
- Units, reference ranges
- Testing metadata

### Laboratory
- Laboratory information
- Contact details and accreditation
- Active status tracking

## MongoDB Integration

This project uses two approaches for MongoDB integration:

1. **Djongo ORM** - Django-style models and queries
2. **Direct PyMongo** - Raw MongoDB operations for complex queries

## Development

To extend the project:

1. Add new models in `core/models.py`
2. Create corresponding views in `core/views.py`
3. Add URL patterns in `core/urls.py`
4. Update database configuration as needed

## Requirements

- Python 3.8+
- Django 5.2+
- MongoDB 4.4+
- See requirements.txt for full dependency list