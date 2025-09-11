from mongoengine import Document, fields
from datetime import datetime
from bson import ObjectId


class SampleLot(Document):
    """
    Sample Lot model for managing laboratory sample lots
    Each sample lot belongs to a job and contains multiple test methods
    """
    job_id = fields.ObjectIdField(required=True)  # Reference to Job._id
    item_no = fields.StringField(max_length=100, unique=True, required=True)
    sample_type = fields.StringField(max_length=100)  # e.g., 'cs', 'stainless steel', 'zinc coated'
    material_type = fields.StringField(max_length=100)  # e.g., 'plate', 'pipe', 'fastner', 'round'
    condition = fields.StringField(max_length=100)  # e.g., 'GOOD', 'HEAT TREATED', 'As welded samples'
    heat_no = fields.StringField(max_length=100)  # heat number
    description = fields.StringField(required=True)  # detailed description
    mtc_no = fields.StringField(max_length=100)  # material test certificate number
    storage_location = fields.StringField(max_length=200)  # where the sample is stored
    test_method_oids = fields.ListField(fields.ObjectIdField())  # References to TestMethod._id
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'sample_lots',
        'indexes': ['job_id', 'item_no', 'sample_type', 'material_type', 'is_active']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.item_no} - {self.sample_type}"
