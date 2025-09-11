from mongoengine import Document, fields
from datetime import datetime
from bson import ObjectId


class Certificate(Document):
    """
    Certificate model for managing laboratory test certificates
    Each certificate is linked to a sample preparation request
    """
    # Core identification
    certificate_id = fields.StringField(max_length=100, unique=True, required=True)  # e.g., "CERT-2025-0195"
    
    # Date fields
    date_of_sampling = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format)
    date_of_testing = fields.StringField(max_length=20)   # Date as string (YYYY-MM-DD format)
    issue_date = fields.StringField(max_length=20)       # Date as string (YYYY-MM-DD format)
    
    # Certificate details
    revision_no = fields.StringField(max_length=50)      # Revision number
    customers_name_no = fields.StringField(max_length=200)  # Customer name/number
    atten = fields.StringField(max_length=200)           # Attention field
    customer_po = fields.StringField(max_length=100)     # Customer purchase order
    
    # Personnel
    tested_by = fields.StringField(max_length=100)       # Person who conducted the test
    reviewed_by = fields.StringField(max_length=100)     # Person who reviewed the certificate
    
    # Relationship to sample preparation
    request_id = fields.ObjectIdField(required=True)     # Reference to SamplePreparation._id
    
    # System fields
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'certificates',
        'indexes': ['certificate_id', 'request_id', 'issue_date', 'is_active']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.certificate_id} - {self.customers_name_no}"
