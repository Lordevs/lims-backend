from mongoengine import Document, fields
from datetime import datetime
from bson import ObjectId


class WelderCard(Document):
    """
    Welder qualification card model for managing welder qualification cards
    """
    company = fields.StringField(max_length=200, required=True)
    welder_id = fields.ObjectIdField(required=True)  # Reference to Welder._id
    authorized_by = fields.StringField(max_length=100, required=True)
    welding_inspector = fields.StringField(max_length=100, required=True)
    law_name = fields.StringField(max_length=200, required=True)
    card_no = fields.StringField(max_length=100, required=True)
    attributes = fields.DictField()  # JSON field for flexible attributes
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'welder_cards',
        'indexes': ['welder_id', 'card_no', 'company', 'is_active', 'created_at']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.card_no} - {self.company}"