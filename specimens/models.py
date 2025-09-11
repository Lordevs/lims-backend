from mongoengine import Document, fields
from datetime import datetime


class Specimen(Document):
    """
    Specimen model for managing laboratory specimens
    Simple model with only specimen_id - each specimen_id must be unique
    """
    specimen_id = fields.StringField(max_length=100, unique=True, required=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'specimens',
        'indexes': ['specimen_id']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Specimen {self.specimen_id}"
