from mongoengine import Document, fields
from datetime import datetime


class Equipment(Document):
    """
    Lab Equipment model for managing laboratory equipment
    """
    # Core identification fields
    equipment_name = fields.StringField(max_length=200, required=True)
    equipment_serial = fields.StringField(max_length=100, required=True, unique=True)
    
    # Equipment status and verification
    status = fields.StringField(
        max_length=50, 
        required=True,
        default='Active'
    )
    
    # Verification and maintenance tracking
    last_verification = fields.DateTimeField()
    verification_due = fields.DateTimeField()
    
    # User tracking
    created_by = fields.StringField(max_length=100, required=True)
    updated_by = fields.StringField(max_length=100)
    
    # Additional information
    remarks = fields.StringField()
    
    # System fields
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'equipment',
        'indexes': [
            'equipment_name',
            'equipment_serial',
            'status',
            'is_active',
            'verification_due',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def is_verification_due(self):
        """Check if equipment verification is due"""
        if not self.verification_due:
            return False
        return datetime.now() > self.verification_due
    
    def days_until_verification_due(self):
        """Get number of days until verification is due"""
        if not self.verification_due:
            return None
        delta = self.verification_due - datetime.now()
        return delta.days
    
    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_serial})"