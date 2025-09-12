from mongoengine import Document, fields, EmbeddedDocument
from datetime import datetime
from bson import ObjectId


class SampleLotInfo(EmbeddedDocument):
    """
    Embedded document for sample lot information within sample preparation
    """
    item_description = fields.StringField(max_length=500, required=True)
    planned_test_date = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format) or null
    dimension_spec = fields.StringField(max_length=200)  # Dimension specifications or null
    request_by = fields.StringField(max_length=100)  # Can be null
    remarks = fields.StringField()  # Can be null
    request_id = fields.ObjectIdField(required=True)  # Reference to SampleLot._id (stored as sample_lot_id in MongoDB)
    test_method_oid = fields.ObjectIdField(required=True)  # Reference to TestMethod._id
    specimen_oids = fields.ListField(fields.ObjectIdField(), required=True)  # List of Specimen._id references


class SamplePreparation(Document):
    """
    Sample Preparation model for managing laboratory sample preparations
    Links Sample Lots, Test Methods, and Specimens together
    """
    request_no = fields.StringField(max_length=100, unique=True)  # Auto-generated if not provided
    sample_lots = fields.ListField(fields.EmbeddedDocumentField(SampleLotInfo), required=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'sample_preparations',
        'indexes': ['request_no', 'created_at']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.request_no} - {len(self.sample_lots)} sample lots"
