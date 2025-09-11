from mongoengine import Document, fields
from datetime import datetime


class Job(Document):
    """
    Job model for managing laboratory jobs
    """
    job_id = fields.StringField(max_length=100, unique=True, required=True)
    client_id = fields.ObjectIdField(required=True)  # Reference to Client._id
    project_name = fields.StringField(max_length=200, required=True)
    end_user = fields.StringField(max_length=100)
    receive_date = fields.DateTimeField(required=True)
    received_by = fields.StringField(max_length=100, required=True)
    remarks = fields.StringField()
    job_created_at = fields.DateTimeField(default=datetime.now)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'jobs',
        'indexes': ['job_id', 'client_id', 'receive_date']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.job_id} - {self.project_name}"
