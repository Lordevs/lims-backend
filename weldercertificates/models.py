from mongoengine import Document, fields, EmbeddedDocument
from datetime import datetime
from bson import ObjectId


class TestResult(EmbeddedDocument):
    """
    Embedded document for test results within welder certificates
    """
    type = fields.StringField(max_length=100, required=True)
    test_performed = fields.BooleanField(required=True)
    results = fields.StringField(max_length=500)
    report_no = fields.StringField(max_length=100)


class TestingVariable(EmbeddedDocument):
    """
    Embedded document for testing variables and qualification limits
    """
    name = fields.StringField(max_length=200, required=True)
    actual_values = fields.StringField(max_length=200, required=True)
    range_values = fields.StringField(max_length=200, required=True)


class WelderCertificate(Document):
    """
    Welder operator qualification certificate model
    """
    welder_card_id = fields.ObjectIdField(required=True)  # Reference to WelderCard._id
    date_of_test = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format)
    identification_of_wps_pqr = fields.StringField(max_length=200)
    qualification_standard = fields.StringField(max_length=200)
    base_metal_specification = fields.StringField(max_length=200)
    joint_type = fields.StringField(max_length=100)
    weld_type = fields.StringField(max_length=100)
    testing_variables_and_qualification_limits = fields.ListField(fields.EmbeddedDocumentField(TestingVariable))  # Array of testing variables
    tests = fields.ListField(fields.EmbeddedDocumentField(TestResult), required=True)
    law_name = fields.StringField(max_length=200, required=True)
    tested_by = fields.StringField(max_length=100, required=True)
    witnessed_by = fields.StringField(max_length=100, required=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'welder_certificates',
        'indexes': [
            'welder_card_id', 
            'date_of_test', 
            'qualification_standard',
            'law_name',
            'tested_by',
            'is_active',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Certificate - {self.law_name} ({self.date_of_test})"