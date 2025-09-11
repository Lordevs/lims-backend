from mongoengine import Document, fields
from datetime import datetime


class Client(Document):
    """
    Client model for managing client information
    """
    client_id = fields.StringField(max_length=100, unique=True, required=True)
    client_name = fields.StringField(max_length=200, required=True)
    company_name = fields.StringField(max_length=200)
    email = fields.EmailField(required=True)
    phone = fields.StringField(max_length=20, required=True)
    address = fields.StringField(required=True)
    contact_person = fields.StringField(max_length=100, required=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'clients',
        'indexes': ['client_id', 'is_active', 'email']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.client_id} - {self.client_name}"
