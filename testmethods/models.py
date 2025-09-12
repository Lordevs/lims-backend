from mongoengine import Document, fields
from datetime import datetime


class TestMethod(Document):
    """
    Test Method model for managing laboratory test methods
    """
    # Core identification fields
    test_name = fields.StringField(max_length=500, required=True)  # e.g., "Adhesion Test ASTM F1281"
    test_description = fields.StringField()  # Detailed description of the test
    
    # Test configuration
    test_columns = fields.ListField(fields.StringField(max_length=100))  # Array of column names
    hasImage = fields.BooleanField(default=False)  # Whether test supports images
    
    # Legacy/migration fields
    # old_key = fields.StringField(max_length=100)  # For data migration purposes
    
    # Timestamps
    createdAt = fields.DateTimeField(default=datetime.now)
    updatedAt = fields.DateTimeField(default=datetime.now)
    
    # System fields
    is_active = fields.BooleanField(default=True)
    
    meta = {
        'collection': 'test_methods',
        'indexes': ['test_name', 'is_active']
    }
    
    def save(self, *args, **kwargs):
        self.updatedAt = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.test_name}"
