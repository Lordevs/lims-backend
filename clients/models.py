from mongoengine import Document, fields
from datetime import datetime


class Client(Document):
    """
    Client model for managing client information
    """
    client_id = fields.IntField(unique=True, required=True)
    client_name = fields.StringField(max_length=200, required=True)
    company_name = fields.StringField(max_length=200)
    email = fields.EmailField()
    phone = fields.StringField(max_length=20)
    address = fields.StringField()
    contact_person = fields.StringField(max_length=100)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'clients',
        'indexes': ['client_id', 'is_active', 'email']
    }
    
    def save(self, *args, **kwargs):
        # Auto-generate client_id if not provided
        if not self.client_id:
            self.client_id = self._generate_next_client_id()
        
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def _generate_next_client_id(self):
        """
        Generate the next sequential client ID
        Returns the next integer in sequence starting from 1
        """
        # Get the highest existing client_id
        last_client = Client.objects.order_by('-client_id').first()
        
        if last_client and last_client.client_id:
            # Return the next number in sequence
            return last_client.client_id + 1
        else:
            # If no clients exist, start from 1
            return 1
        
    def __str__(self):
        return f"{self.client_id} - {self.client_name}"
