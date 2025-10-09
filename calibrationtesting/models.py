from mongoengine import Document, fields
from datetime import datetime


class CalibrationTest(Document):
    calibration_certification = fields.StringField(max_length=200, required=True)
    calibration_date = fields.DateTimeField(required=True)
    calibration_due_date = fields.DateTimeField(required=True)
    calibration_vendor = fields.StringField(max_length=200, required=True)
    created_by = fields.StringField(max_length=100, required=True)
    equipment_name = fields.StringField(max_length=200, required=True)
    equipment_serial = fields.StringField(max_length=100, required=True)
    is_active = fields.BooleanField(default=True)
    remarks = fields.StringField(max_length=1000)
    updated_by = fields.StringField(max_length=100)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        'collection': 'calibration_tests',
        'indexes': [
            'calibration_certification', 'calibration_date', 'calibration_due_date', 
            'calibration_vendor', 'equipment_name', 'equipment_serial', 'is_active', 'created_at'
        ]
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def is_overdue(self):
        """Check if the calibration is overdue"""
        if self.calibration_due_date and datetime.now() > self.calibration_due_date:
            return True
        return False

    def days_until_due(self):
        """Calculate days until calibration due date"""
        if self.calibration_due_date:
            delta = self.calibration_due_date - datetime.now()
            return delta.days
        return None

    def days_since_calibration(self):
        """Calculate days since last calibration"""
        if self.calibration_date:
            delta = datetime.now() - self.calibration_date
            return delta.days
        return None

    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_serial}) - {self.calibration_certification}"