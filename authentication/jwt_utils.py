import jwt
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from .models import RefreshToken


# JWT Configuration
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', secrets.token_urlsafe(32))
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 5  # 5 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days


def generate_access_token(user):
    """
    Generate JWT access token for user
    """
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def generate_refresh_token(user):
    """
    Generate refresh token for user
    """
    # Generate random token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create refresh token document
    refresh_token = RefreshToken(
        user=user,
        token=token,
        expires_at=expires_at
    )
    refresh_token.save()
    
    return token, expires_at


def verify_access_token(token):
    """
    Verify and decode JWT access token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check token type
        if payload.get('type') != 'access':
            return None
        
        # Check expiration
        if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token):
    """
    Verify refresh token
    """
    try:
        refresh_token = RefreshToken.objects.get(token=token)
        
        if refresh_token.is_valid():
            return refresh_token
        else:
            return None
    except RefreshToken.DoesNotExist:
        return None


def revoke_refresh_token(token):
    """
    Revoke a refresh token
    """
    try:
        refresh_token = RefreshToken.objects.get(token=token)
        refresh_token.is_revoked = True
        refresh_token.save()
        return True
    except RefreshToken.DoesNotExist:
        return False


def revoke_all_user_tokens(user):
    """
    Revoke all refresh tokens for a user
    """
    RefreshToken.objects(user=user, is_revoked=False).update(set__is_revoked=True)


def cleanup_expired_tokens():
    """
    Clean up expired refresh tokens
    """
    expired_tokens = RefreshToken.objects(expires_at__lt=datetime.utcnow())
    count = expired_tokens.count()
    expired_tokens.delete()
    return count
