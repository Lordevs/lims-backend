from mongoengine import Document, fields, EmbeddedDocument
from datetime import datetime
from bson import ObjectId


class PerformanceTestResult(EmbeddedDocument):
    """
    Embedded document for test results within welder performance records
    """
    type = fields.StringField(max_length=100, required=True)
    test_performed = fields.BooleanField(required=True)
    results = fields.StringField(max_length=500)
    report_no = fields.StringField(max_length=100)


class PerformanceTestingVariable(EmbeddedDocument):
    """
    Embedded document for testing variables and qualification limits in performance records
    """
    name = fields.StringField(max_length=200, required=True)
    actual_values = fields.StringField(max_length=200, required=True)
    range_values = fields.StringField(max_length=200, required=True)


class WelderPerformanceRecord(Document):
    """
    Welder operator performance qualification record model
    """
    welder_card_id = fields.ObjectIdField(required=True)  # Reference to WelderCard._id
    wps_followed_date = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format)
    date_of_issue = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format)
    date_of_welding = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format)
    joint_weld_type = fields.StringField(max_length=200)
    base_metal_spec = fields.StringField(max_length=200)
    base_metal_p_no = fields.StringField(max_length=100)
    filler_sfa_spec = fields.StringField(max_length=200)
    filler_class_aws = fields.StringField(max_length=100)
    test_coupon_size = fields.StringField(max_length=200)
    positions = fields.StringField(max_length=200)
    testing_variables_and_qualification_limits_automatic = fields.ListField(fields.EmbeddedDocumentField(PerformanceTestingVariable))  # Array of automatic testing variables
    testing_variables_and_qualification_limits_machine = fields.ListField(fields.EmbeddedDocumentField(PerformanceTestingVariable))  # Array of machine testing variables
    tests = fields.ListField(fields.EmbeddedDocumentField(PerformanceTestResult), required=True)
    law_name = fields.StringField(max_length=200, required=True)
    tested_by = fields.StringField(max_length=100, required=True)
    witnessed_by = fields.StringField(max_length=100, required=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'welder_performance_records',
        'indexes': [
            'welder_card_id', 
            'date_of_welding', 
            'date_of_issue',
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
        return f"Performance Record - {self.law_name} ({self.date_of_welding})"