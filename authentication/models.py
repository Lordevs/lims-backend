from mongoengine import Document, fields
from datetime import datetime
import hashlib
import secrets


class User(Document):
    """
    User model for authentication and authorization
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('project_coordinator', 'Project Coordinator'),
        ('lab_engg', 'Lab Engineer'),
    ]
    
    username = fields.StringField(max_length=100, unique=True, required=True)
    email = fields.EmailField(unique=True, required=True)
    password_hash = fields.StringField(required=True)
    first_name = fields.StringField(max_length=100, required=True)
    last_name = fields.StringField(max_length=100, required=True)
    role = fields.StringField(choices=ROLE_CHOICES, required=True)
    is_active = fields.BooleanField(default=True)
    is_verified = fields.BooleanField(default=False)
    last_login = fields.DateTimeField()
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'users',
        'indexes': [
            'username',
            'email',
            'role',
            'is_active',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def set_password(self, password):
        """Hash and set password"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        self.password_hash = f"{salt}:{password_hash.hex()}"
    
    def check_password(self, password):
        """Check if provided password matches stored hash"""
        if ':' not in self.password_hash:
            return False
        
        salt, stored_hash = self.password_hash.split(':', 1)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex() == stored_hash
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name()}) - {self.role}"


class RefreshToken(Document):
    """
    Refresh token model for JWT token management
    """
    user = fields.ReferenceField(User, required=True)
    token = fields.StringField(required=True, unique=True)
    expires_at = fields.DateTimeField(required=True)
    is_revoked = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'refresh_tokens',
        'indexes': [
            'user',
            'token',
            'expires_at',
            'is_revoked',
            'created_at'
        ]
    }
    
    def is_valid(self):
        """Check if refresh token is valid"""
        return not self.is_revoked and self.expires_at > datetime.now()
    
    def __str__(self):
        return f"RefreshToken for {self.user.username} - {'Valid' if self.is_valid() else 'Invalid'}"