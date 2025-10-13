from mongoengine import Document, fields
from datetime import datetime


class Welder(Document):
    """
    Welder model for managing welder/operator information
    """
    operator_name = fields.StringField(max_length=200, required=True)
    operator_id = fields.StringField(max_length=100, unique=True, required=True)
    iqama = fields.StringField(max_length=50, required=True)
    profile_image = fields.StringField(max_length=500)  # Path to image file
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'welders',
        'indexes': ['operator_id', 'iqama', 'is_active', 'created_at']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.operator_id} - {self.operator_name}"