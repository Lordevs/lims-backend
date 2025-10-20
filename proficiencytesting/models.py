from mongoengine import Document, fields
from datetime import datetime


class ProficiencyTest(Document):
    description = fields.StringField(max_length=500, required=True)
    due_date = fields.DateTimeField(required=True)
    is_active = fields.BooleanField(default=True)
    last_test_date = fields.DateTimeField()
    next_scheduled_date = fields.DateTimeField()
    provider1 = fields.StringField(max_length=200, required=True)
    provider2 = fields.StringField(max_length=200)
    remarks = fields.StringField(max_length=1000)
    status = fields.StringField(max_length=50, default='Scheduled')
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        'collection': 'proficiency_tests',
        'indexes': [
            'description', 'due_date', 'status', 'is_active', 'provider1', 'provider2', 'created_at'
        ]
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def is_overdue(self):
        """Check if the proficiency test is overdue"""
        if self.due_date and datetime.now() > self.due_date and self.status not in ['Completed', 'Cancelled']:
            return True
        return False

    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date:
            delta = self.due_date - datetime.now()
            return delta.days
        return None

    def __str__(self):
        return f"{self.description} - {self.status} ({self.provider1})"